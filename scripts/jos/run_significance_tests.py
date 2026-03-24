from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, wilcoxon

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    AUTO_PER_RUN_PATH,
    JOS_STATS_DIR,
    LLM_PER_RUN_PATH,
    MODE_ORDER,
    PAIRWISE_COMPARISONS,
    repeated_file_bundle,
    ensure_dirs,
)


SEED = 20260314
BOOTSTRAP_SAMPLES = 5000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 JOS 统计检验")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="",
        help="重复实验汇总目录；为空时使用 outputs/repeated_experiments_full",
    )
    parser.add_argument(
        "--mode-order",
        type=str,
        default=",".join(MODE_ORDER),
        help="Friedman 检验使用的模式顺序",
    )
    parser.add_argument(
        "--pairwise",
        type=str,
        default=",".join(f"{left}:{right}" for left, right in PAIRWISE_COMPARISONS),
        help="Wilcoxon 配对，格式 left:right,left:right",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="",
        help="输出文件名前缀，例如 external_main 或 transfer_iot_auto",
    )
    parser.add_argument(
        "--supplemental-dir",
        type=str,
        default="",
        help="补充汇总目录列表，用逗号分隔；用于跨证据池合并模式后再做统计",
    )
    return parser.parse_args()


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_pairwise(value: str) -> list[tuple[str, str]]:
    pairs = []
    for item in parse_csv_list(value):
        left, right = item.split(":", 1)
        pairs.append((left.strip(), right.strip()))
    return pairs


def load_metric_frames(primary_dir: str, supplemental_dirs: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    dirs = []
    if primary_dir:
        dirs.append(Path(primary_dir))
    supplemental_paths = [Path(item) for item in supplemental_dirs if item]
    dirs.extend(supplemental_paths)

    if not dirs:
        return (
            pd.read_csv(LLM_PER_RUN_PATH, encoding="utf-8-sig"),
            pd.read_csv(AUTO_PER_RUN_PATH, encoding="utf-8-sig"),
        )

    llm_frames = []
    auto_frames = []
    for directory in dirs:
        bundle = repeated_file_bundle(directory)
        llm_frames.append(pd.read_csv(bundle["llm_per_run"], encoding="utf-8-sig"))
        auto_frames.append(pd.read_csv(bundle["auto_per_run"], encoding="utf-8-sig"))

    llm_df = pd.concat(llm_frames, ignore_index=True)
    auto_df = pd.concat(auto_frames, ignore_index=True)

    llm_df = llm_df.drop_duplicates(subset=["question_index", "question", "mode", "run_index"], keep="first")
    auto_df = auto_df.drop_duplicates(subset=["question_index", "question", "mode", "run_index"], keep="first")
    return llm_df, auto_df


def bootstrap_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    samples = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = rng.choice(values, size=len(values), replace=True)
        samples.append(float(np.mean(sample)))
    alpha = 1.0 - confidence
    low = float(np.quantile(samples, alpha / 2))
    high = float(np.quantile(samples, 1 - alpha / 2))
    return low, high


def rank_biserial(diff: np.ndarray) -> float:
    non_zero = diff[diff != 0]
    if len(non_zero) == 0:
        return 0.0
    ranks = rankdata(np.abs(non_zero))
    pos = float(ranks[non_zero > 0].sum())
    neg = float(ranks[non_zero < 0].sum())
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def holm_correction(p_values: Iterable[float]) -> list[float]:
    pairs = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(pairs)
    m = len(pairs)
    running = 0.0
    for i, (idx, p_val) in enumerate(pairs):
        corrected = min(1.0, (m - i) * p_val)
        running = max(running, corrected)
        adjusted[idx] = running
    return adjusted


def run_friedman(llm_df: pd.DataFrame, mode_order: list[str]) -> list[dict]:
    wide_six = (
        llm_df.pivot_table(index=["question_index", "run_index"], columns="mode", values="total")
        .reindex(columns=mode_order)
        .dropna()
    )
    specs = [("mode_set_total", wide_six)]
    if set(["D_baseline0", "A_template", "B_data_aware", "C_iterative"]).issubset(mode_order):
        wide_main = wide_six[["D_baseline0", "A_template", "B_data_aware", "C_iterative"]]
        specs.append(("main_total", wide_main))
    if set(["C_iterative", "E_ablate_data", "F_ablate_kg"]).issubset(mode_order):
        wide_ablation = wide_six[["C_iterative", "E_ablate_data", "F_ablate_kg"]]
        specs.append(("ablation_total", wide_ablation))
    rows = []
    for name, frame in specs:
        # Friedman 检验至少需要 3 组配对样本；双模式比较只保留后续 Wilcoxon。
        if frame.empty or frame.shape[1] < 3:
            continue
        stat, p_val = friedmanchisquare(*[frame[col].to_numpy() for col in frame.columns])
        rows.append(
            {
                "test": name,
                "blocks": int(frame.shape[0]),
                "k": int(frame.shape[1]),
                "statistic": round(float(stat), 6),
                "p_value": round(float(p_val), 8),
            }
        )
    return rows


def run_pairwise(llm_df: pd.DataFrame, auto_df: pd.DataFrame, pairwise_comparisons: list[tuple[str, str]]) -> list[dict]:
    llm_wide = llm_df.pivot_table(index=["question_index", "run_index"], columns="mode", values="total")
    auto_wide = auto_df.pivot_table(index=["question_index", "run_index"], columns="mode", values="specificity_references")

    rows = []
    p_values = []
    for left, right in pairwise_comparisons:
        if left not in llm_wide.columns or right not in llm_wide.columns:
            continue
        diff_total = (llm_wide[left] - llm_wide[right]).dropna().to_numpy(dtype=float)
        if len(diff_total) == 0:
            continue
        diff_spec = np.array([], dtype=float)
        if left in auto_wide.columns and right in auto_wide.columns:
            diff_spec = (auto_wide[left] - auto_wide[right]).dropna().to_numpy(dtype=float)

        total_stat = wilcoxon(diff_total, zero_method="wilcox", alternative="two-sided", mode="auto")
        total_low, total_high = bootstrap_ci(diff_total)

        rows.append(
            {
                "comparison": f"{left} vs {right}",
                "metric": "llm_total",
                "n": int(len(diff_total)),
                "mean_diff": round(float(np.mean(diff_total)), 4),
                "median_diff": round(float(np.median(diff_total)), 4),
                "ci95_low": round(total_low, 4),
                "ci95_high": round(total_high, 4),
                "statistic": round(float(total_stat.statistic), 6),
                "p_value": round(float(total_stat.pvalue), 8),
                "effect_size_rbc": round(rank_biserial(diff_total), 6),
            }
        )
        p_values.append(float(total_stat.pvalue))

        if len(diff_spec) > 0:
            spec_stat = wilcoxon(diff_spec, zero_method="wilcox", alternative="two-sided", mode="auto")
            spec_low, spec_high = bootstrap_ci(diff_spec)
            rows.append(
                {
                    "comparison": f"{left} vs {right}",
                    "metric": "specificity_references",
                    "n": int(len(diff_spec)),
                    "mean_diff": round(float(np.mean(diff_spec)), 4),
                    "median_diff": round(float(np.median(diff_spec)), 4),
                    "ci95_low": round(spec_low, 4),
                    "ci95_high": round(spec_high, 4),
                    "statistic": round(float(spec_stat.statistic), 6),
                    "p_value": round(float(spec_stat.pvalue), 8),
                    "effect_size_rbc": round(rank_biserial(diff_spec), 6),
                }
            )
            p_values.append(float(spec_stat.pvalue))

    adjusted = holm_correction(p_values)
    for row, corrected in zip(rows, adjusted):
        row["p_value_holm"] = round(float(corrected), 8)
        row["significant_0_05"] = bool(corrected < 0.05)
    return rows


def main() -> None:
    ensure_dirs()
    args = parse_args()

    mode_order = parse_csv_list(args.mode_order)
    pairwise = parse_pairwise(args.pairwise)
    supplemental_dirs = parse_csv_list(args.supplemental_dir)

    llm_df, auto_df = load_metric_frames(args.input_dir, supplemental_dirs)

    friedman_rows = run_friedman(llm_df, mode_order)
    pairwise_rows = run_pairwise(llm_df, auto_df, pairwise)

    friedman_df = pd.DataFrame(friedman_rows)
    pairwise_df = pd.DataFrame(pairwise_rows)

    prefix = f"{args.output_prefix}_" if args.output_prefix else ""
    friedman_path = JOS_STATS_DIR / f"{prefix}friedman_tests.csv"
    pairwise_path = JOS_STATS_DIR / f"{prefix}pairwise_wilcoxon.csv"
    summary_path = JOS_STATS_DIR / f"{prefix}significance_tests.json"

    friedman_df.to_csv(friedman_path, index=False, encoding="utf-8-sig")
    pairwise_df.to_csv(pairwise_path, index=False, encoding="utf-8-sig")

    payload = {
        "seed": SEED,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "friedman": friedman_rows,
        "pairwise": pairwise_rows,
        "mode_order": mode_order,
        "pairwise_comparisons": pairwise,
        "input_dir": args.input_dir or str(LLM_PER_RUN_PATH.parent),
        "supplemental_dirs": supplemental_dirs,
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved: {friedman_path}")
    print(f"Saved: {pairwise_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
