from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "jos_artifacts" / "datasets" / "mozilla_bugzilla_recent.csv"
DEFAULT_METADATA = PROJECT_ROOT / "outputs" / "jos_artifacts" / "datasets" / "mozilla_bugzilla_recent_metadata.json"

BUG_FIELDS = [
    "id",
    "summary",
    "severity",
    "component",
    "product",
    "creation_time",
    "cf_last_resolved",
    "last_change_time",
    "creator",
    "assigned_to",
    "status",
    "priority",
    "resolution",
]

BOT_CREATOR_MARKERS = [
    "@mozilla.bugs",
    "intermittent-bug-filer",
    "bugbug",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从官方 Bugzilla API 抓取跨领域验证所需的软件缺陷数据")
    parser.add_argument("--provider", type=str, default="mozilla", choices=["mozilla"])
    parser.add_argument("--products", type=str, default="Core,Firefox,Toolkit,DevTools,WebExtensions,Fenix", help="逗号分隔的 product 列表")
    parser.add_argument("--per-product", type=int, default=500, help="每个 product 保留的样本数")
    parser.add_argument("--page-size", type=int, default=100, help="单次 API 拉取条数")
    parser.add_argument("--max-pages", type=int, default=30, help="每个 product 最多翻页次数")
    parser.add_argument("--comment-workers", type=int, default=6, help="并发抓取 comments 的线程数")
    parser.add_argument("--max-description-chars", type=int, default=4000, help="description 最大保留字符数")
    parser.add_argument("--output-file", type=str, default=str(DEFAULT_OUTPUT), help="原始 CSV 输出路径")
    parser.add_argument("--metadata-file", type=str, default=str(DEFAULT_METADATA), help="元数据 JSON 输出路径")
    parser.add_argument("--force", action="store_true", help="已存在时强制覆盖")
    return parser.parse_args()


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def request_json(base_url: str, params: dict[str, Any] | None = None, retries: int = 3) -> dict[str, Any]:
    params = params or {}
    query = urlencode(params, doseq=True)
    url = base_url if not query else f"{base_url}?{query}"
    headers = {"User-Agent": "patent-analysis-jos/1.0"}
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            if attempt < retries:
                time.sleep(min(3 * attempt, 10))
    raise RuntimeError(f"request failed after {retries} attempts: {url}") from last_error


def should_skip_bug(bug: dict[str, Any]) -> bool:
    summary = str(bug.get("summary") or "").lower()
    creator = str(bug.get("creator") or "").lower()
    if summary.startswith("[wpt-sync]"):
        return True
    if any(marker in creator for marker in BOT_CREATOR_MARKERS):
        return True
    severity = str(bug.get("severity") or "").strip()
    priority = str(bug.get("priority") or "").strip()
    if severity in ("--", "") and priority in ("--", ""):
        return True
    return False


def fetch_bug_batch(product: str, limit: int, offset: int) -> list[dict[str, Any]]:
    payload = request_json(
        "https://bugzilla.mozilla.org/rest/bug",
        {
            "product": product,
            "limit": limit,
            "offset": offset,
            "order": "bug_id DESC",
            "include_fields": BUG_FIELDS,
        },
    )
    return list(payload.get("bugs") or [])


def fetch_comments(bug_id: int) -> tuple[str, int]:
    payload = request_json(f"https://bugzilla.mozilla.org/rest/bug/{bug_id}/comment")
    bug_payload = (payload.get("bugs") or {}).get(str(bug_id), {})
    comments = list(bug_payload.get("comments") or [])
    if not comments:
        return "", 0
    first_text = str(comments[0].get("text") or "").strip()
    return first_text, len(comments)


def collect_recent_bugs(product: str, per_product: int, page_size: int, max_pages: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    offset = 0

    for _ in range(max_pages):
        bugs = fetch_bug_batch(product=product, limit=page_size, offset=offset)
        if not bugs:
            break
        for bug in bugs:
            bug_id = int(bug.get("id"))
            if bug_id in seen_ids:
                continue
            seen_ids.add(bug_id)
            if should_skip_bug(bug):
                continue
            selected.append(bug)
            if len(selected) >= per_product:
                return selected
        offset += page_size
    return selected


def enrich_with_comments(
    bugs: list[dict[str, Any]],
    max_workers: int,
    max_description_chars: int,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    future_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for bug in bugs:
            future = executor.submit(fetch_comments, int(bug["id"]))
            future_map[future] = bug

        for future in as_completed(future_map):
            bug = future_map[future]
            try:
                description, comments_count = future.result()
            except Exception:
                description, comments_count = "", 0
            description = (description or bug.get("summary") or "").strip()
            if max_description_chars > 0:
                description = description[:max_description_chars]

            resolved_at = bug.get("cf_last_resolved") or ""
            record = {
                "bug_id": int(bug["id"]),
                "title": str(bug.get("summary") or "").strip(),
                "description": description,
                "severity": str(bug.get("severity") or "").strip(),
                "component": str(bug.get("component") or "").strip(),
                "product/project": str(bug.get("product") or "").strip(),
                "created_at": str(bug.get("creation_time") or "").strip(),
                "resolved_at": str(resolved_at).strip(),
                "reporter": str(bug.get("creator") or "").strip(),
                "assignee": str(bug.get("assigned_to") or "").strip(),
                "status": str(bug.get("status") or "").strip(),
                "priority": str(bug.get("priority") or "").strip(),
                "resolution": str(bug.get("resolution") or "").strip(),
                "comments_count": int(comments_count),
            }
            enriched.append(record)

    enriched.sort(key=lambda item: (item["product/project"], item["bug_id"]), reverse=True)
    return enriched


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("没有可写入的数据")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_file)
    metadata_path = Path(args.metadata_file)
    if output_path.exists() and not args.force:
        print(f"[SKIP] 已存在: {output_path}")
        return 0

    products = parse_csv_list(args.products)
    raw_bugs: list[dict[str, Any]] = []
    product_stats: list[dict[str, Any]] = []

    for product in products:
        start = time.time()
        bugs = collect_recent_bugs(
            product=product,
            per_product=args.per_product,
            page_size=args.page_size,
            max_pages=args.max_pages,
        )
        elapsed = round(time.time() - start, 2)
        raw_bugs.extend(bugs)
        product_stats.append(
            {
                "product": product,
                "kept": len(bugs),
                "elapsed_seconds": elapsed,
            }
        )
        print(f"[OK] product={product} kept={len(bugs)} elapsed={elapsed}s")

    enriched = enrich_with_comments(
        bugs=raw_bugs,
        max_workers=max(1, args.comment_workers),
        max_description_chars=max(0, args.max_description_chars),
    )
    write_csv(output_path, enriched)

    metadata = {
        "provider": args.provider,
        "products": products,
        "per_product": args.per_product,
        "row_count": len(enriched),
        "column_count": len(enriched[0]) if enriched else 0,
        "product_stats": product_stats,
        "output_file": str(output_path),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 写入原始 Bugzilla CSV: {output_path}")
    print(f"[OK] 写入元数据: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
