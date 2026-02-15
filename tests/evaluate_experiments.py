"""
实验量化评估脚本
从 12 组实验结果中提取自动化指标 + LLM-as-Judge 对比评分
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
TOTAL_COLUMNS = 22  # 数据集总列数

EXPERIMENT_FILES = [
    "experiment_q1_D_baseline0.json",
    "experiment_q1_A_template.json",
    "experiment_q1_B_data_aware.json",
    "experiment_q1_C_iterative.json",
    "experiment_q2_D_baseline0.json",
    "experiment_q2_A_template.json",
    "experiment_q2_B_data_aware.json",
    "experiment_q2_C_iterative.json",
    "experiment_q3_D_baseline0.json",
    "experiment_q3_A_template.json",
    "experiment_q3_B_data_aware.json",
    "experiment_q3_C_iterative.json",
]

# 用于匹配具体数据引用的正则
SPECIFICITY_PATTERNS = [
    r'\d+\.\d+',                    # 小数（如 0.32, 84.08）
    r'[A-H]\d{2}[A-Z]\d',          # IPC 编码（如 H04L9, G06F21）
    r'H04L9/40',                    # 完整 IPC 子类
    r'\d+%',                        # 百分比
    r'[><=]\s*\d+',                 # 阈值比较（如 >5, <=20）
    r'p\s*[<>=]\s*0\.\d+',         # 统计显著性（如 p<0.05）
    r'degree\s*[>=<]\s*\d+',       # 度阈值
    r'K\s*=\s*\d+',                # 聚类数
]


class ExperimentEvaluator:
    """实验结果量化评估器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or (PROJECT_ROOT / "outputs"))
        self.experiments: List[Dict] = self._load_experiments()
        self.auto_metrics: Optional[Dict] = None
        self.llm_scores: Optional[Dict] = None

    # ──────────────────────────────────────────
    # 数据加载
    # ──────────────────────────────────────────
    def _load_experiments(self) -> List[Dict]:
        """加载所有实验 JSON 文件"""
        experiments = []
        for fname in EXPERIMENT_FILES:
            fpath = self.output_dir / fname
            if not fpath.exists():
                print(f"[WARN] 文件不存在，跳过: {fname}")
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            experiments.append(data)
        print(f"[INFO] 加载了 {len(experiments)} 组实验结果")
        return experiments

    # ──────────────────────────────────────────
    # 辅助：提取所有任务
    # ──────────────────────────────────────────
    def _get_all_tasks(self, experiment: Dict) -> List[Dict]:
        """从实验中提取所有轮次的所有任务"""
        tasks = []
        for rnd in experiment.get("rounds", []):
            blueprint = rnd.get("blueprint", {})
            tasks.extend(blueprint.get("task_graph", []))
        return tasks

    def _get_all_blueprints(self, experiment: Dict) -> List[Dict]:
        """从实验中提取所有轮次的 blueprint"""
        return [rnd.get("blueprint", {}) for rnd in experiment.get("rounds", [])]

    # ──────────────────────────────────────────
    # 自动化指标
    # ──────────────────────────────────────────
    def _column_coverage(self, experiment: Dict) -> float:
        """数据列覆盖率 = 使用的唯一列数 / 总列数"""
        all_columns = set()
        for task in self._get_all_tasks(experiment):
            config = task.get("implementation_config", {})
            cols = config.get("columns_to_load", [])
            all_columns.update(cols)
        return round(len(all_columns) / TOTAL_COLUMNS, 3)

    def _method_diversity(self, experiment: Dict) -> int:
        """方法多样性 = 唯一 task_type 数"""
        types = set()
        for task in self._get_all_tasks(experiment):
            task_type = task.get("task_type", "")
            for sub_type in re.split(r'\s*[+]\s*', task_type):
                sub_type = sub_type.strip()
                if sub_type:
                    types.add(sub_type)
        return len(types)

    def _avg_description_length(self, experiment: Dict) -> float:
        """平均任务描述长度（字符数）"""
        tasks = self._get_all_tasks(experiment)
        if not tasks:
            return 0.0
        lengths = [len(task.get("description", "")) for task in tasks]
        return round(sum(lengths) / len(lengths), 1)

    def _specificity_references(self, experiment: Dict) -> int:
        """方案针对性 = 任务描述+问题中引用具体数据特征的次数"""
        count = 0
        for task in self._get_all_tasks(experiment):
            text = task.get("description", "") + " " + task.get("question", "")
            for pattern in SPECIFICITY_PATTERNS:
                count += len(re.findall(pattern, text))
        for bp in self._get_all_blueprints(experiment):
            for outcome in bp.get("expected_outcomes", []):
                for pattern in SPECIFICITY_PATTERNS:
                    count += len(re.findall(pattern, outcome))
            obj = bp.get("research_objective", "")
            for pattern in SPECIFICITY_PATTERNS:
                count += len(re.findall(pattern, obj))
        return count

    def _control_variable_count(self, experiment: Dict) -> int:
        """控制变量总数"""
        count = 0
        for task in self._get_all_tasks(experiment):
            params = task.get("implementation_config", {}).get("parameters", {})
            for key in ["control_vars", "control_variables"]:
                val = params.get(key, [])
                if isinstance(val, list):
                    count += len(val)
        return count

    def _parameter_richness(self, experiment: Dict) -> int:
        """参数丰富度 = 所有任务 parameters 中非空键值对总数"""
        count = 0
        for task in self._get_all_tasks(experiment):
            params = task.get("implementation_config", {}).get("parameters", {})
            for v in params.values():
                if v is not None and v != "" and v != []:
                    count += 1
        return count

    def _outcome_specificity(self, experiment: Dict) -> float:
        """预期结论具体度 = expected_outcomes 中含具体数值/统计量的条目比例"""
        all_outcomes = []
        for bp in self._get_all_blueprints(experiment):
            all_outcomes.extend(bp.get("expected_outcomes", []))
        if not all_outcomes:
            return 0.0
        has_number = 0
        for outcome in all_outcomes:
            if re.search(
                r'\d+\.\d+|[A-H]\d{2}[A-Z]|\d+%|[><=]\s*\d+|'
                r'效应量|系数|区间|阈值|显著|p值',
                outcome
            ):
                has_number += 1
        return round(has_number / len(all_outcomes), 2)

    def _insight_count(self, experiment: Dict) -> int:
        """数据洞察数量 = 仅在 has_insights=True 的轮次中计入"""
        count = 0
        for rnd in experiment.get("rounds", []):
            if not rnd.get("has_insights", False):
                continue
            bp = rnd.get("blueprint", {})
            trace = bp.get("thinking_trace", {})
            insights = trace.get("selected_insights", [])
            if isinstance(insights, list):
                count += len(insights)
            elif isinstance(insights, str):
                count += max(1, len(re.findall(r'I\d+', insights)))
        return count

    def _total_tasks(self, experiment: Dict) -> int:
        """任务总数"""
        return sum(rnd.get("total_tasks", 0) for rnd in experiment.get("rounds", []))

    def _success_rate(self, experiment: Dict) -> float:
        """执行成功率"""
        total = sum(rnd.get("total_tasks", 0) for rnd in experiment.get("rounds", []))
        success = sum(rnd.get("success_count", 0) for rnd in experiment.get("rounds", []))
        return round(success / total, 2) if total > 0 else 0.0

    def compute_auto_metrics(self) -> Dict:
        """计算所有自动化指标"""
        print("\n" + "=" * 60)
        print("  自动化指标计算")
        print("=" * 60)

        metrics_list = []
        for exp in self.experiments:
            m = {
                "question": exp.get("question", ""),
                "mode": exp.get("mode", ""),
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
            }
            metrics_list.append(m)

        # 按模式聚合
        aggregated = {}
        modes = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
        metric_keys = [
            "column_coverage", "method_diversity", "avg_description_length",
            "specificity_references", "control_variable_count", "parameter_richness",
            "outcome_specificity", "insight_count", "total_tasks", "success_rate",
        ]
        for mode in modes:
            mode_metrics = [m for m in metrics_list if m["mode"] == mode]
            if not mode_metrics:
                continue
            agg = {}
            for key in metric_keys:
                values = [m[key] for m in mode_metrics]
                agg["avg_" + key] = round(sum(values) / len(values), 3)
            aggregated[mode] = agg

        self.auto_metrics = {"metrics": metrics_list, "aggregated": aggregated}

        for m in metrics_list:
            q_short = m["question"][:15] + "..."
            print("  {}  {:15s}  列覆盖={:.2f}  方法={}  针对性={}  控制变量={}  参数={}  洞察={}".format(
                q_short, m["mode"], m["column_coverage"], m["method_diversity"],
                m["specificity_references"], m["control_variable_count"],
                m["parameter_richness"], m["insight_count"]))

        return self.auto_metrics

    # ──────────────────────────────────────────
    # LLM-as-Judge 对比评估
    # ──────────────────────────────────────────
    def _build_comparative_prompt(self, question: str,
                                   blueprints: Dict[str, str]) -> str:
        """构建对比评估 Prompt，支持 3 或 4 个方案"""
        labels = sorted(blueprints.keys())  # e.g., ["W", "X", "Y", "Z"]
        n = len(labels)

        bp_sections = ""
        for label in labels:
            bp_sections += f"## 方案 {label}（匿名）\n{blueprints[label]}\n\n"

        scores_template = {}
        for label in labels:
            scores_template[label] = {"relevance": 0, "specificity": 0, "method_quality": 0, "innovation": 0, "depth": 0}

        analysis_template = {}
        for label in labels:
            analysis_template[f"{label}_strengths"] = f"<方案{label}的优势>"
            analysis_template[f"{label}_weaknesses"] = f"<方案{label}的劣势>"

        prompt = (
            f"你是一位严格的专利分析方法论专家。现在有同一个研究问题的 {n} 个不同分析方案，"
            "请你横向对比后，对每个方案打分。\n\n"
            f"注意：你必须在 {n} 个方案之间拉开分数差距，严格区分优劣。禁止给所有方案都打高分。\n\n"
            "## 研究问题\n" + question + "\n\n"
            + bp_sections +
            "## 评估维度和评分标准\n\n"
            f"请从以下 5 个维度对每个方案分别打分（1-5 分）。打分时必须横向对比，"
            "最好的方案和最差的方案至少差 1 分。\n\n"
            "1. **相关性** (relevance): 分析任务与研究问题的契合程度\n"
            "   - 1分: 任务与问题基本无关\n"
            "   - 2分: 仅部分任务与问题相关\n"
            "   - 3分: 任务大致回答问题但不够精准\n"
            "   - 4分: 每个任务都有明确对应的子问题\n"
            "   - 5分: 每个任务精准回答研究问题的核心子问题，且任务间逻辑连贯\n\n"
            "2. **针对性** (specificity): 方案是否针对该具体数据集设计（vs 通用模板）\n"
            "   - 1分: 完全通用的模板，可套用于任何专利数据集\n"
            "   - 2分: 提到了数据列名但未利用数据特征\n"
            "   - 3分: 引用了部分数据特征（如具体 IPC 编码或统计量）\n"
            "   - 4分: 深度利用数据集特征，分析参数基于数据定制\n"
            "   - 5分: 每个任务都根据数据特征定制，包含具体阈值、子群定义、参数配置\n\n"
            "3. **方法合理性** (method_quality): 分析方法与数据/问题的匹配度\n"
            "   - 1分: 方法与数据类型不匹配\n"
            "   - 2分: 方法基本可用但过于简单\n"
            "   - 3分: 方法合理但缺少控制变量或稳健性考虑\n"
            "   - 4分: 方法与数据匹配良好，有控制变量\n"
            "   - 5分: 方法完美匹配 + 控制变量 + 多种方法三角验证\n\n"
            "4. **创新性** (innovation): 分析角度的非显而易见程度\n"
            "   - 1分: 完全是教科书式常规分析\n"
            "   - 2分: 稍有新意但整体偏常规\n"
            "   - 3分: 有一个新颖角度\n"
            "   - 4分: 提出反直觉假设或跨学科方法\n"
            "   - 5分: 多个非显而易见的创新分析角度，且有数据支撑\n\n"
            "5. **深度** (depth): 分析的层次和因果推断能力\n"
            "   - 1分: 仅描述性统计\n"
            "   - 2分: 有基本的相关性分析\n"
            "   - 3分: 有假设检验和回归分析\n"
            "   - 4分: 多层次分析 + 交互效应 + 子群分析\n"
            "   - 5分: 因果推断 + 机制解释 + 多层次模型 + 稳健性检验\n\n"
            "## 强制要求\n\n"
            f"- 每个维度上，{n} 个方案中最高分和最低分至少差 1 分\n"
            "- 先给出每个方案的总体印象和优劣势分析，再打分\n"
            "- 打分必须基于方案内容，不能因为任务多就给高分\n\n"
            "## 输出格式\n\n"
            "请严格按以下 JSON 格式输出（不要输出其他内容）：\n\n"
            '```json\n'
            '{\n'
            '  "analysis": {\n'
        )
        analysis_lines = []
        for label in labels:
            analysis_lines.append(f'    "{label}_strengths": "<方案{label}的优势>"')
            analysis_lines.append(f'    "{label}_weaknesses": "<方案{label}的劣势>"')
        prompt += ',\n'.join(analysis_lines) + '\n'
        prompt += '  },\n  "scores": {\n'
        score_lines = []
        for label in labels:
            score_lines.append(
                f'    "{label}": {{"relevance": 0, "specificity": 0, "method_quality": 0, "innovation": 0, "depth": 0}}'
            )
        prompt += ',\n'.join(score_lines) + '\n'
        prompt += '  }\n}\n```'
        return prompt

    def _parse_comparative_score(self, response: str, labels: List[str]) -> Optional[Dict]:
        """从对比评估的 LLM 响应中解析评分"""
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
            json_str = re.sub(r'^```\w*\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)

        try:
            result = json.loads(json_str)
            scores = result.get("scores", {})
            analysis = result.get("analysis", {})
            required_dims = ["relevance", "specificity", "method_quality", "innovation", "depth"]

            parsed = {}
            for label in labels:
                s = scores.get(label, {})
                entry = {}
                for dim in required_dims:
                    val = s.get(dim, 0)
                    if not isinstance(val, (int, float)) or val < 1 or val > 5:
                        return None
                    entry[dim] = int(val)
                entry["total"] = sum(entry[dim] for dim in required_dims)
                entry["strengths"] = analysis.get(label + "_strengths", "")
                entry["weaknesses"] = analysis.get(label + "_weaknesses", "")
                parsed[label] = entry

            return parsed
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return None

    def compute_llm_scores(self) -> Dict:
        """使用 LLM 对比评估同一问题的多个方案"""
        print("\n" + "=" * 60)
        print("  LLM-as-Judge 对比评估")
        print("=" * 60)

        from src.utils.llm_client import LLMClient
        llm = LLMClient(model="qwen3-max", temperature=0.1)

        # 按问题分组
        questions = {}
        for exp in self.experiments:
            q = exp.get("question", "")
            mode = exp.get("mode", "")
            if q not in questions:
                questions[q] = {}
            questions[q][mode] = exp

        scores_list = []

        # 动态检测可用模式并分配匿名标签
        all_modes = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]
        anon_labels = ["W", "X", "Y", "Z"]

        for qi, (question, exps) in enumerate(questions.items()):
            q_short = question[:20] + "..."

            # 找出该问题下可用的模式
            available = [(m, l) for m, l in zip(all_modes, anon_labels) if m in exps]
            if len(available) < 2:
                print(f"\n  [{qi+1}] 跳过（方案不足 2 个）: {q_short}")
                continue

            mode_map = {l: m for m, l in available}  # label -> mode
            labels = [l for _, l in available]
            n = len(available)
            print(f"\n  [{qi+1}/{len(questions)}] 对比评估 ({n} 方案): {q_short}")

            # 提取各方案的 blueprint JSON
            bp_jsons = {}
            for mode, label in available:
                exp = exps.get(mode, {})
                all_bps = self._get_all_blueprints(exp)
                if len(all_bps) == 1:
                    bp_obj = all_bps[0]
                elif len(all_bps) > 1:
                    bp_obj = {
                        "round_count": len(all_bps),
                        "rounds": [{"round_" + str(j + 1): bp} for j, bp in enumerate(all_bps)]
                    }
                else:
                    bp_obj = {}
                bp_jsons[label] = json.dumps(bp_obj, ensure_ascii=False, indent=2)

            prompt = self._build_comparative_prompt(question, bp_jsons)

            try:
                response = llm.invoke(prompt)
                if "</think>" in response:
                    response = response.split("</think>")[-1].strip()
                result = self._parse_comparative_score(response, labels)
                if result:
                    parts = []
                    for label in labels:
                        mode = mode_map[label]
                        entry = result[label].copy()
                        entry["question"] = question
                        entry["mode"] = mode
                        scores_list.append(entry)
                        parts.append(f"{label}({mode[0]})={entry['total']}/25")
                    print("    " + "  ".join(parts))
                else:
                    print("    解析失败，原始响应: " + response[:300])
                    for label in labels:
                        mode = mode_map[label]
                        scores_list.append({
                            "question": question, "mode": mode,
                            "relevance": 0, "specificity": 0,
                            "method_quality": 0, "innovation": 0, "depth": 0,
                            "total": 0, "strengths": "", "weaknesses": "解析失败",
                        })
            except Exception as e:
                print("    LLM 调用失败: {}".format(e))
                for label in labels:
                    mode = mode_map[label]
                    scores_list.append({
                        "question": question, "mode": mode,
                        "relevance": 0, "specificity": 0,
                        "method_quality": 0, "innovation": 0, "depth": 0,
                        "total": 0, "strengths": "", "weaknesses": str(e),
                    })

        # 按模式聚合
        aggregated = {}
        score_keys = ["relevance", "specificity", "method_quality", "innovation", "depth", "total"]
        for mode in all_modes:
            mode_scores = [s for s in scores_list if s["mode"] == mode and s["total"] > 0]
            if not mode_scores:
                continue
            agg = {}
            for key in score_keys:
                values = [s[key] for s in mode_scores]
                agg["avg_" + key] = round(sum(values) / len(values), 2)
            aggregated[mode] = agg

        self.llm_scores = {"scores": scores_list, "aggregated": aggregated}
        return self.llm_scores

    # ──────────────────────────────────────────
    # 输出
    # ──────────────────────────────────────────
    def print_summary_table(self):
        """打印汇总对比表"""
        print("\n" + "=" * 80)
        print("  汇总对比表")
        print("=" * 80)

        all_modes = ["D_baseline0", "A_template", "B_data_aware", "C_iterative"]

        if self.auto_metrics:
            print("\n--- 自动化指标（3 问题平均值）---")
            # 只显示有数据的模式
            present_modes = [m for m in all_modes if m in self.auto_metrics["aggregated"]]
            header_parts = ["{:<20s}".format("指标")]
            for m in present_modes:
                header_parts.append("{:>14s}".format(m))
            print("".join(header_parts))
            print("-" * (20 + 14 * len(present_modes)))

            agg = self.auto_metrics["aggregated"]
            display_metrics = [
                ("列覆盖率", "avg_column_coverage"),
                ("方法多样性", "avg_method_diversity"),
                ("描述详细度(字)", "avg_avg_description_length"),
                ("针对性引用数", "avg_specificity_references"),
                ("控制变量数", "avg_control_variable_count"),
                ("参数丰富度", "avg_parameter_richness"),
                ("结论具体度", "avg_outcome_specificity"),
                ("洞察数量", "avg_insight_count"),
                ("任务总数", "avg_total_tasks"),
                ("执行成功率", "avg_success_rate"),
            ]

            for label, key in display_metrics:
                parts = ["  {:<18s}".format(label)]
                for mode in present_modes:
                    v = agg.get(mode, {}).get(key, 0)
                    parts.append("{:>14.2f}".format(v))
                print("".join(parts))

        if self.llm_scores:
            present_modes = [m for m in all_modes if m in self.llm_scores["aggregated"]]
            print("\n--- LLM-as-Judge 对比评分（3 问题平均值，满分 5）---")
            header_parts = ["{:<15s}".format("维度")]
            for m in present_modes:
                header_parts.append("{:>14s}".format(m))
            print("".join(header_parts))
            print("-" * (15 + 14 * len(present_modes)))

            agg = self.llm_scores["aggregated"]
            score_display = [
                ("相关性", "avg_relevance"),
                ("针对性", "avg_specificity"),
                ("方法合理性", "avg_method_quality"),
                ("创新性", "avg_innovation"),
                ("深度", "avg_depth"),
                ("总分(/25)", "avg_total"),
            ]

            for label, key in score_display:
                parts = ["  {:<13s}".format(label)]
                for mode in present_modes:
                    v = agg.get(mode, {}).get(key, 0)
                    parts.append("{:>14.2f}".format(v))
                print("".join(parts))

            # 明细
            print("\n--- LLM 评分明细 ---")
            print("{:<20s}  {:<15s}  {:>4s} {:>4s} {:>4s} {:>4s} {:>4s} {:>5s}".format(
                "问题", "模式", "相关", "针对", "方法", "创新", "深度", "总分"))
            print("-" * 78)
            for s in self.llm_scores["scores"]:
                q_short = s["question"][:18] + ".."
                print("  {:<18s}  {:<15s}  {:>4d} {:>4d} {:>4d} {:>4d} {:>4d} {:>5d}".format(
                    q_short, s["mode"],
                    s["relevance"], s["specificity"], s["method_quality"],
                    s["innovation"], s["depth"], s["total"]))

    def save_results(self):
        """保存评估结果到 JSON"""
        if self.auto_metrics:
            path = self.output_dir / "evaluation_auto_metrics.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.auto_metrics, f, ensure_ascii=False, indent=2)
            print("\n[SAVED] 自动化指标 -> {}".format(path))

        if self.llm_scores:
            path = self.output_dir / "evaluation_llm_scores.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.llm_scores, f, ensure_ascii=False, indent=2)
            print("[SAVED] LLM 评分 -> {}".format(path))


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="实验结果量化评估")
    parser.add_argument("--auto-only", action="store_true",
                        help="仅计算自动化指标，跳过 LLM 评估")
    parser.add_argument("--llm-only", action="store_true",
                        help="仅运行 LLM 评估，跳过自动化指标")
    args = parser.parse_args()

    evaluator = ExperimentEvaluator()

    if not args.llm_only:
        evaluator.compute_auto_metrics()

    if not args.auto_only:
        evaluator.compute_llm_scores()

    evaluator.print_summary_table()
    evaluator.save_results()
