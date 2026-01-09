# 基于文件的架构设计 (File-Based Architecture)

## 核心理念

**每个生成的代码都是完全独立的 Python 脚本**，通过文件系统进行数据传递，而不是内存中的变量传递。

## 为什么要这样设计？

### 问题：内存传递的复杂性

原来的设计：
```python
# 步骤 1: 生成函数
def step_1(df):
    # 训练模型
    lda_model = train_lda(df)
    topic_labels = predict(lda_model, df)
    return {'topic_labels': topic_labels, 'model': lda_model}

# 步骤 2: 需要接收步骤1的返回值
def step_2(df, previous_result):
    lda_model = previous_result['model']  # 从内存获取
    topic_labels = previous_result['topic_labels']
    # ...
```

**问题：**
1. 需要复杂的变量传递机制
2. 模型对象无法序列化（如 NetworkX 图）
3. 调试困难（无法单独运行某一步）
4. 内存占用大（所有中间结果都在内存）

### 解决方案：文件传递

新设计：
```python
# step_1.py - 完全独立的脚本
import pandas as pd
import joblib

# 1. 加载数据
df = pd.read_excel('data/patents.xlsx')

# 2. 训练模型
lda_model = train_lda(df)
topic_labels = predict(lda_model, df)

# 3. 保存结果
pd.DataFrame({'topic_labels': topic_labels}).to_csv('outputs/step_1_results.csv')
joblib.dump(lda_model, 'outputs/step_1_model.pkl')
print("✅ 步骤1完成")
```

```python
# step_2.py - 完全独立的脚本
import pandas as pd
import joblib

# 1. 加载数据
df = pd.read_excel('data/patents.xlsx')
step_1_results = pd.read_csv('outputs/step_1_results.csv')
lda_model = joblib.load('outputs/step_1_model.pkl')

# 2. 合并数据
df = df.merge(step_1_results, left_index=True, right_index=True)

# 3. 使用模型
outliers = detect_outliers(df['topic_labels'])

# 4. 保存结果
pd.DataFrame({'is_outlier': outliers}).to_csv('outputs/step_2_results.csv')
print("✅ 步骤2完成")
```

**优势：**
1. ✅ 每个脚本可以独立运行：`python step_1.py`
2. ✅ 调试简单：直接查看 `outputs/step_1_results.csv`
3. ✅ 可恢复：步骤1失败不影响步骤2重新运行
4. ✅ 可并行：独立步骤可以同时运行
5. ✅ 内存友好：不需要在内存中保留所有中间结果

---

## 架构设计

### 1. Strategist 的输出格式

Strategist 生成的蓝图明确指定文件路径：

```json
{
  "step_id": 1,
  "objective": "主题分类",
  "implementation_config": {
    "input_data_source": {
      "main_data": "data/clean_patents1_with_topics_filled.xlsx",
      "main_data_columns": ["摘要(译)(简体中文)", "标题(译)(简体中文)"],
      "dependencies": []
    },
    "output_files": {
      "results_csv": "outputs/step_1_topic_results.csv",
      "results_columns": ["topic_label", "topic_probs"],
      "model_pkl": "outputs/step_1_lda_model.pkl",
      "model_objects": ["lda_model", "dictionary"]
    }
  }
}
```

### 2. Coding Agent 的代码生成

Coding Agent 根据蓝图生成完整的脚本：

```python
# 自动生成的 step_1.py

import pandas as pd
import joblib
from pathlib import Path
from gensim import corpora, models

# 确保输出目录存在
Path('outputs').mkdir(exist_ok=True)

print("📊 步骤1: 主题分类")
print("-" * 60)

# 1. 加载主数据
print("1️⃣ 加载数据...")
df = pd.read_excel('data/clean_patents1_with_topics_filled.xlsx', sheet_name='clear')
print(f"   ✅ 加载 {len(df)} 条专利")

# 2. 数据预处理
print("2️⃣ 预处理文本...")
texts = (df['摘要(译)(简体中文)'] + ' ' + df['标题(译)(简体中文)']).tolist()
processed_texts = [text.lower().split() for text in texts]
print(f"   ✅ 处理完成")

# 3. 训练 LDA 模型
print("3️⃣ 训练 LDA 模型...")
dictionary = corpora.Dictionary(processed_texts)
corpus = [dictionary.doc2bow(text) for text in processed_texts]
lda_model = models.LdaModel(corpus, num_topics=5, id2word=dictionary, passes=10)
print(f"   ✅ 模型训练完成")

# 4. 预测主题
print("4️⃣ 预测主题...")
topic_labels = []
topic_probs = []
for doc in corpus:
    topics = lda_model[doc]
    # 获取最可能的主题
    main_topic = max(topics, key=lambda x: x[1])[0]
    topic_labels.append(main_topic)
    # 获取所有主题的概率分布
    probs = [0.0] * 5
    for topic_id, prob in topics:
        probs[topic_id] = prob
    topic_probs.append(probs)
print(f"   ✅ 预测完成")

# 5. 保存结果
print("5️⃣ 保存结果...")

# 保存新列
results_df = pd.DataFrame({
    'topic_label': topic_labels,
    'topic_probs': topic_probs
})
results_df.to_csv('outputs/step_1_topic_results.csv', index=False)
print(f"   ✅ 结果已保存: outputs/step_1_topic_results.csv")

# 保存模型
joblib.dump(lda_model, 'outputs/step_1_lda_model.pkl')
joblib.dump(dictionary, 'outputs/step_1_dictionary.pkl')
print(f"   ✅ 模型已保存: outputs/step_1_lda_model.pkl")

print("-" * 60)
print("✅ 步骤1完成！")
```

### 3. 步骤间的依赖关系

**串行依赖示例：**

```json
{
  "step_id": 2,
  "objective": "异常检测",
  "implementation_config": {
    "input_data_source": {
      "main_data": "data/clean_patents1_with_topics_filled.xlsx",
      "main_data_columns": [],
      "dependencies": [
        {
          "file": "outputs/step_1_topic_results.csv",
          "columns": ["topic_probs"],
          "description": "步骤1生成的主题概率分布"
        }
      ]
    }
  }
}
```

生成的代码：

```python
# step_2.py

import pandas as pd
import joblib
from pyod.models.abod import ABOD

# 1. 加载主数据
df = pd.read_excel('data/clean_patents1_with_topics_filled.xlsx', sheet_name='clear')

# 2. 加载步骤1的结果
step_1_results = pd.read_csv('outputs/step_1_topic_results.csv')
df = df.merge(step_1_results, left_index=True, right_index=True)

# 3. 使用 topic_probs 进行异常检测
# ...
```

---

## 文件命名规范

### 结果文件
- 格式：`outputs/step_{step_id}_{description}_results.csv`
- 示例：
  - `outputs/step_1_topic_results.csv`
  - `outputs/step_2_outlier_results.csv`
  - `outputs/step_3_keywords_results.csv`

### 模型文件
- 格式：`outputs/step_{step_id}_{model_name}_model.pkl`
- 示例：
  - `outputs/step_1_lda_model.pkl`
  - `outputs/step_1_dictionary.pkl`
  - `outputs/step_2_abod_model.pkl`

### 主数据
- 固定路径：`data/clean_patents1_with_topics_filled.xlsx`
- Sheet 名：`clear`

---

## 优势总结

| 特性 | 内存传递 | 文件传递 |
|------|---------|---------|
| 独立运行 | ❌ 需要完整流程 | ✅ 每个脚本独立 |
| 调试难度 | ❌ 需要断点调试 | ✅ 直接查看文件 |
| 可恢复性 | ❌ 失败需重跑全部 | ✅ 从失败步骤继续 |
| 并行执行 | ❌ 必须串行 | ✅ 独立步骤可并行 |
| 内存占用 | ❌ 所有结果在内存 | ✅ 按需加载 |
| 代码复杂度 | ❌ 需要传递机制 | ✅ 简单直接 |
| 可读性 | ❌ 函数调用链 | ✅ 清晰的脚本 |

---

## 实现细节

### Strategist 改进

1. **输入数据源结构化**：
   ```json
   "input_data_source": {
     "main_data": "文件路径",
     "main_data_columns": ["列名1", "列名2"],
     "dependencies": [
       {"file": "依赖文件", "columns": ["列名"]}
     ]
   }
   ```

2. **输出文件结构化**：
   ```json
   "output_files": {
     "results_csv": "结果文件路径",
     "results_columns": ["新列名1", "新列名2"],
     "model_pkl": "模型文件路径",
     "model_objects": ["模型对象名"]
   }
   ```

### Coding Agent 改进

1. **生成完整脚本**（不是函数）
2. **包含数据加载代码**
3. **包含结果保存代码**
4. **添加进度打印**
5. **使用 joblib 保存模型**

### 执行方式

```bash
# 串行执行
python outputs/step_1.py
python outputs/step_2.py
python outputs/step_3.py

# 或并行执行（如果步骤独立）
python outputs/step_1.py &
python outputs/step_3.py &
wait
python outputs/step_2.py
```

---

## 未来扩展

1. **任务调度器**：自动识别依赖关系，并行执行独立步骤
2. **缓存机制**：检测文件是否已存在，跳过已完成步骤
3. **版本控制**：为每次运行创建时间戳目录
4. **可视化**：生成依赖关系图（DAG）

---

## 总结

基于文件的架构让系统更加：
- **简单**：每个脚本都是独立的
- **可靠**：失败可恢复
- **灵活**：可以手动修改中间结果
- **透明**：所有中间结果都可见

这是一个更符合实际使用场景的设计！
