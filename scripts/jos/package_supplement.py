from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    CROSS_DOMAIN_REPEATED_DIR,
    EXTERNAL_REPEATED_DIR,
    JOS_HUMAN_REVIEW_DIR,
    JOS_OUTPUT_DIR,
    PAPER_DIR,
    ROOT,
    TRANSFER_REPEATED_DIR,
    ensure_dirs,
)


PACKAGE_DIR = JOS_OUTPUT_DIR / "supplement" / "package"


INCLUDE_PATHS = [
    ROOT / "docs" / "paper_jos" / "FROZEN_CLAIMS.md",
    ROOT / "docs" / "paper_jos" / "experiment_gap_tracker.md",
    ROOT / "docs" / "paper_jos" / "supplement",
    ROOT / "docs" / "paper_jos" / "generated",
    ROOT / "docs" / "paper_jos" / "figures",
    ROOT / "docs" / "paper_jos" / "references.bib",
    ROOT / "outputs" / "jos_artifacts" / "stats",
    ROOT / "outputs" / "jos_artifacts" / "tables",
    ROOT / "outputs" / "jos_artifacts" / "figures",
    ROOT / "outputs" / "jos_artifacts" / "datasets",
    JOS_HUMAN_REVIEW_DIR,
    ROOT / "scripts" / "jos",
    EXTERNAL_REPEATED_DIR,
    TRANSFER_REPEATED_DIR,
    CROSS_DOMAIN_REPEATED_DIR,
]


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> None:
    ensure_dirs()
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    for src in INCLUDE_PATHS:
        if not src.exists():
            manifest.append({"source": str(src), "status": "missing"})
            continue
        rel = src.relative_to(ROOT)
        dst = PACKAGE_DIR / rel
        copy_path(src, dst)
        manifest.append({"source": str(src), "target": str(dst), "status": "copied"})

    manifest_path = JOS_OUTPUT_DIR / "supplement" / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump({"package_dir": str(PACKAGE_DIR), "items": manifest}, f, ensure_ascii=False, indent=2)

    print(f"Saved supplement package to {PACKAGE_DIR}")
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
