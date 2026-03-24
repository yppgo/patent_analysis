from __future__ import annotations

import argparse
import json
import random
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


PAPER_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PAPER_DIR / "generated" / "cross_domain_public_jira.xlsx"
DEFAULT_METADATA = PAPER_DIR / "generated" / "cross_domain_public_jira_metadata.json"

ILLEGAL_XML_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

CANONICAL_COLUMNS = [
    "title",
    "description",
    "severity",
    "component",
    "product/project",
    "created_at",
    "resolved_at",
    "reporter",
    "assignee",
    "status",
    "priority",
    "comments_count",
]

PATHS = {
    "issue_key": ["key", "issue_key", "issue.idReadable", "issue.id"],
    "title": ["title", "summary", "fields.summary"],
    "description": [
        "description",
        "fields.description",
        "renderedFields.description",
        "issue.description",
    ],
    "severity": [
        "severity",
        "fields.severity",
        "fields.severity.name",
        "fields.customfield_severity",
        "fields.customfield_severity.name",
        "fields.customfield_severity.value",
    ],
    "component": [
        "component",
        "components",
        "fields.component",
        "fields.components",
    ],
    "product/project": [
        "product/project",
        "product",
        "project",
        "project_name",
        "fields.project.name",
        "fields.project.key",
        "fields.project",
    ],
    "project_key": [
        "project_key",
        "fields.project.key",
        "project.key",
    ],
    "created_at": [
        "created_at",
        "created",
        "fields.created",
        "issue.created",
    ],
    "resolved_at": [
        "resolved_at",
        "resolved",
        "resolutiondate",
        "fields.resolutiondate",
        "fields.resolved",
        "issue.resolved",
    ],
    "reporter": [
        "reporter",
        "creator",
        "fields.reporter",
        "fields.creator",
        "issue.reporter",
    ],
    "assignee": [
        "assignee",
        "assigned_to",
        "fields.assignee",
        "issue.assignee",
    ],
    "status": [
        "status",
        "fields.status",
        "fields.status.name",
        "issue.status",
    ],
    "priority": [
        "priority",
        "fields.priority",
        "fields.priority.name",
        "issue.priority",
    ],
    "issue_type": [
        "issuetype",
        "issue_type",
        "fields.issuetype",
        "fields.issuetype.name",
    ],
    "comments": [
        "comments",
        "comment",
        "fields.comments",
        "fields.comment",
        "fields.comment.comments",
    ],
    "comments_count": [
        "comments_count",
        "comment_count",
        "fields.comments.total",
        "fields.comment.total",
        "fields.comment.count",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 The Public Jira Dataset 的 issue 导出标准化为当前跨领域实验使用的 xlsx 接口"
    )
    parser.add_argument("--source-file", type=str, required=True, help="Jira issue 导出文件，支持 json/jsonl/ndjson/csv/xlsx")
    parser.add_argument("--json-root", type=str, default="", help="若 JSON 顶层不是列表，可用点路径指定 issue 数组位置")
    parser.add_argument("--sheet-name", type=str, default="cross_domain_public_jira", help="输出工作表名")
    parser.add_argument("--output-file", type=str, default=str(DEFAULT_OUTPUT), help="输出 xlsx 路径")
    parser.add_argument("--metadata-file", type=str, default=str(DEFAULT_METADATA), help="输出元数据 json 路径")
    parser.add_argument("--top-projects", type=int, default=0, help="按 issue 数选择 Top-N 项目；0 表示不过滤")
    parser.add_argument("--sample-per-project", type=int, default=0, help="每个项目均衡抽样条数；0 表示不抽样")
    parser.add_argument("--project-allowlist", type=str, default="", help="只保留这些项目，逗号分隔，可写项目名或 key")
    parser.add_argument("--seed", type=int, default=42, help="抽样随机种子")
    parser.add_argument("--force", action="store_true", help="已存在时强制覆盖")
    return parser.parse_args()


def clean_illegal_chars(value: object) -> object:
    if isinstance(value, str):
        return ILLEGAL_XML_CHARS_RE.sub("", value)
    return value


def looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and stripped[0] in "[{"


def maybe_parse_json(value: Any) -> Any:
    if isinstance(value, str) and looks_like_json(value):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def clean_text(text: str) -> str:
    compact = re.sub(r"[ \t\r\f\v]+", " ", text)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return ILLEGAL_XML_CHARS_RE.sub("", compact).strip()


def extract_rich_text(value: Any) -> str:
    value = maybe_parse_json(value)
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [extract_rich_text(item) for item in value]
        return clean_text("\n".join(part for part in parts if part))
    if isinstance(value, dict):
        parts: list[str] = []
        text = value.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
        for key in ("content", "items", "comments", "paragraphs"):
            nested = value.get(key)
            if nested is not None:
                parts.append(extract_rich_text(nested))
        if not parts:
            for key in ("value", "name", "description", "title"):
                nested = value.get(key)
                if isinstance(nested, str) and nested.strip():
                    parts.append(nested)
        return clean_text("\n".join(part for part in parts if part))
    return clean_text(str(value))


def normalize_datetime(value: Any) -> str:
    value = maybe_parse_json(value)
    if value in (None, "", "nan"):
        return ""
    try:
        dt = pd.to_datetime(value, errors="coerce", utc=True)
    except Exception:
        return clean_text(str(value))
    if pd.isna(dt):
        return clean_text(str(value))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_identity(value: Any) -> str:
    value = maybe_parse_json(value)
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        for key in ("displayName", "display_name", "accountId", "name", "key", "id", "emailAddress"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return clean_text(candidate)
        return clean_text(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return clean_text(str(value))


def normalize_label_like(value: Any) -> str:
    value = maybe_parse_json(value)
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        labels: list[str] = []
        for item in value:
            label = normalize_label_like(item)
            if label:
                labels.append(label)
        deduped: list[str] = []
        seen: set[str] = set()
        for label in labels:
            lowered = label.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(label)
        return "; ".join(deduped)
    if isinstance(value, dict):
        for key in ("name", "value", "key", "displayName"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return clean_text(candidate)
        return extract_rich_text(value)
    return clean_text(str(value))


def normalize_comment_count(raw_value: Any, comments_value: Any) -> int:
    raw_value = maybe_parse_json(raw_value)
    comments_value = maybe_parse_json(comments_value)
    for value in (raw_value, comments_value):
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            for key in ("total", "count", "size"):
                candidate = value.get(key)
                if isinstance(candidate, (int, float)):
                    return int(candidate)
            if isinstance(value.get("comments"), list):
                return len(value["comments"])
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def read_json_records(source_file: Path, json_root: str) -> list[dict[str, Any]]:
    payload = json.loads(source_file.read_text(encoding="utf-8"))
    if json_root:
        for token in json_root.split("."):
            if isinstance(payload, dict):
                payload = payload[token]
            elif isinstance(payload, list) and token.isdigit():
                payload = payload[int(token)]
            else:
                raise ValueError(f"json-root 无法解析到列表: {json_root}")
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        for key in ("issues", "data", "rows", "items"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return [record for record in candidate if isinstance(record, dict)]
    raise ValueError("JSON 顶层不是 issue 列表，请使用 --json-root 指定数组路径")


def load_records(source_file: Path, json_root: str) -> list[dict[str, Any]]:
    suffix = source_file.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        records: list[dict[str, Any]] = []
        with source_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                item = json.loads(stripped)
                if isinstance(item, dict):
                    records.append(item)
        return records
    if suffix == ".json":
        return read_json_records(source_file, json_root)
    if suffix == ".csv":
        return pd.read_csv(source_file).to_dict(orient="records")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source_file).to_dict(orient="records")
    raise ValueError(f"不支持的文件格式: {source_file.suffix}")


def get_value(record: dict[str, Any], path: str) -> Any:
    if path in record:
        return record[path]
    current: Any = record
    for token in path.split("."):
        if isinstance(current, dict):
            if token in current:
                current = current[token]
                continue
            return None
        if isinstance(current, list) and token.isdigit():
            index = int(token)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return None
    return current


def first_value(record: dict[str, Any], field_name: str) -> Any:
    for path in PATHS[field_name]:
        value = get_value(record, path)
        if value not in (None, ""):
            return value
    return None


def choose_severity(record: dict[str, Any]) -> tuple[str, str]:
    severity = normalize_label_like(first_value(record, "severity"))
    if severity:
        return severity, "severity"
    priority = normalize_label_like(first_value(record, "priority"))
    if priority:
        return priority, "priority_fallback"
    issue_type = normalize_label_like(first_value(record, "issue_type"))
    if issue_type:
        return issue_type, "issuetype_fallback"
    return "", "missing"


def normalize_project_name(record: dict[str, Any]) -> tuple[str, str]:
    project_name = normalize_label_like(first_value(record, "product/project"))
    project_key = normalize_label_like(first_value(record, "project_key"))
    if project_name:
        return project_name, project_key
    if project_key:
        return project_key, project_key
    return "", ""


def canonicalize_record(record: dict[str, Any]) -> tuple[dict[str, Any], str]:
    project_name, _project_key = normalize_project_name(record)
    severity, severity_source = choose_severity(record)
    comments_count = normalize_comment_count(first_value(record, "comments_count"), first_value(record, "comments"))

    canonical = {
        "title": extract_rich_text(first_value(record, "title")),
        "description": extract_rich_text(first_value(record, "description")),
        "severity": severity,
        "component": normalize_label_like(first_value(record, "component")),
        "product/project": project_name,
        "created_at": normalize_datetime(first_value(record, "created_at")),
        "resolved_at": normalize_datetime(first_value(record, "resolved_at")),
        "reporter": normalize_identity(first_value(record, "reporter")),
        "assignee": normalize_identity(first_value(record, "assignee")),
        "status": normalize_label_like(first_value(record, "status")),
        "priority": normalize_label_like(first_value(record, "priority")),
        "comments_count": comments_count,
    }
    return canonical, severity_source


def normalize_project_token(value: str) -> str:
    return clean_text(value).casefold()


def filter_and_sample(
    df: pd.DataFrame,
    project_allowlist: list[str],
    top_projects: int,
    sample_per_project: int,
    seed: int,
) -> tuple[pd.DataFrame, list[str]]:
    working = df.copy()
    selected_projects: list[str] = []

    if project_allowlist:
        allow = {normalize_project_token(item) for item in project_allowlist}
        working = working[
            working["product/project"].map(lambda value: normalize_project_token(str(value)) in allow)
        ]
        selected_projects = sorted(working["product/project"].dropna().astype(str).unique().tolist())

    if top_projects > 0:
        counts = (
            working["product/project"]
            .astype(str)
            .value_counts()
            .sort_values(ascending=False)
        )
        selected_projects = counts.head(top_projects).index.tolist()
        working = working[working["product/project"].astype(str).isin(selected_projects)]

    if sample_per_project > 0:
        rng = random.Random(seed)
        sampled_frames: list[pd.DataFrame] = []
        for project_name, project_df in working.groupby("product/project", sort=False):
            if len(project_df) <= sample_per_project:
                sampled_frames.append(project_df)
                continue
            indices = list(project_df.index)
            chosen = sorted(rng.sample(indices, sample_per_project))
            sampled_frames.append(project_df.loc[chosen])
        if sampled_frames:
            working = pd.concat(sampled_frames, ignore_index=False)

    working = working.sort_values(["product/project", "created_at", "title"], na_position="last").reset_index(drop=True)
    return working, selected_projects


def build_metadata(
    source_file: Path,
    output_file: Path,
    metadata_file: Path,
    raw_count: int,
    filtered_count: int,
    df: pd.DataFrame,
    selected_projects: list[str],
    severity_sources: Counter[str],
    dropped_missing_core: int,
) -> dict[str, Any]:
    project_counts = (
        df["product/project"].astype(str).value_counts().sort_values(ascending=False).to_dict()
        if not df.empty
        else {}
    )
    missing_counts = {
        column: int(df[column].replace("", pd.NA).isna().sum())
        for column in CANONICAL_COLUMNS
    }
    return {
        "dataset_label": "The Public Jira Dataset",
        "source_file": str(source_file),
        "output_file": str(output_file),
        "metadata_file": str(metadata_file),
        "row_count_raw": raw_count,
        "row_count_final": filtered_count,
        "column_count": len(CANONICAL_COLUMNS),
        "sheet_name": "cross_domain_public_jira",
        "selected_projects": selected_projects,
        "project_counts": project_counts,
        "severity_source_counts": dict(severity_sources),
        "dropped_missing_core_rows": dropped_missing_core,
        "missing_counts": missing_counts,
        "created_at_min": "" if df.empty else str(df["created_at"].replace("", pd.NA).dropna().min()),
        "created_at_max": "" if df.empty else str(df["created_at"].replace("", pd.NA).dropna().max()),
        "reporter_unique": int(df["reporter"].replace("", pd.NA).dropna().nunique()),
        "assignee_unique": int(df["assignee"].replace("", pd.NA).dropna().nunique()),
        "comments_count_mean": 0.0 if df.empty else round(float(pd.to_numeric(df["comments_count"], errors="coerce").fillna(0).mean()), 2),
        "comments_count_median": 0.0 if df.empty else round(float(pd.to_numeric(df["comments_count"], errors="coerce").fillna(0).median()), 2),
        "materialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    args = parse_args()
    source_file = Path(args.source_file)
    output_file = Path(args.output_file)
    metadata_file = Path(args.metadata_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists() and not args.force:
        print(f"[SKIP] 已存在: {output_file}")
        return 0

    records = load_records(source_file, args.json_root)
    severity_sources: Counter[str] = Counter()
    normalized_rows: list[dict[str, Any]] = []
    dropped_missing_core = 0

    for record in records:
        canonical, severity_source = canonicalize_record(record)
        severity_sources[severity_source] += 1
        if not canonical["title"] or not canonical["product/project"] or not canonical["created_at"]:
            dropped_missing_core += 1
            continue
        if not canonical["description"]:
            canonical["description"] = canonical["title"]
        normalized_rows.append(canonical)

    if not normalized_rows:
        raise ValueError("没有得到可用 issue 记录；请检查输入格式、json-root 或字段映射")

    df = pd.DataFrame(normalized_rows, columns=CANONICAL_COLUMNS)
    df = df.apply(lambda col: col.map(clean_illegal_chars))

    allowlist = [item.strip() for item in args.project_allowlist.split(",") if item.strip()]
    df, selected_projects = filter_and_sample(
        df=df,
        project_allowlist=allowlist,
        top_projects=args.top_projects,
        sample_per_project=args.sample_per_project,
        seed=args.seed,
    )

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=args.sheet_name, index=False)

    metadata = build_metadata(
        source_file=source_file,
        output_file=output_file,
        metadata_file=metadata_file,
        raw_count=len(records),
        filtered_count=len(df),
        df=df,
        selected_projects=selected_projects,
        severity_sources=severity_sources,
        dropped_missing_core=dropped_missing_core,
    )
    metadata["sheet_name"] = args.sheet_name
    metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 已写入标准化数据集: {output_file}")
    print(f"[OK] 已写入元数据: {metadata_file}")
    print(f"[INFO] 原始记录数: {len(records)}")
    print(f"[INFO] 最终记录数: {len(df)}")
    print(f"[INFO] 项目分布: {metadata['project_counts']}")
    print(f"[INFO] 严重性来源: {metadata['severity_source_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
