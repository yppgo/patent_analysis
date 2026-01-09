# 知识图谱入库工具使用说明

## 📋 概述

`ingest_graph.py` 是 Patent-DeepScientist 项目的生产级 Neo4j 知识图谱入库脚本，用于将结构化的科研论文分析数据导入 Neo4j 图数据库。

## 🏗️ 架构设计

### 节点分类

#### 1. 全局基础设施节点 (使用 MERGE - 全局唯一)
- **Intent** (意图): 分析的标准化意图，如"技术趋势分析"
- **Method** (方法): 使用的分析方法，如"专利分析"
- **Dataset** (数据集): 数据来源，如"USPTO"
- **Data** (输入数据): 输入字段，如"Title", "Abstract", "Claims"

#### 2. 动态实例节点 (使用 CREATE - 每次新建)
- **Paper** (论文): 论文元数据 (title, year)
- **AnalysisEvent** (分析事件): 每个分析步骤的实例
- **Conclusion** (结论): 分析得出的结论

### 关系链

```
Paper -[:CONTAINS_EVENT]-> AnalysisEvent
Paper -[:USES_DATASET]-> Dataset
AnalysisEvent -[:TARGETS_INTENT]-> Intent
AnalysisEvent -[:USES_METHOD]-> Method
AnalysisEvent -[:REQUIRES_INPUT]-> Data
AnalysisEvent -[:PRODUCED_CONCLUSION]-> Conclusion
Conclusion -[:ADDRESSES_INTENT]-> Intent
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install neo4j
```

### 2. 配置数据库连接

确保 `neo4j_config.py` 中的配置正确：

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
}
```

### 3. 运行批量入库

```bash
python ingest_graph.py
```

这将自动：
1. 初始化数据库 Schema (创建唯一性约束)
2. 批量导入 `batch_50_results` 文件夹中的所有 JSON 文件

## 📖 使用示例

### 示例 1: 批量入库

```python
from ingest_graph import KnowledgeGraphIngester
from neo4j_config import NEO4J_CONFIG

# 创建入库器
ingester = KnowledgeGraphIngester(
    NEO4J_CONFIG["uri"],
    NEO4J_CONFIG["user"],
    NEO4J_CONFIG["password"]
)

try:
    # 初始化 Schema
    ingester.initialize_schema()
    
    # 批量入库
    stats = ingester.batch_ingest_from_folder("batch_50_results")
    
    print(f"成功: {stats['success']}, 失败: {stats['failed']}")
    
finally:
    ingester.close()
```

### 示例 2: 单个文件入库

```python
import json
from ingest_graph import KnowledgeGraphIngester
from neo4j_config import NEO4J_CONFIG

# 创建入库器
ingester = KnowledgeGraphIngester(
    NEO4J_CONFIG["uri"],
    NEO4J_CONFIG["user"],
    NEO4J_CONFIG["password"]
)

try:
    # 初始化 Schema
    ingester.initialize_schema()
    
    # 读取 JSON 文件
    with open("your_file.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 入库
    success = ingester.ingest_paper(data)
    
finally:
    ingester.close()
```

## 🔍 数据格式要求

输入 JSON 必须包含以下结构：

```json
{
  "paper_meta": {
    "title": "论文标题",
    "year": "2016"
  },
  "dataset_config": {
    "source": "USPTO",
    "dataset_id": "D1",
    "query_condition": "...",
    "size": "...",
    "time_range": "...",
    "preprocessing": "...",
    "notes": "..."
  },
  "analysis_logic_chains": [
    {
      "step_id": 1,
      "objective": "分析目标",
      "standardized_intent": "技术趋势分析 (Trend Analysis)",
      "method_name": "专利分析 (Patent Analysis)",
      "inputs": ["标题 (Title)", "说明书 (Description)", "权利要求 (Claims)"],
      "implementation_config": { ... },
      "evaluation_metrics": [ ... ],
      "success_confidence": 0.8,
      "derived_conclusion": "结论文本"
    }
  ]
}
```

### 关键字段说明

- **inputs**: 必须是列表 (List)，即使为空也应该是 `[]`
- **standardized_intent**: 标准化意图，会创建为 Intent 节点
- **method_name**: 方法名称，会创建为 Method 节点
- **dataset_config.source**: 数据集来源，会创建为 Dataset 节点

## 🧪 测试

运行测试脚本：

```bash
python test_ingest_graph.py
```

测试包括：
1. 单个文件入库测试
2. inputs 列表处理测试 (包括空列表)
3. 批量入库测试 (前 5 个文件)

## 🔧 核心特性

### 1. 原子事务处理

每个分析步骤的入库是一个原子操作，确保数据一致性。

### 2. inputs 列表处理

使用 Cypher 的 `FOREACH` 语句正确处理 inputs 列表：

```cypher
FOREACH (input_name IN $input_list |
    MERGE (dt:Data {name: input_name})
    ON CREATE SET dt.created_at = datetime()
    MERGE (e)-[:REQUIRES_INPUT]->(dt)
)
```

### 3. 唯一性约束

自动创建以下约束，确保全局节点唯一：
- Intent.name
- Method.name
- Dataset.name
- Data.name
- Paper.title

### 4. 错误处理

- 连接失败时提供清晰的错误信息
- JSON 解析错误时跳过该文件并继续
- 提供详细的成功/失败统计

## 📊 查询示例

入库完成后，可以使用以下 Cypher 查询验证数据：

### 查询 1: 查看所有论文

```cypher
MATCH (p:Paper)
RETURN p.title, p.year
ORDER BY p.year DESC
```

### 查询 2: 查看某篇论文的完整分析链

```cypher
MATCH (p:Paper {title: "A Trend Analysis Method for IoT Technologies Using Patent Dataset with Goal and Approach Concepts"})
MATCH (p)-[:CONTAINS_EVENT]->(e:AnalysisEvent)
MATCH (e)-[:TARGETS_INTENT]->(i:Intent)
MATCH (e)-[:USES_METHOD]->(m:Method)
MATCH (e)-[:REQUIRES_INPUT]->(d:Data)
MATCH (e)-[:PRODUCED_CONCLUSION]->(c:Conclusion)
RETURN p, e, i, m, d, c
```

### 查询 3: 统计各意图的使用频率

```cypher
MATCH (i:Intent)<-[:TARGETS_INTENT]-(e:AnalysisEvent)
RETURN i.name, count(e) as usage_count
ORDER BY usage_count DESC
```

### 查询 4: 查看所有输入数据类型

```cypher
MATCH (d:Data)
RETURN d.name, count{(d)<-[:REQUIRES_INPUT]-()} as usage_count
ORDER BY usage_count DESC
```

### 查询 5: 查看使用特定方法的论文

```cypher
MATCH (p:Paper)-[:CONTAINS_EVENT]->(e:AnalysisEvent)-[:USES_METHOD]->(m:Method {name: "专利分析 (Patent Analysis)"})
RETURN DISTINCT p.title, p.year
```

## ⚠️ 注意事项

1. **数据库连接**: 确保 Neo4j 数据库已启动并可访问
2. **内存**: 批量入库大量数据时注意内存使用
3. **重复入库**: Paper 节点使用 MERGE，重复入库同一论文会更新而不是创建新节点
4. **字符编码**: 所有文件使用 UTF-8 编码

## 🐛 故障排查

### 问题 1: 连接失败

```
❌ Neo4j 服务不可用，请检查数据库是否启动
```

**解决方案**: 
- 检查 Neo4j 是否启动: `neo4j status`
- 检查端口是否正确 (默认 7687)

### 问题 2: 认证失败

```
❌ Neo4j 认证失败，请检查用户名和密码
```

**解决方案**: 
- 检查 `neo4j_config.py` 中的用户名和密码
- 确认 Neo4j 用户凭据

### 问题 3: JSON 解析错误

```
✗ JSON 解析错误: ...
```

**解决方案**: 
- 检查 JSON 文件格式是否正确
- 使用 JSON 验证工具检查文件

## 📈 性能优化建议

1. **批量入库**: 使用 `batch_ingest_from_folder()` 而不是逐个文件入库
2. **索引**: Schema 初始化会自动创建必要的唯一性约束
3. **事务大小**: 每篇论文使用独立事务，避免事务过大

## 🔄 版本历史

- **v1.0** (2025-12-09): 初始版本
  - 支持批量入库
  - 严格区分 MERGE 和 CREATE
  - 正确处理 inputs 列表
  - 完整的错误处理和统计

## 📝 许可证

本项目遵循 MIT 许可证。
