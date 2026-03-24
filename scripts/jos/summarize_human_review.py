from __future__ import annotations

import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import JOS_HUMAN_REVIEW_DIR, ensure_dirs


DIMENSIONS = [
    "relevance",
    "specificity",
    "method_quality",
    "innovation",
    "depth",
    "executability",
]


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compute_icc_two_way_random_absolute(pivot: pd.DataFrame) -> dict:
    matrix = pivot.to_numpy(dtype=float)
    n_items, n_reviewers = matrix.shape
    if n_items < 2 or n_reviewers < 2:
        return {}

    grand_mean = float(matrix.mean())
    item_means = matrix.mean(axis=1, keepdims=True)
    reviewer_means = matrix.mean(axis=0, keepdims=True)

    ssr = float(n_reviewers * np.square(item_means - grand_mean).sum())
    ssc = float(n_items * np.square(reviewer_means - grand_mean).sum())
    sse = float(np.square(matrix - item_means - reviewer_means + grand_mean).sum())

    msr = ssr / (n_items - 1)
    msc = ssc / (n_reviewers - 1)
    mse = sse / ((n_items - 1) * (n_reviewers - 1))

    denominator_single = msr + (n_reviewers - 1) * mse + n_reviewers * (msc - mse) / n_items
    denominator_average = msr + (msc - mse) / n_items
    result = {
        "icc_2_1": round(float((msr - mse) / denominator_single), 4) if denominator_single else 0.0,
        "icc_2_k": round(float((msr - mse) / denominator_average), 4) if denominator_average else 0.0,
    }
    return result


def compute_reviewer_agreement(df: pd.DataFrame) -> dict:
    agreement = {"shared_items": 0, "reviewer_count": 0}
    if df.empty or "reviewer_id" not in df.columns:
        return agreement
    pivot = df.pivot_table(
        index=["comparison_group", "question_index", "anonymous_label"],
        columns="reviewer_id",
        values="overall",
    ).dropna()
    agreement["shared_items"] = int(len(pivot))
    agreement["reviewer_count"] = int(pivot.shape[1])
    if pivot.shape[1] >= 2:
        pearsons = []
        spearmans = []
        abs_diffs = []
        for col_a, col_b in itertools.combinations(pivot.columns, 2):
            pearson = pivot[col_a].corr(pivot[col_b], method="pearson")
            spearman = pivot[col_a].corr(pivot[col_b], method="spearman")
            abs_diff = float((pivot[col_a] - pivot[col_b]).abs().mean())
            if not pd.isna(pearson):
                pearsons.append(float(pearson))
            if not pd.isna(spearman):
                spearmans.append(float(spearman))
            abs_diffs.append(abs_diff)
        if pearsons:
            agreement["pairwise_pearson_mean"] = round(float(np.mean(pearsons)), 4)
        if spearmans:
            agreement["pairwise_spearman_mean"] = round(float(np.mean(spearmans)), 4)
        if abs_diffs:
            agreement["pairwise_mean_abs_diff"] = round(float(np.mean(abs_diffs)), 4)
        agreement.update(compute_icc_two_way_random_absolute(pivot))
    return agreement


def main() -> None:
    ensure_dirs()
    admin_mapping = JOS_HUMAN_REVIEW_DIR / "admin" / "anonymous_label_mapping.csv"
    response_dir = JOS_HUMAN_REVIEW_DIR / "responses"
    if not admin_mapping.exists():
        raise FileNotFoundError(f"缺少匿名标签映射: {admin_mapping}")

    response_files = sorted(response_dir.glob("reviewer_*_filled.csv"))
    if not response_files:
        raise FileNotFoundError(f"未找到人工盲评响应文件: {response_dir}")

    mapping_df = pd.DataFrame(load_csv(admin_mapping))
    response_frames = []
    for path in response_files:
        response_frames.append(pd.DataFrame(load_csv(path)))
    responses = pd.concat(response_frames, ignore_index=True)
    if responses.empty:
        raise ValueError("人工盲评响应文件为空")

    for dim in DIMENSIONS:
        responses[dim] = pd.to_numeric(responses[dim], errors="coerce")
    responses["overall"] = responses[DIMENSIONS].mean(axis=1)

    merged = responses.merge(mapping_df, on=["comparison_group", "question_index", "anonymous_label"], how="left")
    if merged["mode"].isna().any():
        missing = merged[merged["mode"].isna()][["comparison_group", "question_index", "anonymous_label"]]
        raise ValueError(f"存在无法映射模式的盲评样本: {missing.to_dict('records')}")

    long_path = JOS_HUMAN_REVIEW_DIR / "human_review_long.csv"
    merged.to_csv(long_path, index=False, encoding="utf-8-sig")

    summary_rows = []
    for mode, frame in merged.groupby("mode"):
        row = {"mode": mode, "n_items": int(len(frame))}
        for dim in DIMENSIONS + ["overall"]:
            row[f"{dim}_mean"] = round(float(frame[dim].mean()), 4)
            row[f"{dim}_std"] = round(float(frame[dim].std(ddof=0)), 4)
        summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows).sort_values("overall_mean", ascending=False)
    summary_path = JOS_HUMAN_REVIEW_DIR / "human_review_summary_by_mode.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    comparison_rows = []
    for (comparison_group, mode), frame in merged.groupby(["comparison_group", "mode"]):
        comparison_rows.append(
            {
                "comparison_group": comparison_group,
                "mode": mode,
                "n_items": int(len(frame)),
                "overall_mean": round(float(frame["overall"].mean()), 4),
                "overall_std": round(float(frame["overall"].std(ddof=0)), 4),
            }
        )
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_path = JOS_HUMAN_REVIEW_DIR / "human_review_summary_by_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False, encoding="utf-8-sig")

    agreement = compute_reviewer_agreement(merged)
    agreement_path = JOS_HUMAN_REVIEW_DIR / "human_review_agreement.json"
    agreement_path.write_text(json.dumps(agreement, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {long_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {comparison_path}")
    print(f"Saved: {agreement_path}")


if __name__ == "__main__":
    main()
