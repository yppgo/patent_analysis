# 专利分析多智能体系统 — 项目认知文档

## 一、项目概述

这是一个**基于双知识图谱架构的多智能体协作专利数据分析系统**。用户输入一个领域关键词（如"数据安全技术趋势"），系统自动完成从研究假设生成到最终分析报告输出的全流程。

**核心理念**：将学术论文中的因果理论知识和方法论知识提取为结构化知识图谱，驱动自动化专利分析。

**技术栈**：Python + LangGraph + 多LLM（Qwen + Claude）+ Neo4j + JSON知识图谱

---

## 二、双知识图谱架构（核心设计）

### Graph A：因果图谱（理论层 — "Why"）
- **数据**：`src/graphs/data/causal/causal_ontology_extracted.json`
- **规模**：30个抽象变量（V01-V33），99条因果路径，42条已验证
- **变量分类**：输入变量(V01-V08)、中介变量(V09-V15,V27,V29)、结果变量(V16-V21,V26,V28,V30)、调节变量(V22-V25)、接口变量(V31-V33)
- **功能**：通过6种策略生成研究假设（理论迁移、路径探索、边界条件、中介机制、反事实推理、交互效应）

### Graph B：方法图谱（方法层 — "How"）
- **数据**：`src/graphs/data/method/method_knowledge_base.json`
- **规模**：50+篇论文、28个变量覆盖、86+种分析方法
- **功能**：提供测量方法（如何从原始数据计算变量）和分析方法（回归、中介、调节等）

### 数据流连接
```
专利元数据字段 → 测量方法(Graph B) → 抽象变量(Graph A) → 因果边(Graph A) → 分析方法(Graph B) → 研究结论
```

---

## 三、多智能体协作系统

系统由4个Agent按DAG工作流协作：

### 1. StrategistAgent V5.0（战略规划者 — "大脑"）
- **文件**：`src/agents/strategist.py`
- **职责**：提取关键词 → 生成研究假设 → 筛选最佳假设 → 检索相关方法 → 生成DAG任务蓝图(2-4个任务)
- **特色**：Schema感知（防止LLM幻觉列名）、数据预览注入、图完整性检查（拓扑排序+变量流验证）

### 2. MethodologistAgent V5.0（方法论架构师）
- **文件**：`src/agents/methodologist.py`
- **职责**：将任务节点转化为技术规格说明（函数签名、伪代码逻辑流、输入输出契约）
- **特色**：变量类型识别（分类型 vs 数值型）、分类变量处理指南

### 3. CodingAgent（代码执行者，多版本迭代）
- **文件**：`src/agents/coding_agent.py` (V2) 到 `coding_agent_v5.py` (V5)
- **主力版本**：V4.2（`coding_agent_v4_2.py`）— 终端增强型，持久化REPL + Shell命令
- **职责**：根据技术规格生成Python代码 → 在REPL中执行 → 错误检测与智能修复 → 保存结果
- **特色**：支持最多15轮迭代，错误类型映射智能恢复

### 4. ReviewerAgent（评审与报告生成者）
- **文件**：`src/agents/reviewer.py`
- **职责**：验证执行结果 → 语义验证（LLM判断结果是否回答了用户问题）→ 生成最终Markdown报告

### 工作流编排
```
用户目标 → Strategist → Methodologist → CodingAgent → Reviewer → 最终报告
```
基于 **LangGraph StateGraph** 实现（`src/core/workflow.py`）。

---

## 四、项目目录结构

| 目录 | 用途 |
|---|---|
| `src/agents/` | 4个Agent的实现（含多个版本迭代） |
| `src/core/` | 工作流编排、状态定义、DAG执行器 |
| `src/graphs/` | 双知识图谱查询模块及数据文件 |
| `src/tools/` | Agent工具（Python REPL、OS操作） |
| `src/utils/` | LLM客户端、Neo4j连接器、变量映射器、数据预览等 |
| `scripts/` | 离线处理脚本（因果提取、图谱构建、报告生成等） |
| `scripts/v2/` | V2双图谱提取与合并脚本 |
| `schemas/` | V2图谱的JSON Schema定义 |
| `prompts/` | LLM提示词模板 |
| `config/` | Neo4j配置、依赖清单 |
| `data/` | 专利数据集(Excel)、提取结果(JSON)、分析报告 |
| `dowland/` | 下载的学术PDF论文（~50篇） |
| `sandbox/` | 原型/可视化工具（HTML图谱浏览器、Agent原型） |
| `docs/` | 架构设计文档、实施计划 |
| `examples/` | 示例/演示脚本 |
| `tests/` | 项目级测试 |
| `outputs/` | 管道输出产物 |

---

## 五、API与外部服务集成

| 服务 | 用途 | 模型/配置 |
|---|---|---|
| **阿里DashScope (Qwen)** | Strategist/Methodologist/Reviewer的默认LLM | `qwen3-max` |
| **Anthropic Claude**（via juheai.top聚合代理） | CodingAgent代码生成 + PDF知识提取 | `claude-sonnet-4-20250514` |
| **Neo4j** | 方法知识图谱存储 | `bolt://localhost:7687` |

**多模型策略**：Qwen用于规划/评审（成本低，中文好），Claude用于代码生成（编码能力强）。

---

## 六、离线知识图谱构建流程

### 流程1：因果图谱构建（V1/V3）
```
学术PDF → scripts/extract_causal_with_claude_v3.py（并行5线程，Claude API）
         → 每篇论文一个JSON → build_causal_graph() 聚合
         → causal_ontology_extracted.json
```

### 流程2：双图谱V2提取（较新）
```
单篇PDF → scripts/v2/extract_dual_graph_v2_from_pdf.py
         → 同时提取Graph A增量 + Graph B增量
         → scripts/v2/merge_dual_graph_v2.py 合并
         → causal_graph_v2.json + method_graph_v2.json
```

---

## 七、关键设计决策

1. **理论与方法分离**：因果关系（为什么）和测量/分析方法（怎么做）分属两个图谱，通过 `method_bridge` 接口连接，一个变量可有多种测量方法
2. **反平凡假设过滤**：自动过滤显而易见的假设（如"越老的专利引用越多"）
3. **DAG任务图**：任务有显式的input/output变量，拓扑排序验证+列名强制检查
4. **Schema感知**：向LLM提供实际Excel列名和语义描述，防止列名幻觉
5. **持久化REPL执行**：CodingAgent在持久Python进程中执行代码，支持增量修复
6. **变量映射器**：25个抽象变量(V01-V25)到具体专利数据字段的映射，包含Python计算代码

---

## 八、项目进度

根据 `docs/IMPLEMENTATION_PLAN.md`：

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 因果图谱构建 | **已完成** |
| Phase 2 | Strategist Agent | **已完成**（质量98.8%） |
| Phase 3 | Methodologist Agent | **已完成**（质量94%） |
| Phase 4 | Coding Agent | **已完成**（V4.2 + Claude集成） |
| Phase 5 | 优化（DataPreview等） | **进行中**（数据预览注入已完成，降级机制待开发） |

---

## 九、数据资产

- **主数据集**：`data/new_data.xlsx`（专利元数据）
- **因果提取结果**：`data/causal_extraction_v3/`（~50个JSON文件）
- **因果本体**：`sandbox/static/data/causal_ontology_extracted.json`（30变量，99路径）
- **方法知识库**：`sandbox/static/data/method_knowledge_base.json`（86+方法）
- **分析报告**：`data/` 下多个 `.md`/`.xlsx` 报告文件
- **学术论文**：`dowland/` 下约50篇PDF

