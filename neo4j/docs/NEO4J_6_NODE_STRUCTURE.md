# Neo4j 6 节点结构 - V3.1

## 🎯 核心设计

### 6 种节点类型

```
1. Paper (论文)
2. Dataset (数据平台) - ✨ 全局共享节点
3. AnalysisEvent (分析步骤)
4. Method (方法)
5. Data (数据字段)
6. Conclusion (结论)
```

---

## 📊 节点详细说明

### 1. Paper (论文)
```cypher
CREATE (p:Paper {
  title: "论文标题",
  year: "2023"
})
```

### 2. Dataset (数据平台) - 全局共享 ✨
```cypher
CREATE (d:Dataset {
  name: "USPTO",
  full_name: "United States Patent and Trademark Office",
  type: "Patent Database",
  url: "https://www.uspto.gov",
  api_endpoint: "https://developer.uspto.gov/api-catalog",
  access_method: "API / Web Interface",
  created_at: datetime()
})
```

**属性说明**:
- `name`: 简称（如 "USPTO"）
- `full_name`: 全称
- `type`: 类型（Patent Database / Scientific Literature Database）
- `url`: 官方网站地址 ✨
- `api_endpoint`: API 接口地址 ✨
- `access_method`: 访问方式（API / Web Interface / Commercial Platform）✨

**特点**:
- 全局唯一，预先创建
- 所有论文共享同一个 Dataset 节点
- 避免重复创建相同的数据平台
- **包含访问信息，Coding Agent 可以直接使用** ✨

**预创建的 Dataset 节点**:
- USPTO, EPO, JPO, CNIPA, WIPO
- Derwent Innovation Index, Google Patents, PatSnap
- Web of Science, Scopus, PubMed, arXiv

### 3. AnalysisEvent (分析步骤)
```cypher
CREATE (ae:AnalysisEvent {
  step_id: 1,
  objective: "获取固态电池专利数据",
  method_name: "Database Query",
  
  // ✨ dataset_config 存储查询配置
  dataset_config: '{
    "source": "USPTO",
    "query": {
      "keywords": "solid-state battery",
      "ipc_codes": ["H01M"],
      "time_range": "2010-2020"
    },
    "filters": {
      "language": "English",
      "remove_duplicates": true
    },
    "scale": {
      "initial_results": "10,000 patents",
      "after_filtering": "5,000 patents"
    }
  }',
  
  config: '{...}',  // method_config
  metrics: '[...]',
  derived_conclusion: "成功获取5000件专利数据"
})
```

### 4. Method (方法)
```cypher
CREATE (m:Method {
  name: "LDA (主题模型)"
})
```

### 5. Data (数据字段)
```cypher
CREATE (d:Data {
  name: "摘要 (Abstract)"
})
```

### 6. Conclusion (结论)
```cypher
CREATE (c:Conclusion {
  content: "成功识别出50个核心技术主题",
  type: "方法有效性（已验证）"
})
```

---

## 🔗 关系结构

### 完整关系图
```
Paper -[:CONDUCTS]-> AnalysisEvent
                         |
                         |-[:QUERIES]-> Dataset (全局)
                         |
                         |-[:EXECUTES]-> Method
                         |
                         |-[:YIELDS]-> Conclusion
                         |
                         ^
                         |
                    Data -[:FEEDS_INTO]-
```

### 关系详细说明

#### 1. Paper → AnalysisEvent
```cypher
(Paper)-[:CONDUCTS]->(AnalysisEvent)
```
- 论文执行分析步骤

#### 2. AnalysisEvent → Dataset ✨ 核心关系
```cypher
(AnalysisEvent)-[:QUERIES]->(Dataset)
```
- 分析步骤查询数据平台
- Dataset 是全局共享的
- dataset_config 存储在 AnalysisEvent 中

#### 3. AnalysisEvent → Method
```cypher
(AnalysisEvent)-[:EXECUTES]->(Method)
```
- 分析步骤执行方法

#### 4. Data → AnalysisEvent
```cypher
(Data)-[:FEEDS_INTO]->(AnalysisEvent)
```
- 数据字段输入到分析步骤

#### 5. AnalysisEvent → Conclusion
```cypher
(AnalysisEvent)-[:YIELDS]->(Conclusion)
```
- 分析步骤产生结论

---

## 💡 关键设计理念

### 为什么 Dataset 是全局共享的？

#### ❌ 错误设计：每篇论文创建新的 Dataset
```
Paper A → Dataset "USPTO 2010-2020 固态电池"
Paper B → Dataset "USPTO 2015-2020 锂电池"
Paper C → Dataset "USPTO 2010-2020 固态电池"  ← 重复！
```

**问题**:
- 大量重复节点
- 无法统计某个平台的使用情况
- 图谱臃肿

#### ✅ 正确设计：全局共享 Dataset
```
         Dataset "USPTO" (全局唯一)
              ↑
              |
    ┌─────────┼─────────┐
    |         |         |
Paper A   Paper B   Paper C
    |         |         |
   AE1       AE2       AE3
(config1) (config2) (config1)
```

**优势**:
- 避免重复
- 易于统计
- 图谱清晰

### dataset_config 的作用

**存储位置**: AnalysisEvent.dataset_config

**内容**: 查询和筛选配置
```json
{
  "source": "USPTO",  // 指向全局 Dataset 节点
  "query": {...},     // 查询条件
  "filters": {...},   // 筛选规则
  "scale": {...}      // 数据规模
}
```

**用途**:
1. 指向全局 Dataset 节点
2. 记录具体的查询条件
3. 让 Coding Agent 能够复现数据获取

---

## 🔍 查询示例

### 1. 查询某个平台的使用情况
```cypher
MATCH (d:Dataset {name: "USPTO"})<-[:QUERIES]-(ae:AnalysisEvent)
RETURN 
  count(DISTINCT ae) as total_queries,
  count(DISTINCT ae.objective) as unique_objectives
```

### 2. 查询某篇论文使用了哪些数据平台
```cypher
MATCH (p:Paper {title: "..."})-[:CONDUCTS]->(ae:AnalysisEvent)-[:QUERIES]->(d:Dataset)
RETURN DISTINCT d.name, d.type
```

### 3. 查询最常用的数据平台
```cypher
MATCH (d:Dataset)<-[:QUERIES]-(ae:AnalysisEvent)
RETURN 
  d.name, 
  d.type,
  count(ae) as usage_count
ORDER BY usage_count DESC
```

### 4. 查询某个平台上的常见查询条件
```cypher
MATCH (d:Dataset {name: "USPTO"})<-[:QUERIES]-(ae:AnalysisEvent)
WHERE ae.dataset_config IS NOT NULL
RETURN ae.dataset_config
LIMIT 10
```

### 5. 查询完整的分析逻辑链（含数据平台）
```cypher
MATCH (p:Paper)-[:CONDUCTS]->(ae:AnalysisEvent)
WHERE p.title = "..."
OPTIONAL MATCH (ae)-[:QUERIES]->(d:Dataset)
OPTIONAL MATCH (ae)-[:EXECUTES]->(m:Method)
OPTIONAL MATCH (data:Data)-[:FEEDS_INTO]->(ae)
OPTIONAL MATCH (ae)-[:YIELDS]->(c:Conclusion)
RETURN 
  ae.step_id,
  ae.objective,
  d.name as dataset,
  ae.dataset_config,
  m.name as method,
  collect(DISTINCT data.name) as data_fields,
  c.content as conclusion
ORDER BY ae.step_id
```

---

## 🚀 导入流程

### 1. 初始化全局 Dataset 节点
```python
importer = PatentAnalysisImporterV3(uri, user, password)
# 自动创建全局 Dataset 节点（如果不存在）
```

### 2. 导入论文数据
```python
importer.import_analysis_data(json_data)
```

### 3. 自动建立关系
- 创建 Paper 节点
- 创建 AnalysisEvent 节点
- 根据 dataset_config.source 连接到全局 Dataset 节点
- 创建其他节点和关系

---

## 📊 数据流示例

### JSON 输入
```json
{
  "paper_meta": {
    "title": "Solid-State Battery Analysis",
    "year": "2023"
  },
  "analysis_logic_chains": [
    {
      "step_id": 1,
      "objective": "获取固态电池专利数据",
      "dataset_config": {
        "source": "USPTO",
        "query": {
          "keywords": "solid-state battery",
          "ipc_codes": ["H01M"],
          "time_range": "2010-2020"
        },
        "scale": {
          "initial_results": "10,000 patents",
          "after_filtering": "5,000 patents"
        }
      },
      "method_name": "Database Query"
    }
  ]
}
```

### Neo4j 图谱
```
(Paper {title: "Solid-State Battery Analysis"})
    |
    |-[:CONDUCTS]->
    |
(AnalysisEvent {
  step_id: 1,
  objective: "获取固态电池专利数据",
  dataset_config: '{...}'
})
    |
    |-[:QUERIES]->
    |
(Dataset {name: "USPTO"})  ← 全局共享节点
```

---

## ✅ 总结

### 核心优势

1. **避免冗余**: Dataset 全局唯一
2. **易于统计**: 快速查询平台使用情况
3. **语义清晰**: Dataset = 平台，dataset_config = 查询配置
4. **可扩展**: 新增平台只需创建一次
5. **可复现**: dataset_config 包含完整的查询信息

### 关键设计

- **6 种节点**: Paper, Dataset, AnalysisEvent, Method, Data, Conclusion
- **Dataset 全局共享**: 预先创建，所有论文共享
- **dataset_config**: 存储在 AnalysisEvent 中，指向 Dataset

---

**版本**: V3.1  
**设计日期**: 2025-12-05  
**核心理念**: Dataset 作为全局共享节点，dataset_config 存储查询配置
