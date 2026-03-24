from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    EXTERNAL_REPEATED_DIR,
    LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH,
    STRONGEST_EXTERNAL_MECHANISM_PATH,
    repeated_file_bundle,
    ensure_dirs,
)


def main() -> None:
    ensure_dirs()
    bundle = repeated_file_bundle(EXTERNAL_REPEATED_DIR)
    llm_path = bundle["llm_by_mode"]
    auto_path = bundle["auto_by_mode"]
    if not llm_path.exists():
        raise FileNotFoundError(f"缺少外部基线 LLM 汇总: {llm_path}")
    if not auto_path.exists():
        raise FileNotFoundError(f"缺少外部基线自动指标汇总: {auto_path}")

    llm_df = pd.read_csv(llm_path, encoding="utf-8-sig")
    auto_df = pd.read_csv(auto_path, encoding="utf-8-sig")
    merged = llm_df.merge(auto_df[["mode", "specificity_references_mean", "specificity_references_std"]], on="mode", how="left")
    candidates = merged[merged["mode"].isin(["G_react_single_agent", "H_execution_feedback"])].copy()
    if candidates.empty:
        raise ValueError("外部基线汇总中未找到 G/H 模式")

    candidates.sort_values(
        by=["total_mean", "total_std", "specificity_references_mean"],
        ascending=[False, True, False],
        inplace=True,
    )
    chosen = candidates.iloc[0].to_dict()
    result = {
        "selected_mode": chosen["mode"],
        "selected_role": "strongest external mechanism baseline",
        "selection_rule": [
            "LLM total mean descending",
            "LLM total std ascending",
            "specificity_references mean descending",
        ],
        "candidates": candidates.to_dict("records"),
    }
    STRONGEST_EXTERNAL_MECHANISM_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Saved: {STRONGEST_EXTERNAL_MECHANISM_PATH}")
    print(f"Saved: {LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH}")


if __name__ == "__main__":
    main()
