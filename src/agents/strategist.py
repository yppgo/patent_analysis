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
from typing import Dict, Any, List, Set, Tuple
from src.agents.base_agent import BaseAgent


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
        self.data_file = data_file or "data/clean_patents1_with_topics_filled.xlsx"
        self.sheet_name = "clear"
    
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
        lines.append("3. 例如：")
        lines.append("   - V16_tech_impact（被引用次数）→ 选择 '被引用专利数量' 列")
        lines.append("   - V09_tech_diversity（IPC多样性）→ 选择 'IPC分类号' 列，计算Shannon熵")
        lines.append("   - V04_international_collab（外国发明人占比）→ 选择 '发明人' 列，需要解析国籍")
        lines.append("")
        
        return "\n".join(lines)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户目标，生成 DAG 战略蓝图
        
        Args:
            input_data: {
                "user_goal": str,
                "available_columns": List[str] (可选，如果不提供则自动从数据文件读取),
                "use_dag": bool (可选，是否使用 DAG 模式，默认 False 保持向后兼容)
            }
            
        Returns:
            {
                "blueprint": dict,  # 包含 task_graph (DAG) 或 analysis_logic_chains (List)
                "graph_context": str,
                "hypotheses": dict (可选，如果有因果图谱)
            }
        """
        user_goal = input_data.get('user_goal', '')
        available_columns = input_data.get('available_columns', None)
        use_dag = input_data.get('use_dag', False)  # 默认 False，保持向后兼容
        
        # 如果没有提供列名，尝试从数据文件读取
        if available_columns is None:
            self.log("未提供列名，尝试从数据文件读取...")
            available_columns = self._load_real_columns()
        
        self.log(f"[V5.0] 开始处理用户目标: {user_goal}")
        self.log(f"模式: {'DAG' if use_dag else 'Legacy (List)'}")
        if available_columns:
            self.log(f"可用列名: {available_columns}")
        else:
            self.log("未获取到列名，将使用默认假设", "warning")
        
        # 步骤 1: 意图转译 - 提取检索关键词
        keywords = self._extract_keywords(user_goal)
        self.log(f"提取的关键词: {keywords}")
        
        # 新增：步骤 1.5 - 因果图谱假设生成（如果有因果图谱）
        hypothesis_result = None
        recommended_hypotheses = None
        if self.causal_graph:
            self.log("检测到因果图谱，开始生成研究假设...")
            hypothesis_result = self._generate_hypotheses_from_causal_graph(user_goal, keywords)
            if hypothesis_result:
                recommended_hypotheses = hypothesis_result.get('step6_recommendation', {})
                self.log(f"生成 {recommended_hypotheses.get('total_count', 0)} 个假设，"
                        f"核心推荐 {recommended_hypotheses.get('core_count', 0)} 个")
        
        # 步骤 2: 方法图谱检索（如果有方法图谱）
        method_context = ""
        if self.method_graph and recommended_hypotheses:
            self.log("从方法图谱检索相关方法...")
            method_context = self._retrieve_methods_for_hypotheses(recommended_hypotheses)
        elif not self.method_graph:
            self.log("未加载方法图谱，跳过方法检索", "warning")
        
        # 步骤 3: 根据模式生成蓝图
        if use_dag:
            # V5.0 DAG 模式（集成假设和方法）
            blueprint = self._generate_with_dag_mode(
                user_goal, 
                method_context, 
                available_columns,
                recommended_hypotheses=recommended_hypotheses
            )
        else:
            # Legacy 模式（保持向后兼容）
            blueprint = self._generate_with_legacy_mode(user_goal, method_context, available_columns)
        
        self.log(f"[V5.0] 战略蓝图生成完成 (模式: {'DAG' if use_dag else 'Legacy'})")
        
        result = {
            'blueprint': blueprint,
            'method_context': method_context  # 改为 method_context
        }
        
        # 如果生成了假设，添加到返回结果中
        if hypothesis_result:
            result['hypotheses'] = hypothesis_result
        
        return result
    
    def _generate_with_dag_mode(
        self, 
        user_goal: str, 
        graph_context: str, 
        available_columns: List[str] = None,
        recommended_hypotheses: Dict = None
    ) -> Dict[str, Any]:
        """
        V5.0 DAG 模式：生成基于 DAG 的蓝图（集成假设）
        
        Args:
            recommended_hypotheses: 因果图谱推荐的假设（可选）
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
            '名称': '专利标题（文本维度，可用于文本分析）',
            '摘要': '专利摘要（文本维度，可用于文本分析、主题建模）',
            '申请(专利权)人': '申请人/权利人（实体维度，可用于实体分析、网络分析）→ 可计算企业规模(V02_firm_size)、研发投资(V03_rd_investment)',
            'IPC分类号': '国际专利分类号（技术维度，可用于技术分类、聚类）→ 可计算技术多样性(V09_tech_diversity)、技术广度(V14_tech_breadth)',
            'CPC分类号': '合作专利分类号（技术维度，可用于技术分类）→ 可计算技术多样性(V09_tech_diversity)',
            '主分类号': '主分类号（技术维度）',
            '发明人': '发明人（实体维度，可用于合作网络分析）→ 可计算国际合作(V04_international_collab)、研发效率(V13_rd_efficiency)',
            '地址': '地址（地理维度，可用于地理分布分析）',
            '代理机构': '代理机构（实体维度）',
            '代理人': '代理人（实体维度）',
            '法律状态': '法律状态（分类维度）',
            '引用文献': '引用文献（关系维度，可用于引用网络分析）→ 可计算科学关联度(V10_science_linkage)',
            '被引用专利': '被引用专利（前向引文，关系维度）→ 可计算技术影响力(V16_tech_impact)',
            '被引用专利数量': '被引用次数（数值维度）→ 技术影响力(V16_tech_impact)的直接度量',
            '引用专利': '引用专利（后向引文，关系维度）→ 可计算科学关联度(V10_science_linkage)',
            '引用专利数量': '引用次数（数值维度）→ 可用于计算知识基础广度',
            '简单同族': '专利家族（关系维度）→ 可计算国际化程度',
            '优先权国家/地区': '优先权国家（地理维度）→ 可计算国际合作(V04_international_collab)',
        }
        
        descriptions = []
        descriptions.append("【实际列名】→【语义说明】→【可计算的理论变量】")
        descriptions.append("")
        descriptions.append("⚠️ 理论变量说明：")
        descriptions.append("  - V02_firm_size: 企业规模（专利数量）")
        descriptions.append("  - V03_rd_investment: 研发投资强度（人均专利产出）")
        descriptions.append("  - V04_international_collab: 国际合作强度（外国发明人占比）")
        descriptions.append("  - V09_tech_diversity: 技术多样性（IPC分类的Shannon熵）")
        descriptions.append("  - V10_science_linkage: 科学关联度（引用科学文献的比例）")
        descriptions.append("  - V13_rd_efficiency: 研发效率（人均专利产出）")
        descriptions.append("  - V14_tech_breadth: 技术广度（IPC分类数量）")
        descriptions.append("  - V16_tech_impact: 技术影响力（被引用次数）")
        descriptions.append("")
        descriptions.append("【列名与理论变量的对应关系】")
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
        recommended_hypotheses: Dict = None
    ) -> Dict[str, Any]:
        """
        生成基于 DAG 的研究战略蓝图（集成假设）
        
        核心改进：
        1. 引入 thinking_trace 字段（CoT）
        2. 使用 task_graph 替代 analysis_logic_chains
        3. 每个任务明确 input_variables 和 output_variables
        4. Schema Awareness：提供列名语义描述
        5. 集成因果图谱假设：提供变量定义和测量方法
        
        Args:
            user_goal: 用户研究目标
            graph_context: 知识图谱检索结果
            retry: 是否为重试生成
            available_columns: 真实数据的列名列表
            recommended_hypotheses: 因果图谱推荐的假设（可选）
        """
        # 格式化列名语义描述
        columns_semantic = self._describe_columns_semantics(available_columns)
        
        # 格式化假设信息（如果有）
        hypotheses_section = self._format_hypotheses_for_prompt(recommended_hypotheses)
        
        prompt = f"""你是专利分析领域的资深研究员和数据科学家。请根据用户的研究目标，设计一个**基于 DAG（有向无环图）的分析方案**。

**用户研究目标:**
{user_goal}

{hypotheses_section}

**当前数据可用列名及语义:**
{columns_semantic}

**⚠️⚠️⚠️ 关键约束（必须遵守）⚠️⚠️⚠️**
1. **列名必须完全匹配**：只能使用上面【实际列名】中列出的列名，一个字都不能改
2. **禁止自创列名**：不要使用任何未在上面列出的列名（如 ID, Title, Abstract, Applicant, Grant Date 等）
3. **直接复制列名**：从【实际列名】中直接复制粘贴，确保完全一致（包括括号、空格等）
4. **数据源路径固定**：主数据路径必须使用 `data/clean_patents1_with_topics_filled.xlsx`，sheet名为 `clear`
5. **变量计算要简单可行**：
   - 技术成熟度(V22)：使用"专利年龄"（当前年份 - 授权年份）作为代理变量
   - 技术多样性(V09)：如果只有"IPC主分类号"（单个值），改用"是否跨IPC大类"或其他可行指标
   - 避免需要复杂分组聚合的计算
6. **结论导向输出**：每个任务必须输出结论性数据（汇总、统计、发现），而不是中间特征或原始数据
7. **假设验证优先**：如果提供了研究假设，优先设计任务来验证这些假设
8. **添加控制变量**：回归分析和假设检验应包含基本控制变量（如专利年龄、申请人类型等）

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
- **数据审计**: 列出可用的列名（从上面【实际列名】中复制），说明每个列的用途
- **假设分析**: 如果提供了研究假设，分析需要计算哪些变量，需要哪些列
- **算法选择**: 根据用户目标和假设，选择最合适的算法
- **结论设计**: 每个任务应该回答什么问题？输出什么结论？

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

### 4. 假设验证任务示例

**如果提供了假设 "V09_tech_diversity → V16_tech_impact":**
```
Task 1: 变量计算
  - 计算 V09_tech_diversity（简化方法：从 'IPC主分类号' 提取大类字母，如 'G06F' → 'G'）
  - 计算 V16_tech_impact（从 '被引用专利数量' 直接获取）
  - 计算控制变量：patent_age（2026 - 授权年份）
  - 输出：variables_calculated.csv

Task 2: 假设检验
  - 使用回归分析验证 V09 → V16 的关系
  - 包含控制变量（patent_age）
  - 注意：控制变量不能与自变量重复
  - 输出：hypothesis_test_result.json（包含系数、p值、结论）
```

**⚠️ 变量计算示例（避免常见错误）：**

✅ **正确示例**：
- V22_tech_maturity: "2026 - pd.to_datetime('授权日').dt.year"
- V09_tech_diversity（类别变量）: "'IPC主分类号'.str[0]  # 保持为字符串，需要虚拟变量编码"
- V13_rd_efficiency: "1.0 / len('发明人'.split(';'))  # 每个发明人的贡献"

❌ **错误示例**：
- 错误1：年份错误 - "2024 - pd.to_datetime('授权日').dt.year"  // 应该是2026
- 错误2：V13公式倒置 - "1 / 发明人.split(';').len()"  // 这是倒数，应该是发明人数的倒数
- 错误3：控制变量与自变量重复 - independent_var和control_vars不能包含相同变量
- 错误4：类别变量用ASCII编码 - "'IPC主分类号'.str[0].apply(lambda x: ord(x))"  // 不要用ord()，会暗示大小关系

**⚠️ 变量计算的简化原则：**
- V22_tech_maturity（技术成熟度）→ 使用"专利年龄"（2026 - 授权年份）
- V09_tech_diversity（技术多样性）→ 
  * 如果只有单个IPC分类号，使用"IPC大类"（前1位字母）作为**类别变量**
  * ⚠️ 重要：IPC大类是类别变量，不要用ASCII编码（ord()）转换为数值
  * 正确做法：保持为字符串（'A', 'B', 'C'...），在回归时使用虚拟变量编码
  * 或者明确说明需要"pd.Categorical()"或"LabelEncoder()"处理
  * 注意：Shannon熵需要在整个数据集层面计算，不是单个专利的属性
- V16_tech_impact（技术影响力）→ 直接使用"被引用专利数量"
- V13_rd_efficiency（研发效率）→ 
  * 单个专利层面：1.0 / 发明人数量（每个发明人的贡献）
  * 申请人层面：专利总数 / 发明人总数（需要分组聚合）
- V04_international_collab（国际合作）→ 从"发明人"或"优先权国家/地区"判断是否有外国参与
- 避免需要复杂时间窗口或分组聚合的计算

**⚠️ 类别变量的处理原则：**
- IPC大类、申请人类型、技术领域等都是**类别变量**（Categorical）
- 不要用ord()、ASCII编码等方式转换为数值（会暗示错误的大小关系）
- 正确处理方式：
  * 方式1：保持为字符串，说明需要虚拟变量编码（推荐）
  * 方式2：使用pd.Categorical()
  * 方式3：明确说明需要LabelEncoder()，但要注意这仍然暗示顺序关系

**⚠️ 控制变量选择原则：**
- 控制变量不能与自变量重复
- 控制变量的计算公式不能与自变量或中介变量相同
- **控制变量不能与自变量高度相关（避免多重共线性）**
  * 例如：如果自变量是"专利年龄"（2026 - 授权年份），控制变量不能是"授权年份"
  * 原因：两者线性相关（r ≈ -1.0），会导致回归系数不稳定
  * 检查方法：如果两个变量来自同一列，且公式相关，则不能同时使用
- 常用控制变量：申请人规模、技术领域（IPC大类）、专利类型
- 中介分析中：控制与中介变量和因变量相关的其他因素

**⚠️⚠️⚠️ 中介分析的硬性约束（必须遵守）⚠️⚠️⚠️**
1. **三个变量必须不同**：independent_var、mediator_var、dependent_var 必须是三个不同的变量ID
2. **禁止自己中介自己**：不能出现 X→X→Y 或 X→Y→Y 的情况
3. **控制变量不能是中介变量**：在中介分析中，control_vars不能包含mediator_var
   - 原因：控制中介变量会消除中介效应，导致分析失效
   - 例如：如果mediator_var是"V09"，control_vars不能包含"V09"
4. **控制变量不能与自变量高度相关**：避免多重共线性
   - 例如：如果independent_var是"V22"（专利年龄），control_vars不能是"授权年份"
5. **数据可得性检查**：如果某个变量无法从可用列计算，不要强行设计中介分析
6. **缺少变量时的处理**：
   - 如果缺少自变量X：跳过该假设，不设计任务
   - 如果缺少中介变量M：改为直接效应检验（X→Y）
   - 如果缺少因变量Y：跳过该假设
7. **只验证核心推荐的第一个假设**：如果有多个假设，优先验证排名第一的核心推荐假设

**错误示例（绝对禁止）：**
- ❌ independent_var: "V13", mediator_var: "V13", dependent_var: "V16"  // 自己中介自己
- ❌ mediator_var: "V09", control_vars: ["V09"]  // 控制变量包含中介变量
- ❌ independent_var: "V22", control_vars: ["V22"]  // 控制变量与自变量相同
- ❌ independent_var: "V22", control_vars: ["patent_age"]，且两者公式都是 "2026 - 授权年份"  // 计算公式相同

**正确示例：**
- ✓ independent_var: "V22", mediator_var: "V09", dependent_var: "V16", control_vars: []  // 简单中介，无控制变量
- ✓ independent_var: "V22", mediator_var: "V09", dependent_var: "V16", control_vars: ["applicant_type"]  // 控制变量不在中介路径上
- ✓ 如果缺少V01数据，直接检验 V13→V16，不要构造 V13→V13→V16

---

## 输出格式（严格 JSON）

{{
  "thinking_trace": {{
    "data_audit": "可用列名：'序号'（ID）、'名称'（标题）、'摘要'（文本）、'授权日'（时间）、'IPC分类号'（技术分类）、'被引用专利数量'（影响力）",
    "hypothesis_analysis": "假设H1需要计算V09（技术多样性，从IPC分类号）和V16（技术影响力，从被引用专利数量）",
    "algorithm_selection": "使用Shannon熵计算技术多样性，使用线性回归验证假设",
    "conclusion_design": "Task 1计算变量；Task 2验证假设，输出回归结果JSON"
  }},
  "research_objective": "研究目标的简洁描述",
  "expected_outcomes": ["预期成果1（结论性）", "预期成果2（结论性）"],
  "task_graph": [
    {{
      "task_id": "task_1",
      "task_type": "variable_calculation",
      "question": "如何计算研究假设中的变量？",
      "input_variables": [],
      "output_variables": ["variables_df"],
      "dependencies": [],
      "description": "计算假设验证所需的变量",
      "implementation_config": {{
        "data_source": "data/clean_patents1_with_topics_filled.xlsx",
        "sheet_name": "clear",
        "columns_to_load": ["序号", "IPC分类号", "被引用专利数量"],
        "variables_to_calculate": [
          {{
            "variable_id": "V09_tech_diversity",
            "variable_name": "技术多样性",
            "calculation_method": "Shannon熵",
            "source_column": "IPC分类号",
            "formula": "H = -Σ(pi * log(pi))"
          }},
          {{
            "variable_id": "V16_tech_impact",
            "variable_name": "技术影响力",
            "calculation_method": "直接使用",
            "source_column": "被引用专利数量"
          }}
        ],
        "output_format": "csv",
        "output_file": "outputs/task_1_variables.csv",
        "output_columns": ["序号", "V09_tech_diversity", "V16_tech_impact"]
      }}
    }},
    {{
      "task_id": "task_2",
      "task_type": "hypothesis_test",
      "question": "假设H1（技术多样性→技术影响力）是否成立？",
      "input_variables": ["variables_df"],
      "output_variables": ["hypothesis_test_result"],
      "dependencies": ["task_1"],
      "description": "使用回归分析验证假设",
      "implementation_config": {{
        "algorithm": "Linear Regression",
        "input_file": "outputs/task_1_variables.csv",
        "independent_var": "V09_tech_diversity",
        "dependent_var": "V16_tech_impact",
        "control_vars": ["patent_age"],
        "output_format": "json",
        "output_file": "outputs/task_2_hypothesis_test.json",
        "output_content": {{
          "hypothesis_id": "H1",
          "hypothesis_statement": "技术多样性对技术影响力有正向影响",
          "test_method": "Linear Regression",
          "results": {{
            "coefficient": "回归系数",
            "p_value": "显著性",
            "r_squared": "拟合优度",
            "conclusion": "假设是否成立"
          }},
          "key_findings": "关键发现"
        }}
      }}
    }}
  ]
}}

**生成前检查清单:**
- [ ] 所有列名都在【实际列名】中
- [ ] 数据源路径为 data/clean_patents1_with_topics_filled.xlsx
- [ ] 变量计算方法简单可行（避免复杂分组聚合）
- [ ] 只验证核心推荐的第一个假设（不要验证所有假设）
- [ ] 中介分析的三个变量（X、M、Y）必须不同
- [ ] 控制变量不能是中介变量本身
- [ ] 控制变量不与自变量的计算公式相同或高度相关
- [ ] 类别变量（如IPC大类）不使用ord()或ASCII编码
- [ ] 年份使用2026（当前年份）
- [ ] V13研发效率公式正确（发明人数的倒数）
- [ ] 每个任务都有明确的 question
- [ ] 每个任务的输出都是结论性的（JSON 汇总 > CSV 表格）
- [ ] output_content 描述了输出的结构和内容

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
        
        prompt = f"""你是专利分析领域的资深研究员和数据科学家。请根据用户的研究目标，设计一个**基于 DAG（有向无环图）的分析方案**。

**用户研究目标:**
{user_goal}

**当前数据可用列名及语义:**
{columns_semantic}

**⚠️⚠️⚠️ 关键约束（必须遵守）⚠️⚠️⚠️**
1. **列名必须完全匹配**：只能使用上面【实际列名】中列出的列名，一个字都不能改
2. **禁止自创列名**：不要使用任何未在上面列出的列名（如 ID, Title, Abstract, Applicant, Grant Date 等）
3. **直接复制列名**：从【实际列名】中直接复制粘贴，确保完全一致（包括括号、空格等）
4. **结论导向输出**：每个任务必须输出结论性数据（汇总、统计、发现），而不是中间特征或原始数据

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
- **数据审计**: 列出可用的列名（从上面【实际列名】中复制），说明每个列的用途
- **算法选择**: 根据用户目标，选择最合适的算法
- **结论设计**: 每个任务应该回答什么问题？输出什么结论？

### 2. DAG 结构（Task Graph）
将研究目标分解为 2-4 个任务节点，每个节点必须：
- 回答一个明确的问题
- 输出结论性数据（JSON 汇总 > CSV 表格 > 原始数据）
- 包含关键发现（key_findings）

任务节点结构：
- `task_id`: 唯一标识（如 "task_1", "task_2"）
- `task_type`: 任务类型（如 "data_summary", "topic_analysis", "trend_analysis", "hotspot_identification"）
- `question`: 该任务要回答的问题（如 "有哪些技术主题？"）
- `input_variables`: 输入变量列表（如 ["df_raw"]）
- `output_variables`: 输出变量列表（如 ["topics_summary", "lda_model"]）
- `dependencies`: 依赖的前序任务 ID 列表（如 ["task_1"]）
- `description`: 任务描述
- `implementation_config`: 实现配置

### 3. 输出格式要求

**优先级（从高到低）:**
1. **JSON 汇总文件**（最优）
   - 包含结论、统计、关键发现
   - 适合报告智能体直接使用
   - 示例：`topics_summary.json`, `trend_analysis.json`

2. **CSV 汇总表格**（次优）
   - 汇总级别的数据（如 8 个主题，不是 1000 条专利）
   - 包含统计指标
   - 示例：`topic_statistics.csv` (8 rows)

3. **原始数据文件**（仅作为备份）
   - 保存用于追溯，但不是主要输出
   - 示例：`df_raw.csv` (1000 rows)

### 4. 结论性输出示例

**❌ 不好的输出（中间特征）:**
```
outputs/task_2_df_with_topics.csv (1000 rows × 10 cols)
序号,topic_0,topic_1,topic_2,...
1,0.05,0.10,0.60,...
```

**✓ 好的输出（结论性数据）:**
```
outputs/task_2_topics_summary.json
{{
  "n_topics": 8,
  "topics": [
    {{
      "topic_id": 0,
      "label": "数据加密技术",
      "top_keywords": ["加密", "密钥", "算法"],
      "patent_count": 234,
      "percentage": 23.4,
      "key_finding": "数据加密是最主要的技术方向"
    }}
  ]
}}
```

---

## 输出格式（严格 JSON）

{{
  "thinking_trace": {{
    "data_audit": "可用列名：'序号'（ID）、'名称'（标题）、'摘要'（文本）、'授权日'（时间）",
    "algorithm_selection": "选择 LDA 进行主题建模，使用 '摘要' 列",
    "conclusion_design": "Task 2 回答'有哪些技术主题'，输出主题汇总 JSON；Task 3 回答'哪些主题在上升'，输出趋势分析 JSON"
  }},
  "research_objective": "研究目标的简洁描述",
  "expected_outcomes": ["预期成果1（结论性）", "预期成果2（结论性）"],
  "task_graph": [
    {{
      "task_id": "task_1",
      "task_type": "data_summary",
      "question": "数据集的基本情况如何？",
      "input_variables": [],
      "output_variables": ["data_summary"],
      "dependencies": [],
      "description": "生成数据集基本统计摘要",
      "implementation_config": {{
        "data_source": "data/clean_patents1_with_topics_filled.xlsx",
        "sheet_name": "clear",
        "columns_to_load": ["序号", "名称", "摘要", "申请(专利权)人", "授权日"],
        "output_format": "json",
        "output_file": "outputs/task_1_data_summary.json",
        "output_content": {{
          "total_patents": "专利总数",
          "date_range": "时间范围",
          "top_applicants": "前 10 申请人及专利数",
          "yearly_distribution": "年度分布统计"
        }},
        "backup_file": "outputs/task_1_df_raw.csv"
      }}
    }},
    {{
      "task_id": "task_2",
      "task_type": "topic_analysis",
      "question": "有哪些主要的技术主题？",
      "input_variables": ["data_summary"],
      "output_variables": ["topics_summary", "lda_model"],
      "dependencies": ["task_1"],
      "description": "使用 LDA 识别技术主题并生成汇总",
      "implementation_config": {{
        "algorithm": "LDA",
        "input_file": "outputs/task_1_df_raw.csv",
        "text_column": "摘要",
        "parameters": {{
          "n_topics": 8,
          "max_iter": 200
        }},
        "output_format": "json",
        "output_file": "outputs/task_2_topics_summary.json",
        "output_content": {{
          "n_topics": "主题数量",
          "topics": [
            {{
              "topic_id": "主题 ID",
              "label": "主题标签（自动生成）",
              "top_keywords": "前 10 关键词",
              "patent_count": "该主题的专利数",
              "percentage": "占比",
              "representative_patents": "代表性专利（3-5 个）",
              "key_finding": "关键发现"
            }}
          ]
        }},
        "model_file": "outputs/task_2_lda_model.pkl"
      }}
    }},
    {{
      "task_id": "task_3",
      "task_type": "trend_analysis",
      "question": "哪些技术主题在上升/下降？",
      "input_variables": ["topics_summary"],
      "output_variables": ["trend_analysis"],
      "dependencies": ["task_2"],
      "description": "分析各主题的时间趋势",
      "implementation_config": {{
        "input_file": "outputs/task_2_lda_model.pkl",
        "raw_data_file": "outputs/task_1_df_raw.csv",
        "time_column": "授权日",
        "output_format": "json",
        "output_file": "outputs/task_3_trend_analysis.json",
        "output_content": {{
          "analysis_period": "分析时间段",
          "hot_topics": [
            {{
              "topic_id": "主题 ID",
              "topic_label": "主题标签",
              "trend": "上升/下降/稳定",
              "growth_rate": "增长率",
              "key_finding": "关键发现（如：2021年起专利申请量激增）",
              "yearly_data": "年度数据（用于绘图）"
            }}
          ],
          "declining_topics": "下降的主题",
          "stable_topics": "稳定的主题"
        }}
      }}
    }}
  ]
}}

**生成前检查清单:**
- [ ] 所有列名都在【实际列名】中
- [ ] 每个任务都有明确的 question
- [ ] 每个任务的输出都是结论性的（JSON 汇总 > CSV 表格）
- [ ] output_content 描述了输出的结构和内容

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
        available_vars = set()  # 当前可用的变量集合
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
- **文件路径固定**：主数据路径固定为 `data/clean_patents1_with_topics_filled.xlsx`，sheet 名为 `clear`。
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
          "main_data": "data/clean_patents1_with_topics_filled.xlsx",
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
          "main_data": "data/clean_patents1_with_topics_filled.xlsx",
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
