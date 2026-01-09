"""
Strategist Agent - 战略智能体
负责从知识图谱检索最佳实践并生成研究方案

基于 core/strategist_graph.py V4.0 的优化版本
"""

import json
from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent


class StrategistAgent(BaseAgent):
    """
    战略智能体（大脑）
    
    职责：
    1. 理解用户研究目标
    2. 从 Neo4j 知识图谱检索相关方法论
    3. 生成详细的研究战略蓝图
    
    核心优化（来自 V4.0）：
    - 意图转译：LLM 自动提取检索关键词
    - 完整逻辑链检索：返回论文的完整分析流程
    - 质量检查：自动评价方案质量
    """
    
    def __init__(self, llm_client, neo4j_connector=None, logger=None):
        """
        初始化 Strategist
        
        Args:
            llm_client: LLM 客户端
            neo4j_connector: Neo4j 连接器（可选）
            logger: 日志记录器
        """
        super().__init__("Strategist", llm_client, logger)
        self.neo4j = neo4j_connector
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户目标，生成战略蓝图
        
        Args:
            input_data: {
                "user_goal": str,
                "available_columns": List[str] (可选，真实数据的列名)
            }
            
        Returns:
            {"blueprint": dict, "graph_context": str}
        """
        user_goal = input_data.get('user_goal', '')
        available_columns = input_data.get('available_columns', None)
        
        self.log(f"开始处理用户目标: {user_goal}")
        if available_columns:
            self.log(f"可用列名: {available_columns}")
        
        # 步骤 1: 意图转译 - 提取检索关键词
        keywords = self._extract_keywords(user_goal)
        self.log(f"提取的关键词: {keywords}")
        
        # 步骤 2: 知识图谱检索
        graph_context = ""
        retrieved_cases = []
        if self.neo4j:
            graph_context, retrieved_cases = self._retrieve_from_graph(keywords)
            self.log(f"检索到 {len(retrieved_cases)} 个相关案例")
        else:
            self.log("未连接 Neo4j，跳过知识图谱检索", "warning")
        
        # 步骤 3: 生成研究方案（注入真实列名）
        blueprint = self._generate_blueprint(user_goal, graph_context, available_columns=available_columns)
        
        # 步骤 4: 质量检查（可选）
        if not self._check_quality(blueprint):
            self.log("方案质量不足，重新生成", "warning")
            blueprint = self._generate_blueprint(user_goal, graph_context, retry=True, available_columns=available_columns)
        
        self.log("战略蓝图生成完成")
        
        return {
            'blueprint': blueprint,
            'graph_context': graph_context
        }
    
    def _extract_keywords(self, user_goal: str) -> List[str]:
        """
        意图转译：从用户目标中提取检索关键词
        
        改进版：同时提取意图和相关的技术/方法关键词
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
    
    def _retrieve_from_graph(self, keywords: List[str]) -> tuple[str, List[Dict]]:
        """
        从知识图谱检索相关案例
        
        使用 V4.1 的完整逻辑链检索策略
        
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
    
    def _generate_blueprint(self, user_goal: str, graph_context: str, retry: bool = False, available_columns: List[str] = None) -> Dict[str, Any]:
        """
        生成研究战略蓝图
        
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
        质量检查：评估生成的方案是否合格
        
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
