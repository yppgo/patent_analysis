from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pymongo import DESCENDING, MongoClient


PAPER_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_OUTPUT = PAPER_DIR / "generated" / "public_jira_project_sample.jsonl"
DEFAULT_METADATA = PAPER_DIR / "generated" / "public_jira_project_sample_metadata.json"


@dataclass(frozen=True)
class ProjectSelection:
    collection: str
    project: str


DEFAULT_SELECTIONS = (
    ProjectSelection("Apache", "Spark"),
    ProjectSelection("Jira", "Jira Server and Data Center"),
    ProjectSelection("RedHat", "Keycloak"),
    ProjectSelection("MongoDB", "Core Server"),
    ProjectSelection("Qt", "Qt"),
    ProjectSelection("JFrog", "Artifactory Binary Repository"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从本地恢复后的 The Public Jira Dataset 中导出按项目均衡抽样的 issue 子集"
    )
    parser.add_argument("--uri", type=str, default="mongodb://127.0.0.1:27017", help="MongoDB 连接串")
    parser.add_argument("--db-name", type=str, default="JiraReposAnon20250623", help="目标数据库名")
    parser.add_argument("--per-project", type=int, default=500, help="每个项目抽样条数")
    parser.add_argument(
        "--selections",
        type=str,
        default="",
        help="自定义项目列表，格式为 collection::project,collection::project",
    )
    parser.add_argument(
        "--min-created-prefix",
        type=str,
        default="2000-",
        help="只保留 created 字段以该前缀之后开头的记录，默认过滤掉异常早年数据",
    )
    parser.add_argument("--raw-output", type=str, default=str(DEFAULT_RAW_OUTPUT), help="输出 JSONL 路径")
    parser.add_argument("--metadata-file", type=str, default=str(DEFAULT_METADATA), help="输出元数据 JSON 路径")
    parser.add_argument("--force", action="store_true", help="已存在时强制覆盖")
    return parser.parse_args()


def parse_selections(raw: str) -> list[ProjectSelection]:
    if not raw.strip():
        return list(DEFAULT_SELECTIONS)
    selections: list[ProjectSelection] = []
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        if "::" not in value:
            raise ValueError(f"无效 selection: {value}，应为 collection::project")
        collection, project = value.split("::", 1)
        selections.append(ProjectSelection(collection.strip(), project.strip()))
    if not selections:
        raise ValueError("selections 为空")
    return selections


def projection() -> dict[str, int]:
    return {
        "_id": 0,
        "key": 1,
        "fields.summary": 1,
        "fields.description": 1,
        "fields.severity": 1,
        "fields.priority": 1,
        "fields.components": 1,
        "fields.project": 1,
        "fields.created": 1,
        "fields.resolutiondate": 1,
        "fields.reporter": 1,
        "fields.assignee": 1,
        "fields.status": 1,
        "fields.comments": 1,
        "fields.issuetype": 1,
    }


def iter_records(db, selections: Iterable[ProjectSelection], per_project: int, min_created_prefix: str):
    summary: list[dict[str, object]] = []
    for selection in selections:
        query = {
            "fields.project.name": selection.project,
            "fields.created": {"$gte": min_created_prefix},
        }
        cursor = (
            db[selection.collection]
            .find(query, projection())
            .sort("fields.created", DESCENDING)
            .limit(per_project)
        )
        count = 0
        min_created = None
        max_created = None
        for doc in cursor:
            count += 1
            created = doc.get("fields", {}).get("created")
            if created is not None:
                min_created = created if min_created is None or created < min_created else min_created
                max_created = created if max_created is None or created > max_created else max_created
            doc["source_collection"] = selection.collection
            doc["source_project_name"] = selection.project
            yield doc
        summary.append(
            {
                "collection": selection.collection,
                "project": selection.project,
                "exported_count": count,
                "min_created": min_created,
                "max_created": max_created,
            }
        )
    return summary


def main() -> int:
    args = parse_args()
    selections = parse_selections(args.selections)
    raw_output = Path(args.raw_output)
    metadata_file = Path(args.metadata_file)
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)

    if raw_output.exists() and not args.force:
        print(f"[SKIP] 已存在: {raw_output}")
        return 0

    client = MongoClient(args.uri)
    db = client[args.db_name]

    exported = 0
    summaries: list[dict[str, object]] = []
    with raw_output.open("w", encoding="utf-8") as handle:
        for selection in selections:
            query = {
                "fields.project.name": selection.project,
                "fields.created": {"$gte": args.min_created_prefix},
            }
            cursor = (
                db[selection.collection]
                .find(query, projection())
                .sort("fields.created", DESCENDING)
                .limit(args.per_project)
            )

            count = 0
            min_created = None
            max_created = None
            for doc in cursor:
                created = doc.get("fields", {}).get("created")
                if created is not None:
                    min_created = created if min_created is None or created < min_created else min_created
                    max_created = created if max_created is None or created > max_created else max_created
                doc["source_collection"] = selection.collection
                doc["source_project_name"] = selection.project
                handle.write(json.dumps(doc, ensure_ascii=False))
                handle.write("\n")
                count += 1
                exported += 1

            summaries.append(
                {
                    "collection": selection.collection,
                    "project": selection.project,
                    "exported_count": count,
                    "min_created": min_created,
                    "max_created": max_created,
                }
            )

    metadata = {
        "source_db": args.db_name,
        "uri": args.uri,
        "per_project": args.per_project,
        "min_created_prefix": args.min_created_prefix,
        "raw_output": str(raw_output),
        "total_exported": exported,
        "selections": summaries,
    }
    metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 已导出 JSONL: {raw_output}")
    print(f"[OK] 已导出元数据: {metadata_file}")
    print(f"[INFO] 总记录数: {exported}")
    for item in summaries:
        print(
            f"[INFO] {item['collection']} :: {item['project']} -> {item['exported_count']} "
            f"({item['min_created']} ~ {item['max_created']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
