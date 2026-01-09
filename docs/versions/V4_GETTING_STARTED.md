# V4.0 快速开始指南

## 🎯 5 分钟快速体验 V4.0

### 步骤 1: 运行测试（2 分钟）

**Windows 用户:**
```bash
run_v4_test.bat
```

**Linux/Mac 用户:**
```bash
chmod +x run_v4_test.sh
./run_v4_test.sh
```

### 步骤 2: 查看输出（1 分钟）

测试会展示三个核心功能：

1. **意图转译测试**
   ```
   输入: 分析固态电池的技术空白
   关键词: 技术空白, 识别, 聚类
   ```

2. **配置提取测试**
   ```
   案例 1:
     论文: 3GPP URLLC patent analysis
     方法: Technology Cycle Time
     配置: {"library": "NetworkX", "params": "..."}
     指标: TCT < 5年
   ```

3. **完整工作流测试**
   ```
   迭代次数: 1
   质量检查: ✅ 通过
   评价: 质量检查通过 (5/5)
   ```

### 步骤 3: 阅读文档（2 分钟）

**快速了解:**
```bash
# 打开快速参考卡片
V4_QUICK_REFERENCE.md
```

**深入理解:**
```bash
# 查看对比示例
V4_BEFORE_AFTER_EXAMPLE.md
```

---

## 📚 完整学习路径

### 路径 A: 快速上手（15 分钟）
1. ✅ 运行 `run_v4_test.bat` - 看实际效果
2. ✅ 阅读 `V4_QUICK_REFERENCE.md` - 了解核心改进
3. ✅ 运行 `python strategist_graph.py` - 完整体验

### 路径 B: 深入理解（1 小时）
1. ✅ 阅读 `V4_BEFORE_AFTER_EXAMPLE.md` - 看对比
2. ✅ 阅读 `V4_OPTIMIZATION_SUMMARY.md` - 理解技术
3. ✅ 查看 `strategist_graph.py` 源码 - 学习实现

### 路径 C: 开发维护（2 小时）
1. ✅ 阅读 `CHANGELOG_V4.md` - 了解所有变更
2. ✅ 运行 `test_v4_optimization.py` - 深入测试
3. ✅ 修改代码并测试 - 自定义优化

---

## 🎓 核心概念速览

### 1. 意图转译 (Intent Translation)
**一句话**: 把人话变成机器能搜的关键词

**示例**:
- 输入: "找蓝海"
- 转译: ["空白", "聚类", "未被利用"]
- 效果: 检索命中率 ↑ 3x

### 2. 详细配置提取 (Config & Metrics)
**一句话**: 不仅告诉你用什么方法，还告诉你怎么用

**示例**:
- V3.0: "使用数据分析"
- V4.0: `{"library": "Gensim", "params": "min_count=5"}`
- 效果: 可直接写代码

### 3. 跨域迁移 (Transfer Learning)
**一句话**: 把 5G 的方法用到电池上

**示例**:
- 图谱: 3GPP 用 TCT 分析通信
- 迁移: 用 TCT 分析固态电池
- 效果: 真正的"举一反三"

### 4. 质量检查 (Quality Check)
**一句话**: 自动检查方案质量，不合格重来

**示例**:
- 检查: 有 config? 有 metrics? 有 reasoning?
- 不合格: 重新生成（最多 2 次）
- 效果: 输出质量有保证

---

## 🔧 实际使用示例

### 示例 1: 分析新兴技术

```python
from strategist_graph import build_graph

app = build_graph()

result = app.invoke({
    "user_goal": "分析固态电池的技术空白",
    "graph_context": "",
    "generated_idea": {},
    "critique": "",
    "quality_passed": False,
    "iteration_count": 0
})

print(result['generated_idea'])
```

**输出**:
```json
{
  "hypothesis": "固态电池技术存在材料-工艺组合空白",
  "reference_case": "参考《3GPP》的 TCT 方法",
  "method_plan": {
    "config": {"library": "NetworkX", "params": "..."},
    "target_metric": "TCT < 5年"
  },
  "reasoning": "3GPP 用 TCT 分析通信，固态电池同样需要..."
}
```

### 示例 2: 批量处理

```python
goals = [
    "分析固态电池的技术空白",
    "研究人工智能在专利分析中的应用",
    "探索区块链技术的专利布局策略"
]

for goal in goals:
    result = app.invoke({
        "user_goal": goal,
        "graph_context": "",
        "generated_idea": {},
        "critique": "",
        "quality_passed": False,
        "iteration_count": 0
    })
    
    # 保存结果
    with open(f"result_{goal[:10]}.json", 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
```

---

## 🐛 常见问题

### Q1: 测试失败怎么办？

**检查清单**:
1. ✅ Neo4j 服务是否运行？
   ```bash
   python test_neo4j_connection.py
   ```

2. ✅ API Key 是否配置？
   ```bash
   python test_api_key.py
   ```

3. ✅ 虚拟环境是否激活？
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

### Q2: 输出质量不满意？

**调整方法**:
1. 修改质量检查标准（`critique_node` 函数）
2. 调整 Prompt（`generate_node` 函数）
3. 增加检索关键词数量（`retrieve_node` 函数）

### Q3: 执行太慢？

**优化方法**:
1. 减少检索关键词数量（2-3 个 → 1-2 个）
2. 降低检索 limit（3 → 2）
3. 关闭质量检查（跳过 `critic` 节点）

### Q4: 如何自定义？

**修改位置**:
- 意图转译 Prompt: `retrieve_node` 第 155 行
- 跨域迁移 Prompt: `generate_node` 第 210 行
- 质量检查标准: `critique_node` 第 290 行
- 最大重试次数: `should_regenerate` 第 330 行

---

## 📊 性能对比

| 场景 | V3.0 | V4.0 | 提升 |
|------|------|------|------|
| 新兴技术分析 | ❌ 搜不到 | ✅ 找到 5 个案例 | **质变** |
| 方案可执行性 | ❌ 抽象描述 | ✅ 具体配置 | **质变** |
| 跨域迁移 | ❌ 无 | ✅ 有 | **新增** |
| 质量保证 | ❌ 无 | ✅ 自动检查 | **新增** |
| 执行时间 | 5s | 8s | +60% |

---

## 🎉 下一步

### 立即体验
```bash
# Windows
run_v4_test.bat

# Linux/Mac
./run_v4_test.sh
```

### 深入学习
1. 阅读 `V4_OPTIMIZATION_SUMMARY.md`
2. 查看 `strategist_graph.py` 源码
3. 运行 `python strategist_graph.py`

### 参与贡献
1. 测试并反馈问题
2. 提出改进建议
3. 提交 Pull Request

---

## 📞 获取帮助

**文档**:
- `V4_QUICK_REFERENCE.md` - 快速参考
- `V4_BEFORE_AFTER_EXAMPLE.md` - 对比示例
- `V4_OPTIMIZATION_SUMMARY.md` - 完整说明

**测试**:
- `python test_v4_optimization.py` - 运行测试
- `python strategist_graph.py` - 完整体验

**社区**:
- 提交 Issue
- 查看 FAQ
- 参与讨论

---

**准备好了吗？开始你的 V4.0 之旅！** 🚀

```bash
# 一键开始
run_v4_test.bat  # Windows
./run_v4_test.sh  # Linux/Mac
```
