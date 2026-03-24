import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_full"
AUTO_BY_MODE_PATH = REPEATED_DIR / "repeated_auto_metrics_summary_by_mode.csv"
AUTO_BY_QM_PATH = REPEATED_DIR / "repeated_auto_metrics_summary_by_question_mode.csv"
LLM_BY_MODE_PATH = REPEATED_DIR / "repeated_llm_scores_summary_by_mode.csv"
LLM_BY_QM_PATH = REPEATED_DIR / "repeated_llm_scores_summary_by_question_mode.csv"

TABLE_DIR = ROOT / "docs" / "thesis" / "tables"
ARTIFACT_DIR = ROOT / "outputs" / "thesis_artifacts"

MAIN_MODES = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
ABLATION_MODES = ["C_iterative", "E_ablate_data", "F_ablate_kg"]
SIX_WAY_MODES = ["D_baseline0", "A_template", "B_data_aware", "C_iterative", "E_ablate_data", "F_ablate_kg"]

QUESTION_ORDER = [
    "分析数据安全领域的技术影响力驱动因素",
    "识别数据安全领域的技术融合趋势",
    "评估不同国家/地区在数据安全领域的竞争态势",
]


def ensure_dirs() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list, fieldnames: list) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def fmt(mean: str, std: str, ndigits: int) -> str:
    return f"{float(mean):.{ndigits}f} ± {float(std):.{ndigits}f}"


def by_mode(rows: list[dict]) -> dict[str, dict]:
    return {row["mode"]: row for row in rows}


def by_question_mode(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["question"], row["mode"]): row for row in rows}


def export_overview_table(llm_by_mode: list[dict]) -> None:
    rows = []
    lookup = by_mode(llm_by_mode)
    for mode in SIX_WAY_MODES:
        row = lookup[mode]
        rows.append([mode, fmt(row["total_mean"], row["total_std"], 2)])
    md = to_markdown_table(["模式", "LLM总分（均值 ± 标准差）"], rows)
    (TABLE_DIR / "表5-1_六模式LLM总分总览.md").write_text(md + "\n", encoding="utf-8")


def export_auto_metrics(auto_by_mode: list[dict]) -> None:
    lookup = by_mode(auto_by_mode)
    metric_map = [
        ("数据列覆盖率", "column_coverage"),
        ("方法多样性", "method_diversity"),
        ("任务描述详细度", "avg_description_length"),
        ("针对性引用数", "specificity_references"),
        ("控制变量数", "control_variable_count"),
        ("参数丰富度", "parameter_richness"),
        ("预期结论具体度", "outcome_specificity"),
        ("数据洞察数量", "insight_count"),
        ("生成任务总数", "total_tasks"),
        ("代码执行成功率", "success_rate"),
    ]

    def build_rows(modes: list[str]) -> tuple[list[list[str]], list[dict]]:
        rows_md = []
        rows_csv = []
        for zh_name, key in metric_map:
            row_md = [zh_name]
            row_csv = {"metric": zh_name}
            for mode in modes:
                row = lookup[mode]
                val = fmt(row[f"{key}_mean"], row[f"{key}_std"], 3)
                row_md.append(val)
                row_csv[mode] = val
            rows_md.append(row_md)
            rows_csv.append(row_csv)
        return rows_md, rows_csv

    main_md, main_csv = build_rows(MAIN_MODES)
    ablation_md, ablation_csv = build_rows(ABLATION_MODES)

    (TABLE_DIR / "表5-2_自动化指标均值.md").write_text(
        to_markdown_table(["指标"] + MAIN_MODES, main_md) + "\n",
        encoding="utf-8",
    )
    (TABLE_DIR / "表5-5_消融自动化指标均值.md").write_text(
        to_markdown_table(["指标"] + ABLATION_MODES, ablation_md) + "\n",
        encoding="utf-8",
    )

    write_csv(ARTIFACT_DIR / "metrics_main_repeated.csv", main_csv, ["metric"] + MAIN_MODES)
    write_csv(ARTIFACT_DIR / "metrics_ablation_repeated.csv", ablation_csv, ["metric"] + ABLATION_MODES)


def export_llm_scores(llm_by_mode: list[dict], llm_by_qm: list[dict]) -> None:
    mode_lookup = by_mode(llm_by_mode)
    qm_lookup = by_question_mode(llm_by_qm)
    dim_map = [
        ("相关性", "relevance"),
        ("针对性", "specificity"),
        ("方法合理性", "method_quality"),
        ("创新性", "innovation"),
        ("深度", "depth"),
        ("总分(/25)", "total"),
    ]

    def build_mode_rows(modes: list[str]) -> tuple[list[list[str]], list[dict]]:
        rows_md = []
        rows_csv = []
        for zh_name, key in dim_map:
            row_md = [zh_name]
            row_csv = {"dimension": zh_name}
            for mode in modes:
                row = mode_lookup[mode]
                val = fmt(row[f"{key}_mean"], row[f"{key}_std"], 2)
                row_md.append(val)
                row_csv[mode] = val
            rows_md.append(row_md)
            rows_csv.append(row_csv)
        return rows_md, rows_csv

    def build_question_rows(modes: list[str]) -> tuple[list[list[str]], list[dict]]:
        rows_md = []
        rows_csv = []
        for question in QUESTION_ORDER:
            row_md = [question]
            row_csv = {"question": question}
            for mode in modes:
                row = qm_lookup[(question, mode)]
                val = fmt(row["total_mean"], row["total_std"], 2)
                row_md.append(val)
                row_csv[mode] = val
            rows_md.append(row_md)
            rows_csv.append(row_csv)
        return rows_md, rows_csv

    main_md, main_csv = build_mode_rows(MAIN_MODES)
    ablation_md, ablation_csv = build_mode_rows(ABLATION_MODES)
    main_q_md, main_q_csv = build_question_rows(MAIN_MODES)
    ablation_q_md, ablation_q_csv = build_question_rows(ABLATION_MODES)

    (TABLE_DIR / "表5-3_LLM评分均值.md").write_text(
        to_markdown_table(["维度"] + MAIN_MODES, main_md) + "\n",
        encoding="utf-8",
    )
    (TABLE_DIR / "表5-4_问题级LLM总分.md").write_text(
        to_markdown_table(["问题"] + MAIN_MODES, main_q_md) + "\n",
        encoding="utf-8",
    )
    (TABLE_DIR / "表5-6_消融LLM评分均值.md").write_text(
        to_markdown_table(["维度"] + ABLATION_MODES, ablation_md) + "\n",
        encoding="utf-8",
    )
    (TABLE_DIR / "表5-7_消融问题级LLM总分.md").write_text(
        to_markdown_table(["问题"] + ABLATION_MODES, ablation_q_md) + "\n",
        encoding="utf-8",
    )

    write_csv(ARTIFACT_DIR / "scores_main_repeated.csv", main_csv, ["dimension"] + MAIN_MODES)
    write_csv(ARTIFACT_DIR / "scores_ablation_repeated.csv", ablation_csv, ["dimension"] + ABLATION_MODES)
    write_csv(ARTIFACT_DIR / "scores_main_questions_repeated.csv", main_q_csv, ["question"] + MAIN_MODES)
    write_csv(ARTIFACT_DIR / "scores_ablation_questions_repeated.csv", ablation_q_csv, ["question"] + ABLATION_MODES)


def main() -> None:
    ensure_dirs()
    auto_by_mode = load_csv(AUTO_BY_MODE_PATH)
    llm_by_mode = load_csv(LLM_BY_MODE_PATH)
    llm_by_qm = load_csv(LLM_BY_QM_PATH)
    export_overview_table(llm_by_mode)
    export_auto_metrics(auto_by_mode)
    export_llm_scores(llm_by_mode, llm_by_qm)
    print("Export complete.")
    print(f"Tables: {TABLE_DIR}")
    print(f"Artifacts: {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
