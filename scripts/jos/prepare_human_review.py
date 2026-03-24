from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    EXTERNAL_REPEATED_DIR,
    JOS_HUMAN_REVIEW_DIR,
    LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH,
    REPEATED_DIR,
    STRONGEST_EXTERNAL_MECHANISM_PATH,
    ensure_dirs,
)


REVIEW_DIMENSIONS = [
    ("relevance", "相关性"),
    ("specificity", "针对性"),
    ("method_quality", "方法合理性"),
    ("innovation", "创新性"),
    ("depth", "深度"),
    ("executability", "可执行性"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="准备人工盲评材料包")
    parser.add_argument("--run-index", type=int, default=1, help="用于抽样的重复轮次，默认 1")
    parser.add_argument(
        "--external-mode",
        type=str,
        default="",
        help="strongest external mechanism baseline；为空时自动读取统计结果",
    )
    parser.add_argument(
        "--question-indexes",
        type=str,
        default="",
        help="盲评抽样问题编号，逗号分隔；为空时自动按可用样本求交集",
    )
    parser.add_argument("--reviewer-count", type=int, default=4, help="生成盲评模板数量，默认 4")
    return parser.parse_args()


def choose_external_mode(explicit_mode: str) -> str:
    if explicit_mode:
        return explicit_mode

    for path in [STRONGEST_EXTERNAL_MECHANISM_PATH, LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH]:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            selected = payload.get("selected_mode", "")
            if selected:
                return selected
    return "H_execution_feedback"


def parse_csv_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def available_question_indexes(base_dir: Path, modes: list[str], run_index: int) -> set[int]:
    available_sets = []
    for mode in modes:
        indexes = set()
        for path in base_dir.glob(f"experiment_q*_{mode}_run{run_index:02d}.json"):
            match = re.search(r"experiment_q(\d+)_", path.name)
            if match:
                indexes.add(int(match.group(1)))
        available_sets.append(indexes)
    return set.intersection(*available_sets) if available_sets else set()


def discover_question_indexes(run_index: int, external_mode: str, explicit_indexes: str) -> list[int]:
    if explicit_indexes:
        return parse_csv_list(explicit_indexes)

    progressive = available_question_indexes(REPEATED_DIR, ["D_baseline0", "B_data_aware", "C_iterative"], run_index)
    ablation = available_question_indexes(REPEATED_DIR, ["C_iterative", "E_ablate_data", "F_ablate_kg"], run_index)
    external = available_question_indexes(REPEATED_DIR, ["C_iterative"], run_index) & available_question_indexes(
        EXTERNAL_REPEATED_DIR,
        [external_mode],
        run_index,
    )
    discovered = sorted(progressive & ablation & external)
    if not discovered:
        raise FileNotFoundError("当前没有同时覆盖三组比较的盲评样本，请先完成对应实验")
    return discovered


def load_experiment(base_dir: Path, question_index: int, mode: str, run_index: int) -> dict:
    path = base_dir / f"experiment_q{question_index}_{mode}_run{run_index:02d}.json"
    if not path.exists():
        raise FileNotFoundError(f"缺少盲评样本文件: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def blueprint_to_markdown(data: dict) -> str:
    lines = []
    lines.append(f"# 匿名方案：{data['anonymous_label']}")
    lines.append("")
    lines.append(f"- 研究问题：Q{data['question_index']} {data['question']}")
    lines.append(f"- 比较组：{data['comparison_group']}")
    lines.append(f"- 轮次数：{len(data['rounds'])}")
    lines.append("")
    for idx, round_data in enumerate(data["rounds"], 1):
        blueprint = round_data.get("blueprint", {})
        lines.append(f"## 第 {idx} 轮规划")
        lines.append("")
        lines.append(f"- 研究目标：{blueprint.get('research_objective', 'N/A')}")
        outcomes = blueprint.get("expected_outcomes", [])
        if outcomes:
            lines.append("- 预期产出：")
            for item in outcomes:
                lines.append(f"  - {item}")
        thinking = blueprint.get("thinking_trace", {})
        if isinstance(thinking, dict) and thinking:
            lines.append("- 思考摘要：")
            for key, value in thinking.items():
                lines.append(f"  - {key}: {value}")
        lines.append("- 任务列表：")
        for task in blueprint.get("task_graph", []):
            config = task.get("implementation_config", {})
            cols = config.get("columns_to_load", [])
            lines.append(
                f"  - {task.get('task_id')}: {task.get('task_type')} | {task.get('question')}"
            )
            lines.append(
                f"    - columns_to_load: {', '.join(cols) if cols else 'N/A'}"
            )
            lines.append(
                f"    - output_file: {config.get('output_file', 'N/A')}"
            )
            lines.append(
                f"    - description: {task.get('description', 'N/A')}"
            )
        lines.append("")
    lines.append("## 评分提示")
    lines.append("")
    lines.append("请仅依据本匿名规划方案本身评分，不参考执行代码与模式猜测。")
    return "\n".join(lines) + "\n"


def write_response_template(path: Path, items: list[dict], reviewer_id: str) -> None:
    fieldnames = [
        "reviewer_id",
        "comparison_group",
        "question_index",
        "anonymous_label",
        "relevance",
        "specificity",
        "method_quality",
        "innovation",
        "depth",
        "executability",
        "comments",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "reviewer_id": reviewer_id,
                    "comparison_group": item["comparison_group"],
                    "question_index": item["question_index"],
                    "anonymous_label": item["anonymous_label"],
                    "comments": "",
                }
            )


def main() -> None:
    args = parse_args()
    ensure_dirs()

    chosen_external_mode = choose_external_mode(args.external_mode)
    question_indexes = discover_question_indexes(args.run_index, chosen_external_mode, args.question_indexes)
    package_dir = JOS_HUMAN_REVIEW_DIR / "review_package"
    admin_dir = JOS_HUMAN_REVIEW_DIR / "admin"
    response_dir = JOS_HUMAN_REVIEW_DIR / "responses"
    for path in [package_dir, admin_dir]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    response_dir.mkdir(parents=True, exist_ok=True)

    comparison_specs = [
        ("main_progressive", REPEATED_DIR, ["D_baseline0", "B_data_aware", "C_iterative"]),
        ("ablation", REPEATED_DIR, ["C_iterative", "E_ablate_data", "F_ablate_kg"]),
        ("external", REPEATED_DIR, ["C_iterative"]),
    ]

    items: list[dict] = []
    label_counter = 1
    mapping_rows = []

    for comparison_group, base_dir, modes in comparison_specs:
        active_modes = list(modes)
        if comparison_group == "external":
            active_modes.append(chosen_external_mode)
        for question_index in question_indexes:
            for mode in active_modes:
                source_dir = EXTERNAL_REPEATED_DIR if mode in {"G_react_single_agent", "H_execution_feedback"} else base_dir
                exp = load_experiment(source_dir, question_index, mode, args.run_index)
                anonymous_label = f"Plan-{label_counter:02d}"
                label_counter += 1
                item = {
                    "anonymous_label": anonymous_label,
                    "comparison_group": comparison_group,
                    "question_index": question_index,
                    "question": exp["question"],
                    "mode": mode,
                    "run_index": args.run_index,
                    "source_dir": str(source_dir),
                    "rounds": [
                        {
                            "round_index": idx,
                            "blueprint": round_data.get("blueprint", {}),
                        }
                        for idx, round_data in enumerate(exp.get("rounds", []), 1)
                    ],
                }
                items.append(item)
                mapping_rows.append(
                    {
                        "anonymous_label": anonymous_label,
                        "comparison_group": comparison_group,
                        "question_index": question_index,
                        "question": exp["question"],
                        "mode": mode,
                        "run_index": args.run_index,
                        "source_dir": str(source_dir),
                    }
                )

                item_dir = package_dir / comparison_group / f"Q{question_index}"
                item_dir.mkdir(parents=True, exist_ok=True)
                (item_dir / f"{anonymous_label}.md").write_text(blueprint_to_markdown(item), encoding="utf-8")
                (item_dir / f"{anonymous_label}.json").write_text(
                    json.dumps(item, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    instructions = [
        "# 人工盲评说明",
        "",
        "- 本盲评只评估匿名化后的规划方案，不评估执行代码。",
        "- 每个方案按 6 个维度打分：相关性、针对性、方法合理性、创新性、深度、可执行性。",
        "- 每项评分范围为 1-5 分，1 表示明显不足，5 表示明显优秀。",
        "- 请不要猜测模式来源，只根据方案内容评分。",
        "- 本轮建议邀请 4 位评审，确保至少 3 位完成有效回收。",
    ]
    (package_dir / "README.md").write_text("\n".join(instructions) + "\n", encoding="utf-8")
    (package_dir / "review_dimensions.json").write_text(
        json.dumps({"dimensions": REVIEW_DIMENSIONS, "external_mode": chosen_external_mode}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    mapping_path = admin_dir / "anonymous_label_mapping.csv"
    with mapping_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(mapping_rows[0].keys()))
        writer.writeheader()
        writer.writerows(mapping_rows)

    for reviewer_idx in range(1, max(1, args.reviewer_count) + 1):
        reviewer_id = f"reviewer_{reviewer_idx:02d}"
        write_response_template(response_dir / f"{reviewer_id}_template.csv", items, reviewer_id)

    manifest = {
        "run_index": args.run_index,
        "external_mode": chosen_external_mode,
        "question_indexes": question_indexes,
        "comparison_groups": [
            {"comparison_group": group, "question_count": len(question_indexes)}
            for group, _, _ in comparison_specs
        ],
        "item_count": len(items),
        "reviewer_count": max(1, args.reviewer_count),
    }
    (JOS_HUMAN_REVIEW_DIR / "package_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved human review package to {package_dir}")
    print(f"Saved admin mapping to {mapping_path}")
    print(f"External baseline in package: {chosen_external_mode}")


if __name__ == "__main__":
    main()
