from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    ABLATION_MODES,
    AUTO_BY_MODE_PATH,
    AUTO_BY_QM_PATH,
    AUTO_METRICS_MAIN,
    CROSS_DOMAIN_MODE_ORDER,
    CROSS_DOMAIN_REPEATED_DIR,
    EXTERNAL_MODE_ORDER,
    EXTERNAL_REPEATED_DIR,
    JOS_HUMAN_REVIEW_DIR,
    JOS_STATS_DIR,
    JOS_TABLE_DIR,
    LLM_BY_MODE_PATH,
    LLM_BY_QM_PATH,
    LLM_DIMENSIONS,
    MAIN_MODES,
    PAPER_GEN_DIR,
    QUESTION_ORDER,
    QUESTION_SHORT,
    REPEATED_DIR,
    SUBDOMAIN_MODE_ORDER,
    TRANSFER_REPEATED_DIR,
    by_mode,
    by_question_mode,
    ensure_dirs,
    fmt_pm,
    latex_escape,
    load_csv,
    load_if_exists,
    ordered_questions_from_rows,
    question_short_from_text,
    repeated_file_bundle,
    unique_mode_order,
)


def merge_mode_level_rows(primary_rows: list[dict], fallback_rows: list[dict], modes: list[str]) -> list[dict]:
    merged = {}
    for row in primary_rows:
        merged[row["mode"]] = row
    for row in fallback_rows:
        merged.setdefault(row["mode"], row)
    return [merged[mode] for mode in modes if mode in merged]


def merge_question_mode_rows(primary_rows: list[dict], fallback_rows: list[dict], modes: list[str]) -> list[dict]:
    merged = {}
    for row in primary_rows:
        key = (row["question"], row["mode"])
        merged[key] = row
    for row in fallback_rows:
        key = (row["question"], row["mode"])
        merged.setdefault(key, row)
    return [row for row in merged.values() if row["mode"] in modes]


def write_tex(path: Path, caption: str, label: str, headers: list[str], rows: list[list[str]], notes: str | None = None) -> None:
    body = []
    body.append("\\begin{table}[htbp]")
    body.append("\\centering")
    body.append(f"\\caption{{{caption}}}")
    body.append(f"\\label{{{label}}}")
    body.append("\\resizebox{\\textwidth}{!}{%")
    body.append("\\begin{tabular}{" + "l" * len(headers) + "}")
    body.append("\\toprule")
    body.append(" & ".join(headers) + " \\\\")
    body.append("\\midrule")
    for row in rows:
        body.append(" & ".join(row) + " \\\\")
    body.append("\\bottomrule")
    body.append("\\end{tabular}%")
    body.append("}")
    if notes:
        body.append("\\vspace{0.3em}")
        body.append("\\begin{minipage}{0.96\\linewidth}")
        body.append("\\footnotesize\\raggedright")
        body.append(notes)
        body.append("\\end{minipage}")
    body.append("\\end{table}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def build_llm_rows(llm_mode: dict[str, dict], modes: list[str]) -> list[list[str]]:
    rows = []
    for key, label in LLM_DIMENSIONS:
        row = [latex_escape(label)]
        for mode in modes:
            item = llm_mode[mode]
            row.append(fmt_pm(item[f"{key}_mean"], item[f"{key}_std"], 2))
        rows.append(row)
    return rows


def build_auto_rows(auto_mode: dict[str, dict], modes: list[str]) -> list[list[str]]:
    rows = []
    for key, label, digits in AUTO_METRICS_MAIN:
        row = [latex_escape(label)]
        for mode in modes:
            item = auto_mode[mode]
            row.append(fmt_pm(item[f"{key}_mean"], item[f"{key}_std"], digits))
        rows.append(row)
    return rows


def export_mode_tables() -> None:
    llm_by_mode = load_csv(LLM_BY_MODE_PATH)
    auto_by_mode = load_csv(AUTO_BY_MODE_PATH)
    llm_by_qm = load_csv(LLM_BY_QM_PATH)
    question_count = len(ordered_questions_from_rows(llm_by_qm, QUESTION_ORDER))
    llm_mode = by_mode(llm_by_mode)
    auto_mode = by_mode(auto_by_mode)

    write_tex(
        PAPER_GEN_DIR / "table_main_llm.tex",
        f"四方案 LLM-as-Judge 评分对比（{question_count} 问题 $\\times$ 5 次重复的均值 $\\pm$ 标准差）",
        "tab:jos-main-llm",
        ["维度"] + [latex_escape(m) for m in MAIN_MODES],
        build_llm_rows(llm_mode, MAIN_MODES),
    )
    write_tex(
        PAPER_GEN_DIR / "table_main_auto.tex",
        f"四方案关键自动化指标对比（{question_count} 问题 $\\times$ 5 次重复的均值 $\\pm$ 标准差）",
        "tab:jos-main-auto",
        ["指标"] + [latex_escape(m) for m in MAIN_MODES],
        build_auto_rows(auto_mode, MAIN_MODES),
        notes="注：本表只保留与规划质量最直接相关的核心结构指标；完整指标集合见补充材料。",
    )
    write_tex(
        PAPER_GEN_DIR / "table_ablation_llm.tex",
        f"组件消融 LLM-as-Judge 评分对比（{question_count} 问题 $\\times$ 5 次重复的均值 $\\pm$ 标准差）",
        "tab:jos-ablation-llm",
        ["维度"] + [latex_escape(m) for m in ABLATION_MODES],
        build_llm_rows(llm_mode, ABLATION_MODES),
    )
    write_tex(
        PAPER_GEN_DIR / "table_ablation_auto.tex",
        f"组件消融关键自动化指标对比（{question_count} 问题 $\\times$ 5 次重复的均值 $\\pm$ 标准差）",
        "tab:jos-ablation-auto",
        ["指标"] + [latex_escape(m) for m in ABLATION_MODES],
        build_auto_rows(auto_mode, ABLATION_MODES),
    )

    pd.DataFrame(llm_by_mode).to_csv(JOS_TABLE_DIR / "summary_by_mode_llm.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(auto_by_mode).to_csv(JOS_TABLE_DIR / "summary_by_mode_auto.csv", index=False, encoding="utf-8-sig")


def export_question_tables() -> None:
    llm_by_qm = load_csv(LLM_BY_QM_PATH)
    auto_by_qm = load_csv(AUTO_BY_QM_PATH)
    llm_lookup = by_question_mode(llm_by_qm)
    auto_lookup = by_question_mode(auto_by_qm)
    question_order = ordered_questions_from_rows(llm_by_qm, QUESTION_ORDER)

    def build_rows(modes: list[str], metric: str) -> list[list[str]]:
        rows = []
        for question in question_order:
            matched_rows = [row for row in llm_by_qm if row["question"] == question]
            q_idx = matched_rows[0].get("question_index", "") if matched_rows else ""
            row = [latex_escape(question_short_from_text(question, q_idx))]
            for mode in modes:
                item = (llm_lookup if metric == "llm" else auto_lookup)[(question, mode)]
                if metric == "llm":
                    row.append(fmt_pm(item["total_mean"], item["total_std"], 2))
                else:
                    row.append(fmt_pm(item["specificity_references_mean"], item["specificity_references_std"], 2))
            rows.append(row)
        return rows

    write_tex(
        PAPER_GEN_DIR / "table_question_main.tex",
        "四方案问题级 LLM 总分明细（均值 $\\pm$ 标准差）",
        "tab:jos-question-main",
        ["研究问题"] + [latex_escape(m) for m in MAIN_MODES],
        build_rows(MAIN_MODES, "llm"),
    )
    write_tex(
        PAPER_GEN_DIR / "table_question_ablation.tex",
        "组件消融问题级 LLM 总分明细（均值 $\\pm$ 标准差）",
        "tab:jos-question-ablation",
        ["研究问题"] + [latex_escape(m) for m in ABLATION_MODES],
        build_rows(ABLATION_MODES, "llm"),
    )

    pd.DataFrame(llm_by_qm).to_csv(JOS_TABLE_DIR / "summary_by_question_llm.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(auto_by_qm).to_csv(JOS_TABLE_DIR / "summary_by_question_auto.csv", index=False, encoding="utf-8-sig")


def export_external_tables() -> None:
    external_bundle = repeated_file_bundle(EXTERNAL_REPEATED_DIR)
    llm_external = load_if_exists(external_bundle["llm_by_mode"])
    if not llm_external:
        return
    main_bundle = repeated_file_bundle(REPEATED_DIR)
    llm_main = load_if_exists(main_bundle["llm_by_mode"])
    auto_external = load_if_exists(external_bundle["auto_by_mode"])
    auto_main = load_if_exists(main_bundle["auto_by_mode"])
    llm_qm_external = load_if_exists(external_bundle["llm_by_qm"])
    llm_qm_main = load_if_exists(main_bundle["llm_by_qm"])

    llm_by_mode = merge_mode_level_rows(llm_external, llm_main, EXTERNAL_MODE_ORDER)
    auto_by_mode = merge_mode_level_rows(auto_external, auto_main, EXTERNAL_MODE_ORDER)
    llm_by_qm = merge_question_mode_rows(llm_qm_external, llm_qm_main, EXTERNAL_MODE_ORDER)
    llm_mode = by_mode(llm_by_mode)
    auto_mode = by_mode(auto_by_mode)

    modes = [mode for mode in EXTERNAL_MODE_ORDER if mode in llm_mode]
    if len(modes) < 2:
        return

    write_tex(
        PAPER_GEN_DIR / "table_external_llm.tex",
        "完整系统与外部基线的 LLM-as-Judge 评分对比（均值 $\\pm$ 标准差）",
        "tab:jos-external-llm",
        ["维度"] + [latex_escape(m) for m in modes],
        build_llm_rows(llm_mode, modes),
    )
    if auto_mode:
        write_tex(
            PAPER_GEN_DIR / "table_external_auto.tex",
            "完整系统与外部基线的关键自动化指标对比（均值 $\\pm$ 标准差）",
            "tab:jos-external-auto",
            ["指标"] + [latex_escape(m) for m in modes],
            build_auto_rows(auto_mode, modes),
        )

    if llm_by_qm:
        lookup = by_question_mode(llm_by_qm)
        rows = []
        questions = []
        for row in llm_by_qm:
            key = (int(row["question_index"]), row["question"])
            if key not in questions:
                questions.append(key)
        questions.sort(key=lambda item: item[0])
        for q_idx, question in questions:
            row = [latex_escape(question_short_from_text(question, q_idx))]
            for mode in modes:
                item = lookup[(question, mode)]
                row.append(fmt_pm(item["total_mean"], item["total_std"], 2))
            rows.append(row)
        write_tex(
            PAPER_GEN_DIR / "table_external_question.tex",
            "完整系统与外部基线的问题级 LLM 总分明细（均值 $\\pm$ 标准差）",
            "tab:jos-external-question",
            ["研究问题"] + [latex_escape(m) for m in modes],
            rows,
        )

    pd.DataFrame(llm_by_mode).to_csv(JOS_TABLE_DIR / "summary_by_mode_external_llm.csv", index=False, encoding="utf-8-sig")
    if auto_by_mode:
        pd.DataFrame(auto_by_mode).to_csv(JOS_TABLE_DIR / "summary_by_mode_external_auto.csv", index=False, encoding="utf-8-sig")
    if llm_by_qm:
        pd.DataFrame(llm_by_qm).to_csv(JOS_TABLE_DIR / "summary_by_question_external_llm.csv", index=False, encoding="utf-8-sig")


def export_transfer_tables() -> None:
    bundle = repeated_file_bundle(TRANSFER_REPEATED_DIR)
    llm_by_mode = load_if_exists(bundle["llm_by_mode"])
    if not llm_by_mode:
        return
    auto_by_mode = load_if_exists(bundle["auto_by_mode"])
    llm_by_qm = load_if_exists(bundle["llm_by_qm"])
    llm_mode = by_mode(llm_by_mode)
    auto_mode = by_mode(auto_by_mode)
    modes = unique_mode_order(llm_by_mode, SUBDOMAIN_MODE_ORDER)

    write_tex(
        PAPER_GEN_DIR / "table_transfer_llm.tex",
        "子领域稳定性验证 LLM-as-Judge 评分对比（均值 $\\pm$ 标准差）",
        "tab:jos-transfer-llm",
        ["维度"] + [latex_escape(m) for m in modes],
        build_llm_rows(llm_mode, modes),
    )
    if auto_mode:
        write_tex(
            PAPER_GEN_DIR / "table_transfer_auto.tex",
            "子领域稳定性验证关键自动化指标对比（均值 $\\pm$ 标准差）",
            "tab:jos-transfer-auto",
            ["指标"] + [latex_escape(m) for m in modes],
            build_auto_rows(auto_mode, modes),
        )
    if llm_by_qm:
        lookup = by_question_mode(llm_by_qm)
        rows = []
        questions = []
        for row in llm_by_qm:
            key = (int(row["question_index"]), row["question"])
            if key not in questions:
                questions.append(key)
        questions.sort(key=lambda item: item[0])
        for q_idx, question in questions:
            row = [latex_escape(question_short_from_text(question, q_idx))]
            for mode in modes:
                item = lookup[(question, mode)]
                row.append(fmt_pm(item["total_mean"], item["total_std"], 2))
            rows.append(row)
        write_tex(
            PAPER_GEN_DIR / "table_transfer_question.tex",
            "子领域稳定性验证问题级 LLM 总分明细（均值 $\\pm$ 标准差）",
            "tab:jos-transfer-question",
            ["研究问题"] + [latex_escape(m) for m in modes],
            rows,
        )

    pd.DataFrame(llm_by_mode).to_csv(JOS_TABLE_DIR / "summary_transfer_llm.csv", index=False, encoding="utf-8-sig")
    if auto_by_mode:
        pd.DataFrame(auto_by_mode).to_csv(JOS_TABLE_DIR / "summary_transfer_auto.csv", index=False, encoding="utf-8-sig")


def export_cross_domain_tables() -> None:
    bundle = repeated_file_bundle(CROSS_DOMAIN_REPEATED_DIR)
    llm_by_mode = load_if_exists(bundle["llm_by_mode"])
    if not llm_by_mode:
        return

    llm_mode = by_mode(llm_by_mode)
    llm_by_qm = load_if_exists(bundle["llm_by_qm"])
    modes = unique_mode_order(llm_by_mode, CROSS_DOMAIN_MODE_ORDER)

    write_tex(
        PAPER_GEN_DIR / "table_cross_domain_llm.tex",
        "跨领域初步验证的 LLM-as-Judge 评分对比（均值 $\\pm$ 标准差）",
        "tab:jos-cross-domain-llm",
        ["维度"] + [latex_escape(m) for m in modes],
        build_llm_rows(llm_mode, modes),
    )

    if llm_by_qm:
        lookup = by_question_mode(llm_by_qm)
        rows = []
        questions = ordered_questions_from_rows(llm_by_qm)
        for question in questions:
            matching_rows = [row for row in llm_by_qm if row["question"] == question]
            q_idx = matching_rows[0].get("question_index", "")
            row = [latex_escape(question_short_from_text(question, q_idx))]
            for mode in modes:
                item = lookup[(question, mode)]
                row.append(fmt_pm(item["total_mean"], item["total_std"], 2))
            rows.append(row)
        write_tex(
            PAPER_GEN_DIR / "table_cross_domain_question.tex",
            "跨领域初步验证的问题级 LLM 总分明细（均值 $\\pm$ 标准差）",
            "tab:jos-cross-domain-question",
            ["研究问题"] + [latex_escape(m) for m in modes],
            rows,
        )

    pd.DataFrame(llm_by_mode).to_csv(JOS_TABLE_DIR / "summary_cross_domain_llm.csv", index=False, encoding="utf-8-sig")


def export_significance_table() -> None:
    pairwise_path = JOS_STATS_DIR / "pairwise_wilcoxon.csv"
    if not pairwise_path.exists():
        return
    df = pd.read_csv(pairwise_path, encoding="utf-8-sig")
    total_df = df[df["metric"] == "llm_total"].copy()
    rows = []
    for _, row in total_df.iterrows():
        rows.append(
            [
                latex_escape(str(row["comparison"])),
                str(int(row["n"])),
                f"{float(row['mean_diff']):.2f}",
                f"[{float(row['ci95_low']):.2f}, {float(row['ci95_high']):.2f}]",
                f"{float(row['p_value']):.4f}",
                f"{float(row['p_value_holm']):.4f}",
                f"{float(row['effect_size_rbc']):.3f}",
            ]
        )
    write_tex(
        PAPER_GEN_DIR / "table_significance.tex",
        "关键配对比较的 Wilcoxon 检验结果（LLM 总分）",
        "tab:jos-significance",
        ["比较", "n", "均值差", "95\\% CI", "p", "Holm校正后p", "效应量"],
        rows,
        notes="注：均值差按“左侧模式减右侧模式”计算，效应量为 rank-biserial correlation。",
    )
    total_df.to_csv(JOS_TABLE_DIR / "significance_total.csv", index=False, encoding="utf-8-sig")


def export_prefixed_significance_table(prefix: str, caption: str, label: str, output_stem: str) -> None:
    pairwise_path = JOS_STATS_DIR / f"{prefix}_pairwise_wilcoxon.csv"
    if not pairwise_path.exists():
        return
    df = pd.read_csv(pairwise_path, encoding="utf-8-sig")
    total_df = df[df["metric"] == "llm_total"].copy()
    if total_df.empty:
        return
    rows = []
    for _, row in total_df.iterrows():
        rows.append(
            [
                latex_escape(str(row["comparison"])),
                str(int(row["n"])),
                f"{float(row['mean_diff']):.2f}",
                f"[{float(row['ci95_low']):.2f}, {float(row['ci95_high']):.2f}]",
                f"{float(row['p_value']):.4f}",
                f"{float(row['p_value_holm']):.4f}",
                f"{float(row['effect_size_rbc']):.3f}",
            ]
        )
    write_tex(
        PAPER_GEN_DIR / f"{output_stem}.tex",
        caption,
        label,
        ["比较", "n", "均值差", "95\\% CI", "p", "Holm校正后p", "效应量"],
        rows,
        notes="注：均值差按“左侧模式减右侧模式”计算，效应量为 rank-biserial correlation。",
    )
    total_df.to_csv(JOS_TABLE_DIR / f"{output_stem}.csv", index=False, encoding="utf-8-sig")


def export_human_review_table() -> None:
    summary_path = JOS_HUMAN_REVIEW_DIR / "human_review_summary_by_mode.csv"
    if not summary_path.exists():
        return
    rows_df = pd.read_csv(summary_path, encoding="utf-8-sig")
    long_path = JOS_HUMAN_REVIEW_DIR / "human_review_long.csv"
    agreement_path = JOS_HUMAN_REVIEW_DIR / "human_review_agreement.json"
    reviewer_count = 0
    if long_path.exists():
        reviewer_count = int(pd.read_csv(long_path, encoding="utf-8-sig")["reviewer_id"].nunique())
    agreement_note = ""
    if agreement_path.exists():
        agreement = json.loads(agreement_path.read_text(encoding="utf-8"))
        icc = agreement.get("icc_2_k")
        if icc is not None:
            agreement_note = f" 评审间一致性以 ICC(2,k)={icc:.3f} 报告。"
    metrics = [
        ("relevance_mean", "相关性"),
        ("specificity_mean", "针对性"),
        ("method_quality_mean", "方法合理性"),
        ("innovation_mean", "创新性"),
        ("depth_mean", "深度"),
        ("executability_mean", "可执行性"),
        ("overall_mean", "总体均分"),
    ]
    modes = list(rows_df["mode"])
    data = by_mode(rows_df.to_dict("records"))
    rows = []
    for mean_key, label in metrics:
        std_key = mean_key.replace("_mean", "_std")
        row = [latex_escape(label)]
        for mode in modes:
            row.append(fmt_pm(data[mode][mean_key], data[mode][std_key], 2))
        rows.append(row)
    write_tex(
        PAPER_GEN_DIR / "table_human_review.tex",
        "人工盲评结果汇总（多位评审的均值 $\\pm$ 标准差）",
        "tab:jos-human-review",
        ["维度"] + [latex_escape(mode) for mode in modes],
        rows,
        notes=f"注：人工盲评对象为匿名化后的规划方案，不包含执行代码。当前汇总基于 {reviewer_count or '待定'} 位评审的有效回收。{agreement_note}",
    )
    rows_df.to_csv(JOS_TABLE_DIR / "human_review.csv", index=False, encoding="utf-8-sig")


def export_current_evidence_snapshot() -> None:
    summary_path = JOS_STATS_DIR / "significance_tests.json"
    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        data = {"friedman": [], "pairwise": []}
    def load_progress(path: Path) -> dict:
        progress_path = path / "repeated_progress_summary.json"
        if not progress_path.exists():
            return {}
        return json.loads(progress_path.read_text(encoding="utf-8"))

    main_progress = load_progress(REPEATED_DIR)
    external_progress = load_progress(EXTERNAL_REPEATED_DIR)
    transfer_progress = load_progress(TRANSFER_REPEATED_DIR)
    cross_domain_progress = load_progress(CROSS_DOMAIN_REPEATED_DIR)

    lines = [
        "# 当前证据快照",
        "",
        "- 主证据源：`outputs/repeated_experiments_full/`",
        f"- 当前主证据完成度：`{main_progress.get('completed_total', 'N/A')}/{main_progress.get('expected_total', 'N/A')}`",
        "- 当前可用于正文的主张已经冻结，禁止回退到单次实验口径。",
        "",
        "## 扩展证据目录",
        "",
        f"- 外部机制基线：`{EXTERNAL_REPEATED_DIR.as_posix()}` ({external_progress.get('completed_total', 0)}/{external_progress.get('expected_total', 'N/A')})",
        f"- 子领域稳定性验证：`{TRANSFER_REPEATED_DIR.as_posix()}` ({transfer_progress.get('completed_total', 0)}/{transfer_progress.get('expected_total', 'N/A')})",
        f"- 跨领域初步验证：`{CROSS_DOMAIN_REPEATED_DIR.as_posix()}` ({cross_domain_progress.get('completed_total', 0)}/{cross_domain_progress.get('expected_total', 'N/A')})",
        f"- 人工盲评：`{JOS_HUMAN_REVIEW_DIR.as_posix()}` {'(已生成)' if JOS_HUMAN_REVIEW_DIR.exists() else '(待生成)'}",
        "",
        "## 已生成统计文件",
        "",
        f"- Friedman: `{(JOS_STATS_DIR / 'friedman_tests.csv').as_posix()}`",
        f"- Pairwise Wilcoxon: `{(JOS_STATS_DIR / 'pairwise_wilcoxon.csv').as_posix()}`",
        "",
        "## 统计摘要",
        "",
    ]
    for row in data.get("friedman", []):
        lines.append(f"- {row['test']}: statistic={row['statistic']}, p={row['p_value']}")
    (PAPER_GEN_DIR / "current_evidence_snapshot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    export_mode_tables()
    export_question_tables()
    export_significance_table()
    export_external_tables()
    export_transfer_tables()
    export_cross_domain_tables()
    export_prefixed_significance_table(
        "external_main",
        "完整系统与外部机制基线的 Wilcoxon 检验结果（LLM 总分）",
        "tab:jos-external-significance",
        "table_external_significance",
    )
    export_prefixed_significance_table(
        "transfer_iot_auto",
        "子领域稳定性验证关键配对比较的 Wilcoxon 检验结果（LLM 总分）",
        "tab:jos-transfer-significance",
        "table_transfer_significance",
    )
    export_human_review_table()
    export_current_evidence_snapshot()
    print(f"Saved tables to {PAPER_GEN_DIR}")
    print(f"Saved CSVs to {JOS_TABLE_DIR}")


if __name__ == "__main__":
    main()
