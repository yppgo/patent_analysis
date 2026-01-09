# 专利分析智能体系统

基于LangGraph的多智能体协作系统，用于自动化专利数据分析。

## 🌟 特性

- **多智能体协作**：Strategist、Methodologist、Coding Agent、Reviewer四个智能体协同工作
- **知识图谱驱动**：从Neo4j知识图谱检索最佳实践
- **自动代码生成**：根据分析需求自动生成Python代码
- **执行即迭代**：代码生成后立即执行，失败自动重试
- **方案多样性**：支持生成不同的分析方案，避免固定模式

## 📁 项目结构

```
.
├── src/
│   ├── agents/          # 智能体实现
│   │   ├── strategist.py
│   │   ├── methodologist.py
│   │   ├── coding_agent_v4_2.py
│   │   └── reviewer.py
│   ├── core/            # 核心工作流
│   │   ├── workflow.py
│   │   └── state.py
│   ├── tools/           # 工具集
│   │   ├── repl.py
│   │   └── os_tools.py
│   └── utils/           # 工具函数
│       └── llm_client.py
├── config/              # 配置文件
├── docs/                # 文档
├── examples/            # 示例代码
├── tests/               # 测试文件
└── sandbox/             # 沙盒环境

```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# LLM配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_base_url

# Neo4j配置（可选）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 运行测试

```bash
python test_full_system_with_real_data.py
```

## 🏗️ 架构设计

### 工作流

```
用户目标
  ↓
Strategist (战略规划)
  ↓
Methodologist (方法设计)
  ↓
Coding Agent (代码生成与执行)
  ↓
Reviewer (结果审查)
  ↓
最终报告
```

### 智能体职责

- **Strategist**：理解用户目标，从知识图谱检索相关案例，生成分析蓝图
- **Methodologist**：为每个分析步骤设计具体的执行方案
- **Coding Agent**：根据执行方案生成Python代码并执行，支持自动重试
- **Reviewer**：验证分析结果，生成最终报告

## 📊 核心功能

### 1. 输出优化

- 只保存ID列和新生成的列，减少95%存储空间
- 自动检测多列展开需求
- 智能合并依赖数据

### 2. 方案多样性

- 提高LLM temperature实现方案多样化
- 抽象化示例避免固定模式
- 支持不同的分析方法组合

### 3. 错误处理

- 自动检测和修复常见错误
- 重复错误识别和提示
- 最多3次重试机制

## 📝 文档

- [Coding Agent V4.2 文档](docs/CODING_AGENT_V4_2_README.md)
- [输出优化说明](docs/OUTPUT_OPTIMIZATION.md)
- [方案多样性改进](docs/DIVERSITY_IMPROVEMENT.md)
- [版本对比](docs/CODING_AGENT_VERSIONS_COMPARISON.md)

## 🔧 开发

### 运行测试

```bash
# 完整系统测试
python test_full_system_with_real_data.py

# 单元测试
python -m pytest tests/
```

### 代码风格

项目遵循PEP 8规范。

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

## 📮 联系方式

- Email: 736698755@qq.com
