from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    ABLATION_MODES,
    AUTO_BY_MODE_PATH,
    CROSS_DOMAIN_MODE_ORDER,
    CROSS_DOMAIN_REPEATED_DIR,
    EXTERNAL_MODE_ORDER,
    EXTERNAL_REPEATED_DIR,
    JOS_HUMAN_REVIEW_DIR,
    JOS_FIG_DIR,
    LLM_BY_MODE_PATH,
    MAIN_MODES,
    MODE_COLORS,
    MODE_PLOT_LABELS,
    PAPER_FIG_DIR,
    SUBDOMAIN_MODE_ORDER,
    TRANSFER_REPEATED_DIR,
    by_mode,
    ensure_dirs,
    load_csv,
    load_if_exists,
    repeated_file_bundle,
)


matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "KaiTi"]
matplotlib.rcParams["axes.unicode_minus"] = False


def merge_mode_level_rows(primary_rows: list[dict], fallback_rows: list[dict], modes: list[str]) -> list[dict]:
    merged = {}
    for row in primary_rows:
        merged[row["mode"]] = row
    for row in fallback_rows:
        merged.setdefault(row["mode"], row)
    return [merged[mode] for mode in modes if mode in merged]


def save_all(filename: str, dpi: int = 240) -> None:
    for base in [JOS_FIG_DIR, PAPER_FIG_DIR]:
        base.mkdir(parents=True, exist_ok=True)
        plt.savefig(base / filename, dpi=dpi, bbox_inches="tight", pad_inches=0.1)


def plot_framework_overview() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 4.6))
    ax.axis("off")

    boxes = {
        "input": (0.03, 0.38, 0.12, 0.22, "#e9f5ff", "研究问题\n+ 数据集"),
        "evidence": (0.20, 0.28, 0.18, 0.42, "#e6f4ea", "Evidence Grounding\nDataPreview / GraphPreview\n分层抽样洞察"),
        "knowledge": (0.42, 0.28, 0.18, 0.42, "#fff3cd", "Knowledge-Constrained\nPlanning\n因果图谱 + 方法图谱"),
        "execution": (0.64, 0.28, 0.15, 0.42, "#f8d7da", "执行与反馈\n代码生成\n结果校验\n差距识别"),
        "output": (0.84, 0.38, 0.12, 0.22, "#ede7f6", "结构化分析计划\n+ 执行产物"),
    }
    for x, y, w, h, color, text in boxes.values():
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#4a4a4a", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)

    kg1 = plt.Rectangle((0.44, 0.08), 0.07, 0.11, facecolor="#fff9e6", edgecolor="#4a4a4a", linewidth=1.0)
    kg2 = plt.Rectangle((0.52, 0.08), 0.07, 0.11, facecolor="#fff9e6", edgecolor="#4a4a4a", linewidth=1.0)
    ax.add_patch(kg1)
    ax.add_patch(kg2)
    ax.text(0.475, 0.135, "因果图谱", ha="center", va="center", fontsize=9.5)
    ax.text(0.555, 0.135, "方法图谱", ha="center", va="center", fontsize=9.5)

    arrow_style = dict(arrowstyle="->", color="#333333", lw=1.4)
    ax.annotate("", xy=(0.20, 0.49), xytext=(0.15, 0.49), arrowprops=arrow_style)
    ax.annotate("", xy=(0.42, 0.49), xytext=(0.38, 0.49), arrowprops=arrow_style)
    ax.annotate("", xy=(0.64, 0.49), xytext=(0.60, 0.49), arrowprops=arrow_style)
    ax.annotate("", xy=(0.84, 0.49), xytext=(0.79, 0.49), arrowprops=arrow_style)
    ax.annotate("", xy=(0.68, 0.20), xytext=(0.76, 0.20), arrowprops=dict(arrowstyle="<-", color="#666666", lw=1.4))
    ax.text(0.72, 0.16, "执行反馈驱动再规划", ha="center", va="center", fontsize=10, color="#444444")
    ax.annotate("", xy=(0.50, 0.28), xytext=(0.50, 0.19), arrowprops=dict(arrowstyle="->", color="#444444", lw=1.2))
    ax.annotate("", xy=(0.56, 0.28), xytext=(0.56, 0.19), arrowprops=dict(arrowstyle="->", color="#444444", lw=1.2))

    ax.set_title("图1 期刊稿方法总框架图", fontsize=13, pad=12)
    plt.tight_layout()
    save_all("fig1_framework_overview.png")
    plt.close(fig)


def plot_three_mechanisms() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.axis("off")

    panels = [
        (0.03, 0.16, 0.29, 0.68, "#e6f4ea", "Evidence Grounding", "输入\n问题 + 数据预览 + 图预览\n\n中间状态\n字段统计 / 结构特征 / 可检验洞察\n\n输出\n证据化规划上下文"),
        (0.355, 0.16, 0.29, 0.68, "#fff3cd", "Knowledge-Constrained Planning", "输入\n证据化上下文 + 双知识图谱\n\n中间状态\n假设空间约束 / 方法空间约束\n\n输出\n结构化分析计划 JSON"),
        (0.68, 0.16, 0.29, 0.68, "#f8d7da", "Iterative Refinement", "输入\n首轮执行结果 + 误差/缺口\n\n中间状态\n补证据 / 换方法 / 增控制\n\n输出\n第二轮修订计划与深化分析"),
    ]
    for x, y, w, h, color, title, text in panels:
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#4a4a4a", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.08, title, ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.03, text, ha="center", va="center", fontsize=10.5, linespacing=1.4)
    ax.annotate("", xy=(0.355, 0.50), xytext=(0.32, 0.50), arrowprops=dict(arrowstyle="->", color="#333333", lw=1.4))
    ax.annotate("", xy=(0.68, 0.50), xytext=(0.645, 0.50), arrowprops=dict(arrowstyle="->", color="#333333", lw=1.4))

    ax.set_title("图2 三机制输入-状态-输出图", fontsize=13, pad=12)
    plt.tight_layout()
    save_all("fig2_three_mechanisms.png")
    plt.close(fig)


def plot_main_total(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    vals = [float(agg[m]["total_mean"]) for m in MAIN_MODES]
    errs = [float(agg[m]["total_std"]) for m in MAIN_MODES]
    labels = [MODE_PLOT_LABELS[m] for m in MAIN_MODES]
    colors = [MODE_COLORS[m] for m in MAIN_MODES]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    x = np.arange(len(MAIN_MODES))
    bars = ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, labels)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, v, e in zip(bars, vals, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + e + 0.35, f"{v:.2f}\n±{e:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("图3 四方案主实验总分对比", fontsize=13)
    plt.tight_layout()
    save_all("fig3_main_total_scores.png")
    plt.close(fig)


def plot_six_mode_overview(llm_rows: list[dict]) -> None:
    order = ["D_baseline0", "A_template", "B_data_aware", "C_iterative", "E_ablate_data", "F_ablate_kg"]
    agg = by_mode(llm_rows)
    vals = [float(agg[m]["total_mean"]) for m in order]
    errs = [float(agg[m]["total_std"]) for m in order]
    labels = [MODE_PLOT_LABELS[m] for m in order]
    colors = [MODE_COLORS[m] for m in order]

    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    x = np.arange(len(order))
    ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, labels)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_title("图4 六模式总览（仅作全局观察）", fontsize=13)
    plt.tight_layout()
    save_all("fig4_six_mode_overview.png")
    plt.close(fig)


def plot_main_radar(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    dims = [
        ("relevance_mean", "相关性"),
        ("specificity_mean", "针对性"),
        ("method_quality_mean", "方法合理性"),
        ("innovation_mean", "创新性"),
        ("depth_mean", "深度"),
    ]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(7.0, 7.0))
    ax = plt.subplot(111, polar=True)
    for mode in MAIN_MODES:
        values = [float(agg[mode][key]) for key, _ in dims]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, color=MODE_COLORS[mode], label=mode)
        ax.fill(angles, values, alpha=0.08, color=MODE_COLORS[mode])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([label for _, label in dims])
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_title("图5 四方案五维评分雷达图", pad=18, fontsize=13)
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.15))
    plt.tight_layout()
    save_all("fig5_main_radar.png")
    plt.close(fig)


def plot_ablation_total(llm_rows: list[dict], auto_rows: list[dict]) -> None:
    llm = by_mode(llm_rows)
    auto = by_mode(auto_rows)
    vals = [float(llm[m]["total_mean"]) for m in ABLATION_MODES]
    errs = [float(llm[m]["total_std"]) for m in ABLATION_MODES]
    refs = [float(auto[m]["specificity_references_mean"]) for m in ABLATION_MODES]
    labels = [MODE_PLOT_LABELS[m] for m in ABLATION_MODES]
    colors = [MODE_COLORS[m] for m in ABLATION_MODES]

    fig, ax1 = plt.subplots(figsize=(8.4, 5.0))
    x = np.arange(len(ABLATION_MODES))
    ax1.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax1.set_xticks(x, labels)
    ax1.set_ylabel("LLM-as-Judge 总分（/25）")
    ax1.set_ylim(0, 27)
    ax1.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax1.set_axisbelow(True)

    ax2 = ax1.twinx()
    ax2.plot(x, refs, color="#111111", marker="o", linewidth=1.8)
    ax2.set_ylabel("针对性引用数均值")
    ax2.set_ylim(0, max(refs) + 5)

    ax1.set_title("图6 组件消融结果：总分与针对性引用数", fontsize=13)
    plt.tight_layout()
    save_all("fig6_ablation_total.png")
    plt.close(fig)


def plot_external_total(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    modes = [mode for mode in EXTERNAL_MODE_ORDER if mode in agg]
    if len(modes) < 2:
        return
    vals = [float(agg[m]["total_mean"]) for m in modes]
    errs = [float(agg[m]["total_std"]) for m in modes]
    labels = [MODE_PLOT_LABELS[m] for m in modes]
    colors = [MODE_COLORS[m] for m in modes]

    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    x = np.arange(len(modes))
    bars = ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, labels)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_title("图7 完整系统与外部机制基线对比", fontsize=13)
    for bar, v, e in zip(bars, vals, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + e + 0.3, f"{v:.2f}\n±{e:.2f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    save_all("fig7_external_total.png")
    plt.close(fig)


def plot_transfer_total(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    modes = [mode for mode in SUBDOMAIN_MODE_ORDER if mode in agg] or list(agg.keys())
    vals = [float(agg[m]["total_mean"]) for m in modes]
    errs = [float(agg[m]["total_std"]) for m in modes]
    labels = [MODE_PLOT_LABELS.get(m, m) for m in modes]
    colors = [MODE_COLORS.get(m, "#7f8c8d") for m in modes]

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    x = np.arange(len(modes))
    bars = ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, labels)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_title("图8 子领域稳定性验证总分对比", fontsize=13)
    for bar, v, e in zip(bars, vals, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + e + 0.3, f"{v:.2f}\n±{e:.2f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    save_all("fig8_transfer_total.png")
    plt.close(fig)


def plot_cross_domain_total(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    modes = [mode for mode in CROSS_DOMAIN_MODE_ORDER if mode in agg] or list(agg.keys())
    vals = [float(agg[m]["total_mean"]) for m in modes]
    errs = [float(agg[m]["total_std"]) for m in modes]
    labels = [MODE_PLOT_LABELS.get(m, m) for m in modes]
    colors = [MODE_COLORS.get(m, "#7f8c8d") for m in modes]

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    x = np.arange(len(modes))
    bars = ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, labels)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_title("图9 跨领域初步验证总分对比", fontsize=13)
    for bar, v, e in zip(bars, vals, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + e + 0.3, f"{v:.2f}\n±{e:.2f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    save_all("fig9_cross_domain_total.png")
    plt.close(fig)


def plot_human_review() -> None:
    summary_path = JOS_HUMAN_REVIEW_DIR / "human_review_summary_by_mode.csv"
    if not summary_path.exists():
        return
    rows = load_csv(summary_path)
    agg = by_mode(rows)
    modes = list(agg.keys())
    vals = [float(agg[m]["overall_mean"]) for m in modes]
    errs = [float(agg[m]["overall_std"]) for m in modes]
    colors = [MODE_COLORS.get(m, "#7f8c8d") for m in modes]

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    x = np.arange(len(modes))
    bars = ax.bar(x, vals, yerr=errs, color=colors, edgecolor="#444444", linewidth=0.8, capsize=4)
    ax.set_xticks(x, [MODE_PLOT_LABELS.get(m, m) for m in modes])
    ax.set_ylabel("人工盲评总体均分（/5）")
    ax.set_ylim(0, 5.5)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_title("图10 人工盲评总体评分对比", fontsize=13)
    for bar, v, e in zip(bars, vals, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + e + 0.08, f"{v:.2f}\n±{e:.2f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    save_all("fig10_human_review.png")
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    llm_rows = load_csv(LLM_BY_MODE_PATH)
    auto_rows = load_csv(AUTO_BY_MODE_PATH)
    plot_framework_overview()
    plot_three_mechanisms()
    plot_main_total(llm_rows)
    plot_six_mode_overview(llm_rows)
    plot_main_radar(llm_rows)
    plot_ablation_total(llm_rows, auto_rows)
    external_bundle = repeated_file_bundle(EXTERNAL_REPEATED_DIR)
    external_llm_rows = merge_mode_level_rows(
        load_if_exists(external_bundle["llm_by_mode"]),
        llm_rows,
        EXTERNAL_MODE_ORDER,
    )
    if external_llm_rows:
        plot_external_total(external_llm_rows)
    transfer_bundle = repeated_file_bundle(TRANSFER_REPEATED_DIR)
    transfer_llm_rows = load_if_exists(transfer_bundle["llm_by_mode"])
    if transfer_llm_rows:
        plot_transfer_total(transfer_llm_rows)
    cross_domain_bundle = repeated_file_bundle(CROSS_DOMAIN_REPEATED_DIR)
    cross_domain_llm_rows = load_if_exists(cross_domain_bundle["llm_by_mode"])
    if cross_domain_llm_rows:
        plot_cross_domain_total(cross_domain_llm_rows)
    plot_human_review()
    print(f"Saved figures to {JOS_FIG_DIR}")
    print(f"Saved figures to {PAPER_FIG_DIR}")


if __name__ == "__main__":
    main()
