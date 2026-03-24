from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.jos.common import (
    EXTERNAL_REPEATED_DIR,
    JOS_HUMAN_REVIEW_DIR,
    LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH,
    REPEATED_DIR,
    STRONGEST_EXTERNAL_MECHANISM_PATH,
    TRANSFER_REPEATED_DIR,
    ensure_dirs,
)


QUESTION_INDEXES = "1,2,3,4,5"
EXTERNAL_MODES = "G_react_single_agent,H_execution_feedback"
MAIN_EXTERNAL_MODE_ORDER = "C_iterative,G_react_single_agent,H_execution_feedback"
MAIN_EXTERNAL_PAIRWISE = "C_iterative:G_react_single_agent,C_iterative:H_execution_feedback"
EXTERNAL_EXPECTED_EXPERIMENTS = 50
TRANSFER_EXPECTED_EXPERIMENTS = 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="外部机制基线完成后自动续跑子领域稳定性验证并导出期刊稿产物")
    parser.add_argument("--poll-seconds", type=int, default=60, help="轮询外部基线完成状态的时间间隔")
    parser.add_argument("--run-index", type=int, default=1, help="盲评包抽样使用的重复轮次")
    return parser.parse_args()


def experiment_count(base_dir: Path) -> int:
    if not base_dir.exists():
        return 0
    return len(list(base_dir.glob("experiment_q*_run*.json")))


def run_checked(args: list[str], cwd: Path | None = None) -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    print(f"[RUN] {' '.join(args)}")
    subprocess.run(args, cwd=str(cwd or PROJECT_ROOT), env=env, check=True)


def assert_progress_complete(base_dir: Path, expected_total: int) -> None:
    path = base_dir / "repeated_progress_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"缺少进度汇总文件: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    completed = int(payload.get("completed_total", 0))
    failed = int(payload.get("failed_total", 0))
    pending = int(payload.get("pending_total", 0))
    if completed != expected_total or failed != 0 or pending != 0:
        raise RuntimeError(
            f"实验尚未完整完成: completed={completed}, failed={failed}, pending={pending}, expected={expected_total}"
        )


def wait_for_external_completion(poll_seconds: int) -> None:
    while True:
        count = experiment_count(EXTERNAL_REPEATED_DIR)
        print(f"[WAIT] external count={count}/{EXTERNAL_EXPECTED_EXPERIMENTS}")
        if count >= EXTERNAL_EXPECTED_EXPERIMENTS:
            return
        time.sleep(max(10, poll_seconds))


def summarize_external() -> None:
    run_checked(
        [
            sys.executable,
            "tests/summarize_repeated_experiments.py",
            "--output-dir",
            str(EXTERNAL_REPEATED_DIR),
            "--expected-repeats",
            "5",
            "--question-indexes",
            QUESTION_INDEXES,
            "--modes",
            EXTERNAL_MODES,
            "--with-llm",
        ]
    )
    assert_progress_complete(EXTERNAL_REPEATED_DIR, EXTERNAL_EXPECTED_EXPERIMENTS)
    run_checked(
        [
            sys.executable,
            "scripts/jos/run_significance_tests.py",
            "--input-dir",
            str(EXTERNAL_REPEATED_DIR),
            "--supplemental-dir",
            str(REPEATED_DIR),
            "--mode-order",
            MAIN_EXTERNAL_MODE_ORDER,
            "--pairwise",
            MAIN_EXTERNAL_PAIRWISE,
            "--output-prefix",
            "external_main",
        ]
    )
    run_checked([sys.executable, "scripts/jos/select_strongest_external.py"])


def load_strongest_external() -> str:
    for path in [STRONGEST_EXTERNAL_MECHANISM_PATH, LEGACY_STRONGEST_EXTERNAL_BASELINE_PATH]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        selected = payload.get("selected_mode", "")
        if selected:
            return selected
    raise FileNotFoundError("缺少 strongest external mechanism baseline 结果文件")


def run_transfer(strongest_mode: str) -> None:
    run_checked(
        [
            sys.executable,
            "scripts/jos/run_repeated_batches.py",
            "--dataset",
            "transfer_iot_auto",
            "--modes",
            f"D_baseline0,B_data_aware,C_iterative,{strongest_mode}",
            "--question-indexes",
            QUESTION_INDEXES,
            "--repeats",
            "3",
            "--output-dir",
            str(TRANSFER_REPEATED_DIR),
        ]
    )

    run_checked(
        [
            sys.executable,
            "tests/summarize_repeated_experiments.py",
            "--output-dir",
            str(TRANSFER_REPEATED_DIR),
            "--expected-repeats",
            "3",
            "--question-indexes",
            QUESTION_INDEXES,
            "--modes",
            f"D_baseline0,B_data_aware,C_iterative,{strongest_mode}",
            "--with-llm",
        ]
    )
    assert_progress_complete(TRANSFER_REPEATED_DIR, TRANSFER_EXPECTED_EXPERIMENTS)
    run_checked(
        [
            sys.executable,
            "scripts/jos/run_significance_tests.py",
            "--input-dir",
            str(TRANSFER_REPEATED_DIR),
            "--mode-order",
            f"D_baseline0,B_data_aware,C_iterative,{strongest_mode}",
            "--pairwise",
            f"C_iterative:{strongest_mode},C_iterative:B_data_aware,C_iterative:D_baseline0",
            "--output-prefix",
            "transfer_iot_auto",
        ]
    )


def finalize_artifacts(strongest_mode: str, run_index: int) -> None:
    run_checked([sys.executable, "scripts/jos/export_jos_tables.py"])
    run_checked([sys.executable, "scripts/jos/plot_jos_figures.py"])
    run_checked(
        [
            sys.executable,
            "scripts/jos/prepare_human_review.py",
            "--run-index",
            str(run_index),
            "--external-mode",
            strongest_mode,
        ]
    )
    run_checked([sys.executable, "scripts/jos/package_supplement.py"])


def main() -> None:
    args = parse_args()
    ensure_dirs()
    JOS_HUMAN_REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    wait_for_external_completion(args.poll_seconds)
    summarize_external()
    strongest_mode = load_strongest_external()
    print(f"[INFO] strongest external mechanism baseline: {strongest_mode}")
    run_transfer(strongest_mode)
    finalize_artifacts(strongest_mode, args.run_index)
    print("[DONE] submission continuation pipeline completed")


if __name__ == "__main__":
    main()
