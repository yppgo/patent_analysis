# 🚀 从这里开始！

## 欢迎使用 Patent-DeepScientist V2.0

这是一个基于 LangGraph 的三 Agent 协作系统，用于自动化专利分析代码生成。

## 📖 快速导航

### 🎯 我想立即开始使用

```bash
# 1. 运行快速启动脚本
python quick_start.py

# 2. 查看生成的结果
ls outputs/quick_start/
```

就这么简单！系统会自动：
- ✅ 创建示例数据
- ✅ 执行完整分析流程
- ✅ 生成可运行的代码
- ✅ 保存所有结果

### 📚 我想了解系统架构

阅读这些文档：
1. **[README_V2.md](README_V2.md)** - 项目概述和快速开始
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - 详细的系统架构
3. **[src/README.md](src/README.md)** - 完整的 API 文档

### 🧪 我想运行测试

```bash
# 运行交互式测试
python tests/test_three_agents.py

# 选择测试模式:
# 1. 测试 Strategist Agent
# 2. 测试 Methodologist Agent
# 3. 测试 Coding Agent V2
# 4. 测试完整工作流
# 5. 运行所有测试
```

### 💻 我想使用命令行

```bash
# 基本使用
python src/main.py "分析专利数据中的技术空白"

# 使用真实数据
python src/main.py "分析技术趋势" --data data/patents.csv

# 指定输出目录
python src/main.py "分析技术空白" --output outputs/my_analysis

# 查看帮助
python src/main.py --help
```

### 🐍 我想使用 Python API

```python
from src import (
    StrategistAgent,
    MethodologistAgent,
    CodingAgentV2,
    build_full_workflow,
    get_llm_client,
    Neo4jConnector
)

# 初始化
llm = get_llm_client()
neo4j = Neo4jConnector()

strategist = StrategistAgent(llm, neo4j)
methodologist = MethodologistAgent(llm)
coding_agent = CodingAgentV2(llm, test_data=df)

# 构建工作流
workflow = build_full_workflow(strategist, methodologist, coding_agent)

# 执行
result = workflow.invoke({
    'user_goal': '分析专利数据中的技术空白',
    'test_data': df,
    'blueprint': {},
    'graph_context': '',
    'execution_specs': [],
    'generated_codes': [],
    'code_metadata': []
})
```

### 🔧 我需要配置环境

1. **安装依赖**
   ```bash
   pip install -r config/requirements.txt
   ```

2. **配置 .env 文件**
   ```env
   # LLM 配置
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4
   
   # Neo4j 配置（可选）
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **运行快速启动**
   ```bash
   python quick_start.py
   ```

### 🆕 我从旧版本迁移

阅读迁移指南：
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - 完整的迁移指南
- **[VERSION.md](VERSION.md)** - 版本变更说明

### ❓ 我遇到了问题

1. **查看文档**
   - [README_V2.md](README_V2.md) - 常见问题
   - [CHECKLIST.md](CHECKLIST.md) - 故障排除

2. **运行测试**
   ```bash
   python tests/test_three_agents.py
   ```

3. **查看日志**
   - 检查控制台输出
   - 查看生成的文件

## 🎯 系统概览

### 三个 Agent

```
用户目标
    ↓
┌─────────────────────────────────────────────────────────┐
│                    LangGraph 工作流                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐      ┌────────┐│
│  │ Strategist   │  →   │ Methodologist│  →   │ Coding ││
│  │ (战略家)     │      │ (方法论家)    │      │ (执行者)││
│  └──────────────┘      └──────────────┘      └────────┘│
│       ↓                      ↓                     ↓    │
│   战略蓝图              执行规格              Python代码 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 核心特性

- ✅ **模块化设计** - 清晰的职责分离
- ✅ **运行时测试** - 自动测试生成的代码
- ✅ **自动修复** - 发现问题自动改进
- ✅ **知识增强** - 使用 Neo4j 知识图谱
- ✅ **完善文档** - 详细的使用指南

## 📊 快速示例

### 输入
```
"分析专利数据中的技术空白"
```

### 输出
```python
def detect_technology_gaps(df: pd.DataFrame) -> Dict[str, Any]:
    """检测技术空白"""
    try:
        # 数据预处理
        features = df[['citations', 'year']].values
        
        # ABOD 检测
        clf = ABOD(n_neighbors=5)
        labels = clf.fit_predict(features)
        
        # 返回结果
        return {
            'gaps': df[labels == 1],
            'statistics': {...}
        }
    except Exception as e:
        return {'error': str(e)}
```

## 📚 完整文档列表

### 必读文档
1. **[README_V2.md](README_V2.md)** ⭐⭐⭐⭐⭐
   - 项目概述
   - 快速开始
   - 使用方法

2. **[quick_start.py](quick_start.py)** ⭐⭐⭐⭐⭐
   - 快速启动脚本
   - 完整示例

### 详细文档
3. **[src/README.md](src/README.md)** ⭐⭐⭐⭐
   - API 文档
   - 使用指南
   - 扩展方法

4. **[ARCHITECTURE.md](ARCHITECTURE.md)** ⭐⭐⭐⭐
   - 系统架构
   - 设计原则
   - 扩展点

### 重构相关
5. **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** ⭐⭐⭐
   - 重构总结
   - 迁移指南
   - 对比分析

6. **[REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)** ⭐⭐⭐
   - 完成说明
   - 成果展示
   - 使用指南

### 其他文档
7. **[CHECKLIST.md](CHECKLIST.md)** ⭐⭐
   - 检查清单
   - 测试建议
   - 故障排除

8. **[VERSION.md](VERSION.md)** ⭐⭐
   - 版本历史
   - 变更日志
   - 迁移指南

9. **[重构完成总结.md](重构完成总结.md)** ⭐⭐
   - 完整总结
   - 文件清单
   - 统计数据

## 🎊 开始使用吧！

选择你的方式：

### 方式 1: 快速启动（推荐新手）
```bash
python quick_start.py
```

### 方式 2: 命令行（推荐日常使用）
```bash
python src/main.py "你的分析目标"
```

### 方式 3: Python API（推荐开发者）
```python
from src import build_full_workflow, get_llm_client
# ... 详见上文
```

### 方式 4: 测试模式（推荐学习）
```bash
python tests/test_three_agents.py
```

## 💡 提示

- 🚀 **第一次使用？** 运行 `python quick_start.py`
- 📖 **想了解更多？** 阅读 [README_V2.md](README_V2.md)
- 🐛 **遇到问题？** 查看 [CHECKLIST.md](CHECKLIST.md)
- 🔧 **想扩展？** 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)

## 🙏 需要帮助？

1. 查看文档（上面列出的）
2. 运行测试（`python tests/test_three_agents.py`）
3. 查看示例（`quick_start.py`）
4. 提交 Issue（GitHub）

---

**版本**: 2.0.0  
**状态**: ✅ 生产就绪  
**开始使用**: `python quick_start.py`

🎉 **祝使用愉快！** 🎉
