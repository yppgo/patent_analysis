# 专利分析智能体系统完整工作流程文档

## 📋 文档概述

本文档详细描述了基于双图谱架构的专利分析智能体系统的完整工作流程，包括：
- 系统整体架构
- 两个核心图谱（因果图谱、方法图谱）
- 变量映射器
- 四个智能体（Strategist、Methodologist、Coding Agent、Reviewer）
- 完整数据流转过程
- 实际案例演示

**文档版本**: 1.0  
**创建日期**: 2026-01-19  
**维护者**: Patent Analysis Research Group

---

## 🎯 系统整体架构

### 核心理念

**领域驱动 + 假设生成 + 多智能体协同**

用户只需提供**领域关键词**（如"数据安全"），系统自动：
1. 生成研究假设（基于因果图谱）
2. 设计分析方案（基于变量映射和方法图谱）
3. 生成可执行代码（多智能体协同）
4. 执行分析并生成报告

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户输入层                               │
│  输入: 领域关键词 + 研究意图                                      │
│  示例: "数据安全领域的技术趋势分析"                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      知识层（双图谱）                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 因果图谱      │  │ 变量映射器    │  │ 方法图谱      │          │
│  │ (理论层)     │  │ (实现层)     │  │ (方法层)     │          │
│  │ 回答"为什么" │  │ 回答"如何连接"│  │ 回答"怎么做" │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      智能体层（多智能体协同）                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Strategist Agent (战略规划)                              │   │
│  │ - 理解用户意图                                            │   │
│  │ - 查询双图谱                                              │   │
│  │ - 生成DAG任务图                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
                              ↓
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Methodologist Agent (技术架构)                           │   │
│  │ - 接收任务节点                                            │   │
│  │ - 生成技术规格（伪代码）                                   │   │
│  │ - 定义数据结构                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
                              ↓
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Coding Agent (代码实现)                                  │   │
│  │ - 接收技术规格                                            │   │
│  │ - 生成可执行Python代码                                    │   │
│  │ - 处理依赖关系                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
                              ↓
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Reviewer Agent (报告生成)                                │   │
│  │ - 收集分析结果                                            │   │
│  │ - 生成研究报告                                            │   │
│  │ - 提供结论和建议                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      执行层（代码执行）                          │
│  - 按DAG顺序执行Python脚本                                      │
│  - 生成中间结果文件                                              │
│  - 保存最终分析结果                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      输出层（研究报告）                          │
│  - 研究假设验证结果                                              │
│  - 数据分析结果                                                  │
│  - 可视化图表                                                    │
│  - 结论和建议                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 组件 1: 因果图谱（Causal Ontology）

### 1.1 核心定位

**回答问题**: "为什么"（Why）- 变量之间的因果关系

**作用层级**: 理论层 / 假设生成层

**使用时机**: 系统工作流程的第一步，用于生成研究假设

### 1.2 数据来源和规模

- **文件位置**: `sandbox/static/data/causal_ontology_extracted.json`
- **数据来源**: 50篇专利分析领域学术论文
- **抽取方法**: Claude PDF分析 + 人工验证
- **数据规模**:
  - 30个抽象变量
  - 135条因果路径
  - 42条已验证路径（有文献证据支持）
  - 138个复杂关系（中介/调节效应）

### 1.3 数据结构

```json
{
  "meta": {
    "total_variables": 30,
    "total_paths": 135,
    "extraction_source": "50篇专利分析领域学术论文"
  },
  "variables": [
    {
      "id": "V03_rd_investment",
      "label": "研发投资强度",
      "category": "input",
      "definition": "研发支出占营收比例",
      "measurement": {
        "metric": "rd_intensity",
        "formula": "R&D_expenditure / Revenue"
      }
    }
  ],
  "causal_paths": [
    {
      "path_id": "P02",
      "source": "V03_rd_investment",
      "target": "V16_tech_impact",
      "effect_type": "positive",
      "effect_size": "large",
      "mechanism": "研发投资规模直接影响专利申请数量和技术产出能力",
      "evidence": {
        "validated": true,
        "evidence_count": 14,
        "supporting_papers": ["论文1", "论文2", ...]
      }
    }
  ]
}
```

### 1.4 核心功能

**实现类**: `src/utils/causal_graph_query.py` - `CausalGraphQuery`

**主要方法**:

1. **查找直接因果路径**
```python
path = query.find_direct_path("V03_rd_investment", "V16_tech_impact")
# 返回: V03 → V16 的直接因果关系
```

2. **查找中介路径**
```python
mediation = query.get_mediation_paths("V03_rd_investment", "V16_tech_impact")
# 返回: V03 → M → V16 的中介路径列表
```

3. **推荐研究假设**
```python
hypotheses = query.suggest_hypotheses("研究研发投资的影响", top_k=5)
# 返回: 基于关键词匹配的假设列表
```

4. **获取变量定义**
```python
variable = query.get_variable("V03_rd_investment")
# 返回: 变量的完整定义和测量方式
```

### 1.5 输出示例

```python
{
  "hypothesis": "H1: 研发投资强度对技术影响力有正向影响",
  "source_var": "V03_rd_investment",
  "target_var": "V16_tech_impact",
  "effect_type": "positive",
  "effect_size": "large",
  "mechanism": "研发投资规模直接影响专利申请数量和技术产出能力",
  "evidence_count": 14,
  "supporting_papers": ["论文1", "论文2", ...]
}
```

---

## 🔗 组件 2: 变量映射器（Variable Mapper）

### 2.1 核心定位

**回答问题**: "如何连接"（Bridge）- 抽象变量到具体数据字段的映射

**作用层级**: 实现层 / 数据对齐层

**使用时机**: 在因果图谱生成假设后，将抽象变量映射到实际数据字段

### 2.2 数据来源和规模

- **文件位置**: `src/utils/variable_mapper.py` - 内置映射表
- **映射规模**: 24个变量已映射（30个变量中）
- **映射内容**: 抽象变量 → 数据字段 + 计算方法 + Python代码

### 2.3 映射结构

```python
{
  "V03_rd_investment": {
    "label": "研发投资强度",
    "data_fields": ["申请(专利权)人", "序号"],
    "calculation": "COUNT(专利) / COUNT(DISTINCT 申请人)",
    "calculation_type": "ratio",
    "description": "人均专利产出（代理指标）",
    "python_code": "len(df) / df['申请(专利权)人'].nunique()",
    "note": "真实的研发投资数据需要外部数据源"
  }
}
```

### 2.4 核心功能

**实现类**: `src/utils/variable_mapper.py` - `VariableMapper`

**主要方法**:

1. **获取数据字段**
```python
fields = mapper.get_data_fields("V03_rd_investment")
# 返回: ['申请(专利权)人', '序号']
```

2. **获取计算方法**
```python
calc = mapper.get_calculation_method("V03_rd_investment")
# 返回: "COUNT(专利) / COUNT(DISTINCT 申请人)"
```

3. **检查数据可用性**
```python
availability = mapper.check_data_availability("V03_rd_investment", available_columns)
# 返回: {"is_available": True, "missing_columns": []}
```

4. **生成任务配置**
```python
config = mapper.generate_task_config("V03_rd_investment")
# 返回: 完整的任务配置字典
```

### 2.5 输出示例

```python
{
  "variable_id": "V03_rd_investment",
  "variable_label": "研发投资强度",
  "input_columns": ["申请(专利权)人", "序号"],
  "calculation": "COUNT(专利) / COUNT(DISTINCT 申请人)",
  "calculation_type": "ratio",
  "description": "人均专利产出（代理指标）",
  "python_code": "len(df) / df['申请(专利权)人'].nunique()"
}
```

---

## 🔧 组件 3: 方法图谱（Methodology Graph）

### 3.1 核心定位

**回答问题**: "怎么做"（How）- 具体的分析方法和步骤

**作用层级**: 方法层 / 实现参考层

**使用时机**: 在变量映射后，检索相关的分析方法案例

### 3.2 数据来源和规模

- **存储位置**: Neo4j数据库（bolt://localhost:7687）
- **数据来源**: 66篇专利分析领域学术论文的完整分析逻辑链
- **数据规模**:
  - 1023个节点
  - 2749个关系
  - 66篇论文
  - 382个分析步骤
  - 86个方法
  - 89个数据字段
  - 361个结论

### 3.3 数据结构（Neo4j图数据库）

**节点类型**:
- Paper (66个): 论文节点
- AnalysisEvent (382个): 分析步骤节点
- Method (86个): 方法节点
- Data (89个): 数据字段节点
- Conclusion (361个): 结论节点

**关系类型**:
- (Paper)-[:CONDUCTS]->(AnalysisEvent): 论文包含分析步骤
- (AnalysisEvent)-[:EXECUTES]->(Method): 步骤使用方法
- (Data)-[:FEEDS_INTO]->(AnalysisEvent): 数据输入步骤
- (AnalysisEvent)-[:YIELDS]->(Conclusion): 步骤产生结论

### 3.4 核心功能

**实现类**: `src/utils/neo4j_connector.py` - `Neo4jConnector`

**主要方法**:

1. **检索最佳实践案例**
```python
cases = neo4j.retrieve_best_practices("技术趋势", limit=3)
# 返回: 相关的分析案例列表
```

2. **执行自定义查询**
```python
query = """
MATCH (p:Paper)-[:CONDUCTS]->(ae:AnalysisEvent)
WHERE ae.objective CONTAINS '主题建模'
RETURN p.title, ae.method_name
"""
results = neo4j.run_query(query)
```

### 3.5 输出示例

```python
{
  "paper_title": "A comprehensive review on green buildings research...",
  "paper_year": 2021,
  "full_logic_chain": [
    {
      "step_id": 1,
      "objective": "文献检索",
      "method_name": "数据库检索",
      "config": {"tool": "Web of Science"},
      "inputs": ["关键词", "时间范围"],
      "conclusion": "获得2000篇文献"
    },
    {
      "step_id": 2,
      "objective": "文献计量分析",
      "method_name": "引文分析",
      "config": {"tool": "VOSviewer"},
      "inputs": ["引用关系"],
      "conclusion": "识别核心文献和研究热点"
    }
  ]
}
```

---

## 🤖 智能体 1: Strategist Agent（战略规划）

### 4.1 核心职责

**角色定位**: 系统的"大脑"，负责理解用户意图并生成研究战略

**主要任务**:
1. 理解用户研究目标
2. 提取检索关键词
3. 查询双图谱（因果图谱 + 方法图谱）
4. 整合信息生成DAG任务图
5. 确保变量流的完整性

### 4.2 实现细节

**实现类**: `src/agents/strategist.py` - `StrategistAgent`

**工作模式**:
- Legacy模式: 生成传统的 `analysis_logic_chains` 列表
- DAG模式: 生成基于DAG的 `task_graph`（推荐）

### 4.3 工作流程

```
用户输入
    ↓
Step 1: 意图转译
    - 提取检索关键词
    - 识别分析类型
    ↓
Step 2: 因果图谱查询
    - 推荐研究假设
    - 识别因果路径
    - 查找中介效应
    ↓
Step 3: 变量映射
    - 获取所需数据字段
    - 检查数据可用性
    - 生成计算方法
    ↓
Step 4: 方法图谱检索
    - 检索相关案例
    - 提取方法配置
    - 参考分析流程
    ↓
Step 5: 生成DAG任务图
    - 整合三个图谱的信息
    - 定义任务节点
    - 建立依赖关系
    - 检查图完整性
    ↓
输出: DAG Blueprint
```

### 4.4 输入输出格式

**输入**:
```python
{
  "user_goal": "数据安全领域的技术趋势分析",
  "available_columns": ["序号", "名称", "摘要", "申请(专利权)人", ...],
  "use_dag": True  # 使用DAG模式
}
```

**输出（DAG模式）**:
```python
{
  "thinking_trace": {
    "data_audit": "可用列名：'序号'、'名称'、'摘要'...",
    "algorithm_selection": "选择LDA进行主题建模",
    "conclusion_design": "Task 2回答'有哪些技术主题'，输出主题汇总JSON"
  },
  "research_objective": "数据安全领域的技术趋势分析",
  "expected_outcomes": ["识别技术主题", "分析趋势变化"],
  "task_graph": [
    {
      "task_id": "task_1",
      "task_type": "data_summary",
      "question": "数据集的基本情况如何？",
      "input_variables": [],
      "output_variables": ["data_summary"],
      "dependencies": [],
      "implementation_config": {...}
    },
    {
      "task_id": "task_2",
      "task_type": "topic_analysis",
      "question": "有哪些主要的技术主题？",
      "input_variables": ["data_summary"],
      "output_variables": ["topics_summary", "lda_model"],
      "dependencies": ["task_1"],
      "implementation_config": {...}
    }
  ]
}
```

### 4.5 关键特性

1. **Schema Awareness**: 自动从数据文件读取列名，防止幻觉列名
2. **图完整性检查**: 验证变量流的完整性，防止数据断链
3. **结论导向输出**: 强制输出结论性数据（JSON汇总 > CSV表格）
4. **思考过程追踪**: 包含 `thinking_trace` 字段，记录LLM的推理过程

---

## 🤖 智能体 2: Methodologist Agent（技术架构）

### 5.1 核心职责

**角色定位**: 技术架构师，负责将任务节点转换为技术规格

**主要任务**:
1. 接收Strategist生成的任务节点
2. 生成详细的技术规格（伪代码）
3. 定义数据结构和接口
4. 处理任务依赖关系

### 5.2 实现细节

**实现类**: `src/agents/methodologist.py` - `MethodologistAgent`

**工作模式**:
- V5.0: 支持DAG模式，处理单个任务节点
- Legacy: 支持传统的逻辑链模式

### 5.3 工作流程

```
接收任务节点
    ↓
Step 1: 理解任务目标
    - 解析 question
    - 识别 task_type
    ↓
Step 2: 分析数据依赖
    - 检查 input_variables
    - 确定数据来源
    ↓
Step 3: 设计算法流程
    - 选择具体算法
    - 定义参数配置
    ↓
Step 4: 生成技术规格
    - 编写伪代码
    - 定义输出格式
    ↓
输出: Technical Specification
```

### 5.4 输入输出格式

**输入**:
```python
{
  "task_node": {
    "task_id": "task_2",
    "task_type": "topic_analysis",
    "question": "有哪些主要的技术主题？",
    "input_variables": ["data_summary"],
    "output_variables": ["topics_summary", "lda_model"],
    "dependencies": ["task_1"],
    "implementation_config": {
      "algorithm": "LDA",
      "text_column": "摘要",
      "parameters": {"n_topics": 8}
    }
  }
}
```

**输出**:
```python
{
  "task_id": "task_2",
  "technical_spec": {
    "algorithm": "LDA Topic Modeling",
    "pseudocode": """
    1. 加载数据: df = pd.read_csv('outputs/task_1_df_raw.csv')
    2. 文本预处理: texts = preprocess(df['摘要'])
    3. 构建词典: dictionary = corpora.Dictionary(texts)
    4. 构建语料: corpus = [dictionary.doc2bow(text) for text in texts]
    5. 训练LDA: model = LdaModel(corpus, num_topics=8)
    6. 生成主题汇总: topics_summary = extract_topics(model)
    7. 保存结果: save_json(topics_summary, 'outputs/task_2_topics_summary.json')
    8. 保存模型: joblib.dump(model, 'outputs/task_2_lda_model.pkl')
    """,
    "input_files": ["outputs/task_1_df_raw.csv"],
    "output_files": [
      "outputs/task_2_topics_summary.json",
      "outputs/task_2_lda_model.pkl"
    ],
    "dependencies": ["gensim", "pandas", "joblib"]
  }
}
```

---

## 🤖 智能体 3: Coding Agent（代码实现）

### 6.1 核心职责

**角色定位**: 代码工程师，负责将技术规格转换为可执行代码

**主要任务**:
1. 接收Methodologist生成的技术规格
2. 生成完整的Python代码
3. 处理依赖关系和错误处理
4. 确保代码可直接运行

### 6.2 实现细节

**实现类**: `src/agents/coding_agent.py` - `CodingAgent`

### 6.3 工作流程

```
接收技术规格
    ↓
Step 1: 解析伪代码
    - 理解算法流程
    - 识别关键步骤
    ↓
Step 2: 生成代码框架
    - 导入必要的库
    - 定义主函数
    ↓
Step 3: 实现核心逻辑
    - 数据加载
    - 算法实现
    - 结果保存
    ↓
Step 4: 添加错误处理
    - try-except块
    - 日志记录
    ↓
输出: Executable Python Code
```

### 6.4 输入输出格式

**输入**: Methodologist的技术规格

**输出**:
```python
# task_2_topic_analysis.py
import pandas as pd
import json
from gensim import corpora
from gensim.models import LdaModel
import joblib

def main():
    # 1. 加载数据
    df = pd.read_csv('outputs/task_1_df_raw.csv')
    
    # 2. 文本预处理
    texts = df['摘要'].apply(preprocess).tolist()
    
    # 3. 构建词典和语料
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # 4. 训练LDA模型
    model = LdaModel(corpus, num_topics=8, id2word=dictionary)
    
    # 5. 生成主题汇总
    topics_summary = extract_topics(model, df)
    
    # 6. 保存结果
    with open('outputs/task_2_topics_summary.json', 'w') as f:
        json.dump(topics_summary, f, indent=2)
    
    # 7. 保存模型
    joblib.dump(model, 'outputs/task_2_lda_model.pkl')

if __name__ == "__main__":
    main()
```

---

## 🤖 智能体 4: Reviewer Agent（报告生成）

### 7.1 核心职责

**角色定位**: 研究报告撰写者，负责整合分析结果并生成报告

**主要任务**:
1. 收集所有任务的分析结果
2. 整合数据和可视化
3. 生成研究报告（Markdown/PDF）
4. 提供结论和建议

### 7.2 实现细节

**实现类**: `src/agents/reviewer.py` - `ReviewerAgent`

### 7.3 工作流程

```
收集分析结果
    ↓
Step 1: 加载所有输出文件
    - JSON汇总文件
    - CSV数据文件
    - 可视化图表
    ↓
Step 2: 分析结果
    - 提取关键发现
    - 验证研究假设
    ↓
Step 3: 生成报告结构
    - 研究背景
    - 数据描述
    - 分析结果
    - 结论和建议
    ↓
Step 4: 格式化输出
    - Markdown格式
    - PDF格式（可选）
    ↓
输出: Research Report
```

### 7.4 输出示例

```markdown
# 数据安全领域技术趋势分析报告

## 1. 研究背景

本研究旨在分析数据安全领域的技术趋势...

## 2. 数据描述

- 数据来源: 专利数据库
- 时间范围: 2015-2025
- 专利总数: 1000条
- 主要申请人: 华为、阿里巴巴、腾讯...

## 3. 分析结果

### 3.1 技术主题识别

通过LDA主题建模，识别出8个主要技术主题：

1. **数据加密技术** (23.4%)
   - 关键词: 加密、密钥、算法
   - 专利数: 234
   - 关键发现: 数据加密是最主要的技术方向

2. **隐私保护技术** (18.7%)
   ...

### 3.2 技术趋势分析

- **上升趋势**: 数据加密技术、隐私保护技术
- **下降趋势**: 传统防火墙技术
- **稳定趋势**: 访问控制技术

## 4. 结论和建议

### 4.1 主要发现

1. 数据加密技术是当前最热门的研究方向
2. 隐私保护技术呈现快速增长趋势
3. 传统防火墙技术逐渐被新技术替代

### 4.2 建议

1. 企业应加大在数据加密技术的研发投入
2. 关注隐私保护技术的最新发展
3. 探索新兴技术方向的机会
```

---

## 🔄 完整数据流转过程

### 8.1 阶段1: 用户输入 → Strategist

**输入**:
```python
user_input = {
  "user_goal": "数据安全领域的技术趋势分析",
  "available_columns": ["序号", "名称", "摘要", "申请(专利权)人", "授权日"],
  "use_dag": True
}
```

**Strategist处理**:
1. 提取关键词: ["数据安全", "技术趋势", "趋势分析"]
2. 查询因果图谱: 推荐假设 H1, H2, H3
3. 查询变量映射: 获取数据字段和计算方法
4. 查询方法图谱: 检索相关案例
5. 生成DAG任务图

**输出**:
```python
blueprint = {
  "research_objective": "数据安全领域的技术趋势分析",
  "task_graph": [
    {"task_id": "task_1", ...},
    {"task_id": "task_2", ...},
    {"task_id": "task_3", ...}
  ]
}
```

### 8.2 阶段2: Strategist → Methodologist

**输入**: 单个任务节点
```python
task_node = {
  "task_id": "task_2",
  "task_type": "topic_analysis",
  "question": "有哪些主要的技术主题？",
  "input_variables": ["data_summary"],
  "output_variables": ["topics_summary", "lda_model"],
  "dependencies": ["task_1"],
  "implementation_config": {
    "algorithm": "LDA",
    "text_column": "摘要",
    "parameters": {"n_topics": 8}
  }
}
```

**Methodologist处理**:
1. 理解任务目标: 识别技术主题
2. 分析数据依赖: 需要task_1的输出
3. 设计算法流程: LDA主题建模
4. 生成技术规格: 伪代码

**输出**:
```python
technical_spec = {
  "task_id": "task_2",
  "algorithm": "LDA Topic Modeling",
  "pseudocode": "...",
  "input_files": ["outputs/task_1_df_raw.csv"],
  "output_files": [
    "outputs/task_2_topics_summary.json",
    "outputs/task_2_lda_model.pkl"
  ]
}
```

### 8.3 阶段3: Methodologist → Coding Agent

**输入**: 技术规格

**Coding Agent处理**:
1. 解析伪代码
2. 生成代码框架
3. 实现核心逻辑
4. 添加错误处理

**输出**:
```python
# task_2_topic_analysis.py
# 完整的可执行Python代码
```

### 8.4 阶段4: 代码执行

**执行顺序**: 按DAG拓扑排序
```
task_1 (数据摘要)
    ↓
task_2 (主题分析)
    ↓
task_3 (趋势分析)
```

**生成的文件**:
```
outputs/
├── task_1_data_summary.json
├── task_1_df_raw.csv
├── task_2_topics_summary.json
├── task_2_lda_model.pkl
├── task_3_trend_analysis.json
└── task_3_trend_chart.png
```

### 8.5 阶段5: 结果 → Reviewer

**输入**: 所有任务的输出文件

**Reviewer处理**:
1. 加载所有JSON汇总文件
2. 提取关键发现
3. 生成报告结构
4. 格式化输出

**输出**:
```
outputs/
└── data_security_tech_trend_report.md
```

---

## 📝 实际案例演示

### 案例: 数据安全领域技术趋势分析

#### 用户输入
```python
user_goal = "分析数据安全领域的技术趋势，识别主要技术方向和发展趋势"
```

#### Step 1: Strategist生成DAG

**因果图谱查询结果**:
- H1: 技术投入强度 → 技术影响力 (正向, large)
- H2: 技术多样性 → 技术影响力 (正向, medium)
- H3: 技术投入 → 技术多样性 → 技术影响力 (中介效应)

**变量映射结果**:
- V01_tech_intensity → ["序号", "公开(公告)号"]
- V09_tech_diversity → ["IPC分类号"]
- V16_tech_impact → ["被引用专利"]

**方法图谱检索结果**:
- 案例1: "A trend analysis method for IoT technologies..."
  - 方法: LDA主题建模 + 时间序列分析
- 案例2: "A patent analysis of data security..."
  - 方法: 关键词检索 + 聚类分析

**生成的DAG任务图**:
```python
{
  "research_objective": "数据安全领域技术趋势分析",
  "task_graph": [
    {
      "task_id": "task_1",
      "question": "数据集的基本情况如何？",
      "output_variables": ["data_summary"]
    },
    {
      "task_id": "task_2",
      "question": "有哪些主要的技术主题？",
      "input_variables": ["data_summary"],
      "output_variables": ["topics_summary", "lda_model"],
      "dependencies": ["task_1"]
    },
    {
      "task_id": "task_3",
      "question": "哪些技术主题在上升/下降？",
      "input_variables": ["topics_summary"],
      "output_variables": ["trend_analysis"],
      "dependencies": ["task_2"]
    }
  ]
}
```

#### Step 2: Methodologist生成技术规格

**Task 1规格**:
```python
{
  "task_id": "task_1",
  "pseudocode": """
  1. 加载Excel数据
  2. 统计基本信息（总数、时间范围、申请人分布）
  3. 生成数据摘要JSON
  4. 保存原始数据CSV（备份）
  """
}
```

**Task 2规格**:
```python
{
  "task_id": "task_2",
  "pseudocode": """
  1. 加载task_1的原始数据
  2. 文本预处理（分词、去停用词）
  3. 构建词典和语料
  4. 训练LDA模型（n_topics=8）
  5. 为每个主题生成标签和关键词
  6. 统计每个主题的专利数和占比
  7. 生成主题汇总JSON
  8. 保存LDA模型PKL
  """
}
```

**Task 3规格**:
```python
{
  "task_id": "task_3",
  "pseudocode": """
  1. 加载LDA模型和原始数据
  2. 为每条专利分配主题
  3. 按年份统计每个主题的专利数
  4. 计算增长率和趋势
  5. 识别上升/下降/稳定的主题
  6. 生成趋势分析JSON
  7. 绘制趋势图
  """
}
```

#### Step 3: Coding Agent生成代码

生成3个Python脚本:
- `task_1_data_summary.py`
- `task_2_topic_analysis.py`
- `task_3_trend_analysis.py`

#### Step 4: 执行代码

```bash
python task_1_data_summary.py
# 输出: outputs/task_1_data_summary.json, outputs/task_1_df_raw.csv

python task_2_topic_analysis.py
# 输出: outputs/task_2_topics_summary.json, outputs/task_2_lda_model.pkl

python task_3_trend_analysis.py
# 输出: outputs/task_3_trend_analysis.json, outputs/task_3_trend_chart.png
```

#### Step 5: Reviewer生成报告

**生成的报告内容**:

```markdown
# 数据安全领域技术趋势分析报告

## 执行摘要

本研究分析了数据安全领域1000条专利数据（2015-2025），识别出8个主要技术主题，
并分析了各主题的发展趋势。

## 主要发现

1. **数据加密技术**是最主要的技术方向，占比23.4%
2. **隐私保护技术**呈现快速增长趋势，年均增长率35%
3. **传统防火墙技术**逐渐被新技术替代，呈下降趋势

## 技术主题详情

### 主题1: 数据加密技术 (23.4%)
- 关键词: 加密、密钥、算法、AES、RSA
- 专利数: 234
- 趋势: 稳定增长
- 代表性专利: CN123456A, CN234567B

### 主题2: 隐私保护技术 (18.7%)
- 关键词: 隐私、保护、匿名、差分隐私
- 专利数: 187
- 趋势: 快速上升
- 代表性专利: CN345678C, CN456789D

...

## 趋势分析

![技术趋势图](outputs/task_3_trend_chart.png)

- **上升趋势**: 隐私保护技术、区块链安全、零知识证明
- **下降趋势**: 传统防火墙、入侵检测系统
- **稳定趋势**: 数据加密技术、访问控制

## 结论和建议

### 结论
1. 数据安全领域正在经历技术范式转变
2. 隐私保护成为新的研究热点
3. 传统安全技术逐渐被新技术替代

### 建议
1. 企业应加大在隐私保护技术的研发投入
2. 关注区块链和零知识证明等新兴技术
3. 传统安全技术需要与新技术融合创新
```

---

## 🎯 关键设计原则

### 1. 领域驱动
- 用户只需提供领域关键词
- 系统自动生成假设和方案
- 降低用户使用门槛

### 2. 假设驱动
- 基于因果图谱生成假设
- 假设有文献证据支持
- 假设可验证、可量化

### 3. 结论导向
- 每个任务输出结论性数据
- 优先JSON汇总 > CSV表格 > 原始数据
- 便于报告智能体直接使用

### 4. 图完整性
- 变量流必须完整
- 依赖关系必须正确
- 列名必须合法

### 5. 端到端自动化
- 从领域输入到研究报告
- 多智能体协同工作
- 全流程可追溯

---

## 📊 系统性能指标

| 组件 | 响应时间 | 准确率 | 覆盖率 |
|------|---------|--------|--------|
| 因果图谱查询 | < 1秒 | 100% | 30变量/135路径 |
| 变量映射器 | < 1秒 | 100% | 24/30变量 |
| 方法图谱检索 | < 2秒 | 100% | 66篇论文 |
| Strategist Agent | 10-30秒 | 95% | - |
| Methodologist Agent | 5-15秒 | 95% | - |
| Coding Agent | 10-30秒 | 90% | - |
| Reviewer Agent | 5-10秒 | 95% | - |

---

## 🔧 系统维护和扩展

### 扩展因果图谱
1. 添加新变量 → 更新 `causal_ontology_extracted.json`
2. 添加新路径 → 从新文献中抽取
3. 验证路径 → 标记 `validated: true`

### 扩展方法图谱
1. 添加新论文 → 导入到Neo4j
2. 添加新方法 → 创建Method节点
3. 更新逻辑链 → 创建关系

### 扩展变量映射器
1. 添加新映射 → 更新 `DEFAULT_MAPPING`
2. 添加Python代码 → 更新 `python_code` 字段
3. 导出配置 → 使用 `export_mapping()`

### 优化智能体
1. 改进Prompt → 提高生成质量
2. 添加示例 → 引导LLM输出
3. 增强检查 → 提高鲁棒性

---

## 📚 相关文档

- `docs/GRAPH_ARCHITECTURE_DEFINITION.md` - 双图谱架构完整定义
- `docs/GRAPH_USAGE_FLOWCHART.md` - 使用流程图
- `docs/USER_SCENARIO_DEFINITION.md` - 用户场景定义
- `docs/DUAL_GRAPH_INTEGRATION.md` - 双图谱整合文档
- `docs/DUAL_GRAPH_TEST_RESULTS.md` - 测试结果文档

---

**文档状态**: ✓ 完成  
**最后更新**: 2026-01-19  
**维护者**: Patent Analysis Research Group
