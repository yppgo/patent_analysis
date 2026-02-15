"""
Strategist Agent V5.0 - 战略智能体
基于 Dynamic DAG 和 Variable Flow 的架构升级

核心改进：
1. 从 List 到 DAG：引入动态计算图结构
2. 严格变量流管理：每个任务明确输入/输出变量
3. 图完整性自检：防止数据断链和幻觉列名
4. 增强 CoT：强制 LLM 进行数据审计和算法选择
5. 自动数据感知：从真实数据文件读取列名
"""

import json
import pandas as pd
from typing import Dict, Any, List, Set, Tuple, Optional
from src.agents.base_agent import BaseAgent
from src.utils.data_preview import DataPreview
from src.utils.graph_preview import GraphPreview


class StrategistAgent(BaseAgent):
    """
    战略智能体 V5.0（大脑）
    
    职责：
    1. 理解用户研究目标
    2. 从 Neo4j 知识图谱检索相关方法论
    3. 生成基于 DAG 的研究战略蓝图
    4. 确保变量流的完整性和一致性
    
    架构升级：
    - 废弃 analysis_logic_chains (List)
    - 引入 task_graph (DAG)
    - 每个 Task 包含 input_variables 和 output_variables
    - 自动检查图完整性
    """
    
    def __init__(self, llm_client, neo4j_connector=None, causal_graph=None, method_graph=None, logger=None, data_file=None):
        """
        初始化 Strategist V5.0
        
        Args:
            llm_client: LLM 客户端
            neo4j_connector: Neo4j 连接器（已废弃，保留用于向后兼容）
            causal_graph: 因果图谱查询器（可选，用于假设生成）
            method_graph: 方法图谱查询器（可选，用于方法推荐）
            logger: 日志记录器
            data_file: 数据文件路径（可选，用于自动读取列名）
        """
        super().__init__("Strategist_V5", llm_client, logger)
        self.neo4j = neo4j_connector  # 保留用于向后兼容，但不再使用
        self.causal_graph = causal_graph
        self.method_graph = method_graph
        self.data_file = data_file or "data/new_data.XLSX"
        self.sheet_name = "sheet1"
    
    def _load_real_columns(self) -> List[str]:
        """
        从真实数据文件读取列名
        
        Returns:
            列名列表，如果读取失败则返回 None
        """
        try:
            # 只读取列名，不读取数据（nrows=0）
            df = pd.read_excel(self.data_file, sheet_name=self.sheet_name, nrows=0)
            columns = list(df.columns)
            self.log(f"✓ 从数据文件读取到 {len(columns)} 个列名")
            return columns
        except Exception as e:
            self.log(f"⚠️ 无法从数据文件读取列名: {e}", "warning")
            return None
    
    def _generate_hypotheses_from_causal_graph(self, user_goal: str, keywords: List[str]) -> Dict:
        """
        从因果图谱生成研究假设
        
        Args:
            user_goal: 用户研究目标
            keywords: 提取的关键词
            
        Returns:
            假设生成结果（包含6步流程）
        """
        try:
            # 从用户目标中提取领域和意图
            domain = self._extract_domain(user_goal, keywords)
            intent = self._extract_intent(user_goal, keywords)
            
            self.log(f"提取的领域: {domain}")
            self.log(f"提取的意图: {intent}")
            
            # 调用因果图谱的假设生成器
            result = self.causal_graph.generate_hypotheses_v2({
                "domain": domain,
                "intent": intent
            })
            
            return result
            
        except Exception as e:
            self.log(f"假设生成失败: {e}", "error")
            return None
    
    def _extract_domain(self, user_goal: str, keywords: List[str]) -> str:
        """
        从用户目标中提取领域
        
        简单版本：使用第一个关键词作为领域
        """
        # 过滤掉分析意图相关的关键词
        intent_keywords = ["分析", "识别", "评估", "预测", "趋势", "空白", "竞争", "影响"]
        
        for keyword in keywords:
            if keyword not in intent_keywords:
                return keyword
        
        # 如果没有找到，返回第一个关键词
        return keywords[0] if keywords else "专利分析"
    
    def _extract_intent(self, user_goal: str, keywords: List[str]) -> str:
        """
        从用户目标中提取意图
        
        简单版本：基于关键词匹配
        """
        intent_map = {
            "趋势": "技术趋势分析",
            "空白": "技术空白识别",
            "竞争": "竞争格局分析",
            "影响": "技术影响力分析",
            "突破": "技术突破性研究",
            "价值": "商业价值评估"
        }
        
        for keyword in keywords:
            for key, intent in intent_map.items():
                if key in keyword:
                    return intent
        
        # 默认意图
        return "技术影响力驱动因素分析"
    
    def _retrieve_methods_for_hypotheses(self, recommended_hypotheses: Dict) -> str:
        """
        从方法图谱检索假设相关的方法
        
        Args:
            recommended_hypotheses: 推荐的假设字典
            
        Returns:
            格式化的方法文本
        """
        if not self.method_graph:
            return ""
        
        lines = []
        
        # 获取核心推荐假设
        core_recs = recommended_hypotheses.get('core_recommendations', [])
        
        for i, rec in enumerate(core_recs[:2], 1):  # 只取前2个假设的方法
            h = rec['hypothesis']
            
            lines.append(f"假设 {i} 的相关方法:")
            lines.append(f"  假设: {h['statement']}")
            lines.append("")
            
            # 获取方法
            method_text = self.method_graph.format_methods_for_prompt(h)
            lines.append(method_text)
            lines.append("")
        
        return "\n".join(lines)

    def _select_top_core_hypothesis(self, recommended_hypotheses: Optional[Dict]) -> Optional[Dict]:
        """仅保留评分最高的核心推荐假设用于验证。"""
        if not recommended_hypotheses:
            return None

        core_recs = recommended_hypotheses.get('core_recommendations', [])
        if not core_recs:
            return recommended_hypotheses

        top_rec = core_recs[0]
        filtered = dict(recommended_hypotheses)
        filtered['core_recommendations'] = [top_rec]
        filtered['core_count'] = 1
        filtered['alternative_recommendations'] = []
        return filtered
    
    def _format_hypotheses_for_prompt(self, recommended_hypotheses: Dict = None) -> str:
        """
        格式化假设信息用于Prompt
        
        Args:
            recommended_hypotheses: 推荐的假设字典
            
        Returns:
            格式化的假设文本
        """
        if not recommended_hypotheses or not recommended_hypotheses.get('core_recommendations'):
            return ""
        
        lines = []
        lines.append("**【因果图谱 - 推荐的研究假设】**")
        lines.append("")
        
        # 核心推荐假设
        core_recs = recommended_hypotheses.get('core_recommendations', [])
        for i, rec in enumerate(core_recs, 1):
            h = rec['hypothesis']
            eval_data = h.get('evaluation', {})
            variables = h.get('variables', {})
            
            lines.append(f"假设 {i} (新颖性: {eval_data.get('novelty_score', 0)}, "
                        f"质量: {eval_data.get('quality_score', 0):.0f}): {h['statement']}")
            lines.append(f"  - 策略: {h.get('strategy_description', '')}")
            
            # 变量信息
            indep = variables.get('independent', [])
            dep = variables.get('dependent', [])
            if indep and dep:
                lines.append(f"  - 变量: {' + '.join(indep)} → {' + '.join(dep)}")
            
            # 变量定义（从因果图谱获取）
            if hasattr(self, 'causal_graph') and self.causal_graph:
                lines.append(f"  - 变量定义:")
                for var_id in indep + dep:
                    var_info = self.causal_graph.get_variable(var_id)
                    if var_info:
                        lines.append(f"    * {var_id}: {var_info.get('definition', '')}")
            
            lines.append(f"  - 理论依据: {h.get('theoretical_basis', '')}")
            
            evidence = h.get('evidence', {})
            lines.append(f"  - 文献支持: {evidence.get('evidence_count', 0)}篇")
            
            lines.append("")
        
        lines.append("**⚠️ 重要提示：**")
        lines.append("1. 根据假设中的变量定义，从【当前数据可用列名】中选择最合适的列")
        lines.append("2. 设计任务来计算这些变量并验证假设")
        lines.append("")
        
        return "\n".join(lines)

    # ─── 数据洞察生成（Phase 2 新增）────────────────────────

    def _generate_data_insights(
        self,
        data_preview_text: str,
        graph_preview_text: Optional[str],
        abstracts_text: Optional[str],
        user_goal: str,
    ) -> Optional[Dict[str, Any]]:
        """
        调用 LLM 基于三份输入生成 5-8 条数据洞察。
        """
        prompt = f"""你是一位资深的专利数据分析师。以下是一份专利数据集的统计特征、图结构分析和领域摘要样本。
请基于这些信息，围绕用户的研究目标生成 5-8 条**数据洞察**。

**用户研究目标：** {user_goal}

---

**【数据统计特征】**
{data_preview_text}

{f'**【图结构分析】**{chr(10)}{graph_preview_text}' if graph_preview_text else ''}

{f'**【领域摘要样本】**{chr(10)}{abstracts_text}' if abstracts_text else ''}

---

**洞察生成要求：**

1. **每条洞察必须引用输入中的具体数字**（如相关系数、社区数量、桥梁节点介数、分组均值差异等）
2. **每条洞察必须指定**：用哪些数据列、什么分析方法来深入验证
3. **洞察分三类**：
   - `statistical`：基于相关系数、分组对比、时间趋势等统计信号
   - `graph_structural`：基于社区结构、桥梁节点、连通分量、度分布等图特征
   - `content_driven`：基于摘要内容发现的技术主题或趋势
4. **禁止常识性结论**（如"越老的专利引用越多"、"大公司专利多"）

**输出格式（严格 JSON）：**
{{
  "domain_summary": "基于摘要内容的 2-3 句技术领域描述",
  "insights": [
    {{
      "id": "I1",
      "type": "statistical | graph_structural | content_driven",
      "title": "洞察标题",
      "observation": "数据/图/摘要中的具体观察（必须引用具体数字）",
      "hypothesis": "可检验的假设",
      "data_columns": ["列名1", "列名2"],
      "analysis_method": "建议的分析方法",
      "novelty_reason": "为什么这不是常识"
    }}
  ],
  "recommended_analyses": ["推荐的 2-3 种深入分析方向"]
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            insights = json.loads(content)
            n = len(insights.get('insights', []))
            self.log(f"✓ 生成 {n} 条数据洞察")
            return insights

        except Exception as e:
            self.log(f"⚠️ 数据洞察生成失败: {e}", "warning")
            return None

    def _format_data_insights_for_prompt(self, insights: Dict[str, Any]) -> str:
        """格式化数据洞察为 Prompt 可注入文本。"""
        if not insights:
            return ""

        lines = ["**【数据驱动的研究洞察】**", ""]
        if insights.get('domain_summary'):
            lines.append(f"领域概述: {insights['domain_summary']}")
            lines.append("")

        for ins in insights.get('insights', []):
            lines.append(f"**{ins['id']}. {ins['title']}** [{ins.get('type', '')}]")
            lines.append(f"  观察: {ins['observation']}")
            lines.append(f"  假设: {ins['hypothesis']}")
            lines.append(f"  数据列: {ins['data_columns']}")
            lines.append(f"  建议方法: {ins['analysis_method']}")
            lines.append("")

        rec = insights.get('recommended_analyses', [])
        if rec:
            lines.append(f"推荐分析方向: {', '.join(rec)}")
            lines.append("")

        lines.append("**⚠️ 重要：请基于上述洞察设计分析任务，优先选择有具体数据支撑的洞察。**")
        return "\n".join(lines)

    def _generate_refined_blueprint(
        self,
        user_goal: str,
        previous_results: List[Dict],
        data_insights: Optional[Dict],
        available_columns: List[str],
        data_preview_text: Optional[str],
        graph_preview_text: Optional[str],
        graph_context: str = "",
    ) -> Dict[str, Any]:
        """
        第二轮专用：基于第一轮结果生成深入分析方案。
        """
        columns_semantic = self._describe_columns_semantics(available_columns)
        insights_section = self._format_data_insights_for_prompt(data_insights) if data_insights else ""

        # 格式化第一轮结果
        results_lines = []
        for r in previous_results:
            results_lines.append(f"任务 {r.get('task_id', '?')}: {r.get('question', '')}")
            results_lines.append(f"  状态: {r.get('status', 'unknown')}")
            if r.get('key_findings'):
                results_lines.append(f"  发现: {r['key_findings']}")
            results_lines.append("")
        formatted_results = "\n".join(results_lines)

        prompt = f"""你是专利分析领域的资深研究员。你已经完成了第一轮探索性分析，现在需要设计更深入的第二轮分析。

**用户研究目标:** {user_goal}

**【第一轮分析结果】**
{formatted_results}

{insights_section}

**当前数据可用列名及语义:**
{columns_semantic}

**数据预览:**
{data_preview_text or "（未提供）"}

{f'**图结构预览:**{chr(10)}{graph_preview_text}' if graph_preview_text else ''}

---

请基于第一轮发现，设计更深入的第二轮分析：
1. 第一轮发现了什么有意思的信号？哪些值得深挖？
2. 第一轮没覆盖到但洞察中提到的分析，是否需要补充？
3. 对第一轮的初步结论，如何加入控制变量、交互效应或非线性检验来增强？

设计 2-3 个深入分析任务。

**⚠️ 关键约束：**
1. 列名必须完全匹配【实际列名】
2. 数据源路径: data/new_data.XLSX, sheet: sheet1
3. 输出结论性数据（JSON 汇总优先）

**输出格式（严格 JSON）：**
{{
  "thinking_trace": {{
    "round1_assessment": "第一轮结果评估：哪些发现有价值，哪些需要深入",
    "gap_analysis": "第一轮的分析空白",
    "deepening_strategy": "深入策略：控制变量/交互效应/非线性检验"
  }},
  "research_objective": "第二轮研究目标",
  "expected_outcomes": ["预期成果1", "预期成果2"],
  "task_graph": [
    {{
      "task_id": "task_r2_1",
      "task_type": "分析类型",
      "question": "本步骤要回答的问题",
      "input_variables": [],
      "output_variables": ["result"],
      "dependencies": [],
      "description": "步骤说明",
      "implementation_config": {{
        "data_source": "data/new_data.XLSX",
        "sheet_name": "sheet1",
        "columns_to_load": ["列名"],
        "parameters": {{}},
        "output_format": "json",
        "output_file": "outputs/task_r2_1_result.json",
        "output_content": {{
          "key_findings": "关键发现"
        }}
      }}
    }}
  ]
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            blueprint = json.loads(content)
            return blueprint
        except Exception as e:
            self.log(f"第二轮蓝图生成失败: {e}", "error")
            return {'error': str(e), 'research_objective': user_goal, 'task_graph': []}

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户目标，生成 DAG 战略蓝图

        Args:
            input_data: {
                "user_goal": str,
                "available_columns": List[str] (可选),
                "use_dag": bool (可选，默认 False),
                "round": int (可选，默认 1，用于两轮迭代),
                "previous_results": List[Dict] (可选，第一轮结果摘要),
                "disable_data_insights": bool (可选，禁用数据洞察生成，用于基线实验)
            }

        Returns:
            {
                "blueprint": dict,
                "method_context": str,
                "data_preview": str,
                "data_insights": dict (如果生成了),
                "graph_preview": str (如果生成了),
                "hypotheses": dict (如果有因果图谱)
            }
        """
        user_goal = input_data.get('user_goal', '')
        available_columns = input_data.get('available_columns', None)
        use_dag = input_data.get('use_dag', False)
        round_num = input_data.get('round', 1)
        previous_results = input_data.get('previous_results', None)
        disable_data_insights = input_data.get('disable_data_insights', False)
        disable_causal_hypotheses = input_data.get('disable_causal_hypotheses', False)

        # 允许外部覆盖数据源
        data_file = input_data.get('data_file')
        sheet_name = input_data.get('sheet_name')
        if data_file:
            self.data_file = data_file
        if sheet_name:
            self.sheet_name = sheet_name

        # ─── 生成 DataPreview ───────────────────────────────
        data_preview_text: Optional[str] = None
        abstracts_text: Optional[str] = None
        data_preview_obj: Optional[DataPreview] = None
        try:
            data_preview_obj = DataPreview.from_file(self.data_file, self.sheet_name)
            data_preview_text = data_preview_obj.to_prompt_string()
            abstracts_text = data_preview_obj.get_abstracts_prompt_string()
        except Exception as e:
            self.log(f"⚠️ DataPreview 生成失败: {e}", "warning")

        # ─── 生成 GraphPreview ──────────────────────────────
        graph_preview_text: Optional[str] = None
        if not disable_data_insights and data_preview_obj is not None:
            try:
                gp = GraphPreview(data_preview_obj.df).build_all()
                graph_preview_text = gp.to_prompt_string()
                self.log(f"✓ GraphPreview: 构建了 {len(gp.graphs)} 个图")
            except Exception as e:
                self.log(f"⚠️ GraphPreview 生成失败: {e}", "warning")

        # ─── 生成数据洞察 ───────────────────────────────────
        data_insights: Optional[Dict] = None
        if not disable_data_insights and data_preview_text:
            self.log("生成数据洞察...")
            data_insights = self._generate_data_insights(
                data_preview_text, graph_preview_text, abstracts_text, user_goal
            )

        # 如果没有提供列名，尝试从数据文件读取
        if available_columns is None:
            self.log("未提供列名，尝试从数据文件读取...")
            available_columns = self._load_real_columns()

        self.log(f"[V5.0] 开始处理用户目标: {user_goal}")
        self.log(f"模式: {'DAG' if use_dag else 'Legacy (List)'}, 轮次: {round_num}")
        if available_columns:
            self.log(f"可用列名: {available_columns}")

        # 步骤 1: 意图转译 - 提取检索关键词
        keywords = self._extract_keywords(user_goal)
        self.log(f"提取的关键词: {keywords}")

        # 步骤 1.5: 因果图谱假设生成（如果有因果图谱且未禁用）
        hypothesis_result = None
        recommended_hypotheses = None
        if disable_causal_hypotheses:
            # Baseline0 模式：跳过因果图谱和方法图谱，纯 LLM 生成
            self.log("Baseline0 模式：跳过因果图谱假设生成")
        elif self.causal_graph and not disable_data_insights:
            self.log("检测到因果图谱，开始生成研究假设...")
            hypothesis_result = self._generate_hypotheses_from_causal_graph(user_goal, keywords)
            if hypothesis_result:
                recommended_hypotheses = hypothesis_result.get('step6_recommendation', {})
                self.log(f"生成 {recommended_hypotheses.get('total_count', 0)} 个假设，"
                        f"核心推荐 {recommended_hypotheses.get('core_count', 0)} 个")
                recommended_hypotheses = self._select_top_core_hypothesis(recommended_hypotheses)
        elif disable_data_insights and self.causal_graph:
            # 基线模式A：仅用因果图谱
            self.log("基线模式：仅使用因果图谱假设...")
            hypothesis_result = self._generate_hypotheses_from_causal_graph(user_goal, keywords)
            if hypothesis_result:
                recommended_hypotheses = hypothesis_result.get('step6_recommendation', {})
                recommended_hypotheses = self._select_top_core_hypothesis(recommended_hypotheses)

        # 步骤 2: 方法图谱检索
        method_context = ""
        if self.method_graph and recommended_hypotheses:
            self.log("从方法图谱检索相关方法...")
            method_context = self._retrieve_methods_for_hypotheses(recommended_hypotheses)

        # 步骤 3: 根据模式和轮次生成蓝图
        if use_dag:
            if round_num == 2 and previous_results:
                # 第二轮：基于第一轮结果生成深入方案
                self.log("第二轮迭代：基于第一轮结果生成深入方案")
                blueprint = self._generate_refined_blueprint(
                    user_goal, previous_results, data_insights,
                    available_columns, data_preview_text, graph_preview_text,
                    graph_context=method_context,
                )
            else:
                # 第一轮或默认：使用 DAG 模式
                blueprint = self._generate_with_dag_mode(
                    user_goal, method_context, available_columns,
                    recommended_hypotheses=recommended_hypotheses,
                    data_preview_text=data_preview_text,
                    data_insights=data_insights,
                    graph_preview_text=graph_preview_text,
                )
        else:
            blueprint = self._generate_with_legacy_mode(user_goal, method_context, available_columns)

        self.log(f"[V5.0] 战略蓝图生成完成 (模式: {'DAG' if use_dag else 'Legacy'}, 轮次: {round_num})")

        result = {
            'blueprint': blueprint,
            'method_context': method_context,
            'data_preview': data_preview_text,
        }

        if data_insights:
            result['data_insights'] = data_insights
        if graph_preview_text:
            result['graph_preview'] = graph_preview_text
        if hypothesis_result:
            result['hypotheses'] = hypothesis_result

        return result
    
    def _generate_with_dag_mode(
        self,
        user_goal: str,
        graph_context: str,
        available_columns: List[str] = None,
        recommended_hypotheses: Dict = None,
        data_preview_text: Optional[str] = None,
        data_insights: Optional[Dict] = None,
        graph_preview_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        V5.0 DAG 模式：生成基于 DAG 的蓝图（集成假设 + 数据洞察）
        """
        max_retries = 3
        blueprint = None

        for attempt in range(max_retries):
            self.log(f"生成 DAG 蓝图 (尝试 {attempt + 1}/{max_retries})")
            blueprint = self._generate_dag_blueprint(
                user_goal,
                graph_context,
                available_columns=available_columns,
                recommended_hypotheses=recommended_hypotheses,
                data_preview_text=data_preview_text,
                data_insights=data_insights,
                graph_preview_text=graph_preview_text,
                retry=attempt > 0
            )
            
            # 图完整性检查
            if self._check_graph_integrity(blueprint, available_columns):
                self.log("✓ 图完整性检查通过")
                break
            else:
                self.log(f"✗ 图完整性检查失败 (尝试 {attempt + 1}/{max_retries})", "warning")
                if attempt == max_retries - 1:
                    self.log("达到最大重试次数，返回最后一次生成的蓝图", "error")
        
        return blueprint
    
    def _generate_with_legacy_mode(
        self, 
        user_goal: str, 
        graph_context: str, 
        available_columns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Legacy 模式：生成传统的 analysis_logic_chains 列表（保持向后兼容）
        """
        blueprint = self._generate_blueprint(user_goal, graph_context, available_columns=available_columns)
        
        # 质量检查
        if not self._check_quality(blueprint):
            self.log("方案质量不足，重新生成", "warning")
            blueprint = self._generate_blueprint(user_goal, graph_context, retry=True, available_columns=available_columns)
        
        return blueprint
    
    def _extract_keywords(self, user_goal: str) -> List[str]:
        """
        意图转译：从用户目标中提取检索关键词
        
        同时提取意图和相关的技术/方法关键词
        """
        prompt = f"""你是专利分析领域的专家。请从用户的研究目标中提取 3-5 个**检索关键词**，用于在知识图谱中查找相关的分析案例。

**用户目标:**
{user_goal}

**关键要求:**
1. 提取用户的**分析意图**（如：技术空白识别、趋势分析、竞争分析等）
2. 提取**领域关键词**（如：数据安全、人工智能、新能源等）
3. 可以包含**常用方法名**（如：聚类、主题建模、专利地图等），这些有助于匹配知识图谱中的案例

**示例:**
用户目标: "分析数据安全领域的技术空白"
关键词: ["技术空白识别", "数据安全", "空白分析", "专利分析", "聚类"]

用户目标: "识别人工智能领域的技术趋势"  
关键词: ["技术趋势", "人工智能", "趋势分析", "时间序列", "专利计量"]

**输出格式（严格 JSON）:**
{{
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 清理响应
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            return result.get('keywords', [])
        except Exception as e:
            self.log(f"关键词提取失败: {e}", "error")
            # 降级：使用简单的关键词提取
            return [user_goal.split()[0]] if user_goal else []
    
    def _retrieve_from_graph(self, keywords: List[str]) -> Tuple[str, List[Dict]]:
        """
        从知识图谱检索相关案例
        
        使用完整逻辑链检索策略
        
        Returns:
            (格式化的文本, 案例列表)
        """
        if not self.neo4j or not keywords:
            return "", []
        
        all_cases = []
        
        for keyword in keywords:
            try:
                # 使用完整逻辑链检索
                cases = self.neo4j.retrieve_best_practices(keyword, limit=2)
                all_cases.extend(cases)
            except Exception as e:
                self.log(f"检索关键词 '{keyword}' 失败: {e}", "warning")
        
        # 格式化为文本
        if not all_cases:
            return "", []
        
        context_parts = []
        for i, case in enumerate(all_cases, 1):
            paper_title = case.get('paper_title', 'Unknown')
            logic_chain = case.get('full_logic_chain', [])
            
            context_parts.append(f"案例 {i}: {paper_title}")
            context_parts.append(f"分析步骤数: {len(logic_chain)}")
            
            for step in logic_chain:
                context_parts.append(f"  - 步骤 {step.get('step_id')}: {step.get('objective')}")
                context_parts.append(f"    方法: {step.get('method_name')}")
                if step.get('config'):
                    context_parts.append(f"    配置: {step.get('config')}")
            
            context_parts.append("")
        
        return "\n".join(context_parts), all_cases
    
    def _describe_columns_semantics(self, columns: List[str]) -> str:
        """
        Schema Awareness: 将列名转换为语义描述（增强版：包含理论变量映射提示）
        
        防止 LLM 误用列名（如将 '公开(公告)号' 误认为日期）
        
        ⚠️ 重要：提供实际列名、语义说明、以及对应的理论变量提示
        
        Args:
            columns: 列名列表
            
        Returns:
            格式化的语义描述字符串
        """
        if not columns:
            return "（数据未加载，请假设标准列名）"
        
        # 常见列名的语义映射（包含理论变量提示）
        semantic_map = {
            '序号': '唯一标识符（整数）',
            '公开(公告)号': '专利编号（如 CN123456A），字符串格式，不是日期',
            '公开(公告)日': '公开日期（时间维度，可用于时间序列分析）',
            '授权日': '授权日期（时间维度，可用于时间序列分析）',
            '申请日': '申请日期（时间维度，可用于时间序列分析）',
            '标题(译)(简体中文)': '专利标题（文本维度，可用于文本分析）',
            '摘要(译)(简体中文)': '专利摘要（文本维度，可用于文本分析、主题建模）',
            '名称': '专利标题（文本维度，可用于文本分析）',
            '摘要': '专利摘要（文本维度，可用于文本分析、主题建模）',
            '申请(专利权)人': '申请人/权利人（实体维度，可用于申请人分布、协作网络分析）',
            '当前申请(专利权)人': '当前申请人/权利人（实体维度，可用于申请人分布分析）',
            '原始申请(专利权)人': '原始申请人（实体维度）',
            '[标]当前申请(专利权)人': '标准化当前申请人（实体维度，已标准化）',
            '[标]原始申请(专利权)人': '标准化原始申请人（实体维度，已标准化）',
            'IPC分类号': '国际专利分类号（技术维度，多值分隔符 |，可用于技术分类、聚类、共现网络）',
            'IPC主分类号': 'IPC 主分类号（技术维度，单值）',
            'CPC分类号': '合作专利分类号（技术维度，可用于技术分类）',
            '主分类号': '主分类号（技术维度）',
            '发明人': '发明人（实体维度，多值分隔符 |，可用于合作网络分析、团队规模统计）',
            '第一发明人': '第一发明人（实体维度，单值）',
            '第一发明人地址': '第一发明人地址（地理维度）',
            '地址': '地址（地理维度，可用于地理分布分析）',
            '代理机构': '代理机构（实体维度）',
            '代理人': '代理人（实体维度）',
            '法律状态/事件': '法律状态（分类维度，如"授权"、"授权|权利转移"等）',
            '被引用专利': '被引用专利列表（前向引文，多值分隔符 |，可用于引用网络分析）',
            '被引用专利数量': '被引用次数（数值维度，反映专利影响力）',
            '引用专利': '引用专利列表（后向引文，多值分隔符 |，可用于引用网络分析）',
            '引用专利数量': '引用次数（数值维度）',
            '简单同族': '专利家族（关系维度，多值分隔符 |，可用于国际化/扩展度分析）',
            '简单同族编号': '同族编号（数值维度）',
            '优先权国家/地区': '优先权国家（地理维度，可用于国家/地区分布分析）',
        }
        
        descriptions = []
        descriptions.append("【实际列名】→【语义说明】")
        descriptions.append("")
        descriptions.append("【列名语义说明】")
        descriptions.append("")
        
        for col in columns:
            semantic = semantic_map.get(col, f"未知语义，请谨慎使用")
            descriptions.append(f"  '{col}' → {semantic}")
        
        descriptions.append("")
        descriptions.append("⚠️ 重要：使用列名时，请直接复制上面的【实际列名】（包括引号内的内容），不要使用任何其他名称！")
        descriptions.append("⚠️ 提示：根据研究假设中的变量定义，从上面的列名中选择最合适的列进行计算")
        
        return "\n".join(descriptions)
    
    def _generate_dag_blueprint(
        self,
        user_goal: str,
        graph_context: str,
        retry: bool = False,
        available_columns: List[str] = None,
        recommended_hypotheses: Dict = None,
        data_preview_text: Optional[str] = None,
        data_insights: Optional[Dict] = None,
        graph_preview_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成基于 DAG 的研究战略蓝图（集成数据洞察 + 假设 + 图结构）
        """
        # 格式化列名语义描述
        columns_semantic = self._describe_columns_semantics(available_columns)

        # 格式化假设信息（如果有，降级为可选参考）
        hypotheses_section = self._format_hypotheses_for_prompt(recommended_hypotheses)

        # 格式化数据洞察（如果有，作为主驱动）
        insights_section = self._format_data_insights_for_prompt(data_insights) if data_insights else ""
        
        prompt = f"""你是专利分析领域的资深研究员和数据科学家。请根据用户的研究目标，设计一个**基于 DAG（有向无环图）的分析方案**。

**用户研究目标:**
{user_goal}

{insights_section}

{hypotheses_section if hypotheses_section else "（因果图谱假设：未提供或已禁用）"}

**当前数据可用列名及语义:**
{columns_semantic}

**数据预览（结构统计 + 关键列样例 + 跨列统计）:**
{data_preview_text or "（未提供数据预览）"}

{f'**图结构预览（自动构建的网络分析结果）:**{chr(10)}{graph_preview_text}' if graph_preview_text else ''}

**⚠️⚠️⚠️ 关键约束（必须遵守）⚠️⚠️⚠️**
1. **列名必须完全匹配**：只能使用上面【实际列名】中列出的列名，一个字都不能改
2. **禁止自创列名**：不要使用任何未在上面列出的列名（如 ID, Title, Abstract, Applicant, Grant Date 等）
3. **直接复制列名**：从【实际列名】中直接复制粘贴，确保完全一致（包括括号、空格等）
4. **数据源路径固定**：主数据路径必须使用 `data/new_data.XLSX`，sheet名为 `sheet1`

**错误示例（禁止）:**
- ❌ "ID" （应该使用 "序号"）
- ❌ "Title" （应该使用 "名称"）
- ❌ "Abstract" （应该使用 "摘要"）
- ❌ 输出 1000 行的 topic_0, topic_1, ... 特征矩阵（应该输出主题汇总）

**正确示例（必须）:**
- ✓ "序号"
- ✓ "名称"
- ✓ "摘要"
- ✓ 输出主题汇总 JSON（8 个主题，每个包含标签、关键词、专利数）

**相关案例参考:**
{graph_context if graph_context else "（无相关案例，请基于你的专业知识设计）"}

---

## 设计要求

### 1. 思考过程（Thinking Trace）
在生成方案前，请先进行以下思考（填入 `thinking_trace` 字段）：
- **领域理解**: 基于摘要和数据特征，简述该技术领域的特点
- **数据审计**: 列出可用的列名（从上面【实际列名】中复制），说明每个列的用途
- **洞察选择**: 如果提供了数据洞察，选择 2-3 个最有价值的洞察，说明理由
- **假设分析**: 如果提供了研究假设，分析需要计算哪些变量，需要哪些列
- **创新性评估**: ⚠️ **关键步骤** - 评估当前方案的结论是否有洞察力：
  * 这个结论是否是"常识"（如"老专利被引用多"、"大公司专利多"）？
  * 如果是常识性结论，必须调整方案，挖掘更有价值的维度
  * 好的结论应该是：反直觉的、有比较的、能指导决策的
- **算法选择**: 根据用户目标和假设，选择最合适的算法
- **结论设计**: 每个任务应该回答什么问题？输出什么结论？

**⚠️ 避免常识性结论陷阱**：
以下是**没有洞察价值**的常识性结论，必须避免：
- ❌ "专利年龄越大，被引用次数越多" — 这是时间累积效应，谁都知道
- ❌ "大公司的专利数量多" — 这是资源差异，没有洞察
- ❌ "热门领域的专利增长快" — 这是定义循环
- ❌ "引用多的专利被引用也多" — 这是网络效应常识

以下是**有洞察价值**的结论类型，应该追求：
- ✅ "团队规模存在最优点：3-5人团队的专利影响力最高，超过大团队" — 倒U型关系
- ✅ "G06F领域的投入产出比是H04L的2倍" — 跨领域比较
- ✅ "中国专利的年化引用率正在超越美国" — 趋势反转
- ✅ "高引用专利的发明人往往不是高产发明人" — 反直觉发现

### 2. DAG 结构（Task Graph）
将研究目标分解为 2-4 个任务节点，每个节点必须：
- 回答一个明确的问题
- 输出结论性数据（JSON 汇总 > CSV 表格 > 原始数据）
- 包含关键发现（key_findings）
- 如果有假设，优先设计假设验证任务

任务节点结构：
- `task_id`: 唯一标识（如 "task_1", "task_2"）
- `task_type`: 任务类型（如 "data_summary", "hypothesis_test", "variable_calculation", "regression_analysis"）
- `question`: 该任务要回答的问题（如 "假设H1是否成立？"）
- `input_variables`: 输入变量列表（如 ["df_raw"]）
- `output_variables`: 输出变量列表（如 ["hypothesis_test_result", "regression_model"]）
- `dependencies`: 依赖的前序任务 ID 列表（如 ["task_1"]）
- `description`: 任务描述
- `implementation_config`: 实现配置

### 3. 输出格式要求

**优先级（从高到低）:**
1. **JSON 汇总文件**（最优）
   - 包含结论、统计、关键发现
   - 适合报告智能体直接使用
   - 示例：`hypothesis_test_result.json`, `regression_analysis.json`

2. **CSV 汇总表格**（次优）
   - 汇总级别的数据（如 8 个主题，不是 1000 条专利）
   - 包含统计指标
   - 示例：`variable_statistics.csv` (30 rows)

3. **原始数据文件**（仅作为备份）
   - 保存用于追溯，但不是主要输出
   - 示例：`df_raw.csv` (1000 rows)

### 4. 假设验证与中介分析通用原则（不预设指标）

- 若提供研究假设，**基于假设语义 + 可用列名**自主定义变量与计算方式。
- **不要预设固定指标或变量编号**，变量命名以当前任务语义为准。
- 中介分析时，independent_var/mediator_var/dependent_var 必须不同。
- 控制变量不能与自变量或中介变量重复，且避免高度相关（共线性）变量。
- 若关键变量无法由现有列计算，应跳过或改为更直接的检验方式。

---

## 输出格式（严格 JSON）

{{
  "thinking_trace": {{
    "domain_understanding": "基于摘要和数据特征的领域理解",
    "data_audit": "简要列出可用列名及用途（从【实际列名】复制）",
    "selected_insights": "选择的 2-3 个核心洞察及理由（如有数据洞察）",
    "hypothesis_analysis": "若有假设，说明如何把假设语义映射到可用列",
    "algorithm_selection": "选择方法的理由",
    "conclusion_design": "每个任务预期输出的结论"
  }},
  "research_objective": "研究目标的简洁描述",
  "expected_outcomes": ["预期成果1（结论性）", "预期成果2（结论性）"],
  "task_graph": [
    {{
      "task_id": "task_1",
      "task_type": "analysis",
      "question": "本步骤要回答的问题",
      "input_variables": [],
      "output_variables": ["result_1"],
      "dependencies": [],
      "description": "步骤说明",
      "implementation_config": {{
        "data_source": "data/new_data.XLSX",
        "sheet_name": "sheet1",
        "columns_to_load": ["<列名1>", "<列名2>"],
        "parameters": {{}},
        "output_format": "json",
        "output_file": "outputs/task_1_result.json",
        "output_content": {{
          "key_findings": "关键发现"
        }}
      }}
    }}
  ]
}}

**⚠️ 回归分析的输出要求（所有类型）：**
```json
"output_content": {{
  "hypothesis_id": "H1",
  "hypothesis_statement": "假设陈述",
  "test_method": "Linear Regression / Mediation Analysis",
  "effect_size_criteria": {{
    "small": "< 0.3",
    "medium": "0.3 - 0.5",
    "large": "> 0.5"
  }},
  "results": {{
    "coefficient": "回归系数（float）",
    "std_error": "标准误（float）",
    "p_value": "显著性（float）",
    "r_squared": "拟合优度（float）",
    "effect_size": "small/medium/large（基于标准化系数）",
    "standardized_coefficient": "标准化系数（用于判断效应量）",
    "conclusion": "假设是否成立"
  }},
  "key_findings": "包含效应量的实质性解释，例如：'技术成熟度对影响力有中等正向效应（β=0.35）'"
}}
```

**⚠️ 中介分析的输出要求（如果是中介假设）：**
```json
"output_content": {{
  "hypothesis_id": "H1",
  "hypothesis_statement": "M中介X对Y的影响",
  "test_method": "Bootstrap Mediation Analysis (5000 samples)",
  "effect_size_criteria": {{
    "small": "< 0.3",
    "medium": "0.3 - 0.5",
    "large": "> 0.5"
  }},
  "path_coefficients": {{
    "total_effect": {{
      "coefficient": "float",
      "p_value": "float",
      "effect_size": "small/medium/large",
      "interpretation": "X对Y的总效应"
    }},
    "a_path": {{
      "coefficient": "float",
      "p_value": "float",
      "effect_size": "small/medium/large",
      "interpretation": "X对M的影响"
    }},
    "b_path": {{
      "coefficient": "float",
      "p_value": "float",
      "effect_size": "small/medium/large",
      "interpretation": "M对Y的影响（控制X）"
    }},
    "direct_effect": {{
      "coefficient": "float",
      "p_value": "float",
      "effect_size": "small/medium/large",
      "interpretation": "X对Y的直接效应（控制M）"
    }},
    "indirect_effect": {{
      "coefficient": "float",
      "ci_95": "[lower, upper]",
      "p_value": "float",
      "effect_size": "small/medium/large",
      "interpretation": "通过M的间接效应"
    }}
  }},
  "mediation_ratio": "float (0-100，间接效应/总效应×100%)",
  "mediation_type": "完全中介/部分中介/无中介",
  "conclusion": "中介效应是否显著，方向（正/负）",
  "key_findings": "包含效应量和中介比例的实质性解释，例如：'M贡献了60%的效应，是关键中介机制'"
}}
```

**生成前检查清单:**
- [ ] 所有列名都在【实际列名】中
- [ ] 数据源路径为 data/new_data.XLSX（sheet1）
- [ ] 变量命名与计算方式来源于任务语义与可用列（不预设固定指标）
- [ ] 中介分析的三个变量（X、M、Y）必须不同
- [ ] 控制变量不能是中介变量本身
- [ ] 控制变量不与自变量的计算公式相同或高度相关
- [ ] 每个任务都有明确的 question
- [ ] 每个任务的输出都是结论性的（JSON 汇总 > CSV 表格）
- [ ] output_content 包含 effect_size 字段（所有回归分析）
- [ ] 中介分析包含 mediation_ratio 字段

{"**⚠️ 重试提示**: 上次生成使用了错误的列名或输出了中间特征，请严格使用【实际列名】并输出结论性数据！" if retry else ""}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 清理响应
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            blueprint = json.loads(content)
            
            # 验证必要字段
            required_fields = ['research_objective', 'task_graph']
            for field in required_fields:
                if field not in blueprint:
                    self.log(f"警告: 缺少必要字段 {field}", "warning")
            
            return blueprint
            
        except json.JSONDecodeError as e:
            self.log(f"JSON 解析失败: {e}", "error")
            return {
                'error': f'JSON 解析失败: {e}',
                'raw_response': content,
                'research_objective': user_goal,
                'task_graph': []
            }
        except Exception as e:
            self.log(f"DAG 蓝图生成失败: {e}", "error")
            return {
                'error': str(e),
                'research_objective': user_goal,
                'task_graph': []
            }
        
    def _check_graph_integrity(
        self, 
        blueprint: Dict[str, Any], 
        available_columns: List[str] = None
    ) -> bool:
        """
        图完整性检查：模拟执行 DAG，验证变量流的完整性
        
        检查项：
        1. 基本结构完整性
        2. 变量流一致性（输入变量必须由前序任务产出）
        3. 依赖关系正确性（无循环依赖）
        4. 列名合法性（不使用幻觉列名）
        
        Args:
            blueprint: 生成的蓝图
            available_columns: 可用列名列表
            
        Returns:
            bool: 是否通过检查
        """
        # 检查 1: 基本结构
        if 'error' in blueprint:
            self.log("完整性检查失败: 蓝图包含错误", "error")
            return False
        
        task_graph = blueprint.get('task_graph', [])
        if not task_graph:
            self.log("完整性检查失败: task_graph 为空", "error")
            return False
        
        # 检查 2: 任务节点完整性
        for task in task_graph:
            required_fields = ['task_id', 'input_variables', 'output_variables', 'dependencies']
            for field in required_fields:
                if field not in task:
                    self.log(f"完整性检查失败: 任务 {task.get('task_id', 'unknown')} 缺少字段 {field}", "error")
                    return False
        
        # 检查 3: 变量流一致性
        # 初始化可用变量：包含测试数据（如果提供）
        available_vars = {'df_raw'}
        
        task_outputs = {}  # 记录每个任务的输出变量
        
        # 按依赖关系排序任务（拓扑排序）
        sorted_tasks = self._topological_sort(task_graph)
        if sorted_tasks is None:
            self.log("完整性检查失败: 存在循环依赖", "error")
            return False
        
        for task in sorted_tasks:
            task_id = task['task_id']
            input_vars = set(task.get('input_variables', []))
            output_vars = set(task.get('output_variables', []))
            
            # 检查输入变量是否可用
            missing_vars = input_vars - available_vars
            if missing_vars:
                self.log(
                    f"完整性检查失败: 任务 {task_id} 需要变量 {missing_vars}，但这些变量未被前序任务产出",
                    "error"
                )
                self.log(f"  当前可用变量: {available_vars}", "error")
                return False
            
            # 更新可用变量集合
            available_vars.update(output_vars)
            task_outputs[task_id] = output_vars
        
        # 检查 4: 列名合法性（如果提供了 available_columns）
        if available_columns:
            if not self._check_column_validity(task_graph, available_columns):
                return False
        
        self.log(f"完整性检查通过: {len(task_graph)} 个任务，变量流完整")
        return True
    
    def _topological_sort(self, task_graph: List[Dict]) -> List[Dict]:
        """
        拓扑排序：按依赖关系排序任务
        
        Args:
            task_graph: 任务图
            
        Returns:
            排序后的任务列表，如果存在循环依赖则返回 None
        """
        # 构建任务 ID 到任务对象的映射
        task_map = {task['task_id']: task for task in task_graph}
        
        # 计算每个任务的入度
        in_degree = {task['task_id']: 0 for task in task_graph}
        for task in task_graph:
            for dep in task.get('dependencies', []):
                if dep in in_degree:
                    in_degree[task['task_id']] += 1
        
        # 找到所有入度为 0 的任务
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []
        
        while queue:
            # 取出一个入度为 0 的任务
            task_id = queue.pop(0)
            sorted_tasks.append(task_map[task_id])
            
            # 减少依赖该任务的其他任务的入度
            for task in task_graph:
                if task_id in task.get('dependencies', []):
                    in_degree[task['task_id']] -= 1
                    if in_degree[task['task_id']] == 0:
                        queue.append(task['task_id'])
        
        # 如果排序后的任务数量不等于原任务数量，说明存在循环依赖
        if len(sorted_tasks) != len(task_graph):
            return None
        
        return sorted_tasks
    
    def _check_column_validity(
        self, 
        task_graph: List[Dict], 
        available_columns: List[str]
    ) -> bool:
        """
        检查列名合法性：确保任务中使用的列名都在 available_columns 中
        
        Args:
            task_graph: 任务图
            available_columns: 可用列名列表
            
        Returns:
            bool: 是否通过检查
        """
        available_set = set(available_columns)
        
        for task in task_graph:
            config = task.get('implementation_config', {})
            
            # 检查 columns_to_load
            columns_to_load = config.get('columns_to_load', [])
            if columns_to_load:
                invalid_cols = set(columns_to_load) - available_set
                if invalid_cols:
                    self.log(
                        f"列名检查失败: 任务 {task['task_id']} 使用了不存在的列名 {invalid_cols}",
                        "error"
                    )
                    self.log(f"  可用列名: {available_columns}", "error")
                    return False
            
            # 检查 text_column
            text_column = config.get('text_column')
            if text_column and text_column not in available_set:
                self.log(
                    f"列名检查失败: 任务 {task['task_id']} 使用了不存在的文本列 {text_column}",
                    "error"
                )
                return False
        
        return True
    
    # ==================== Legacy 模式方法（保持向后兼容）====================
    
    def _generate_blueprint(self, user_goal: str, graph_context: str, retry: bool = False, available_columns: List[str] = None) -> Dict[str, Any]:
        """
        生成研究战略蓝图（Legacy 模式）
        
        整合了 V4.0 的跨域迁移 Prompt + V4.1 的列名注入和模型文件意识
        
        Args:
            user_goal: 用户研究目标
            graph_context: 知识图谱检索结果
            retry: 是否为重试生成
            available_columns: 真实数据的列名列表（防止幻觉列名）
        """
        # 格式化可用列名
        columns_info = "（数据未加载，请假设标准列名如 'title', 'abstract', 'applicant', 'ipc_code'）"
        if available_columns:
            columns_info = str(available_columns)
        
        prompt = f"""你是专利分析领域的资深研究员。请根据用户的研究目标，设计一个**创新且有针对性**的分析方案。

**用户研究目标:**
{user_goal}

**当前数据可用列名（必须从中选择输入列）:**
{columns_info}

**相关案例参考:**
{graph_context if graph_context else "（无相关案例，请基于你的专业知识设计）"}

**设计要求:**
1. 将研究目标分解为 2-4 个**独立可运行的 Python 脚本**。
2. **鼓励创新**：根据用户目标选择最合适的方法，不要局限于常见方法。可以考虑：
   - 文本分析：LDA、NMF、BERTopic、Word2Vec、TF-IDF
   - 聚类：KMeans、DBSCAN、层次聚类、谱聚类
   - 异常检测：ABOD、Isolation Forest、LOF、One-Class SVM
   - 网络分析：共现网络、引用网络、技术演化路径
   - 时间序列：趋势分析、突变检测、周期性分析
   - 其他创新方法
3. 每个脚本是完全独立的，明确：
   - **输入数据源**: 
     * 主数据：从 Excel 文件加载（列名必须使用【当前数据可用列名】）
     * 前置依赖：如果需要前一步的结果，从文件加载（如 `step_1_results.csv` 或 `step_1_model.pkl`）
   - **输出文件**: 
     * 新列数据：保存为 CSV（如 `step_1_results.csv`，包含新生成的列）
     * 模型文件：保存为 PKL（如 `step_1_lda_model.pkl`，使用 joblib）
   - **方法**: 具体算法名称
4. 步骤关系：
   - 串行：Step 2 需要加载 Step 1 保存的文件。
   - 并行：独立运行，不依赖其他步骤。

**重要提示：**
- **严禁幻觉列名**：输入列名必须严格匹配【当前数据可用列名】中提供的列表。
- **理解列的含义**：
  * `公开(公告)号` 是专利编号（如 "CN123456A"），不是日期
  * `授权日` 是日期列，用于时间序列分析
  * 不要混淆这两列的用途
- **输出格式要求**：
  * 数值型结果：直接保存数值（int, float）
  * 分类结果：保存类别标签（str, int）
  * 时间序列结果：保存数值统计（如变化点数量、趋势值），不要保存 Timestamp 对象或列表
- **不要复制示例**：下面的示例仅供参考格式，列名必须使用实际提供的列名。
- **文件路径固定**：主数据路径固定为 `data/new_data.XLSX`，sheet 名为 `sheet1`。
- **文件传递思维**：
  - 步骤 1 保存 `outputs/step_1_results.csv`（包含新生成的列）
  - 步骤 2 加载 `outputs/step_1_results.csv`，使用新生成的列
  - 步骤 1 保存 `outputs/step_1_model.pkl`（如果有模型）
  - 步骤 2 加载 `outputs/step_1_model.pkl` 使用模型
- **参数粒度**：只需提供关键参数建议（如 n_topics: 5），具体参数由后续 Agent 填充。
- 避免抽象概念（❌"构建知识图谱"），使用具体操作（✅"LDA主题分类"）。
- 每个脚本可以直接运行：`python step_1.py`

{"**注意**: 这是第二次生成，请提高方案的详细程度和可执行性。" if retry else ""}

**输出格式（严格 JSON）:**
下面是**格式示例**（仅供参考结构，请根据用户目标创新设计）：

{{
  "research_objective": "研究目标的简洁描述",
  "expected_outcomes": ["预期成果1", "预期成果2"],
  "analysis_logic_chains": [
    {{
      "step_id": 1,
      "objective": "第一步的分析目标（根据用户需求设计）",
      "method": "选择合适的方法（参考上面的方法列表）",
      "implementation_config": {{
        "algorithm": "具体算法名称",
        "input_data_source": {{
          "main_data": "data/new_data.XLSX",
          "main_data_columns": ["从可用列名中选择需要的列"],
          "dependencies": []
        }},
        "output_files": {{
          "results_csv": "outputs/step_1_results.csv",
          "results_columns": ["result_col1", "result_col2"],
          "column_types": {{"result_col1": "数据类型", "result_col2": "数据类型"}},
          "format_notes": "只保存 ID 列（序号、公开(公告)号）和新生成的列",
          "model_pkl": "outputs/step_1_model.pkl",
          "model_objects": ["model_name"]
        }},
        "parameters": {{"param1": "value1"}}
      }},
      "notes": "步骤说明",
      "depends_on": []
    }},
    {{
      "step_id": 2,
      "objective": "第二步的分析目标（可以依赖步骤1）",
      "method": "选择合适的方法",
      "implementation_config": {{
        "algorithm": "具体算法名称",
        "input_data_source": {{
          "main_data": "data/new_data.XLSX",
          "main_data_columns": [],
          "dependencies": [
            {{
              "file": "outputs/step_1_results.csv",
              "columns": ["result_col1", "result_col2"],
              "description": "步骤1生成的结果"
            }}
          ]
        }},
        "output_files": {{
          "results_csv": "outputs/step_2_results.csv",
          "results_columns": ["new_col1"],
          "format_notes": "只保存 ID 列和新生成的列",
          "model_pkl": null,
          "model_objects": []
        }},
        "parameters": {{"param1": "value1"}}
      }},
      "notes": "步骤说明",
      "depends_on": [1]
    }}
  ]
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 清理响应
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            blueprint = json.loads(content)
            
            # 验证必要字段
            required_fields = ['research_objective', 'analysis_logic_chains']
            for field in required_fields:
                if field not in blueprint:
                    self.log(f"警告: 缺少必要字段 {field}", "warning")
            
            return blueprint
            
        except json.JSONDecodeError as e:
            self.log(f"JSON 解析失败: {e}", "error")
            return {
                'error': f'JSON 解析失败: {e}',
                'raw_response': content,
                'research_objective': user_goal,
                'analysis_logic_chains': []
            }
        except Exception as e:
            self.log(f"蓝图生成失败: {e}", "error")
            return {
                'error': str(e),
                'research_objective': user_goal,
                'analysis_logic_chains': []
            }
    
    def _check_quality(self, blueprint: Dict[str, Any]) -> bool:
        """
        质量检查：评估生成的方案是否合格（Legacy 模式）
        
        V4.1 增强：检查文件传递结构
        """
        # 基本检查
        if 'error' in blueprint:
            return False
        
        logic_chains = blueprint.get('analysis_logic_chains', [])
        
        # 检查步骤数量
        if len(logic_chains) < 2:
            self.log("质量检查失败: 步骤数量不足", "warning")
            return False
        
        # 检查每个步骤的完整性
        for step in logic_chains:
            required_fields = ['step_id', 'objective', 'method', 'implementation_config']
            for field in required_fields:
                if field not in step:
                    self.log(f"质量检查失败: 步骤 {step.get('step_id')} 缺少字段 {field}", "warning")
                    return False
            
            # 检查 implementation_config 的详细程度
            config = step.get('implementation_config', {})
            if not config or len(config) < 2:
                self.log(f"质量检查失败: 步骤 {step.get('step_id')} 配置不够详细", "warning")
                return False
            
            # V4.1: 检查必要的配置字段（文件传递结构）
            config_required = ['input_data_source', 'output_files']
            for field in config_required:
                if field not in config:
                    self.log(f"质量检查失败: 步骤 {step.get('step_id')} 配置缺少 {field}", "warning")
                    return False
            
            # 验证 input_data_source 结构
            input_source = config.get('input_data_source', {})
            if 'main_data' not in input_source or 'dependencies' not in input_source:
                self.log(f"质量检查失败: 步骤 {step.get('step_id')} 的 input_data_source 结构不完整", "warning")
                return False
            
            # 验证 output_files 结构
            output_files = config.get('output_files', {})
            if 'results_csv' not in output_files or 'results_columns' not in output_files:
                self.log(f"质量检查失败: 步骤 {step.get('step_id')} 的 output_files 结构不完整", "warning")
                return False
        
        return True
