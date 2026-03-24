from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[3]
PAPER_DIR = Path(__file__).resolve().parents[1]
RAW_BASE = ROOT / "outputs" / "jos_artifacts" / "datasets" / "public_jira_raw" / "ThePublicJiraDataset" / "0. DataDefinition"
SAMPLE_METADATA = ROOT / "outputs" / "jos_artifacts" / "datasets" / "public_jira_project_sample_metadata.json"
NORMALIZED_METADATA = ROOT / "outputs" / "jos_artifacts" / "datasets" / "cross_domain_public_jira_metadata.json"

DEFAULT_XLSX = ROOT / "outputs" / "jos_artifacts" / "datasets" / "public_jira_metadata_summary.xlsx"
DEFAULT_MD = PAPER_DIR / "generated" / "public_jira_metadata_summary.md"


CANONICAL_FIELD_RULES = {
    "summary": {
        "names": {"summary"},
        "systems": {"summary"},
    },
    "description": {
        "names": {"description"},
        "systems": {"description"},
    },
    "priority": {
        "names": {"priority"},
        "systems": {"priority"},
    },
    "status": {
        "names": {"status"},
        "systems": {"status"},
    },
    "components": {
        "names": {"components", "component/s", "component"},
        "systems": {"components"},
    },
    "project": {
        "names": {"project"},
        "systems": {"project"},
    },
    "created": {
        "names": {"created"},
        "systems": {"created"},
    },
    "resolutiondate": {
        "names": {"resolved", "resolution date", "resolutiondate"},
        "systems": {"resolutiondate"},
    },
    "reporter": {
        "names": {"reporter"},
        "systems": {"reporter"},
    },
    "assignee": {
        "names": {"assignee"},
        "systems": {"assignee"},
    },
    "comment": {
        "names": {"comment", "comments"},
        "systems": {"comment"},
    },
    "issuetype": {
        "names": {"issue type", "issuetype"},
        "systems": {"issuetype"},
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 The Public Jira Dataset 的官方元数据与本地恢复统计")
    parser.add_argument("--uri", type=str, default="mongodb://127.0.0.1:27017", help="MongoDB 连接串")
    parser.add_argument("--db-name", type=str, default="JiraReposAnon20250623", help="恢复后的数据库名")
    parser.add_argument("--xlsx-output", type=str, default=str(DEFAULT_XLSX), help="输出工作簿路径")
    parser.add_argument("--md-output", type=str, default=str(DEFAULT_MD), help="输出 Markdown 路径")
    parser.add_argument("--force", action="store_true", help="已存在时强制覆盖")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    return int(text)


def normalize_name(value: str) -> str:
    return value.strip().casefold()


def match_canonical_field(field_info: dict[str, Any]) -> str | None:
    name = normalize_name(str(field_info.get("name", "")))
    schema = field_info.get("schema") or {}
    system = normalize_name(str(schema.get("system", "")))
    for canonical, rule in CANONICAL_FIELD_RULES.items():
        if name in rule["names"] or system in rule["systems"]:
            return canonical
    return None


def field_stats_for_source(fields: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    documented_field_count = len(fields)
    custom_field_count = sum(1 for field in fields if field.get("custom"))
    canonical_matches: dict[str, list[dict[str, Any]]] = {key: [] for key in CANONICAL_FIELD_RULES}
    for field in fields:
        matched = match_canonical_field(field)
        if matched:
            canonical_matches[matched].append(field)

    summary = {
        "documented_field_count": documented_field_count,
        "custom_field_count": custom_field_count,
        "standard_field_count": documented_field_count - custom_field_count,
    }
    for canonical, matched_fields in canonical_matches.items():
        summary[f"has_{canonical}"] = bool(matched_fields)
        summary[f"{canonical}_match_count"] = len(matched_fields)

    mapping_rows: list[dict[str, Any]] = []
    for canonical, matched_fields in canonical_matches.items():
        if matched_fields:
            for field in matched_fields:
                schema = field.get("schema") or {}
                mapping_rows.append(
                    {
                        "canonical_field": canonical,
                        "matched_field_id": field.get("id", ""),
                        "matched_field_name": field.get("name", ""),
                        "schema_type": schema.get("type", ""),
                        "schema_system": schema.get("system", ""),
                        "custom": bool(field.get("custom")),
                    }
                )
        else:
            mapping_rows.append(
                {
                    "canonical_field": canonical,
                    "matched_field_id": "",
                    "matched_field_name": "",
                    "schema_type": "",
                    "schema_system": "",
                    "custom": False,
                }
            )
    return summary, mapping_rows


def collection_stats(db, collection_name: str) -> dict[str, Any]:
    collection = db[collection_name]
    pipeline = [
        {
            "$group": {
                "_id": None,
                "issue_count": {"$sum": 1},
                "min_created": {"$min": "$fields.created"},
                "max_created": {"$max": "$fields.created"},
                "resolved_count": {
                    "$sum": {"$cond": [{"$ne": ["$fields.resolutiondate", None]}, 1, 0]}
                },
                "assignee_count": {
                    "$sum": {"$cond": [{"$ne": ["$fields.assignee", None]}, 1, 0]}
                },
                "component_count": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$size": {"$ifNull": ["$fields.components", []]}}, 0]},
                            1,
                            0,
                        ]
                    }
                },
                "commented_issue_count": {
                    "$sum": {"$cond": [{"$ne": ["$fields.comments", None]}, 1, 0]}
                },
            }
        }
    ]
    grouped = list(collection.aggregate(pipeline, allowDiskUse=True))
    if grouped:
        row = grouped[0]
    else:
        row = {
            "issue_count": 0,
            "min_created": "",
            "max_created": "",
            "resolved_count": 0,
            "assignee_count": 0,
            "component_count": 0,
            "commented_issue_count": 0,
        }
    project_count = len(collection.distinct("fields.project.name"))
    row["project_count"] = project_count
    return row


def load_sample_selections() -> dict[tuple[str, str], dict[str, Any]]:
    if not SAMPLE_METADATA.exists():
        return {}
    data = load_json(SAMPLE_METADATA)
    selections = {}
    for row in data.get("selections", []):
        selections[(row["collection"], row["project"])] = row
    return selections


def load_normalized_metadata() -> dict[str, Any]:
    if not NORMALIZED_METADATA.exists():
        return {}
    return load_json(NORMALIZED_METADATA)


def build_workbook_frames(uri: str, db_name: str) -> dict[str, pd.DataFrame]:
    data_sources = load_json(RAW_BASE / "jira_data_sources.json")
    field_information = load_json(RAW_BASE / "jira_field_information.json")
    client = MongoClient(uri)
    db = client[db_name]

    sample_selections = load_sample_selections()
    normalized_metadata = load_normalized_metadata()

    overview_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []

    for source_name, source_meta in data_sources.items():
        fields = field_information.get(source_name, [])
        field_summary, source_mapping_rows = field_stats_for_source(fields)
        stats = collection_stats(db, source_name)
        source_projects = [
            selection
            for (collection_name, _project_name), selection in sample_selections.items()
            if collection_name == source_name
        ]
        selected_projects = "; ".join(selection["project"] for selection in source_projects)

        row = {
            "source_name": source_name,
            "company_url": source_meta.get("company_url", ""),
            "jira_url": source_meta.get("jira_url", ""),
            "rough_issue_count": safe_int(source_meta.get("rough_issue_count")),
            "restored_issue_count": stats["issue_count"],
            "project_count": stats["project_count"],
            "documented_field_count": field_summary["documented_field_count"],
            "custom_field_count": field_summary["custom_field_count"],
            "standard_field_count": field_summary["standard_field_count"],
            "min_created": stats["min_created"],
            "max_created": stats["max_created"],
            "resolved_count": stats["resolved_count"],
            "assignee_count": stats["assignee_count"],
            "component_count": stats["component_count"],
            "commented_issue_count": stats["commented_issue_count"],
            "selected_for_paper_sample": bool(source_projects),
            "selected_projects": selected_projects,
        }
        for canonical in CANONICAL_FIELD_RULES:
            row[f"has_{canonical}"] = field_summary[f"has_{canonical}"]
            row[f"{canonical}_match_count"] = field_summary[f"{canonical}_match_count"]
        overview_rows.append(row)

        for mapping_row in source_mapping_rows:
            mapping_rows.append(
                {
                    "source_name": source_name,
                    **mapping_row,
                }
            )

    overview_df = pd.DataFrame(overview_rows).sort_values("restored_issue_count", ascending=False).reset_index(drop=True)
    mapping_df = pd.DataFrame(mapping_rows).sort_values(["source_name", "canonical_field"]).reset_index(drop=True)

    sample_rows = []
    for selection in sample_selections.values():
        sample_rows.append(selection)
    sample_df = pd.DataFrame(sample_rows).sort_values(["collection", "project"]).reset_index(drop=True) if sample_rows else pd.DataFrame()

    normalized_rows = []
    if normalized_metadata:
        project_counts = normalized_metadata.get("project_counts", {})
        missing_counts = normalized_metadata.get("missing_counts", {})
        normalized_rows = [
            {"metric": "dataset_label", "value": normalized_metadata.get("dataset_label", "")},
            {"metric": "row_count_final", "value": normalized_metadata.get("row_count_final", 0)},
            {"metric": "column_count", "value": normalized_metadata.get("column_count", 0)},
            {"metric": "created_at_min", "value": normalized_metadata.get("created_at_min", "")},
            {"metric": "created_at_max", "value": normalized_metadata.get("created_at_max", "")},
            {"metric": "reporter_unique", "value": normalized_metadata.get("reporter_unique", 0)},
            {"metric": "assignee_unique", "value": normalized_metadata.get("assignee_unique", 0)},
            {"metric": "comments_count_mean", "value": normalized_metadata.get("comments_count_mean", 0)},
            {"metric": "comments_count_median", "value": normalized_metadata.get("comments_count_median", 0)},
            {"metric": "severity_source_counts", "value": json.dumps(normalized_metadata.get("severity_source_counts", {}), ensure_ascii=False)},
            {"metric": "project_counts", "value": json.dumps(project_counts, ensure_ascii=False)},
            {"metric": "missing_counts", "value": json.dumps(missing_counts, ensure_ascii=False)},
        ]
    normalized_df = pd.DataFrame(normalized_rows)

    return {
        "source_overview": overview_df,
        "canonical_mapping": mapping_df,
        "paper_sample": sample_df,
        "normalized_dataset": normalized_df,
    }


def write_markdown(path: Path, frames: dict[str, pd.DataFrame]) -> None:
    overview_df = frames["source_overview"]
    sample_df = frames["paper_sample"]
    normalized_df = frames["normalized_dataset"]

    selected_cols = [
        "source_name",
        "restored_issue_count",
        "project_count",
        "documented_field_count",
        "custom_field_count",
        "min_created",
        "max_created",
        "selected_for_paper_sample",
        "selected_projects",
    ]
    overview_md = overview_df[selected_cols].to_markdown(index=False)

    lines = [
        "# The Public Jira Dataset Metadata Summary",
        "",
        "这份总表把 TPJD 官方分散的 metadata 与本地恢复后的 collection 统计合并到了一处。",
        "",
        "## 1. Source Overview",
        "",
        overview_md,
        "",
    ]

    if not sample_df.empty:
        lines.extend(
            [
                "## 2. Paper Sample",
                "",
                sample_df.to_markdown(index=False),
                "",
            ]
        )

    if not normalized_df.empty:
        lines.extend(
            [
                "## 3. Normalized Dataset Summary",
                "",
                normalized_df.to_markdown(index=False),
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    xlsx_output = Path(args.xlsx_output)
    md_output = Path(args.md_output)
    xlsx_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.parent.mkdir(parents=True, exist_ok=True)

    if xlsx_output.exists() and not args.force:
        print(f"[SKIP] 已存在: {xlsx_output}")
        return 0

    frames = build_workbook_frames(args.uri, args.db_name)
    with pd.ExcelWriter(xlsx_output, engine="openpyxl") as writer:
        for sheet_name, df in frames.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    write_markdown(md_output, frames)

    print(f"[OK] 已写入工作簿: {xlsx_output}")
    print(f"[OK] 已写入 Markdown: {md_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
