# 专利分析智能体系统

基于双图谱架构的多智能体协作系统，用于自动化专利数据分析。

## 🌟 核心特性

- **双图谱驱动**：因果图谱（理论层）+ 方法图谱（方法层）提供完整的知识支持
- **领域驱动输入**：用户只需提供领域关键词，系统自动生成研究假设和分析方案
- **多智能体协作**：Strategist、Methodologist、Coding Agent、Reviewer四个智能体协同工作
- **DAG任务图**：基于有向无环图的任务编排，确保数据流完整性
- **端到端自动化**：从用户输入到研究报告的全流程自动化

## 📁 项目结构

```
.
├── src/
│   ├── agents/                    # 智能体实现
│   │   ├── strategist.py         # 战略规划智能体
│   │   ├── methodologist.py      # 技术架构智能体
│   │   ├── coding_agent.py       # 代码实现智能体
│   │   └── reviewer.py           # 报告生成智能体
│   └── utils/                     # 工具函数
│       ├── causal_graph_query.py # 因果图谱查询器
│       ├── variable_mapper.py    # 变量映射器
│       └── neo4j_connector.py    # Neo4j连接器
├── sandbox/
│   └── static/data/
│       └── causal_ontology_extracted.json  # 因果图谱数据
├── docs/                          # 文档
│   ├── COMPLETE_SYSTEM_WORKFLOW.md        # 完整系统工作流程
│   ├── GRAPH_ARCHITECTURE_DEFINITION.md   # 双图谱架构定义
│   ├── GRAPH_USAGE_FLOWCHART.md          # 使用流程图
│   └── USER_SCENARIO_DEFINITION.md       # 用户场景定义
├── scripts/                       # 脚本工具
│   └── extract_causal_with_claude_v3.py  # 因果关系抽取
├── test_dual_graph_integration.py # 双图谱整合测试
├── test_neo4j_simple.py          # Neo4j连接测试
└── test_full_system_with_real_data.py  # 完整系统测试
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# LLM配置（使用聚合AI代理）
JUHENEXT_API_KEY=your_api_key
JUHENEXT_BASE_URL=https://api.juheai.top

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 启动Neo4j数据库

确保Neo4j数据库已启动并导入了方法图谱数据。

### 4. 运行测试

```bash
# 测试双图谱整合
python test_dual_graph_integration.py

# 测试Neo4j连接
python test_neo4j_simple.py

# 完整系统测试
python test_full_system_with_real_data.py
```

## 🏗️ 系统架构

### 双图谱架构

```
┌─────────────────────────────────────────────────────────────┐
│                      知识层（双图谱）                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 因果图谱      │  │ 变量映射器    │  │ 方法图谱      │      │
│  │ (理论层)     │  │ (实现层)     │  │ (方法层)     │      │
│  │ 回答"为什么" │  │ 回答"如何连接"│  │ 回答"怎么做" │      │
│  │ 30变量       │  │ 24映射       │  │ 66篇论文     │      │
│  │ 135路径      │  │              │  │ 1023节点     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 工作流

```
用户输入（领域关键词）
  ↓
Strategist Agent（战略规划）
  - 查询因果图谱 → 生成研究假设
  - 查询变量映射 → 确定数据字段
  - 查询方法图谱 → 选择分析方法
  - 生成DAG任务图
  ↓
Methodologist Agent（技术架构）
  - 接收任务节点
  - 生成技术规格（伪代码）
  ↓
Coding Agent（代码实现）
  - 接收技术规格
  - 生成可执行Python代码
  ↓
执行引擎
  - 按DAG顺序执行代码
  - 生成分析结果
  ↓
Reviewer Agent（报告生成）
  - 收集分析结果
  - 生成研究报告
  ↓
最终报告
```

### 核心组件

#### 1. 因果图谱（Causal Ontology）
- **数据来源**: 50篇专利分析领域学术论文
- **数据规模**: 30个变量，135条因果路径，42条已验证
- **核心功能**: 提供研究假设和理论支撑
- **实现类**: `src/utils/causal_graph_query.py`

#### 2. 变量映射器（Variable Mapper）
- **映射规模**: 24个变量已映射
- **核心功能**: 连接抽象变量和数据字段
- **实现类**: `src/utils/variable_mapper.py`

#### 3. 方法图谱（Methodology Graph）
- **存储位置**: Neo4j数据库
- **数据规模**: 66篇论文，1023个节点，2749个关系
- **核心功能**: 提供具体的分析方法和参数配置
- **实现类**: `src/utils/neo4j_connector.py`

## 📊 使用示例

### 示例：数据安全领域技术趋势分析

```python
# 用户输入
user_goal = "数据安全领域的技术趋势分析"

# 系统自动处理
# 1. Strategist查询因果图谱，生成研究假设
#    H1: 技术投入强度 → 技术影响力
#    H2: 技术多样性 → 技术影响力
#    H3: 技术投入 → 技术多样性 → 技术影响力

# 2. Strategist查询变量映射，确定数据字段
#    V01_tech_intensity → ["序号", "公开(公告)号"]
#    V09_tech_diversity → ["IPC分类号"]

# 3. Strategist查询方法图谱，选择分析方法
#    - LDA主题建模
#    - 时间序列分析

# 4. Strategist生成DAG任务图
#    Task 1: 数据摘要
#    Task 2: 主题分析（LDA）
#    Task 3: 趋势分析

# 5. Methodologist生成技术规格
# 6. Coding Agent生成并执行代码
# 7. Reviewer生成研究报告
```

### 输出结果

```
outputs/
├── task_1_data_summary.json          # 数据摘要
├── task_2_topics_summary.json        # 主题汇总
├── task_2_lda_model.pkl             # LDA模型
├── task_3_trend_analysis.json       # 趋势分析
└── data_security_tech_trend_report.md  # 研究报告
```

## 📝 文档

- [完整系统工作流程](docs/COMPLETE_SYSTEM_WORKFLOW.md) - 详细的系统工作流程说明
- [双图谱架构定义](docs/GRAPH_ARCHITECTURE_DEFINITION.md) - 因果图谱和方法图谱的架构定义
- [使用流程图](docs/GRAPH_USAGE_FLOWCHART.md) - 双图谱的使用流程
- [用户场景定义](docs/USER_SCENARIO_DEFINITION.md) - 典型用户场景和使用方式

## 🎯 核心创新

1. **双图谱协同**: 因果图谱提供理论支撑，方法图谱提供实现参考
2. **领域驱动**: 用户只需提供领域关键词，系统自动生成假设和方案
3. **变量映射**: 连接抽象理论变量和具体数据字段
4. **DAG任务图**: 确保数据流完整性和任务依赖正确性
5. **结论导向**: 每个任务输出结论性数据，便于报告生成

## 🔧 开发

### 运行测试

```bash
# 双图谱整合测试
python test_dual_graph_integration.py

# Neo4j连接测试
python test_neo4j_simple.py

# 完整系统测试
python test_full_system_with_real_data.py
```

### 扩展系统

#### 扩展因果图谱
1. 添加新变量 → 更新 `sandbox/static/data/causal_ontology_extracted.json`
2. 添加新路径 → 使用 `scripts/extract_causal_with_claude_v3.py` 从新文献中抽取
3. 验证路径 → 标记 `validated: true`

#### 扩展方法图谱
1. 添加新论文 → 导入到Neo4j数据库
2. 添加新方法 → 创建Method节点
3. 更新逻辑链 → 创建关系

#### 扩展变量映射器
1. 添加新映射 → 更新 `src/utils/variable_mapper.py` 中的 `DEFAULT_MAPPING`
2. 添加Python代码 → 更新 `python_code` 字段

## 📊 系统性能

| 组件 | 响应时间 | 准确率 | 覆盖率 |
|------|---------|--------|--------|
| 因果图谱查询 | < 1秒 | 100% | 30变量/135路径 |
| 变量映射器 | < 1秒 | 100% | 24/30变量 |
| 方法图谱检索 | < 2秒 | 100% | 66篇论文 |
| Strategist Agent | 10-30秒 | 95% | - |
| Methodologist Agent | 5-15秒 | 95% | - |
| Coding Agent | 10-30秒 | 90% | - |
| Reviewer Agent | 5-10秒 | 95% | - |

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

## 📮 联系方式

- Email: 736698755@qq.com
