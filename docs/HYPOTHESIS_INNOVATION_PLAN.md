# 假设创新性增强实施方案（给 Claude 评审版）

## 0. 目标与原则
- 目标：显著提升“假设创新性”，同时保持可检验、可复现、可执行。
- 核心原则：
  - 异常发现由固定代码完成（避免 LLM 随机性）。
  - LLM 负责机制解释与假设表达。
  - 任何假设必须通过“可检验性网关”才可进入执行链。

---

## 1. 系统改造总览

### 1.1 新增模块
1) `src/utils/anomaly_seed_generator.py`
- 作用：从数据与图结构提取异常种子（候选创新信号）。
- 输出：`outputs/anomaly_seeds.json`

2) `src/utils/hypothesis_scorer.py`
- 作用：对候选假设打创新分并过滤。
- 输出：Top-K 假设 + 打分明细。

3) `src/utils/hypothesis_gateway.py`
- 作用：可检验性网关（字段存在、样本量、方法可执行性等）。
- 输出：通过/拒绝 + 原因。

### 1.2 修改模块
1) `src/agents/strategist.py`
- 在数据洞察前插入异常种子；
- Prompt 增加强约束：每条假设必须引用 seed_id、机制类型、检验路径；
- 接入打分器与网关，输出“最终可执行创新假设”。

2) `tests/test_full_pipeline_with_coding_v4_2.py`
- 新增实验模式 `E_seed_enhanced`（异常种子增强版）。

3) `tests/evaluate_experiments.py`
- 新增种子相关指标与 E 方案对比。

---

## 2. 异常种子设计（固定代码）

### 2.1 种子统一结构
```json
{
  "seed_id": "S1",
  "type": "subgroup_reversal | tail_anomaly | structural_bridge | temporal_break",
  "observation": "...",
  "evidence": {"n": 420, "stat": "...", "value": 0.31},
  "candidate_variables": ["..."],
  "suggested_mechanisms": ["mediation|moderation|interaction|stage"],
  "novelty_hint": "...",
  "confidence": 0.0
}
```

### 2.2 四类检测器（MVP）
1) 子群反转 `subgroup_reversal`
- 条件：`sign(global_r) != sign(subgroup_r)`
- 阈值：`|global_r|>0.15`, `|subgroup_r|>0.15`, `n_subgroup>=80`

2) 尾部异常 `tail_anomaly`
- 条件：Top5%（或1%）与其余组在关键指标差异显著
- 阈值：`|Δ|/std > 0.5`

3) 结构桥接 `structural_bridge`（基于 GraphPreview）
- 条件：betweenness 前10%，degree 在中位区间（40%-70%）
- 含跨社区桥信息。

4) 时间断点 `temporal_break`
- 条件：前后窗口相关差 `|Δr| > 0.25` 或趋势方向反转
- 要求每窗口最小样本量阈值。

### 2.3 输出文件
- `outputs/anomaly_seeds.json`
- `outputs/anomaly_seeds_summary.md`（可读摘要，用于 Prompt 注入）

---

## 3. Strategist 假设生成改造

### 3.1 生成流程（新）
1) DataPreview / GraphPreview
2) AnomalySeedGenerator（新增）
3) 数据洞察（LLM）
4) 候选假设生成（LLM，必须引用 seed）
5) 假设打分（固定代码）
6) 可检验性网关（固定代码）
7) 输出蓝图（仅保留通过网关的 Top-K 假设）

### 3.2 Prompt 强约束（必须）
- 每条假设必须包含：
  - `seed_id`
  - `mechanism_type`（mediation/moderation/interaction/stage）
  - `variables`（可映射到现有列）
  - `test_plan`（方法 + 预期方向 + 输出指标）
- 禁止输出未绑定 seed 的假设。

---

## 4. 假设评分与过滤策略

### 4.1 评分函数
`InnovationScore = N × T × U × G`（0~1）
- N（Novelty）：与历史/文献相似度低 → 高分
- T（Testability）：列可映射 + 方法可执行 + 样本量足够
- U（Untriviality）：常识惩罚（命中黑名单降分）
- G（Gain）：是否解释反常现象（seed 对应度）

### 4.2 过滤规则
- 硬过滤：
  - 无 `seed_id`、无 test_plan、变量无法映射、样本不足
- 软过滤：
  - 语义重复（相似度>阈值）去重
  - 常识假设降权（如“专利年龄→被引”类型）

### 4.3 输出
- `outputs/hypothesis_scoring.json`
- `outputs/hypothesis_topk.json`

---

## 5. 可检验性网关（进入 Methodologist 前）

必须全部通过：
1) 变量映射完整（对应真实列）
2) 方法可执行（有可用统计方法模板）
3) 样本量与分组规模达标
4) 输出契约完整（效应量、置信区间、p值）

未通过返回结构化拒绝原因，供 Strategist 重试。

---

## 6. 实验设计（新增 E 方案）

### 6.1 方案矩阵
- D_baseline0：纯 LLM
- A_template：图谱模板
- B_data_aware：数据感知
- C_iterative：数据感知+两轮
- E_seed_enhanced：C + 异常种子 + 打分网关（新增）

### 6.2 指标（新增重点）
- Seed 命中率：最终假设引用 seed 比例
- 创新假设通过率：通过网关比例
- 机制多样性：mediation/moderation/interaction/stage 覆盖度
- 假设重复率：Top-K 语义重复比例
- 原有指标继续保留（成功率、方法多样性、针对性等）

### 6.3 统计稳健性
- LLM-as-Judge 重复 3 次（均值±方差）
- 对关键维度做显著性检验（E vs C，E vs D）

---

## 7. 交付物清单

1) 代码
- `src/utils/anomaly_seed_generator.py`
- `src/utils/hypothesis_scorer.py`
- `src/utils/hypothesis_gateway.py`
- `src/agents/strategist.py`（改造）

2) 测试与脚本
- `tests/test_full_pipeline_with_coding_v4_2.py`（新增 E 模式）
- `tests/evaluate_experiments.py`（新增 seed 指标）

3) 产物
- `outputs/anomaly_seeds.json`
- `outputs/hypothesis_scoring.json`
- `outputs/evaluation_auto_metrics.json`
- `outputs/evaluation_llm_scores.json`
- `docs/EXPERIMENT_SUMMARY_TABLES.md`（更新）

---

## 8. 里程碑与时间（建议 10 天）

- Day 1-2：异常种子生成器 + 输出
- Day 3-4：Strategist 接 seed + Prompt 强约束
- Day 5：打分器 + 网关
- Day 6-7：跑 E 方案实验
- Day 8：评估脚本扩展 + 统计检验
- Day 9：文档与论文表格更新
- Day 10：复跑与答辩材料整理

---

## 9. 风险与回退

- 风险1：种子质量低 → 假设质量无提升
  - 回退：调阈值 + 仅保留高置信种子 + 增加最小样本限制

- 风险2：约束太强导致假设数量不足
  - 回退：Top-K不足时降级放宽一个约束（先放宽 U，不放宽 T）

- 风险3：LLM 依赖导致评分波动
  - 回退：固定温度 + 多次重复均值 + 保存原始评分日志
