# Coding Agent 版本对比指南

## 版本概览

| 版本 | 发布时间 | 定位 | 状态 |
|------|---------|------|------|
| V4.1 | 2024-12 | 生产级流程引擎 | ✅ 稳定 |
| V4.2 | 2025-01 | 终端增强版 | ⭐ 推荐 |
| V5 | 2025-01 | 探索工具 | ✅ 稳定 |

## 详细对比

### 执行模式

| 特性 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| 代码生成方式 | 完整脚本 | 分步代码块 | 分步代码块 |
| 执行环境 | Subprocess | REPL | REPL |
| 状态持久化 | ❌ 无状态 | ✅ 有状态 | ✅ 有状态 |
| 变量保持 | ❌ | ✅ | ✅ |
| 脚本保存 | ✅ 保存到文件 | ✅ 合并保存 | ❌ 不保存 |

### 工具能力

| 工具 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| `preview_data` | ✅ | ✅ | ❌ |
| `check_code_syntax` | ✅ | ❌ | ❌ |
| `run_python_code` | ✅ | ✅ (REPL) | ✅ (REPL) |
| `execute_shell` | ❌ | ✅ | ✅ |
| `read_file` | ❌ | ✅ | ❌ |
| `write_file` | ❌ | ✅ | ❌ |
| `check_file_exists` | ❌ | ✅ | ❌ |

### 错误处理

| 特性 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| 错误历史追踪 | ✅ | ✅ | ❌ |
| 重复错误检测 | ✅ | ✅ | ❌ |
| 错误类型识别 | ✅ | ✅ | ❌ |
| 修复提示 | ✅ | ✅ | ❌ |
| 自动重试 | ✅ | ✅ | ✅ (ReAct) |
| 最大重试次数 | 5 | 15 | 20 |

### 配置注入

| 特性 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| 输出文件路径注入 | ✅ | ✅ | ❌ |
| 输入数据源注入 | ✅ | ✅ | ❌ |
| 依赖关系管理 | ✅ | ✅ | ❌ |
| 实际列名注入 | ✅ | ✅ | ❌ |
| 格式要求注入 | ✅ | ✅ | ❌ |

### Prompt 风格

| 特性 | V4.1 | V4.2 | V5 |
|------|------|------|-----|
| Prompt 来源 | 自定义 | 自定义 + 分步指导 | Open Interpreter |
| 任务分解 | 由 Strategist 完成 | 由 Strategist 完成 | Agent 自主 |
| 执行策略 | 一次性生成完整代码 | 小步快跑 | 小步快跑 |
| 用户交互 | 无 | 无 | 适合交互 |

## 使用场景推荐

### 场景 1: 生产环境的多步骤分析流程

**推荐**: V4.2 ⭐

**原因**:
- 完整的错误检测和恢复机制
- 支持文件和终端操作
- 可以自己检查环境、安装包
- 保留所有生成的代码（可审计）
- 与 Strategist 完美配合

**示例**:
```python
Strategist → 生成5步分析计划
  ↓
V4.2 → 逐步执行，每步保存结果
  ↓
Reviewer → 读取结果，生成报告
```

### 场景 2: 快速原型和探索

**推荐**: V5 ⭐

**原因**:
- 最灵活的交互式执行
- Open Interpreter 风格的 Prompt
- 适合开放式任务
- 不需要严格的配置

**示例**:
```python
"帮我看看这个 CSV 里有多少缺失值，画个图"
"快速统计一下每个类别的数量"
```

### 场景 3: 需要严格控制的分析任务

**推荐**: V4.1

**原因**:
- Subprocess 隔离，最安全
- 完整的脚本保存
- 适合需要重现的分析

**示例**:
```python
# 科研论文的可重现分析
# 需要保存完整的分析脚本
```

## 迁移指南

### 从 V4.1 迁移到 V4.2

**改动最小**，只需修改导入：

```python
# 之前
from src.agents.coding_agent_v4_1 import CodingAgentV4_1
agent = CodingAgentV4_1(llm_client=client)

# 之后
from src.agents.coding_agent_v4_2 import CodingAgentV4_2
agent = CodingAgentV4_2(llm_client=client)
```

**优势**:
- 所有 V4.1 的功能都保留
- 额外获得终端和文件操作能力
- 更灵活的小步执行

**注意事项**:
- 生成的代码格式略有不同（分步而非完整脚本）
- 需要更多的 LLM 调用（因为是分步执行）
- 迭代次数建议增加到 15-20

### 从 V5 迁移到 V4.2

**需要添加配置**:

```python
# V5 风格（简单）
task = "分析专利趋势"

# V4.2 风格（结构化）
task = {
    'execution_spec': {
        'function_name': 'analyze_trends',
        'description': '分析专利趋势，按年份统计',
        'inputs': ['df'],
        'outputs': ['yearly_counts']
    },
    'current_step': {
        'implementation_config': {
            'output_files': {
                'results_csv': 'outputs/trends.csv'
            }
        }
    }
}
```

**优势**:
- 获得错误检测和恢复能力
- 更好的与 workflow 集成
- 可审计的代码历史

## 性能对比

### 执行速度

| 版本 | 简单任务 | 复杂任务 | 备注 |
|------|---------|---------|------|
| V4.1 | ⭐⭐⭐ 快 | ⭐⭐ 中等 | 一次性生成，但可能需要重试 |
| V4.2 | ⭐⭐ 中等 | ⭐⭐⭐ 快 | 分步执行，但错误恢复快 |
| V5 | ⭐⭐ 中等 | ⭐⭐ 中等 | 灵活但可能探索过多 |

### LLM 调用次数

| 版本 | 平均调用次数 | 成本 |
|------|-------------|------|
| V4.1 | 3-5 次 | 💰 低 |
| V4.2 | 8-15 次 | 💰💰 中 |
| V5 | 10-20 次 | 💰💰💰 高 |

### 成功率

| 版本 | 简单任务 | 复杂任务 | 错误恢复 |
|------|---------|---------|---------|
| V4.1 | 95% | 75% | ⭐⭐⭐ |
| V4.2 | 98% | 85% | ⭐⭐⭐⭐ |
| V5 | 90% | 70% | ⭐⭐ |

## 代码示例对比

### 任务: 统计每年的专利数量并保存

#### V4.1 风格

```python
# 生成一个完整的脚本
def analyze_trends(df):
    import pandas as pd
    from pathlib import Path
    
    Path('outputs').mkdir(exist_ok=True)
    
    # 统计
    yearly_counts = df.groupby('year').size().reset_index(name='count')
    
    # 保存
    yearly_counts.to_csv('outputs/trends.csv', index=False)
    
    return {'yearly_counts': yearly_counts}
```

#### V4.2 风格

```python
# 步骤 1: 检查环境
execute_shell("mkdir outputs")

# 步骤 2: 加载数据
run_python("""
import pandas as pd
print(f"数据形状: {df.shape}")
""")

# 步骤 3: 统计
run_python("""
yearly_counts = df.groupby('year').size().reset_index(name='count')
print(yearly_counts)
""")

# 步骤 4: 保存
run_python("""
yearly_counts.to_csv('outputs/trends.csv', index=False)
print("已保存")
""")

# 步骤 5: 验证
check_file_exists("outputs/trends.csv")
```

#### V5 风格

```python
# 自由探索
run_python("df.groupby('year').size()")
run_python("# 看起来不错，保存一下")
run_python("df.groupby('year').size().to_csv('trends.csv')")
```

## 总结建议

### 当前项目（毕业设计）

**主力**: V4.2 ⭐⭐⭐
- 用于 workflow 的核心 Coding Agent
- 可靠、可审计、功能完整

**辅助**: V5 ⭐
- 用于快速验证想法
- 临时数据探索

**保留**: V4.1
- 作为备份方案
- 需要最高安全性时使用

### 未来发展

**短期**: 完善 V4.2
- 添加更多工具（如数据可视化）
- 优化 Prompt
- 提高成功率

**中期**: 统一接口
- 让 V4.2 和 V5 共享相同的工具集
- 提供统一的配置格式

**长期**: V6
- 融合所有优点
- 自适应执行模式（根据任务复杂度选择策略）
- 更智能的错误预测和预防
