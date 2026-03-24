from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.experiment_registry import get_question_indexes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按问题/模式拆分运行重复实验，适合长批次安全续跑")
    parser.add_argument("--dataset", type=str, required=True, help="数据集配置 ID")
    parser.add_argument("--modes", type=str, required=True, help="模式列表，逗号分隔")
    parser.add_argument("--repeats", type=int, required=True, help="每组重复次数")
    parser.add_argument("--output-dir", type=str, required=True, help="输出目录")
    parser.add_argument("--question-indexes", type=str, default="", help="问题编号列表，逗号分隔；为空时按数据集默认问题集合")
    parser.add_argument("--pause-seconds", type=int, default=3, help="每个子批次之间的暂停秒数")
    return parser.parse_args()


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_subprocess_env() -> dict[str, str]:
    """构建子进程环境，优先使用当前解释器所属站点包目录。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    exe_dir = Path(sys.executable).resolve().parent
    candidate_site_packages = exe_dir / "Lib" / "site-packages"
    if candidate_site_packages.exists():
        existing = env.get("PYTHONPATH", "")
        pythonpath_parts = [str(candidate_site_packages)]
        if existing:
            pythonpath_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    return env


def inspect_run_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "failed"
    rounds = payload.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return "failed"
    for round_payload in rounds:
        blueprint = round_payload.get("blueprint", {})
        task_graph = blueprint.get("task_graph") if isinstance(blueprint, dict) else None
        total_tasks = int(round_payload.get("total_tasks", 0) or 0)
        success_count = int(round_payload.get("success_count", 0) or 0)
        if not isinstance(blueprint, dict):
            return "failed"
        if blueprint.get("error"):
            return "failed"
        if not isinstance(task_graph, list) or not task_graph:
            return "failed"
        if total_tasks <= 0:
            return "failed"
        if success_count <= 0 or success_count < total_tasks:
            return "failed"
    return "success"


def run_checked(args: list[str]) -> None:
    env = _build_subprocess_env()
    print(f"[RUN] {' '.join(args)}")
    subprocess.run(args, cwd=str(PROJECT_ROOT), env=env, check=True)


def main() -> None:
    args = parse_args()
    modes = parse_csv_list(args.modes)
    question_indexes = (
        [int(item) for item in parse_csv_list(args.question_indexes)]
        if args.question_indexes
        else get_question_indexes(args.dataset)
    )
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_failures: list[dict[str, object]] = []

    for question_index in question_indexes:
        for mode in modes:
            rerun_indexes = []
            for run_index in range(1, args.repeats + 1):
                exp_path = output_dir / f"experiment_q{question_index}_{mode}_run{run_index:02d}.json"
                status = inspect_run_status(exp_path)
                if status != "success":
                    rerun_indexes.append(run_index)

            if not rerun_indexes:
                print(f"[SKIP] q{question_index} {mode} 已全部完成")
                continue

            command = [
                sys.executable,
                "tests/repeat_pipeline_experiments.py",
                "--dataset",
                args.dataset,
                "--modes",
                mode,
                "--question-indexes",
                str(question_index),
                "--repeats",
                str(args.repeats),
                "--run-indexes",
                ",".join(str(item) for item in rerun_indexes),
                "--output-dir",
                args.output_dir,
                "--force",
                "--manifest-file",
                f"manifest_q{question_index}_{mode}.jsonl",
                "--summary-file",
                f"batch_summary_q{question_index}_{mode}.json",
            ]

            try:
                run_checked(command)
            except subprocess.CalledProcessError as exc:
                batch_failures.append(
                    {
                        "question_index": question_index,
                        "mode": mode,
                        "run_indexes": rerun_indexes,
                        "returncode": exc.returncode,
                    }
                )
                print(
                    f"[WARN] q{question_index} {mode} 子批次失败，已记录并继续后续任务 "
                    f"(runs={rerun_indexes}, returncode={exc.returncode})"
                )

            if args.pause_seconds > 0:
                subprocess.run(
                    [sys.executable, "-c", f"import time; time.sleep({max(0, args.pause_seconds)})"],
                    check=True,
                )

    if batch_failures:
        print("[WARN] 以下子批次仍需后续修复:")
        for failure in batch_failures:
            print(json.dumps(failure, ensure_ascii=False))
    print("[DONE] batched repeated experiment execution completed")


if __name__ == "__main__":
    main()
