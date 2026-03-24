from pathlib import Path
import csv

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# 中文字体配置（Windows）
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

ROOT = Path(__file__).resolve().parents[2]
REPEATED_DIR = ROOT / "outputs" / "repeated_experiments_full"
LLM_BY_MODE_PATH = REPEATED_DIR / "repeated_llm_scores_summary_by_mode.csv"
AUTO_BY_MODE_PATH = REPEATED_DIR / "repeated_auto_metrics_summary_by_mode.csv"
DOC_FIG_DIR = ROOT / "docs" / "thesis" / "figures"
LATEX_FIG_DIR = ROOT / "docs" / "thesis" / "中国人民大学信息学院硕士毕业论文latex模板__1_ (1)" / "figures"

MODES = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
MODE_LABELS = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
MODE_PLOT_LABELS = [
    "D_baseline0\n(纯LLM基线)",
    "A_template\n(+知识图谱)",
    "B_data_aware\n(+数据感知)",
    "C_iterative\n(+两轮迭代)",
]
COLORS = ["#6c757d", "#adb5bd", "#74c69d", "#2d6a4f"]
SIX_WAY_MODES = ["A_template", "D_baseline0", "B_data_aware", "E_ablate_data", "C_iterative", "F_ablate_kg"]
SIX_WAY_LABELS = ["A\ntemplate", "D\nbaseline0", "B\ndata_aware", "E\nablate_data", "C\niterative", "F\nablate_kg"]
SIX_WAY_COLORS = ["#f28482", "#6cc3c0", "#67b7cc", "#eea889", "#97cdc3", "#e59898"]

FIG_EXPORTS = {
    "图5-1_四方案LLM总分柱状图.png": [
        DOC_FIG_DIR / "图5-1_四方案LLM总分柱状图.png",
        LATEX_FIG_DIR / "图5-1_四方案LLM总分柱状图.png",
        LATEX_FIG_DIR / "图5-2_四方案LLM总分柱状图.png",
    ],
    "图5-2_五维评分雷达图.png": [
        DOC_FIG_DIR / "图5-2_五维评分雷达图.png",
        LATEX_FIG_DIR / "图5-2_五维评分雷达图.png",
        LATEX_FIG_DIR / "图5-3_五维评分雷达图.png",
    ],
    "图5-3_自动化指标对比图.png": [
        DOC_FIG_DIR / "图5-3_自动化指标对比图.png",
        LATEX_FIG_DIR / "图5-3_自动化指标对比图.png",
        LATEX_FIG_DIR / "图5-1_自动化指标对比图.png",
    ],
    "图5-2_六方案LLM总分柱状图.png": [
        DOC_FIG_DIR / "图5-2_六方案LLM总分柱状图.png",
        LATEX_FIG_DIR / "图5-2_六方案LLM总分柱状图.png",
    ],
}


def ensure_dir() -> None:
    for export_paths in FIG_EXPORTS.values():
        for path in export_paths:
            path.parent.mkdir(parents=True, exist_ok=True)


def save_current_figure(filename: str, dpi: int = 220) -> None:
    for path in FIG_EXPORTS[filename]:
        plt.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.12)


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def by_mode(rows: list[dict]) -> dict[str, dict]:
    return {row["mode"]: row for row in rows}


def plot_llm_total_bar(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    vals = [float(agg[m]["total_mean"]) for m in MODES]
    errs = [float(agg[m]["total_std"]) for m in MODES]

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    x = np.arange(len(MODES))
    bars = ax.bar(
        x,
        vals,
        width=0.72,
        color=COLORS,
        edgecolor="#4f4f4f",
        linewidth=0.6,
        yerr=errs,
        error_kw={"elinewidth": 1.0, "ecolor": "#444444", "capsize": 4},
    )
    ax.set_xticks(x, MODE_PLOT_LABELS)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_xlabel("实验方案", labelpad=8)
    ax.set_ylim(0, max(vals) + 3.0)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.22)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, v, e in zip(bars, vals, errs):
        ax.annotate(
            f"{v:.2f}\n±{e:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, v + e),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 0.3},
        )

    fig.tight_layout()
    save_current_figure("图5-1_四方案LLM总分柱状图.png")
    plt.close(fig)


def plot_llm_total_bar_6way(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    vals = [float(agg[m]["total_mean"]) for m in SIX_WAY_MODES]
    errs = [float(agg[m]["total_std"]) for m in SIX_WAY_MODES]

    fig, ax = plt.subplots(figsize=(8.3, 5.0))
    x = np.arange(len(SIX_WAY_MODES))
    bars = ax.bar(
        x,
        vals,
        width=0.8,
        color=SIX_WAY_COLORS,
        edgecolor="#333333",
        linewidth=0.75,
        yerr=errs,
        error_kw={"elinewidth": 1.0, "ecolor": "#444444", "capsize": 4},
    )
    ax.set_xticks(x, SIX_WAY_LABELS)
    ax.set_ylabel("LLM-as-Judge 总分（/25）")
    ax.set_xlabel("实验方案", labelpad=4)
    ax.set_ylim(0, 27)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.22)
    ax.set_axisbelow(True)

    c_val = float(agg["C_iterative"]["total_mean"])
    ax.axhline(c_val, color="#6fbf73", linestyle="--", linewidth=1.0, alpha=0.9)
    ax.text(len(SIX_WAY_MODES) - 0.4, c_val + 0.18, f"C={c_val:.2f}", color="#333333", fontsize=9, ha="left", va="bottom")

    for bar, v, e in zip(bars, vals, errs):
        ax.annotate(
            f"{v:.2f}\n±{e:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, v + e),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    legend_text = (
        "六模式总览仅用于全局观察；机制归因以四方案渐进叠加与 C/E/F 组件消融为主。"
    )
    fig.text(
        0.5,
        0.975,
        legend_text,
        ha="center",
        va="top",
        fontsize=9.5,
        bbox={"boxstyle": "round,pad=0.32", "facecolor": "#f4efe7", "edgecolor": "#9a8f80", "alpha": 0.95},
    )

    fig.subplots_adjust(top=0.86, bottom=0.14, left=0.09, right=0.97)
    save_current_figure("图5-2_六方案LLM总分柱状图.png")
    plt.close(fig)


def plot_llm_radar(llm_rows: list[dict]) -> None:
    agg = by_mode(llm_rows)
    dims = ["relevance_mean", "specificity_mean", "method_quality_mean", "innovation_mean", "depth_mean"]
    dim_labels = ["相关性", "针对性", "方法合理性", "创新性", "深度"]

    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    plt.figure(figsize=(6.8, 6.8))
    ax = plt.subplot(111, polar=True)

    for m, lbl, c in zip(MODES, MODE_LABELS, COLORS):
        vals = [float(agg[m][d]) for d in dims]
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2, label=lbl, color=c)
        ax.fill(angles, vals, alpha=0.08, color=c)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_labels)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_ylim(0, 5)
    plt.title("图 5-2 五维评分雷达图", pad=20)
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.15))
    plt.tight_layout()
    save_current_figure("图5-2_五维评分雷达图.png")
    plt.close()


def plot_auto_key_metrics(auto_rows: list[dict]) -> None:
    agg = by_mode(auto_rows)
    metrics = [
        ("column_coverage_mean", "列覆盖率"),
        ("method_diversity_mean", "方法多样性"),
        ("specificity_references_mean", "针对性引用数"),
        ("parameter_richness_mean", "参数丰富度"),
    ]

    x = np.arange(len(metrics))
    width = 0.18

    plt.figure(figsize=(9, 4.8))
    for idx, (m, label, c) in enumerate(zip(MODES, MODE_LABELS, COLORS)):
        y = [float(agg[m][k]) for k, _ in metrics]
        plt.bar(x + (idx - 1.5) * width, y, width=width, label=label, color=c)

    plt.xticks(x, [name for _, name in metrics])
    plt.ylabel("指标值")
    plt.title("图 5-3 关键自动化指标对比")
    plt.legend(title="方案")
    plt.tight_layout()
    save_current_figure("图5-3_自动化指标对比图.png")
    plt.close()


def main() -> None:
    ensure_dir()
    llm_rows = load_csv(LLM_BY_MODE_PATH)
    auto_rows = load_csv(AUTO_BY_MODE_PATH)
    plot_llm_total_bar(llm_rows)
    plot_llm_total_bar_6way(llm_rows)
    plot_llm_radar(llm_rows)
    plot_auto_key_metrics(auto_rows)
    print("图表已导出至:")
    print(f"- {DOC_FIG_DIR}")
    print(f"- {LATEX_FIG_DIR}")


if __name__ == "__main__":
    main()
