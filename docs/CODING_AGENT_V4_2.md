# Coding Agent V4.2 - 终端增强版

## 概述

Coding Agent V4.2 是 V4.1 的增强版本，融合了 V5 的终端和文件操作能力，同时保留了 V4.1 的所有核心功能。

## 核心特性

### 1. 🐍 有状态的 Python REPL

```python
# 第一次调用
run_python("x = 100")

# 第二次调用（变量 x 仍然存在）
run_python("print(x + 50)")  # 输出: 150
```

- 变量在多次调用间保持
- 适合逐步构建复杂分析
- 类似 Jupyter Notebook 的体验

### 2. 💻 Shell 命令执行

```python
execute_shell("ls outputs")           # 列出文件
execute_shell("mkdir test_outputs")   # 创建目录
execute_shell("pip install tabulate") # 安装包
execute_shell("cat data.csv | head")  # 查看文件
```

- 完整的终端访问权限
- 支持所有标准 Shell 命令
- 自动安全检查（拦截危险命令）

### 3. 📁 文件操作工具

```python
# 检查文件是否存在
check_file_exists("outputs/results.csv")

# 读取文件
content = read_file("data/input.txt", lines=10)

# 写入文件
write_file("outputs/report.txt", "分析结果...")
```

- 简化的文件 I/O 接口
- 自动创建目录
- 支持编码处理

### 4. 🔧 V4.1 核心功能（完全保留）

- ✅ 智能错误检测和恢复
- ✅ 重复错误识别（2次相同错误立即停止）
- ✅ 文件路径注入（从 execution_spec 提取）
- ✅ 输入数据源管理（依赖关系处理）
- ✅ 实际列名注入（避免"幻影列"）
- ✅ 错误类型识别和修复提示

## 工具列表

| 工具 | 功能 | 使用场景 |
|------|------|---------|
| `preview_data()` | 预览数据结构 | 了解列名和数据类型 |
| `run_python(code)` | 执行 Python 代码 | 数据分析、模型训练 |
| `execute_shell(cmd)` | 执行 Shell 命令 | 文件管理、包安装 |
| `read_file(path)` | 读取文件 | 查看配置、日志 |
| `write_file(path, content)` | 写入文件 | 保存报告、配置 |
| `check_file_exists(path)` | 检查文件存在性 | 验证依赖、输出 |

## 工作流程

### 标准分析任务流程

```
1. 环境准备
   ├─ execute_shell("mkdir outputs")
   └─ check_file_exists("data/input.xlsx")

2. 数据探索
   ├─ preview_data()
   └─ run_python("print(df.head())")

3. 逐步分析
   ├─ run_python("# 步骤1: 加载数据")
   ├─ run_python("# 步骤2: 数据清洗")
   ├─ run_python("# 步骤3: 特征工程")
   └─ run_python("# 步骤4: 模型训练")

4. 保存结果
   ├─ run_python("df.to_csv('outputs/results.csv')")
   └─ check_file_exists("outputs/results.csv")
```

## 与其他版本的对比

| 特性 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| 执行方式 | Subprocess | REPL | REPL |
| 状态管理 | 无状态 | 有状态 | 有状态 |
| Shell 命令 | ❌ | ✅ | ✅ |
| 文件操作 | ❌ | ✅ | ✅ |
| 错误检测 | ✅ | ✅ | ❌ |
| 路径注入 | ✅ | ✅ | ❌ |
| 依赖管理 | ✅ | ✅ | ❌ |
| 适用场景 | 生产流程 | 生产流程 | 探索任务 |

## 使用示例

### 示例 1: 基本数据分析

```python
from src.agents.coding_agent_v4_2 import CodingAgentV4_2
from src.utils.llm_client import LLMClient
import pandas as pd

# 初始化
client = LLMClient.from_env()
agent = CodingAgentV4_2(llm_client=client)

# 准备数据
test_data = pd.read_excel('data/patents.xlsx')

# 定义任务
task = {
    'execution_spec': {
        'function_name': 'analyze_trends',
        'description': '分析专利趋势，按年份统计数量',
        'inputs': ['df'],
        'outputs': ['yearly_counts']
    },
    'test_data': test_data
}

# 执行
result = agent.process(task)
print(result['generated_code'])
```

### 示例 2: 多步骤分析（带依赖）

```python
task = {
    'execution_spec': {
        'function_name': 'topic_analysis',
        'description': '基于前一步的主题结果，分析主题趋势',
        'inputs': ['df', 'previous_topics'],
        'outputs': ['topic_trends']
    },
    'test_data': test_data,
    'current_step': {
        'implementation_config': {
            'input_data_source': {
                'main_data': 'data/patents.xlsx',
                'main_data_columns': ['patent_id', 'year', 'title'],
                'dependencies': [
                    {
                        'file': 'outputs/step_1_topics.csv',
                        'columns': ['patent_id', 'topic_id'],
                        'description': '前一步的主题分类结果'
                    }
                ]
            },
            'output_files': {
                'results_csv': 'outputs/step_2_trends.csv',
                'results_columns': ['topic_id', 'year', 'count']
            }
        }
    }
}

result = agent.process(task)
```

### 示例 3: 错误恢复

```python
# Agent 会自动检测和修复错误
task = {
    'execution_spec': {
        'description': '统计每个类别的平均值'
    },
    'test_data': df_with_tricky_columns  # 列名有空格或特殊字符
}

result = agent.process(task)

# 查看错误历史
print(f"遇到 {len(result['error_history'])} 个错误")
for err in result['error_history']:
    print(f"- {err['type']}: {err['detail']}")
```

## 关键改进点

### 1. 小步执行策略

V4.2 采用"小步快跑"策略，不再生成一个完整的脚本，而是：

```python
# 步骤 1
run_python("""
import pandas as pd
df = pd.read_excel('data.xlsx')
print(f"数据加载: {df.shape}")
""")

# 步骤 2（基于步骤1的结果）
run_python("""
df_clean = df.dropna()
print(f"清洗后: {df_clean.shape}")
""")

# 步骤 3
run_python("""
result = df_clean.groupby('category').mean()
print(result)
""")
```

### 2. 环境自检能力

Agent 可以自己检查和准备环境：

```python
# 检查目录
execute_shell("ls outputs")

# 如果不存在，创建
execute_shell("mkdir outputs")

# 检查依赖包
run_python("import sklearn")  # 如果失败...

# 自动安装
execute_shell("pip install scikit-learn")
```

### 3. 智能错误恢复

```python
# 第1次尝试
run_python("df['Patent_ID'].mean()")  # KeyError

# Agent 自动：
# 1. 识别错误类型: KeyError
# 2. 查看实际列名: preview_data()
# 3. 修正代码

# 第2次尝试
run_python("df['patent_id'].mean()")  # 成功

# 如果第2次还是相同错误 → 立即停止，避免无限循环
```

## 最佳实践

### 1. 任务描述要清晰

```python
# ❌ 不好
'description': '分析数据'

# ✅ 好
'description': """
1. 加载主数据和前一步的主题结果
2. 按 patent_id 合并
3. 统计每个主题每年的专利数量
4. 保存到 outputs/topic_trends.csv
"""
```

### 2. 提供完整的配置信息

```python
'current_step': {
    'implementation_config': {
        'input_data_source': {
            'main_data': '明确的文件路径',
            'dependencies': [...]  # 明确的依赖关系
        },
        'output_files': {
            'results_csv': '明确的输出路径',
            'results_columns': [...]  # 明确的列名
        }
    }
}
```

### 3. 合理设置迭代次数

```python
# 简单任务
agent = CodingAgentV4_2(llm_client=client, max_iterations=10)

# 复杂任务
agent = CodingAgentV4_2(llm_client=client, max_iterations=20)
```

## 故障排查

### 问题 1: 重复错误

**现象**: Agent 一直报相同的错误

**原因**: 
- 列名不匹配
- 文件路径错误
- 数据类型问题

**解决**:
- 检查 `actual_columns` 是否正确
- 使用 `preview_data()` 确认数据结构
- 查看 `error_history` 了解错误模式

### 问题 2: 文件未保存

**现象**: 代码执行成功，但文件不存在

**原因**:
- 路径错误
- 目录不存在
- 权限问题

**解决**:
- 使用 `check_file_exists()` 验证
- 使用 `execute_shell("ls")` 查看目录
- 确保 `output_files` 配置正确

### 问题 3: 包导入失败

**现象**: `ModuleNotFoundError`

**解决**:
```python
# Agent 会自动：
execute_shell("pip install <package>")
```

## 总结

V4.2 = V4.1 的健壮性 + V5 的灵活性

- 适合生产环境的多步骤分析流程
- 保留了所有错误检测和恢复机制
- 增加了终端和文件操作能力
- 采用小步执行策略，更容易调试

**推荐使用场景**: 
- 当前 workflow 系统的核心 Coding Agent
- 需要可靠性和可审计性的分析任务
- 多步骤串联的复杂分析流程
