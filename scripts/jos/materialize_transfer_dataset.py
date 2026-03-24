from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import JOS_DATASET_DIR, ensure_dirs
from scripts.jos.experiment_registry import get_dataset_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="物化期刊稿迁移实验数据集")
    parser.add_argument(
        "--dataset",
        type=str,
        default="transfer_iot_auto",
        help="迁移数据集配置 ID",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="已存在时强制重建数据集文件",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    dataset = get_dataset_config(args.dataset)
    if not dataset.source_dataset or not dataset.filter_column or not dataset.filter_value:
        raise ValueError(f"数据集 {dataset.dataset_id} 未配置物化参数")

    source_path = PROJECT_ROOT / dataset.source_dataset
    target_path = PROJECT_ROOT / dataset.data_file
    target_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = JOS_DATASET_DIR / f"{dataset.dataset_id}_metadata.json"

    if target_path.exists() and not args.force:
        print(f"[SKIP] 已存在: {target_path}")
        if metadata_path.exists():
            print(f"[META] {metadata_path}")
        return 0

    df = pd.read_excel(source_path, sheet_name=dataset.source_sheet_name)
    filtered = df[df[dataset.filter_column] == dataset.filter_value].copy()

    with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
        filtered.to_excel(writer, sheet_name=dataset.sheet_name, index=False)

    metadata = {
        "dataset_id": dataset.dataset_id,
        "label": dataset.label,
        "domain_name": dataset.domain_name,
        "source_dataset": dataset.source_dataset,
        "source_sheet_name": dataset.source_sheet_name,
        "filter_column": dataset.filter_column,
        "filter_value": dataset.filter_value,
        "target_file": dataset.data_file,
        "target_sheet_name": dataset.sheet_name,
        "row_count": int(len(filtered)),
        "column_count": int(len(filtered.columns)),
        "columns": list(filtered.columns),
        "materialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 写入迁移数据集: {target_path}")
    print(f"[OK] 写入元数据: {metadata_path}")
    print(json.dumps({k: metadata[k] for k in ['dataset_id', 'row_count', 'column_count', 'filter_value']}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
