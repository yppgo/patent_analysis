#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重复运行完整流程实验，支持续跑与分批执行。

默认行为：
- 6 个模式 × 默认问题集合 × N 轮重复
- 每次运行独立保存为 outputs/repeated_experiments/experiment_q{n}_{mode}_run{xx}.json
- 已存在结果时自动跳过，便于中断后续跑
"""

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from src.graphs.causal_graph_query import CausalGraphQuery
from src.graphs.method_graph_query import MethodGraphQuery
from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent
from src.agents.coding_agent_v4_2 import CodingAgentV4_2
from src.utils.llm_client import get_llm_client
from scripts.jos.experiment_registry import (
    MODE_CONFIGS,
    REPEAT_HINTS,
    get_dataset_config,
    get_questions,
    list_config_snapshot,
    resolve_modes,
)
from test_full_pipeline_with_coding_v4_2 import load_test_data, run_single_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="重复运行论文实验")
    parser.add_argument(
        "--dataset",
        type=str,
        default="main_data_security",
        help="数据集配置 ID，默认 main_data_security",
    )
    parser.add_argument(
        "--mode-bundle",
        type=str,
        default="thesis_six",
        help="模式组合名称；当 --modes 为空时生效",
    )
    parser.add_argument("--repeats", type=int, default=5, help="每个问题-模式组合重复次数")
    parser.add_argument(
        "--run-indexes",
        type=str,
        default="",
        help="仅运行指定 run 编号，逗号分隔；为空时运行 1..repeats",
    )
    parser.add_argument(
        "--question-indexes",
        type=str,
        default="1,2,3,4,5",
        help="要运行的问题编号，逗号分隔，默认 1,2,3,4,5",
    )
    parser.add_argument(
        "--modes",
        type=str,
        default="",
        help="要运行的模式，逗号分隔；为空时使用 --mode-bundle",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/repeated_experiments",
        help="重复实验输出目录",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="即使结果已存在也重跑并覆盖",
    )
    parser.add_argument(
        "--manifest-file",
        type=str,
        default="manifest.jsonl",
        help="清单文件名，默认写入 output-dir/manifest.jsonl",
    )
    parser.add_argument(
        "--summary-file",
        type=str,
        default="batch_summary.json",
        help="汇总文件名，默认写入 output-dir/batch_summary.json",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="列出当前可用的数据集、模式和 bundle 配置",
    )
    return parser.parse_args()


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _compact_result(
    mode: str,
    q_idx: int,
    question: str,
    run_idx: int,
    exp_result: dict,
    elapsed: float,
    dataset_config,
) -> dict:
    return {
        "dataset_id": dataset_config.dataset_id,
        "dataset_label": dataset_config.label,
        "data_file": dataset_config.data_file,
        "sheet_name": dataset_config.sheet_name,
        "mode": mode,
        "question_index": q_idx,
        "question": question,
        "run_index": run_idx,
        "elapsed_seconds": round(elapsed, 3),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rounds": [
            {
                "total_tasks": r["total_tasks"],
                "success_count": r["success_count"],
                "strategist_time": round(r["strategist_time"], 3),
                "has_insights": "data_insights" in r["blueprint_result"],
                "has_graph_preview": "graph_preview" in r["blueprint_result"],
                "blueprint": r["blueprint_result"].get("blueprint", {}),
            }
            for r in exp_result["rounds"]
        ],
    }


def _validate_round_result(round_result: dict, round_index: int) -> str | None:
    blueprint_result = round_result.get("blueprint_result", {})
    if not isinstance(blueprint_result, dict):
        return f"round_{round_index}: blueprint_result_missing"

    blueprint = blueprint_result.get("blueprint", {})
    if not isinstance(blueprint, dict):
        return f"round_{round_index}: blueprint_not_dict"

    if blueprint.get("error"):
        return f"round_{round_index}: blueprint_error={blueprint.get('error')}"

    task_graph = blueprint.get("task_graph")
    if not isinstance(task_graph, list):
        return f"round_{round_index}: task_graph_missing"
    if not task_graph:
        return f"round_{round_index}: task_graph_empty"

    total_tasks = int(round_result.get("total_tasks", 0) or 0)
    if total_tasks <= 0:
        return f"round_{round_index}: total_tasks_zero"

    success_count = int(round_result.get("success_count", 0) or 0)
    if success_count <= 0:
        return f"round_{round_index}: success_count_zero"
    if success_count < total_tasks:
        return f"round_{round_index}: partial_success={success_count}/{total_tasks}"

    return None


def _validate_experiment_result(exp_result: dict) -> str | None:
    rounds = exp_result.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return "rounds_missing"

    for idx, round_result in enumerate(rounds, start=1):
        error = _validate_round_result(round_result, idx)
        if error:
            return error
    return None


def _build_components():
    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")

    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph,
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)
    return strategist, methodologist, coding_agent


def main() -> int:
    args = parse_args()
    if args.list_configs:
        print(json.dumps(list_config_snapshot(), ensure_ascii=False, indent=2))
        return 0

    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_config = get_dataset_config(args.dataset)
    questions = get_questions(dataset_config.dataset_id)
    dataset_path = PROJECT_ROOT / dataset_config.data_file
    if not dataset_path.exists():
        print(f"数据集文件不存在: {dataset_path}")
        if dataset_config.source_dataset:
            print(
                "可先运行: py -3 scripts/jos/materialize_transfer_dataset.py "
                f"--dataset {dataset_config.dataset_id}"
            )
        return 1

    selected_q_indexes = []
    for token in _parse_csv_list(args.question_indexes):
        q_idx = int(token)
        if q_idx < 1 or q_idx > len(questions):
            raise ValueError(f"question index 超出范围: {q_idx}")
        selected_q_indexes.append(q_idx)

    explicit_modes = _parse_csv_list(args.modes) if args.modes else []
    selected_modes = resolve_modes(explicit_modes=explicit_modes, mode_bundle=args.mode_bundle)
    unknown_modes = [mode for mode in selected_modes if mode not in MODE_CONFIGS]
    if unknown_modes:
        raise ValueError(f"未知模式: {unknown_modes}")

    if args.run_indexes:
        selected_run_indexes = sorted({int(token) for token in _parse_csv_list(args.run_indexes)})
    else:
        selected_run_indexes = list(range(1, args.repeats + 1))
    invalid_run_indexes = [run_idx for run_idx in selected_run_indexes if run_idx <= 0]
    if invalid_run_indexes:
        raise ValueError(f"run index 必须为正整数: {invalid_run_indexes}")

    total_jobs = len(selected_q_indexes) * len(selected_modes) * len(selected_run_indexes)
    print("=" * 80)
    print("重复实验批处理")
    print("=" * 80)
    print(f"数据集: {dataset_config.dataset_id} | {dataset_config.label}")
    print(f"数据文件: {dataset_config.data_file} @ {dataset_config.sheet_name}")
    print(f"输出目录: {output_dir}")
    print(f"问题: {selected_q_indexes}")
    print(f"模式: {selected_modes}")
    print(f"重复次数: {args.repeats}")
    print(f"运行编号: {selected_run_indexes}")
    print(f"总任务数: {total_jobs}")
    hint = REPEAT_HINTS.get(args.mode_bundle)
    if hint is not None and hint != args.repeats:
        print(f"提示: 当前 bundle `{args.mode_bundle}` 的建议重复次数为 {hint}")

    strategist, methodologist, coding_agent = _build_components()
    test_data = load_test_data(dataset_config.data_file, dataset_config.sheet_name)
    if test_data is None:
        print("无法加载测试数据，终止。")
        return 1

    completed = 0
    skipped = 0
    failed = 0
    manifest_path = output_dir / args.manifest_file

    for q_idx in selected_q_indexes:
        question = questions[q_idx - 1]
        for mode in selected_modes:
            for run_idx in selected_run_indexes:
                out_path = output_dir / f"experiment_q{q_idx}_{mode}_run{run_idx:02d}.json"
                if out_path.exists() and not args.force:
                    skipped += 1
                    print(f"[SKIP] q{q_idx} {mode} run{run_idx:02d} -> {out_path.name}")
                    continue

                print("\n" + "#" * 80)
                print(f"开始: q{q_idx} | {mode} | run {run_idx:02d}")
                print("#" * 80)
                t0 = time.time()
                status = "success"
                error_message = ""

                try:
                    exp_result = run_single_experiment(
                        mode=mode,
                        user_goal=question,
                        strategist=strategist,
                        methodologist=methodologist,
                        coding_agent=coding_agent,
                        test_data=test_data,
                        data_file=dataset_config.data_file,
                        sheet_name=dataset_config.sheet_name,
                    )
                    validation_error = _validate_experiment_result(exp_result)
                    if validation_error:
                        raise RuntimeError(f"invalid_experiment_result: {validation_error}")
                    elapsed = time.time() - t0
                    compact = _compact_result(mode, q_idx, question, run_idx, exp_result, elapsed, dataset_config)
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(compact, f, ensure_ascii=False, indent=2)
                    completed += 1
                    print(f"[OK] {out_path.name} ({elapsed:.1f}s)")
                except Exception as exc:
                    elapsed = time.time() - t0
                    status = "failed"
                    error_message = str(exc)
                    failed += 1
                    error_payload = {
                        "dataset_id": dataset_config.dataset_id,
                        "dataset_label": dataset_config.label,
                        "data_file": dataset_config.data_file,
                        "sheet_name": dataset_config.sheet_name,
                        "mode": mode,
                        "question_index": q_idx,
                        "question": question,
                        "run_index": run_idx,
                        "elapsed_seconds": round(elapsed, 3),
                        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": error_message,
                    }
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(error_payload, f, ensure_ascii=False, indent=2)
                    print(f"[FAIL] {out_path.name} ({elapsed:.1f}s): {error_message}")

                manifest_record = {
                    "file": out_path.name,
                    "dataset_id": dataset_config.dataset_id,
                    "status": status,
                    "mode": mode,
                    "question_index": q_idx,
                    "run_index": run_idx,
                    "elapsed_seconds": round(elapsed, 3),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                if error_message:
                    manifest_record["error"] = error_message
                with open(manifest_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(manifest_record, ensure_ascii=False) + "\n")

    summary = {
        "output_dir": str(output_dir),
        "dataset_id": dataset_config.dataset_id,
        "dataset_label": dataset_config.label,
        "data_file": dataset_config.data_file,
        "sheet_name": dataset_config.sheet_name,
        "repeats": args.repeats,
        "run_indexes": selected_run_indexes,
        "question_indexes": selected_q_indexes,
        "modes": selected_modes,
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(output_dir / args.summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("批处理完成")
    print("=" * 80)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
