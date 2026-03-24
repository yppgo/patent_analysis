#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重复实验汇总脚本

用途：
1. 统计重复实验当前进度（已完成 / 失败 / 缺失）
2. 计算每次运行的自动化指标
3. 按「问题×模式」与「模式总体」输出 mean / std / 95% CI
4. 可选执行 LLM-as-Judge，对每个问题×run 做 6-way 评分后再聚合
"""

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Dict, Iterable, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scipy.stats import t as student_t
except Exception:  # pragma: no cover
    student_t = None

from tests.evaluate_experiments import (
    ExperimentEvaluator,
    TOTAL_COLUMNS,
    SPECIFICITY_PATTERNS,
)
from scripts.jos.experiment_registry import get_questions


DEFAULT_QUESTIONS = {idx + 1: question for idx, question in enumerate(get_questions("main_data_security"))}

DEFAULT_MODES = [
    "D_baseline0",
    "A_template",
    "B_data_aware",
    "C_iterative",
    "E_ablate_data",
    "F_ablate_kg",
]

AUTO_METRIC_KEYS = [
    "column_coverage",
    "method_diversity",
    "avg_description_length",
    "specificity_references",
    "control_variable_count",
    "parameter_richness",
    "outcome_specificity",
    "insight_count",
    "total_tasks",
    "success_rate",
    "elapsed_seconds",
    "strategist_time_sum",
]

LLM_METRIC_KEYS = [
    "relevance",
    "specificity",
    "method_quality",
    "innovation",
    "depth",
    "total",
]


def parse_csv_list(value: str, cast=None) -> list:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if cast is None:
        return items
    return [cast(item) for item in items]


def stats_summary(values: Iterable[float]) -> Dict[str, float]:
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "ci95_low": 0.0, "ci95_high": 0.0, "min": 0.0, "max": 0.0}

    avg = mean(vals)
    std = stdev(vals) if n > 1 else 0.0
    if n > 1:
        if student_t is not None:
            t_crit = float(student_t.ppf(0.975, n - 1))
        else:  # pragma: no cover
            t_crit = 1.96
        margin = t_crit * std / math.sqrt(n)
    else:
        margin = 0.0

    return {
        "n": n,
        "mean": round(avg, 3),
        "std": round(std, 3),
        "ci95_low": round(avg - margin, 3),
        "ci95_high": round(avg + margin, 3),
        "min": round(min(vals), 3),
        "max": round(max(vals), 3),
    }


class RepeatedExperimentSummarizer(ExperimentEvaluator):
    def __init__(
        self,
        output_dir: Path,
        expected_repeats: int,
        question_indexes: list[int],
        modes: list[str],
    ):
        self.output_dir = Path(output_dir)
        self.expected_repeats = expected_repeats
        self.question_indexes = question_indexes
        self.modes = modes
        self.experiments = self._load_experiments()
        self.auto_metrics = None
        self.llm_scores = None
        self.progress = None

    def _load_experiments(self) -> List[Dict]:
        experiments: list[dict] = []
        for path in sorted(self.output_dir.glob("experiment_q*_run*.json")):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_file"] = path.name
            experiments.append(data)
        print(f"[INFO] 从 {self.output_dir} 加载 {len(experiments)} 个重复实验文件")
        return experiments

    def _is_valid_experiment(self, exp: Dict[str, Any]) -> bool:
        rounds = exp.get("rounds")
        if not isinstance(rounds, list) or not rounds:
            return False

        for round_payload in rounds:
            blueprint = round_payload.get("blueprint", {})
            if not isinstance(blueprint, dict):
                return False
            if blueprint.get("error"):
                return False
            task_graph = blueprint.get("task_graph")
            if not isinstance(task_graph, list) or not task_graph:
                return False
            total_tasks = int(round_payload.get("total_tasks", 0) or 0)
            if total_tasks <= 0:
                return False
            success_count = int(round_payload.get("success_count", 0) or 0)
            if success_count != total_tasks:
                return False
        return True

    def _valid_experiments(self) -> List[Dict]:
        return [exp for exp in self.experiments if self._is_valid_experiment(exp)]

    def _error_experiments(self) -> List[Dict]:
        return [exp for exp in self.experiments if not self._is_valid_experiment(exp)]

    def _mode_sort_key(self, mode: str) -> int:
        return self.modes.index(mode) if mode in self.modes else 999

    def summarize_progress(self) -> Dict[str, Any]:
        expected_keys = {
            (q_idx, mode, run_idx)
            for q_idx in self.question_indexes
            for mode in self.modes
            for run_idx in range(1, self.expected_repeats + 1)
        }

        completed_keys = set()
        failed_keys = set()
        file_map: dict[tuple[int, str, int], str] = {}
        question_name_map = dict(DEFAULT_QUESTIONS)

        for exp in self.experiments:
            q_idx = int(exp.get("question_index", 0))
            mode = exp.get("mode", "")
            run_idx = int(exp.get("run_index", 0))
            key = (q_idx, mode, run_idx)
            if q_idx:
                question_name_map[q_idx] = exp.get("question", question_name_map.get(q_idx, ""))
            file_map[key] = exp.get("_file", "")
            if self._is_valid_experiment(exp):
                completed_keys.add(key)
            else:
                failed_keys.add(key)

        pending_keys = sorted(expected_keys - completed_keys - failed_keys)

        per_group = []
        for q_idx in self.question_indexes:
            for mode in self.modes:
                completed_runs = sorted(run for (q, m, run) in completed_keys if q == q_idx and m == mode)
                failed_runs = sorted(run for (q, m, run) in failed_keys if q == q_idx and m == mode)
                missing_runs = [run for run in range(1, self.expected_repeats + 1) if run not in completed_runs and run not in failed_runs]
                per_group.append({
                    "question_index": q_idx,
                    "question": question_name_map.get(q_idx, DEFAULT_QUESTIONS.get(q_idx, "")),
                    "mode": mode,
                    "completed_runs": completed_runs,
                    "failed_runs": failed_runs,
                    "missing_runs": missing_runs,
                    "completed_count": len(completed_runs),
                    "failed_count": len(failed_runs),
                    "expected_count": self.expected_repeats,
                })

        self.progress = {
            "expected_total": len(expected_keys),
            "completed_total": len(completed_keys),
            "failed_total": len(failed_keys),
            "pending_total": len(pending_keys),
            "completion_rate": round(len(completed_keys) / len(expected_keys), 3) if expected_keys else 0.0,
            "groups": per_group,
            "pending_examples": [
                {"question_index": q, "mode": m, "run_index": run}
                for q, m, run in pending_keys[:20]
            ],
        }
        return self.progress

    def compute_repeated_auto_metrics(self) -> Dict[str, Any]:
        records = []
        for exp in self._valid_experiments():
            record = {
                "file": exp.get("_file", ""),
                "question_index": int(exp.get("question_index", 0)),
                "question": exp.get("question", ""),
                "mode": exp.get("mode", ""),
                "run_index": int(exp.get("run_index", 0)),
                "column_coverage": self._column_coverage(exp),
                "method_diversity": self._method_diversity(exp),
                "avg_description_length": self._avg_description_length(exp),
                "specificity_references": self._specificity_references(exp),
                "control_variable_count": self._control_variable_count(exp),
                "parameter_richness": self._parameter_richness(exp),
                "outcome_specificity": self._outcome_specificity(exp),
                "insight_count": self._insight_count(exp),
                "total_tasks": self._total_tasks(exp),
                "success_rate": self._success_rate(exp),
                "elapsed_seconds": round(float(exp.get("elapsed_seconds", 0.0)), 3),
                "strategist_time_sum": round(sum(float(r.get("strategist_time", 0.0)) for r in exp.get("rounds", [])), 3),
            }
            records.append(record)

        summary_by_qm = self._aggregate_records(records, ["question_index", "question", "mode"], AUTO_METRIC_KEYS)
        summary_by_mode = self._aggregate_records(records, ["mode"], AUTO_METRIC_KEYS)
        self.auto_metrics = {
            "per_run": records,
            "summary_by_question_mode": summary_by_qm,
            "summary_by_mode": summary_by_mode,
        }
        return self.auto_metrics

    def compute_repeated_llm_scores(self) -> Dict[str, Any]:
        from src.utils.llm_client import LLMClient

        llm = LLMClient(model="qwen3-max", temperature=0.1)

        grouped: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for exp in self._valid_experiments():
            key = (int(exp.get("question_index", 0)), int(exp.get("run_index", 0)))
            grouped[key].append(exp)

        score_records = []
        anon_labels = ["W", "X", "Y", "Z", "U", "V"]

        for (q_idx, run_idx) in sorted(grouped):
            exps = grouped[(q_idx, run_idx)]
            question = exps[0].get("question", DEFAULT_QUESTIONS.get(q_idx, ""))
            available_modes = [mode for mode in self.modes if any(exp.get("mode") == mode for exp in exps)]
            if len(available_modes) != len(self.modes):
                print(f"[LLM] 跳过 q{q_idx} run{run_idx:02d}：模式不完整 ({len(available_modes)}/{len(self.modes)})")
                continue

            bp_jsons = {}
            label_to_mode = {}
            for label, mode in zip(anon_labels, self.modes):
                exp = next(exp for exp in exps if exp.get("mode") == mode)
                all_bps = self._get_all_blueprints(exp)
                if len(all_bps) == 1:
                    bp_obj = all_bps[0]
                else:
                    bp_obj = {
                        "round_count": len(all_bps),
                        "rounds": [{"round_" + str(j + 1): bp} for j, bp in enumerate(all_bps)],
                    }
                bp_jsons[label] = json.dumps(bp_obj, ensure_ascii=False, indent=2)
                label_to_mode[label] = mode

            prompt = self._build_comparative_prompt(question, bp_jsons)
            response = llm.invoke(prompt)
            if "</think>" in response:
                response = response.split("</think>")[-1].strip()

            parsed = self._parse_comparative_score(response, list(label_to_mode.keys()))
            if not parsed:
                raise RuntimeError(f"LLM 评分解析失败: q{q_idx} run{run_idx:02d}")

            for label, mode in label_to_mode.items():
                entry = parsed[label]
                score_records.append({
                    "question_index": q_idx,
                    "question": question,
                    "mode": mode,
                    "run_index": run_idx,
                    "relevance": entry["relevance"],
                    "specificity": entry["specificity"],
                    "method_quality": entry["method_quality"],
                    "innovation": entry["innovation"],
                    "depth": entry["depth"],
                    "total": entry["total"],
                    "strengths": entry.get("strengths", ""),
                    "weaknesses": entry.get("weaknesses", ""),
                })
            score_line = "  ".join(f"{label_to_mode[label]}={parsed[label]['total']}" for label in label_to_mode)
            print(f"[LLM] q{q_idx} run{run_idx:02d}: {score_line}")

        summary_by_qm = self._aggregate_records(score_records, ["question_index", "question", "mode"], LLM_METRIC_KEYS)
        summary_by_mode = self._aggregate_records(score_records, ["mode"], LLM_METRIC_KEYS)
        self.llm_scores = {
            "per_run": score_records,
            "summary_by_question_mode": summary_by_qm,
            "summary_by_mode": summary_by_mode,
        }
        return self.llm_scores

    def _aggregate_records(self, records: List[Dict], group_keys: List[str], metric_keys: List[str]) -> List[Dict]:
        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for record in records:
            key = tuple(record[k] for k in group_keys)
            grouped[key].append(record)

        summary = []
        for key, items in sorted(grouped.items(), key=lambda pair: tuple(pair[0])):
            entry = {group_keys[idx]: key[idx] for idx in range(len(group_keys))}
            entry["n_runs"] = len(items)
            entry["run_indexes"] = sorted(int(item.get("run_index", 0)) for item in items if item.get("run_index") is not None)
            for metric_key in metric_keys:
                entry[metric_key] = stats_summary(item[metric_key] for item in items)
            summary.append(entry)
        return summary

    def save_outputs(self) -> None:
        if self.progress is not None:
            with open(self.output_dir / "repeated_progress_summary.json", "w", encoding="utf-8") as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)

        if self.auto_metrics is not None:
            with open(self.output_dir / "repeated_auto_metrics.json", "w", encoding="utf-8") as f:
                json.dump(self.auto_metrics, f, ensure_ascii=False, indent=2)
            self._write_csv(
                self.output_dir / "repeated_auto_metrics_per_run.csv",
                self.auto_metrics["per_run"],
            )
            self._write_csv(
                self.output_dir / "repeated_auto_metrics_summary_by_question_mode.csv",
                self._flatten_summary_rows(self.auto_metrics["summary_by_question_mode"], AUTO_METRIC_KEYS),
            )
            self._write_csv(
                self.output_dir / "repeated_auto_metrics_summary_by_mode.csv",
                self._flatten_summary_rows(self.auto_metrics["summary_by_mode"], AUTO_METRIC_KEYS),
            )

        if self.llm_scores is not None:
            with open(self.output_dir / "repeated_llm_scores.json", "w", encoding="utf-8") as f:
                json.dump(self.llm_scores, f, ensure_ascii=False, indent=2)
            self._write_csv(
                self.output_dir / "repeated_llm_scores_per_run.csv",
                self.llm_scores["per_run"],
            )
            self._write_csv(
                self.output_dir / "repeated_llm_scores_summary_by_question_mode.csv",
                self._flatten_summary_rows(self.llm_scores["summary_by_question_mode"], LLM_METRIC_KEYS),
            )
            self._write_csv(
                self.output_dir / "repeated_llm_scores_summary_by_mode.csv",
                self._flatten_summary_rows(self.llm_scores["summary_by_mode"], LLM_METRIC_KEYS),
            )

        self._write_markdown_report()

    def _write_csv(self, path: Path, rows: List[Dict]) -> None:
        if not rows:
            return
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _flatten_summary_rows(self, rows: List[Dict], metric_keys: List[str]) -> List[Dict]:
        flat_rows = []
        for row in rows:
            base = {}
            for key, value in row.items():
                if key in metric_keys:
                    continue
                base[key] = value
            for metric_key in metric_keys:
                stats = row.get(metric_key, {})
                for stat_key, stat_val in stats.items():
                    base[f"{metric_key}_{stat_key}"] = stat_val
            flat_rows.append(base)
        return flat_rows

    def _write_markdown_report(self) -> None:
        lines = ["# Repeated Experiment Summary", ""]

        if self.progress is not None:
            p = self.progress
            lines.extend([
                "## Progress",
                "",
                f"- Expected total: {p['expected_total']}",
                f"- Completed: {p['completed_total']}",
                f"- Failed: {p['failed_total']}",
                f"- Pending: {p['pending_total']}",
                f"- Completion rate: {p['completion_rate']:.1%}",
                "",
                "| Question | Mode | Completed | Failed | Missing |",
                "| --- | --- | ---: | ---: | --- |",
            ])
            for group in self.progress["groups"]:
                missing = ",".join(str(x) for x in group["missing_runs"]) if group["missing_runs"] else "-"
                lines.append(
                    f"| Q{group['question_index']} | {group['mode']} | {group['completed_count']}/{group['expected_count']} | "
                    f"{group['failed_count']} | {missing} |"
                )
            lines.append("")

        if self.auto_metrics is not None:
            lines.extend([
                "## Auto Metrics By Mode",
                "",
                "| Mode | ColCoverage | Methods | SpecificityRefs | Params | Tasks | SuccessRate | Elapsed(s) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ])
            for row in sorted(self.auto_metrics["summary_by_mode"], key=lambda item: self._mode_sort_key(item["mode"])):
                lines.append(
                    f"| {row['mode']} | "
                    f"{row['column_coverage']['mean']:.3f} ± {row['column_coverage']['std']:.3f} | "
                    f"{row['method_diversity']['mean']:.3f} ± {row['method_diversity']['std']:.3f} | "
                    f"{row['specificity_references']['mean']:.3f} ± {row['specificity_references']['std']:.3f} | "
                    f"{row['parameter_richness']['mean']:.3f} ± {row['parameter_richness']['std']:.3f} | "
                    f"{row['total_tasks']['mean']:.3f} ± {row['total_tasks']['std']:.3f} | "
                    f"{row['success_rate']['mean']:.3f} ± {row['success_rate']['std']:.3f} | "
                    f"{row['elapsed_seconds']['mean']:.3f} ± {row['elapsed_seconds']['std']:.3f} |"
                )
            lines.append("")

        if self.llm_scores is not None:
            lines.extend([
                "## LLM Scores By Mode",
                "",
                "| Mode | Relevance | Specificity | Method | Innovation | Depth | Total |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ])
            for row in sorted(self.llm_scores["summary_by_mode"], key=lambda item: self._mode_sort_key(item["mode"])):
                lines.append(
                    f"| {row['mode']} | "
                    f"{row['relevance']['mean']:.3f} ± {row['relevance']['std']:.3f} | "
                    f"{row['specificity']['mean']:.3f} ± {row['specificity']['std']:.3f} | "
                    f"{row['method_quality']['mean']:.3f} ± {row['method_quality']['std']:.3f} | "
                    f"{row['innovation']['mean']:.3f} ± {row['innovation']['std']:.3f} | "
                    f"{row['depth']['mean']:.3f} ± {row['depth']['std']:.3f} | "
                    f"{row['total']['mean']:.3f} ± {row['total']['std']:.3f} |"
                )
            lines.append("")

        with open(self.output_dir / "repeated_summary_report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def print_brief(self) -> None:
        if self.progress is not None:
            print("\n" + "=" * 80)
            print("Progress")
            print("=" * 80)
            print(json.dumps({
                "expected_total": self.progress["expected_total"],
                "completed_total": self.progress["completed_total"],
                "failed_total": self.progress["failed_total"],
                "pending_total": self.progress["pending_total"],
                "completion_rate": self.progress["completion_rate"],
            }, ensure_ascii=False, indent=2))

        if self.auto_metrics is not None:
            print("\n" + "=" * 80)
            print("Auto Metrics (By Mode)")
            print("=" * 80)
            for row in sorted(self.auto_metrics["summary_by_mode"], key=lambda item: self._mode_sort_key(item["mode"])):
                print(
                    f"{row['mode']:<15} "
                    f"spec_refs={row['specificity_references']['mean']:.3f}±{row['specificity_references']['std']:.3f}  "
                    f"tasks={row['total_tasks']['mean']:.3f}±{row['total_tasks']['std']:.3f}  "
                    f"success={row['success_rate']['mean']:.3f}±{row['success_rate']['std']:.3f}  "
                    f"elapsed={row['elapsed_seconds']['mean']:.1f}s"
                )

        if self.llm_scores is not None:
            print("\n" + "=" * 80)
            print("LLM Scores (By Mode)")
            print("=" * 80)
            for row in sorted(self.llm_scores["summary_by_mode"], key=lambda item: self._mode_sort_key(item["mode"])):
                print(
                    f"{row['mode']:<15} "
                    f"total={row['total']['mean']:.3f}±{row['total']['std']:.3f}  "
                    f"rel={row['relevance']['mean']:.3f}  spec={row['specificity']['mean']:.3f}  "
                    f"method={row['method_quality']['mean']:.3f}  innovation={row['innovation']['mean']:.3f}  depth={row['depth']['mean']:.3f}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="重复实验汇总脚本")
    parser.add_argument("--output-dir", type=str, default="outputs/repeated_experiments_full")
    parser.add_argument("--expected-repeats", type=int, default=5)
    parser.add_argument("--question-indexes", type=str, default="1,2,3,4,5")
    parser.add_argument("--modes", type=str, default=",".join(DEFAULT_MODES))
    parser.add_argument("--with-llm", action="store_true", help="额外执行 LLM-as-Judge 聚合")
    args = parser.parse_args()

    question_indexes = parse_csv_list(args.question_indexes, int)
    modes = parse_csv_list(args.modes, str)

    summarizer = RepeatedExperimentSummarizer(
        output_dir=PROJECT_ROOT / args.output_dir,
        expected_repeats=args.expected_repeats,
        question_indexes=question_indexes,
        modes=modes,
    )
    summarizer.summarize_progress()
    summarizer.compute_repeated_auto_metrics()
    if args.with_llm:
        summarizer.compute_repeated_llm_scores()
    summarizer.save_outputs()
    summarizer.print_brief()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
