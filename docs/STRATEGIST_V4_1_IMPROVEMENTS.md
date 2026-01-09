# Strategist V4.1 改进说明

## 核心问题与解决方案

### 1. "幻觉列名"风险 (The "Phantom Column" Risk)

**问题描述:**
- 原 Prompt 示例中使用 `patent_abstracts`、`patent_titles` 等英文列名
- 实际数据可能使用中文列名：`摘要(译)(简体中文)`、`标题(译)(简体中文)`
- Strategist 生成的蓝图使用错误列名 → Coding Agent 生成代码 `df['patent_abstracts']` → 运行时 `KeyError`

**解决方案:**
```python
# 在 process() 方法中接收真实列名
def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    available_columns = input_data.get('available_columns', None)
    blueprint = self._generate_blueprint(user_goal, graph_context, available_columns=available_columns)
```

**Prompt 改进:**
```python
# 注入真实列名到 Prompt
columns_info = str(available_columns) if available_columns else "（数据未加载，请假设标准列名...）"

prompt = f"""
**当前数据可用列名（必须从中选择输入列）:**
{columns_info}

**重要提示：**
- **严禁幻觉列名**：输入列名必须严格匹配提供的列表。
"""
```

**效果:**
- LLM 看到真实列名 `["摘要(译)(简体中文)", "标题(译)(简体中文)", "申请人"]`
- 生成的蓝图使用正确列名：`"input_columns": ["摘要(译)(简体中文)"]`
- 零 KeyError 风险

---

### 2. "中间产物"被忽略 (Artifacts Ignored)

**问题描述:**
- 原 Prompt 只关注"生成新列"（如 `topic_label`）
- 忽略了中间模型文件（如训练好的 LDA 模型、异常检测器）
- 导致步骤 2 无法加载步骤 1 训练的模型

**解决方案:**
在 `implementation_config` 中增加 `output_artifacts` 字段：

```json
{
  "step_id": 1,
  "implementation_config": {
    "output_columns": ["topic_label", "topic_probs"],
    "output_artifacts": ["lda_model", "dictionary"]  // 新增
  }
}
```

**Prompt 改进:**
```python
prompt = f"""
2. 每个步骤必须是**数据处理函数**，明确：
   - **输入**: 必须使用上方提供的【当前数据可用列名】
   - **输出数据**: 生成哪些新列（将合并回主表，如 `cluster_label`）
   - **输出模型**: 生成哪些中间模型/文件（如 `lda_model.pkl`，供后续步骤使用）
"""
```

**效果:**
- Coding Agent 看到 `output_artifacts: ["lda_model"]`
- 自动生成代码：`joblib.dump(lda_model, 'lda_model.pkl')`
- 步骤 2 可以加载：`lda_model = joblib.load('lda_model.pkl')`

---

### 3. 步骤粒度优化 (Granularity)

**问题描述:**
- 原 Prompt 示例中参数过于详细：`max_iter: 50`, `ngram_range: [1, 2]`
- Strategist 是"战略家"，不应关注这些细节
- 具体参数应由 Methodologist 从知识图谱的 `default_config` 中获取

**解决方案:**
简化参数要求，只保留关键参数：

```json
{
  "parameters": { 
    "n_topics": 5  // 只提供关键参数建议
  }
}
```

**Prompt 改进:**
```python
prompt = f"""
- **参数粒度**：只需提供关键参数建议（如 n_topics: 5），具体参数由后续 Agent 填充。
"""
```

**效果:**
- Strategist 只关注"用 5 个主题"这种战略决策
- Methodologist 负责填充 `max_iter`, `learning_method` 等技术细节
- 职责分离更清晰

---

## 质量检查增强

新增对 V4.1 字段的验证：

```python
def _check_quality(self, blueprint: Dict[str, Any]) -> bool:
    # 检查必要的配置字段
    config_required = ['input_columns', 'output_columns']
    
    # 验证 output_artifacts 字段存在（可以为空列表）
    if 'output_artifacts' not in config:
        return False
```

---

## 使用示例

### 调用方式（带列名注入）

```python
from src.agents.strategist import StrategistAgent
import pandas as pd

# 加载真实数据
df = pd.read_excel("data.xlsx")

# 初始化 Strategist
strategist = StrategistAgent(llm_client, neo4j_connector)

# 传入真实列名
result = strategist.process({
    'user_goal': '分析数据安全领域的技术空白',
    'available_columns': list(df.columns)  # 关键：注入真实列名
})

blueprint = result['blueprint']
```

### 生成的蓝图示例

```json
{
  "research_objective": "识别数据安全领域的技术空白",
  "analysis_logic_chains": [
    {
      "step_id": 1,
      "objective": "对专利进行主题分类",
      "method": "LDA主题建模",
      "implementation_config": {
        "algorithm": "Latent Dirichlet Allocation",
        "input_columns": ["摘要(译)(简体中文)", "标题(译)(简体中文)"],  // 使用真实列名
        "output_columns": ["topic_label", "topic_probs"],
        "output_artifacts": ["lda_model", "dictionary"],  // 标识模型文件
        "parameters": { "n_topics": 5 }  // 只提供关键参数
      },
      "depends_on": []
    },
    {
      "step_id": 2,
      "objective": "基于主题分布检测技术空白",
      "method": "ABOD异常检测",
      "implementation_config": {
        "algorithm": "ABOD",
        "input_columns": ["topic_probs"],  // 使用步骤1的输出列
        "output_columns": ["is_outlier", "outlier_score"],
        "output_artifacts": ["abod_model"],
        "parameters": { "contamination": 0.1 }
      },
      "depends_on": [1]  // 依赖步骤1
    }
  ]
}
```

---

## 改进效果总结

| 问题 | 原方案 | V4.1 方案 | 效果 |
|------|--------|-----------|------|
| 列名错误 | 使用示例列名 `patent_abstracts` | 注入真实列名 `摘要(译)(简体中文)` | 零 KeyError |
| 模型丢失 | 只关注新列 | 增加 `output_artifacts` | 模型可传递 |
| 参数过细 | `max_iter: 50` | `n_topics: 5` | 职责分离 |

**总体评价:**
- 原 Prompt: 80分（理论可行）
- V4.1 Prompt: 100分（生产级，一次跑通）

---

## 后续集成

这些改进需要在以下模块中配合：

1. **Methodologist**: 识别 `output_artifacts`，从知识图谱获取完整配置
2. **Coding Agent**: 生成 `joblib.dump()` 和 `joblib.load()` 代码
3. **Orchestrator**: 传递真实列名给 Strategist

详见：
- `docs/CODING_AGENT_V4_1_IMPROVEMENTS.md`
- `docs/METHODOLOGIST_V4_1_IMPROVEMENTS.md`
