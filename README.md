# 专利分析多智能体系统

基于双知识图谱（因果图谱 + 方法图谱）的多智能体专利分析系统，支持从研究问题到分析代码与报告的端到端自动化。

## 核心能力

- 四 Agent 协作：`Strategist → Methodologist → CodingAgent → Reviewer`
- DAG 任务规划：显式输入/输出变量与依赖关系校验
- 数据感知规划：`DataPreview + GraphPreview + 数据洞察` 驱动任务设计
- 两轮迭代分析：第一轮探索，第二轮基于结果深入分析

## 当前数据资产（仓库内）

- 因果图谱：`src/graphs/data/causal/causal_ontology_extracted.json`
  - 变量数：30
  - 因果路径数：99
- 方法图谱：`src/graphs/data/method/method_knowledge_base.json`
  - 变量测量方法覆盖：28 个变量
  - 统计分析方法：86 种
- 主数据集：`data/new_data.XLSX`（`sheet1`）

## 关键目录

```text
patent_analysis/
├── src/
│   ├── agents/            # Strategist / Methodologist / CodingAgent / Reviewer
│   ├── core/              # LangGraph 工作流与状态定义
│   ├── graphs/            # 双图谱查询器与图谱数据
│   ├── tools/             # REPL 与系统工具
│   └── utils/             # DataPreview、GraphPreview、LLM 客户端等
├── tests/                 # 端到端与组件测试
├── scripts/               # 数据抽取/构建/报告脚本
├── data/                  # 输入数据与历史分析产物
├── outputs/               # 实验输出与运行结果
└── config/requirements.txt
```

## 安装

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# 或 Windows CMD
.venv\Scripts\activate.bat

pip install -r config/requirements.txt
```

## 环境变量

在项目根目录创建 `.env`：

```env
# 默认（Strategist / Methodologist / Reviewer）
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_key
DASHSCOPE_MODEL=qwen3-max

# Coding Agent 可单独配置（可选）
CODING_LLM_PROVIDER=anthropic
CODING_ANTHROPIC_API_KEY=your_key
CODING_ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
# 若走代理可配：CODING_ANTHROPIC_BASE_URL
```

## 快速运行

### 1) 单次端到端测试

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py
```

### 2) 四方案对比实验（D/A/B/C）

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py --compare
```

### 3) 仅运行纯 LLM 基线（D_baseline0）

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py --baseline0
```

### 4) 实验量化评估（自动指标 + LLM-as-Judge）

```bash
# 全量评估
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py

# 仅自动化指标
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py --auto-only

# 仅 LLM 评分
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py --llm-only
```

实验结果会写入 `outputs/experiment_*.json`、`outputs/experiment_summary.json`、`outputs/evaluation_*.json`。

## 主要文档

- `docs/PROJECT_OVERVIEW.md`：项目整体认知
- `docs/IMPLEMENTATION_PLAN.md`：实施计划与阶段记录
- `docs/项目进展记录.md`：近期迭代与实验结果
- `docs/EXPERIMENT_SUMMARY_TABLES.md`：论文可直接引用的实验总表
- `docs/DUAL_GRAPH_V2_ARCHITECTURE.md`：双图谱 V2 架构

## 备注

- Windows 控制台建议设置 `PYTHONIOENCODING=utf-8`，避免中文/emoji 编码问题。
- 若需要 Neo4j，仅在对应功能分支中启用，默认主流程使用本地 JSON 图谱即可运行。
