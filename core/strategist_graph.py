"""
Patent-DeepScientist 系统 - Idea 提出模块 V4.0
使用 LangGraph 框架实现知识检索和研究方案生成

✨ V4.0 核心优化 (2025-12-05):
1. 意图转译 (Intent Translation): LLM 自动提取检索关键词，提高命中率
2. 详细配置提取: Cypher 查询返回 config 和 metrics，方案更具可执行性
3. 跨域迁移 Prompt: 强化类比推理，实现真正的"举一反三"
4. 质量检查节点: 自动评价方案质量，不合格则重新生成

优化建议来源: geimin
"""

import os
import json
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

from neo4j_config import NEO4J_CONFIG

# 加载环境变量
load_dotenv()


# ============================================================================
# 1. 定义状态 (State)
# ============================================================================

class AgentState(TypedDict):
    """Agent 工作流状态"""
    user_goal: str              # 用户输入的研究目标
    graph_context: str          # 从知识图谱检索到的上下文
    generated_idea: dict        # 生成的研究方案 (JSON)
    critique: str               # 自我反思/评价
    quality_passed: bool        # ✨ 质量检查是否通过
    iteration_count: int        # ✨ 迭代次数（防止无限循环）


# ============================================================================
# 2. Neo4j 知识图谱工具
# ============================================================================

class GraphTool:
    """Neo4j 知识图谱查询工具"""
    
    def __init__(self):
        """初始化 Neo4j 驱动"""
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"],
            auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
        )
        print("✓ Neo4j 连接已建立")
    
    def close(self):
        """关闭连接"""
        self.driver.close()
    
    def run_cypher(self, query: str, parameters: dict = None) -> List[Dict]:
        """
        执行 Cypher 查询
        
        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def retrieve_best_practices(self, keyword: str, limit: int = 3) -> List[Dict]:
        """
        检索最佳实践案例
        
        ✨ V4.1 优化：全链检索 (Full Logic Chain Retrieval)
        一旦某篇论文的某个步骤命中了关键词，就返回该论文的【完整分析逻辑链】。
        这样智能体才能学到 Step 1 -> Step 2 -> Step 3 的完整流程。
        
        优化建议来源: geimin
        """
        query = """
        // 1. 锚定：先找到包含关键词的那个具体步骤，锁定对应的论文
        MATCH (p:Paper)-[:CONDUCTS]->(target_ae:AnalysisEvent)
        WHERE target_ae.objective CONTAINS $keyword 
           OR p.title CONTAINS $keyword
           OR target_ae.method_name CONTAINS $keyword
        
        // 2. 扩展：基于找到的论文，把它所有的步骤都找出来
        WITH DISTINCT p
        MATCH (p)-[:CONDUCTS]->(all_ae:AnalysisEvent)
        
        // 3. 关联：获取每个步骤的详细信息（方法、数据、结论）
        OPTIONAL MATCH (all_ae)-[:EXECUTES]->(m:Method)
        OPTIONAL MATCH (all_ae)-[:YIELDS]->(c:Conclusion)
        OPTIONAL MATCH (d:Data)-[:FEEDS_INTO]->(all_ae)
        
        // 4. 聚合：按 step_id 排序，重组为完整的 Story
        WITH p, all_ae, m, c, collect(DISTINCT d.name) AS data_fields
        ORDER BY all_ae.step_id ASC
        
        // 5. 返回结构化数据：一篇论文一行，包含一个 steps 数组
        RETURN 
            p.title AS paper_title,
            p.year AS paper_year,
            collect({
                step_id: all_ae.step_id,
                objective: all_ae.objective,
                method_name: all_ae.method_name,
                method: m.name,
                config: all_ae.config,
                metrics: all_ae.metrics,
                inputs: data_fields,
                conclusion_type: c.type,
                conclusion: c.content
            }) AS full_logic_chain
        ORDER BY p.year DESC
        LIMIT $limit
        """
        
        return self.run_cypher(query, {"keyword": keyword, "limit": limit})
    
    def retrieve_research_gaps(self, limit: int = 3) -> List[Dict]:
        """
        检索研究空白
        
        查询策略：找到常用的数据字段，但尚未与某些方法组合使用的情况
        """
        query = """
        // 找到使用频率高的数据字段
        MATCH (d:Data)-[:FEEDS_INTO]->(ae:AnalysisEvent)
        WITH d, count(ae) as freq
        WHERE freq >= 3
        
        // 找到所有方法
        MATCH (m:Method)
        
        // 检查该数据字段是否与该方法组合过
        WHERE NOT EXISTS {
            MATCH (d)-[:FEEDS_INTO]->(ae2:AnalysisEvent)-[:EXECUTES]->(m)
        }
        
        RETURN 
            d.name AS data_field,
            d.description AS data_description,
            freq AS usage_frequency,
            m.name AS unused_method,
            m.description AS method_description
        ORDER BY freq DESC
        LIMIT $limit
        """
        
        return self.run_cypher(query, {"limit": limit})
    
    def retrieve_context(self, goal: str) -> str:
        """
        根据用户目标检索知识图谱上下文
        
        Args:
            goal: 用户研究目标
            
        Returns:
            格式化的上下文字符串
        """
        # 提取关键词（简单实现：取第一个实体词）
        keyword = self._extract_keyword(goal)
        
        print(f"  🔍 检索关键词: {keyword}")
        
        # 检索最佳实践
        best_practices = self.retrieve_best_practices(keyword)
        
        # 检索研究空白
        research_gaps = self.retrieve_research_gaps()
        
        # 格式化上下文
        context = self._format_context(best_practices, research_gaps)
        
        return context
    
    def _extract_keyword(self, goal: str) -> str:
        """从用户目标中提取关键词（简化版）"""
        # 简单实现：移除常见词汇
        stop_words = ["分析", "研究", "的", "技术", "空白", "方法", "如何"]
        words = goal.split()
        for word in words:
            if word not in stop_words and len(word) > 1:
                return word
        return goal[:10]  # 如果没找到，返回前10个字符
    
    def _format_context(self, best_practices: List[Dict], research_gaps: List[Dict]) -> str:
        """
        格式化检索结果为可读文本
        ✨ V4.1 增强：展示完整的逻辑链 (Full Logic Chain)
        """
        context_parts = []
        
        # 格式化最佳实践
        context_parts.append("=== 📚 相关最佳实践 (完整逻辑链) ===\n")
        if best_practices:
            for i, practice in enumerate(best_practices, 1):
                context_parts.append(f"{i}. 论文: {practice.get('paper_title', 'N/A')} ({practice.get('paper_year', 'N/A')})")
                
                # ✨ V4.1 新增：展示完整的步骤链
                logic_chain = practice.get('full_logic_chain', [])
                if logic_chain:
                    context_parts.append(f"   完整分析流程 ({len(logic_chain)} 个步骤):")
                    for step in logic_chain:
                        step_id = step.get('step_id', '?')
                        context_parts.append(f"\n   【Step {step_id}】")
                        context_parts.append(f"     目标: {step.get('objective', 'N/A')}")
                        context_parts.append(f"     方法: {step.get('method', 'N/A')}")
                        
                        # 显示配置和指标
                        if step.get('config'):
                            context_parts.append(f"     配置: {step.get('config')}")
                        if step.get('metrics'):
                            context_parts.append(f"     指标: {step.get('metrics')}")
                        
                        # 显示输入数据
                        inputs = step.get('inputs', [])
                        if inputs:
                            context_parts.append(f"     输入数据: {', '.join(inputs)}")
                        
                        # 显示结论
                        if step.get('conclusion'):
                            conclusion_preview = str(step.get('conclusion', ''))[:100]
                            context_parts.append(f"     结论: {conclusion_preview}...")
                else:
                    # 兼容旧格式（如果没有 full_logic_chain）
                    context_parts.append(f"   目标: {practice.get('objective', 'N/A')}")
                    context_parts.append(f"   方法: {practice.get('method', 'N/A')}")
                
                context_parts.append("")
        else:
            context_parts.append("  (未找到相关案例)\n")
        
        # 格式化研究空白
        context_parts.append("=== 🔬 潜在研究空白 ===\n")
        if research_gaps:
            for i, gap in enumerate(research_gaps, 1):
                context_parts.append(f"{i}. 数据字段: {gap.get('data_field', 'N/A')} (使用频率: {gap.get('usage_frequency', 0)})")
                context_parts.append(f"   未使用的方法: {gap.get('unused_method', 'N/A')}")
                context_parts.append(f"   方法描述: {gap.get('method_description', 'N/A')}")
                context_parts.append("")
        else:
            context_parts.append("  (未找到明显空白)\n")
        
        return "\n".join(context_parts)


# ============================================================================
# 3. LLM 配置
# ============================================================================

def get_llm() -> ChatOpenAI:
    """获取配置好的 Qwen LLM"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY")
    
    return ChatOpenAI(
        model="qwen-max",
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        openai_api_key=api_key,
        temperature=0.7,
    )


# ============================================================================
# 4. 定义节点 (Nodes)
# ============================================================================

# 全局 GraphTool 实例
graph_tool = None

def initialize_graph_tool():
    """初始化全局 GraphTool"""
    global graph_tool
    if graph_tool is None:
        graph_tool = GraphTool()


def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: 知识检索节点 (Librarian)
    
    ✨ V4.0 增强：增加意图转译 (Intent Translation)
    从 Neo4j 知识图谱中检索相关上下文
    """
    print("\n" + "="*60)
    print("📚 [检索者] 正在分析用户意图并检索图谱...")
    print("="*60)
    
    initialize_graph_tool()
    
    user_goal = state["user_goal"]
    print(f"  📝 用户目标: {user_goal}")
    
    # ✨ 步骤 1: 意图转译 - 用 LLM 提取检索关键词
    llm = get_llm()
    trans_prompt = f"""你是专利分析领域的专家。用户想进行专利分析，目标是："{user_goal}"。

请提取 2-3 个核心的"分析意图关键词"，用于在知识图谱中检索相似的分析任务。
这些关键词应该是方法论术语、分析目标或技术领域。

示例：
- 用户："分析固态电池技术空白" -> 关键词：技术空白, 识别, 聚类
- 用户："竞争对手分析" -> 关键词：竞争对手, 市场份额, HHI
- 用户："技术演化路径" -> 关键词：技术演化, 路径分析, 引用网络

只返回关键词，用逗号分隔，不要其他解释。"""

    keywords_response = llm.invoke(trans_prompt)
    keywords_str = keywords_response.content.strip()
    keywords = [k.strip() for k in keywords_str.split(",")]
    
    print(f"  🧠 意图关键词: {keywords}")
    
    # ✨ 步骤 2: 多关键词检索 - 循环检索所有关键词
    all_practices = []
    for kw in keywords:
        print(f"     🔍 检索关键词: {kw}")
        res = graph_tool.retrieve_best_practices(kw, limit=2)
        all_practices.extend(res)
    
    # 去重（基于论文标题）
    unique_practices = {p['paper_title']: p for p in all_practices}.values()
    unique_practices = list(unique_practices)
    
    print(f"  ✓ 检索到 {len(unique_practices)} 个独特案例")
    
    # ✨ 步骤 3: 检索研究空白
    gaps = graph_tool.retrieve_research_gaps()
    
    # ✨ 步骤 4: 格式化上下文
    context = graph_tool._format_context(unique_practices, gaps)
    
    print(f"  ✓ 检索完成，构建了 {len(context)} 字符的上下文")
    
    return {"graph_context": context}


def generate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: 方案生成节点 (Strategist)
    
    ✨ V4.0 增强：强化跨域迁移 (Transfer Learning) 能力
    基于检索到的上下文，生成研究方案
    """
    print("\n" + "="*60)
    print("💡 [战略家] 正在生成研究方案...")
    print("="*60)
    
    user_goal = state["user_goal"]
    graph_context = state["graph_context"]
    
    # ✨ 构建跨域迁移 Prompt
    prompt = f"""你是一位精通"跨域创新"的专利分析战略家。你的核心能力是**类比推理**和**方法论迁移**。

**用户目标:** 
{user_goal}

**图谱记忆 (历史上的成功案例):**
{graph_context}

**任务:** 
请模仿图谱中的成功方法论（Best Practices），为用户的目标领域设计一个详细的研究方案。

**🔑 关键思考逻辑:**
1. **观察模式**: 图谱中别人是如何解决类似问题的？
   - 例如：别人用 TCT 算技术周期，用 HHI 算市场垄断，用聚类识别空白
2. **跨域迁移**: 将这些方法**移植**到用户的问题上
   - 即使图谱中没有关于"{user_goal}"的直接案例，你也要从其他领域（如通信、生物、能源）迁移方法
3. **具体化**: 必须提供**可执行的配置**和**可测量的指标**
   - 参考图谱中的 config 和 metrics 字段
   - 例如：config: {{"library": "Gensim", "params": "min_count=5"}}, metrics: "TCT < 5年"

**⚠️ 重要约束:**
- 即使用户的目标领域在图谱中没有直接出现，你也必须进行类比
- 必须包含具体的执行配置（Library, Params）和预期指标（Metrics）
- 方案必须是可操作的，不能只有抽象描述

**输出格式 (严格 JSON):**
{{
  "hypothesis": "核心研究假设",
  "reference_case": "参考了图谱中的哪篇论文/哪个方法",
  "method_plan": {{
    "method_name": "具体方法名称",
    "config": {{
      "library": "使用的工具库（如 Gensim, NetworkX, Scikit-learn）",
      "params": "关键参数配置"
    }},
    "target_metric": "预期指标（如 TCT < 5年, HHI > 0.6, 聚类数 = 5-8）"
  }},
  "data_sources": ["数据字段1", "数据字段2"],
  "reasoning": "为什么这个旧方法适用于这个新问题？（类比推理过程）",
  "innovation_points": ["创新点1", "创新点2"]
}}

请直接输出 JSON，不要包含任何其他文字。"""

    # 调用 LLM
    llm = get_llm()
    response = llm.invoke(prompt)
    
    # 解析 JSON
    try:
        # 提取 JSON 内容（处理可能的 markdown 代码块）
        content = response.content.strip()
        if content.startswith("```"):
            # 移除 markdown 代码块标记
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        idea_json = json.loads(content)
        print("  ✓ 方案生成成功")
        
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON 解析失败: {e}")
        print(f"  原始响应: {response.content[:200]}...")
        idea_json = {
            "error": "JSON 解析失败",
            "raw_response": response.content
        }
    
    return {"generated_idea": idea_json}


def critique_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: 反思/评价节点 (Critic)
    
    ✨ V4.0 新增：检查生成方案的质量
    确保方案包含具体的 config 和 metrics
    """
    print("\n" + "="*60)
    print("🔍 [评价者] 正在检查方案质量...")
    print("="*60)
    
    generated_idea = state["generated_idea"]
    iteration_count = state.get("iteration_count", 0)
    
    # 检查是否有错误
    if "error" in generated_idea:
        print("  ⚠️ 方案生成失败，跳过质量检查")
        return {
            "critique": "方案生成失败",
            "quality_passed": False,
            "iteration_count": iteration_count + 1
        }
    
    # 质量检查标准
    checks = {
        "有 method_plan": "method_plan" in generated_idea,
        "有 config": "method_plan" in generated_idea and "config" in generated_idea.get("method_plan", {}),
        "有 library": "method_plan" in generated_idea and "library" in generated_idea.get("method_plan", {}).get("config", {}),
        "有 target_metric": "method_plan" in generated_idea and "target_metric" in generated_idea.get("method_plan", {}),
        "有 reasoning": "reasoning" in generated_idea and len(generated_idea.get("reasoning", "")) > 20,
    }
    
    # 统计通过的检查项
    passed_checks = sum(checks.values())
    total_checks = len(checks)
    
    print(f"  📊 质量检查: {passed_checks}/{total_checks} 项通过")
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"     {status} {check_name}")
    
    # 判断是否通过
    quality_passed = passed_checks >= 4  # 至少通过 4/5 项
    
    if quality_passed:
        critique = f"质量检查通过 ({passed_checks}/{total_checks})"
        print(f"  ✅ {critique}")
    else:
        critique = f"质量不足 ({passed_checks}/{total_checks})，缺少具体配置或指标"
        print(f"  ⚠️ {critique}")
    
    return {
        "critique": critique,
        "quality_passed": quality_passed,
        "iteration_count": iteration_count + 1
    }


def should_regenerate(state: AgentState) -> str:
    """
    条件边：决定是否需要重新生成
    
    返回:
        - "end": 质量通过或达到最大迭代次数，结束流程
        - "regenerate": 质量不通过且未达到最大迭代次数，重新生成
    """
    quality_passed = state.get("quality_passed", False)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = 2  # 最多重试 2 次
    
    if quality_passed:
        print("  ✅ 质量检查通过，流程结束")
        return "end"
    elif iteration_count >= max_iterations:
        print(f"  ⚠️ 已达到最大迭代次数 ({max_iterations})，流程结束")
        return "end"
    else:
        print(f"  🔄 质量不足，重新生成 (第 {iteration_count + 1} 次尝试)")
        return "regenerate"


# ============================================================================
# 5. 构建 LangGraph 工作流
# ============================================================================

def build_graph() -> Any:
    """
    构建 LangGraph 工作流
    
    ✨ V4.0 增强流程: 
    START -> librarian -> strategist -> critic -> [判断] -> END 或 regenerate
    """
    print("\n🔧 构建 LangGraph 工作流...")
    
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("librarian", retrieve_node)      # 检索者
    workflow.add_node("strategist", generate_node)     # 战略家
    workflow.add_node("critic", critique_node)         # ✨ 评价者
    
    # 设置入口点
    workflow.set_entry_point("librarian")
    
    # 添加边
    workflow.add_edge("librarian", "strategist")
    workflow.add_edge("strategist", "critic")
    
    # ✨ 添加条件边：根据质量检查结果决定是否重新生成
    workflow.add_conditional_edges(
        "critic",
        should_regenerate,
        {
            "end": END,
            "regenerate": "strategist"  # 回到生成节点
        }
    )
    
    print("  ✓ 工作流构建完成")
    print("  流程: START -> librarian -> strategist -> critic -> [质量检查] -> END/regenerate")
    
    # 编译图
    return workflow.compile()


# ============================================================================
# 6. 主函数
# ============================================================================

def main():
    """主执行函数"""
    print("\n" + "="*60)
    print("🚀 Patent-DeepScientist - Idea 提出模块")
    print("="*60)
    
    # 构建工作流
    app = build_graph()
    
    # 测试用例
    test_goals = [
        "分析固态电池的技术空白",
        "研究人工智能在专利分析中的应用",
        "探索区块链技术的专利布局策略"
    ]
    
    # 执行第一个测试
    user_goal = test_goals[0]
    print(f"\n🎯 测试目标: {user_goal}")
    
    try:
        # 调用工作流
        result = app.invoke({
            "user_goal": user_goal,
            "graph_context": "",
            "generated_idea": {},
            "critique": "",
            "quality_passed": False,
            "iteration_count": 0
        })
        
        # 输出结果
        print("\n" + "="*60)
        print("📊 最终生成的研究方案:")
        print("="*60)
        print(json.dumps(result['generated_idea'], indent=2, ensure_ascii=False))
        
        # 保存结果
        output_file = "strategist_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        if graph_tool:
            graph_tool.close()
            print("\n✓ Neo4j 连接已关闭")
    
    print("\n" + "="*60)
    print("✅ 执行完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
