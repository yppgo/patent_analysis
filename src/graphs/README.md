# 图谱模块 (Graphs Module)

本模块统一管理项目中使用的因果图谱和方法图谱。

## 📁 目录结构

```
src/graphs/
├── __init__.py                    # 模块初始化，导出查询器
├── causal_graph_query.py          # 因果图谱查询器
├── method_graph_query.py          # 方法图谱查询器
└── data/                          # 图谱数据
    ├── causal/                    # 因果图谱数据
    │   └── causal_ontology_extracted.json
    └── method/                    # 方法图谱数据
        └── method_knowledge_base.json
```

## 🚀 使用方法

### 导入查询器

```python
from src.graphs import CausalGraphQuery, MethodGraphQuery

# 使用默认路径初始化
causal_graph = CausalGraphQuery()
method_graph = MethodGraphQuery()

# 或指定自定义路径
causal_graph = CausalGraphQuery("path/to/causal_ontology.json")
method_graph = MethodGraphQuery("path/to/method_knowledge.json")
```

### 因果图谱查询

```python
# 生成研究假设
result = causal_graph.generate_hypotheses_v2({
    "domain": "数据安全",
    "intent": "技术趋势分析"
})

# 获取统计信息
stats = causal_graph.get_statistics()
print(f"变量总数: {stats['total_variables']}")
print(f"因果路径: {stats['total_paths']}")
```

### 方法图谱查询

```python
# 查询测量方法
methods = method_graph.query_measurement_methods("技术多样性")

# 查询分析方法
analysis = method_graph.query_analysis_methods("时间序列分析")

# 获取统计信息
stats = method_graph.get_statistics()
print(f"论文数: {stats['total_papers_processed']}")
```

## 📊 数据说明

### 因果图谱
- **数据来源**: 50篇专利分析领域学术论文
- **数据规模**: 30个变量，135条因果路径
- **核心功能**: 提供研究假设和理论支撑

### 方法图谱
- **数据来源**: 66篇方法论相关论文
- **数据规模**: 1023个节点，2749个关系
- **核心功能**: 提供具体的分析方法和参数配置

## 🔄 迁移说明

从旧路径迁移到新路径：

**旧导入方式**:
```python
from src.utils.causal_graph_query import CausalGraphQuery
from src.utils.method_graph_query import MethodGraphQuery
```

**新导入方式**:
```python
from src.graphs import CausalGraphQuery, MethodGraphQuery
```

所有测试文件和代码已更新为使用新路径。
