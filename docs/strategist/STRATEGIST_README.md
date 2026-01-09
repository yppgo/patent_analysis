# Patent-DeepScientist - Idea 提出模块

基于 LangGraph 框架实现的智能研究方案生成系统。

## 📋 功能概述

该模块实现了一个双节点的 LangGraph 工作流：

1. **检索者 (Librarian)**: 从 Neo4j 知识图谱中检索相关上下文
   - 查询最佳实践案例
   - 识别研究空白
   
2. **生成者 (Strategist)**: 基于检索到的上下文生成研究方案
   - 使用 Qwen-Max 大模型
   - 输出结构化的 JSON 研究计划

## 🏗️ 系统架构

```
用户输入目标
    ↓
[检索者节点]
    ├─ 查询最佳实践 (Cypher)
    ├─ 查询研究空白 (Cypher)
    └─ 格式化上下文
    ↓
[生成者节点]
    ├─ 构建 Prompt
    ├─ 调用 Qwen LLM
    └─ 解析 JSON 结果
    ↓
输出研究方案
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

确保 `.env` 文件包含：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 配置 Neo4j

确保 `neo4j_config.py` 中的配置正确：

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
}
```

### 4. 运行主程序

```bash
python strategist_graph.py
```

### 5. 运行测试

```bash
python test_strategist.py
```

## 📊 输出格式

生成的研究方案为 JSON 格式：

```json
{
  "research_question": "明确的研究问题",
  "data_sources": ["数据字段1", "数据字段2"],
  "methods": ["方法1", "方法2"],
  "expected_conclusions": ["预期结论类型1", "预期结论类型2"],
  "innovation_points": ["创新点1", "创新点2"],
  "rationale": "方案设计理由"
}
```

## 🔍 核心查询逻辑

### 查询最佳实践

```cypher
MATCH (p:Paper)-[:CONDUCTS]->(ae:AnalysisEvent)
WHERE ae.objective CONTAINS $keyword OR p.title CONTAINS $keyword
OPTIONAL MATCH (ae)-[:EXECUTES]->(m:Method)
OPTIONAL MATCH (ae)-[:YIELDS]->(c:Conclusion)
OPTIONAL MATCH (d:Data)-[:FEEDS_INTO]->(ae)
RETURN 
    p.title AS paper_title,
    ae.objective AS objective,
    m.name AS method,
    c.type AS conclusion_type,
    collect(DISTINCT d.name) AS data_fields
ORDER BY p.year DESC
LIMIT 3
```

### 查询研究空白

```cypher
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
    freq AS usage_frequency,
    m.name AS unused_method
ORDER BY freq DESC
LIMIT 3
```

## 🛠️ 自定义扩展

### 添加新的检索策略

在 `GraphTool` 类中添加新方法：

```python
def retrieve_custom_pattern(self, params):
    query = """
    // 你的自定义 Cypher 查询
    """
    return self.run_cypher(query, params)
```

### 添加反思节点（未来扩展）

```python
def critique_node(state: AgentState) -> Dict[str, Any]:
    """评估生成的方案并提供改进建议"""
    # 实现自我反思逻辑
    pass

# 在工作流中添加循环
workflow.add_node("critic", critique_node)
workflow.add_edge("strategist", "critic")
workflow.add_conditional_edges(
    "critic",
    lambda x: "regenerate" if x["critique_score"] < 0.7 else "end",
    {
        "regenerate": "strategist",
        "end": END
    }
)
```

## 📝 使用示例

### 基本使用

```python
from strategist_graph import build_graph

# 构建工作流
app = build_graph()

# 执行
result = app.invoke({
    "user_goal": "分析固态电池的技术空白",
    "graph_context": "",
    "generated_idea": {},
    "critique": ""
})

# 获取结果
print(result['generated_idea'])
```

### 批量处理

```python
goals = [
    "研究人工智能在专利分析中的应用",
    "探索区块链技术的专利布局策略"
]

app = build_graph()

for goal in goals:
    result = app.invoke({
        "user_goal": goal,
        "graph_context": "",
        "generated_idea": {},
        "critique": ""
    })
    # 处理结果...
```

## 🐛 故障排除

### 问题 1: Neo4j 连接失败

**解决方案**: 
- 检查 Neo4j 服务是否运行
- 验证 `neo4j_config.py` 中的连接信息
- 测试连接: `python test_neo4j_connection.py`

### 问题 2: API Key 错误

**解决方案**:
- 确认 `.env` 文件中的 `DASHSCOPE_API_KEY` 正确
- 测试 API: `python test_api_key.py`

### 问题 3: JSON 解析失败

**解决方案**:
- 检查 LLM 返回的原始内容
- 调整 Prompt 使其更明确要求 JSON 格式
- 增加错误处理逻辑

## 📚 依赖说明

- **langgraph**: 工作流编排框架
- **langchain-openai**: LLM 接口
- **neo4j**: 图数据库驱动
- **python-dotenv**: 环境变量管理

## 🔄 版本历史

- **v1.0** (2024-12): 初始版本
  - 实现双节点工作流
  - 支持最佳实践和研究空白检索
  - 集成 Qwen-Max 生成方案

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**License**: MIT
