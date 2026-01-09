# 专利分析逻辑链 Neo4j 导入工具

## 📋 功能说明

将专利分析 JSON 数据导入到 Neo4j 图数据库，构建以 **AnalysisEvent（分析事件）** 为核心的知识图谱。

## 🏗️ 图谱模型 (Schema)

### 节点类型 (Nodes)

1. **Paper** - 论文
   - `title` (String, 主键): 论文标题
   - `year` (String): 发表年份

2. **AnalysisEvent** - 分析事件（核心枢纽）
   - `event_id` (String, 唯一标识): `{paper_title}_step_{step_id}`
   - `step_id` (Integer): 步骤编号
   - `objective` (String): 分析目标
   - `notes` (String): 备注说明
   - `config` (String): 实现配置（JSON 序列化）
   - `metrics` (String): 评估指标（JSON 序列化）

3. **Method** - 方法
   - `name` (String, 主键): 方法名称

4. **Data** - 数据/字段
   - `name` (String, 主键): 数据名称

5. **Conclusion** - 结论
   - `type` (String, 主键): 结论类型

### 关系类型 (Relationships)

- `(:Paper)-[:CONDUCTS]->(:AnalysisEvent)` - 论文执行分析事件
- `(:AnalysisEvent)-[:EXECUTES]->(:Method)` - 分析事件使用方法
- `(:Data)-[:FEEDS_INTO]->(:AnalysisEvent)` - 数据输入到分析事件
- `(:AnalysisEvent)-[:YIELDS]->(:Conclusion)` - 分析事件产生结论

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install neo4j
```

### 2. 配置 Neo4j 连接

编辑 `neo4j_config.py` 文件，修改数据库连接信息：

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_actual_password"  # 修改为你的密码
}
```

### 3. 导入单个文件

```bash
python import_to_neo4j.py
```

默认导入文件：
```
batch_50_results/'Green chasm' in clean-tech for air pollution_ Patent evidence of a long innovation cycle and a technological level gap_analysis_result.json
```

### 4. 批量导入整个文件夹

```bash
python batch_import_to_neo4j.py
```

默认导入 `batch_50_results` 文件夹中的所有 `*_analysis_result.json` 文件。

## 📊 Cypher 查询示例

### 查看所有论文
```cypher
MATCH (p:Paper)
RETURN p.title, p.year
```

### 查看某篇论文的完整分析链
```cypher
MATCH (p:Paper {title: "'Green chasm' in clean-tech for air pollution: Patent evidence of a long innovation cycle and a technological level gap"})
      -[:CONDUCTS]->(ae:AnalysisEvent)
      -[:EXECUTES]->(m:Method)
RETURN p, ae, m
ORDER BY ae.step_id
```

### 查找使用特定方法的所有分析事件
```cypher
MATCH (ae:AnalysisEvent)-[:EXECUTES]->(m:Method {name: "专利分析 (Patent Analysis)"})
RETURN ae.objective, ae.step_id
```

### 查找特定数据字段的使用情况
```cypher
MATCH (d:Data {name: "申请人 / 专利权人 (Applicant / Assignee)"})
      -[:FEEDS_INTO]->(ae:AnalysisEvent)
      -[:EXECUTES]->(m:Method)
RETURN d.name, ae.objective, m.name
```

### 查看完整的分析路径（包含输入和输出）
```cypher
MATCH path = (p:Paper)-[:CONDUCTS]->(ae:AnalysisEvent)
OPTIONAL MATCH (d:Data)-[:FEEDS_INTO]->(ae)
OPTIONAL MATCH (ae)-[:EXECUTES]->(m:Method)
OPTIONAL MATCH (ae)-[:YIELDS]->(c:Conclusion)
RETURN path, d, m, c
LIMIT 50
```

### 统计各类方法的使用频率
```cypher
MATCH (ae:AnalysisEvent)-[:EXECUTES]->(m:Method)
RETURN m.name AS 方法名称, count(ae) AS 使用次数
ORDER BY 使用次数 DESC
```

### 查找产生特定类型结论的分析事件
```cypher
MATCH (ae:AnalysisEvent)-[:YIELDS]->(c:Conclusion {type: "技术空白（已识别）"})
RETURN ae.objective, ae.notes
```

## 🔍 数据验证

导入后，可以运行以下查询验证数据完整性：

```cypher
// 统计各类节点数量
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

```cypher
// 统计各类关系数量
MATCH ()-[r]->()
RETURN type(r) AS RelationType, count(r) AS Count
ORDER BY Count DESC
```

## ⚠️ 注意事项

1. **唯一性保证**：使用 `MERGE` 语句避免重复创建节点
2. **AnalysisEvent 唯一标识**：`{paper_title}_step_{step_id}` 确保同一论文的步骤不会重复
3. **全局共享节点**：Method 和 Data 节点在整个图谱中共享（基于 name 属性）
4. **JSON 序列化**：复杂对象（config, metrics）以 JSON 字符串形式存储

## 📝 文件说明

- `import_to_neo4j.py` - 单文件导入脚本
- `batch_import_to_neo4j.py` - 批量导入脚本
- `neo4j_config.py` - 配置文件
- `NEO4J_IMPORT_README.md` - 本说明文档

## 🛠️ 故障排查

### 连接失败
- 检查 Neo4j 服务是否启动
- 验证 URI、用户名、密码是否正确
- 确认防火墙是否允许 7687 端口

### 导入失败
- 检查 JSON 文件格式是否正确
- 查看错误日志获取详细信息
- 确认 Neo4j 数据库有足够的存储空间

### 数据重复
- 脚本使用 MERGE 语句，重复运行不会创建重复节点
- 如需重新导入，可先清空数据库：`MATCH (n) DETACH DELETE n`
