from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_full"
EXTERNAL_REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_external_main"
TRANSFER_REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_transfer_iot_auto"
CROSS_DOMAIN_REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_cross_domain_bugzilla"
JOS_OUTPUT_DIR = ROOT / "outputs" / "jos_artifacts"
JOS_STATS_DIR = JOS_OUTPUT_DIR / "stats"
JOS_TABLE_DIR = JOS_OUTPUT_DIR / "tables"
JOS_FIG_DIR = JOS_OUTPUT_DIR / "figures"
JOS_DATASET_DIR = JOS_OUTPUT_DIR / "datasets"
JOS_HUMAN_REVIEW_DIR = JOS_OUTPUT_DIR / "human_review"
STRONGEST_EXTERNAL_MECHANISM_PATH = JOS_STATS_DIR / "strongest_external_mechanism_baseline.json"
LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH = JOS_STATS_DIR / "strongest_external_baseline.json"

PAPER_DIR = ROOT / "docs" / "paper_jos"
PAPER_GEN_DIR = PAPER_DIR / "generated"
PAPER_FIG_DIR = PAPER_DIR / "figures"

LLM_BY_MODE_PATH = REPEATED_DIR / "repeated_llm_scores_summary_by_mode.csv"
LLM_BY_QM_PATH = REPEATED_DIR / "repeated_llm_scores_summary_by_question_mode.csv"
LLM_PER_RUN_PATH = REPEATED_DIR / "repeated_llm_scores_per_run.csv"
AUTO_BY_MODE_PATH = REPEATED_DIR / "repeated_auto_metrics_summary_by_mode.csv"
AUTO_BY_QM_PATH = REPEATED_DIR / "repeated_auto_metrics_summary_by_question_mode.csv"
AUTO_PER_RUN_PATH = REPEATED_DIR / "repeated_auto_metrics_per_run.csv"
SUMMARY_REPORT_PATH = REPEATED_DIR / "repeated_summary_report.md"

MODE_ORDER = [
    "D_baseline0",
    "A_template",
    "B_data_aware",
    "C_iterative",
    "E_ablate_data",
    "F_ablate_kg",
]
EXTERNAL_MODE_ORDER = [
    "C_iterative",
    "G_react_single_agent",
    "H_execution_feedback",
]
SUBDOMAIN_MODE_ORDER = [
    "D_baseline0",
    "B_data_aware",
    "C_iterative",
    "H_execution_feedback",
]
CROSS_DOMAIN_MODE_ORDER = [
    "D_baseline0",
    "C_iterative",
]
MAIN_MODES = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
ABLATION_MODES = ["C_iterative", "E_ablate_data", "F_ablate_kg"]

MODE_LABELS_ZH = {
    "D_baseline0": "D_baseline0",
    "A_template": "A_template",
    "B_data_aware": "B_data_aware",
    "C_iterative": "C_iterative",
    "E_ablate_data": "E_ablate_data",
    "F_ablate_kg": "F_ablate_kg",
    "G_react_single_agent": "G_react_single_agent",
    "H_execution_feedback": "H_execution_feedback",
}

MODE_PLOT_LABELS = {
    "D_baseline0": "D_baseline0\n(纯LLM)",
    "A_template": "A_template\n(+知识模板)",
    "B_data_aware": "B_data_aware\n(+数据感知)",
    "C_iterative": "C_iterative\n(完整系统)",
    "E_ablate_data": "E_ablate_data\n(-数据感知)",
    "F_ablate_kg": "F_ablate_kg\n(-知识图谱)",
    "G_react_single_agent": "G_react_single_agent\n(ReAct单智能体)",
    "H_execution_feedback": "H_execution_feedback\n(执行反馈基线)",
}

MODE_COLORS = {
    "D_baseline0": "#6c757d",
    "A_template": "#8d99ae",
    "B_data_aware": "#2a9d8f",
    "C_iterative": "#1d3557",
    "E_ablate_data": "#f4a261",
    "F_ablate_kg": "#e76f51",
    "G_react_single_agent": "#457b9d",
    "H_execution_feedback": "#264653",
}

QUESTION_ORDER = [
    "分析数据安全领域的技术影响力驱动因素",
    "识别数据安全领域的技术融合趋势",
    "评估不同国家/地区在数据安全领域的竞争态势",
    "判断数据安全领域关键技术所处的生命周期阶段",
    "评估数据安全领域专利组合的风险与薄弱环节",
]

QUESTION_SHORT = {
    "分析数据安全领域的技术影响力驱动因素": "Q1 技术影响力驱动因素",
    "识别数据安全领域的技术融合趋势": "Q2 技术融合趋势识别",
    "评估不同国家/地区在数据安全领域的竞争态势": "Q3 国家竞争态势评估",
    "判断数据安全领域关键技术所处的生命周期阶段": "Q4 技术生命周期阶段判断",
    "评估数据安全领域专利组合的风险与薄弱环节": "Q5 专利组合风险评估",
    "分析软件缺陷分析中的缺陷严重性或问题影响因素": "Q1 缺陷影响因素分析",
    "识别软件缺陷分析中的缺陷类型与模块演化趋势": "Q2 缺陷与模块演化趋势",
    "评估不同项目或组件在软件缺陷分析中的质量差异": "Q3 项目/组件质量评估",
}

LLM_DIMENSIONS = [
    ("relevance", "相关性"),
    ("specificity", "针对性"),
    ("method_quality", "方法合理性"),
    ("innovation", "创新性"),
    ("depth", "深度"),
    ("total", "总分(/25)"),
]

AUTO_METRICS_MAIN = [
    ("column_coverage", "数据列覆盖率", 3),
    ("method_diversity", "方法多样性", 3),
    ("specificity_references", "针对性引用数", 3),
    ("parameter_richness", "参数丰富度", 3),
    ("total_tasks", "生成任务总数", 3),
    ("success_rate", "代码执行成功率", 3),
]

PAIRWISE_COMPARISONS = [
    ("B_data_aware", "A_template"),
    ("B_data_aware", "D_baseline0"),
    ("C_iterative", "B_data_aware"),
    ("C_iterative", "E_ablate_data"),
    ("C_iterative", "F_ablate_kg"),
]


def ensure_dirs() -> None:
    for path in [
        JOS_OUTPUT_DIR,
        JOS_STATS_DIR,
        JOS_TABLE_DIR,
        JOS_FIG_DIR,
        JOS_DATASET_DIR,
        JOS_HUMAN_REVIEW_DIR,
        PAPER_DIR,
        PAPER_GEN_DIR,
        PAPER_FIG_DIR,
        CROSS_DOMAIN_REPEATED_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fmt_pm(mean: float | str, std: float | str, digits: int = 2) -> str:
    return f"{float(mean):.{digits}f} ± {float(std):.{digits}f}"


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def by_mode(rows: list[dict]) -> dict[str, dict]:
    return {row["mode"]: row for row in rows}


def by_question_mode(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["question"], row["mode"]): row for row in rows}


def repeated_file_bundle(base_dir: Path) -> dict[str, Path]:
    return {
        "llm_by_mode": base_dir / "repeated_llm_scores_summary_by_mode.csv",
        "llm_by_qm": base_dir / "repeated_llm_scores_summary_by_question_mode.csv",
        "llm_per_run": base_dir / "repeated_llm_scores_per_run.csv",
        "auto_by_mode": base_dir / "repeated_auto_metrics_summary_by_mode.csv",
        "auto_by_qm": base_dir / "repeated_auto_metrics_summary_by_question_mode.csv",
        "auto_per_run": base_dir / "repeated_auto_metrics_per_run.csv",
        "summary_report": base_dir / "repeated_summary_report.md",
    }


def load_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return load_csv(path)


def question_short_from_text(question: str, question_index: str | int | None = None) -> str:
    if question in QUESTION_SHORT:
        return QUESTION_SHORT[question]
    if question_index not in (None, "", 0, "0"):
        return f"Q{question_index} {question}"
    return question


def ordered_questions_from_rows(rows: list[dict], fallback_order: list[str] | None = None) -> list[str]:
    if rows:
        keyed_questions = []
        seen = set()
        for row in rows:
            question = row.get("question", "")
            if not question or question in seen:
                continue
            seen.add(question)
            try:
                q_idx = int(row.get("question_index", 999))
            except Exception:
                q_idx = 999
            keyed_questions.append((q_idx, question))
        keyed_questions.sort(key=lambda item: (item[0], item[1]))
        return [question for _, question in keyed_questions]
    return list(fallback_order or QUESTION_ORDER)


def unique_mode_order(rows: list[dict], preferred_order: list[str] | None = None) -> list[str]:
    if preferred_order:
        available = {row.get("mode", "") for row in rows}
        ordered = [mode for mode in preferred_order if mode in available]
        if ordered:
            return ordered
    seen = set()
    ordered = []
    for row in rows:
        mode = row.get("mode", "")
        if mode and mode not in seen:
            seen.add(mode)
            ordered.append(mode)
    return ordered
