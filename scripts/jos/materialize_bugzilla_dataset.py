from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ILLEGAL_XML_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def clean_illegal_chars(value: object) -> object:
    """Remove characters that openpyxl rejects in worksheet cells."""
    if isinstance(value, str):
        return ILLEGAL_XML_CHARS_RE.sub("", value)
    return value

from scripts.jos.common import JOS_DATASET_DIR, ensure_dirs
from scripts.jos.experiment_registry import get_dataset_config


CANONICAL_COLUMNS = {
    "title": ["title", "summary", "bug_summary", "short_desc"],
    "description": ["description", "desc", "bug_description"],
    "severity": ["severity", "bug_severity"],
    "component": ["component"],
    "product/project": ["product/project", "product", "project"],
    "created_at": ["created_at", "creation_time", "created", "opendate"],
    "resolved_at": ["resolved_at", "cf_last_resolved", "resolved", "resolution_time"],
    "reporter": ["reporter", "creator", "reported_by"],
    "assignee": ["assignee", "assigned_to"],
    "status": ["status", "bug_status"],
    "priority": ["priority"],
    "comments_count": ["comments_count", "comment_count", "longdescs_count"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 Bugzilla 原始导出整理为跨领域验证所需的标准数据集")
    parser.add_argument("--source-file", type=str, required=True, help="原始 Bugzilla 导出文件，支持 csv/xlsx/json")
    parser.add_argument("--dataset", type=str, default="cross_domain_bugzilla", help="目标数据集配置 ID")
    parser.add_argument("--sheet-name", type=str, default="", help="读取 Excel 时使用的工作表名")
    parser.add_argument("--force", action="store_true", help="已存在时强制覆盖")
    return parser.parse_args()


def load_frame(source_file: Path, sheet_name: str) -> pd.DataFrame:
    suffix = source_file.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source_file)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source_file, sheet_name=sheet_name or 0)
    if suffix == ".json":
        return pd.read_json(source_file)
    raise ValueError(f"不支持的源文件格式: {source_file.suffix}")


def resolve_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lowered = {str(column).strip().lower(): column for column in df.columns}
    for alias in aliases:
        match = lowered.get(alias.lower())
        if match is not None:
            return str(match)
    return None


def main() -> int:
    args = parse_args()
    ensure_dirs()

    dataset = get_dataset_config(args.dataset)
    source_path = Path(args.source_file)
    target_path = PROJECT_ROOT / dataset.data_file
    target_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = JOS_DATASET_DIR / f"{dataset.dataset_id}_metadata.json"

    if target_path.exists() and not args.force:
        print(f"[SKIP] 已存在: {target_path}")
        return 0

    df = load_frame(source_path, args.sheet_name)
    standardized = {}
    resolved = {}
    for canonical, aliases in CANONICAL_COLUMNS.items():
        source_column = resolve_column(df, aliases)
        if source_column is None:
            if canonical in {
                "title",
                "description",
                "severity",
                "component",
                "product/project",
                "created_at",
                "reporter",
                "assignee",
            }:
                raise ValueError(f"缺少必需字段 `{canonical}`，当前列名为: {list(df.columns)}")
            continue
        standardized[canonical] = df[source_column]
        resolved[canonical] = source_column

    normalized_df = pd.DataFrame(standardized)
    normalized_df = normalized_df.apply(lambda col: col.map(clean_illegal_chars))
    with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
        normalized_df.to_excel(writer, sheet_name=dataset.sheet_name, index=False)

    metadata = {
        "dataset_id": dataset.dataset_id,
        "source_file": str(source_path),
        "target_file": str(target_path),
        "row_count": int(len(normalized_df)),
        "column_count": int(len(normalized_df.columns)),
        "resolved_columns": resolved,
        "materialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 写入跨领域数据集: {target_path}")
    print(f"[OK] 写入元数据: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
