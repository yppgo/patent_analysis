# 双图谱接入实施计划

## 📋 项目概述

**目标**：将因果图谱和方法图谱完整接入到Strategist Agent中，实现从用户输入到DAG任务图的自动生成。

**核心价值**：
- 用户输入领域关键词 → 系统自动生成研究假设 → 生成完整的DAG任务图
- 假设生成基于6种策略（理论迁移、路径探索、边界条件、中介机制、反事实推理、交互效应）
- 双图谱协同工作（因果图谱提供假设，方法图谱提供方法）

**项目状态**：✅ 阶段1-3已完成（2026-01-20）

---

## 🎉 项目完成总结

### 已完成的核心功能

#### ✅ 双图谱接入（阶段1-2）

**1. 因果图谱 - 完整集成**
- 数据规模：30个变量，135条因果路径
- 假设生成：6种策略，分层推荐（核心3个 + 备选2-3个）
- 评分体系：新颖性（0.6-0.9）+ 质量（0-100）
- 测试通过率：100%

**2. 方法图谱 - 完整集成**
- 数据规模：50篇论文，28个变量覆盖，86个分析方法
- 功能：为每个假设推荐测量方法和统计方法
- 集成方式：方法信息整合到Strategist的Prompt中
- 测试通过率：100%

#### ✅ Strategist Agent（阶段2）

**核心能力**：
- 假设生成：自动生成7个研究假设（覆盖6种策略）
- DAG任务图：生成2-3个任务节点，正确识别依赖关系
- 列名匹配：准确率100%
- 质量评分：98.8%（79/80分）

**双图谱协同**：
- 因果图谱：提供假设和变量定义
- 方法图谱：提供测量方法和分析方法
- LLM正确使用双图谱建议（如"Bootstrap Mediation Analysis"）

#### ✅ Methodologist Agent（阶段3）

**核心能力**：
- 技术规格生成：正确识别类别变量，生成虚拟变量编码方案
- 统计方法：多项逻辑回归、Bootstrap中介分析
- 质量评分：94%（优化后）

**新增功能 - Execution Plan**：
- 执行顺序：拓扑排序
- 数据流图：nodes + edges
- 验证规则：输出文件、契约、错误处理
- 质量评分：100%

**端到端测试**：
- Strategist → Methodologist 流程完整 ✅
- 任务依赖关系正确 ✅
- 数据流正确 ✅

### 项目清理（2026-01-20）

**文档清理**：
- 删除：`src/docs/` 整个文件夹（7个过时文档）
- 归档：`docs/archive/`（3个重复文档）
- 保留：`README.md` + `docs/IMPLEMENTATION_PLAN.md`

**测试文件清理**：
- 核心测试：移到 `tests/`（4个）
- 中间测试：归档到 `tests/archive/`（4个）
- 删除：无用测试（4个）

**最终结构**：
```
项目根目录/
├── README.md
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   └── archive/
├── tests/
│   ├── test_hypothesis_generation.py
│   ├── test_strategist_with_dual_graphs.py
│   ├── test_strategist_to_methodologist.py
│   ├── test_execution_plan_generation.py
│   └── archive/
└── [其他项目文件...]
```

---

## 📅 实施阶段详情

### 阶段1：完善因果图谱查询器 ✅

**目标**：将CausalGraphQuery升级为完整的假设生成器

**完成任务**：
- ✅ Task 1.1：实现6种假设生成策略
- ✅ Task 1.2：实现变量匹配逻辑
- ✅ Task 1.3：实现文献检查逻辑
- ✅ Task 1.4：创建测试脚本

**关键成果**：
- 生成8个假设，覆盖全部6种策略
- 新颖性评分范围：0.65-0.9（平均0.78）
- 变量匹配准确率：100%
- 文献检查：识别4个已验证路径，6个未探索路径

**优化记录**：
- 增加中介假设数量：从1个增加到3个
- 添加路径质量排序：基于文献证据、效应大小、验证状态
- 质量评分系统：0-100分（文献证据40分 + 效应大小30分 + 验证状态30分）
- 新颖性动态调整：根据路径质量调整（0.65-0.85）

**完成时间**：2026-01-19

---

### 阶段2：升级Strategist Agent ✅

**目标**：将完整的假设生成流程集成到Strategist中，增强列名匹配能力

**完成任务**：
- ✅ Task 2.1：修改Strategist的process方法（集成双图谱）
- ✅ Task 2.2：增强列名匹配能力
- ✅ Task 2.3：修改Prompt
- ✅ Task 2.4：创建端到端测试
- ✅ Task 2.5：优化Prompt质量（6轮迭代）

**关键成果**：
- 双图谱集成：因果图谱生成假设，方法图谱推荐方法
- 列名匹配：准确率100%
- 蓝图质量：从85.7%提升到98.8%
- 测试结果：生成7个假设，3个核心推荐，3个备选推荐

**Prompt优化历程**：
1. 修复f-string格式化错误
2. 添加类别变量处理指南
3. 添加控制变量共线性约束
4. 添加中介分析控制变量约束
5. 优化输出格式和验证规则
6. 最终质量：98.8%

**完成时间**：2026-01-19

---

### 阶段3：Methodologist Agent集成 ✅

**目标**：将Strategist生成的DAG蓝图转换为技术规格

**完成任务**：
- ✅ Task 3.1：测试Methodologist处理Strategist蓝图
- ✅ Task 3.2：优化Methodologist的Prompt
- ✅ Task 3.3：创建端到端测试
- ✅ Task 3.4：实现Execution Plan生成功能

**关键成果**：
- 技术规格质量：从86.5%提升到94%
- 正确识别类别变量（V09）
- 生成正确的统计方法（多项逻辑回归、Bootstrap）
- 新增execution_plan功能（质量100%）

**发现的问题（Task 3.1）**：
- ❌ 未识别V09是类别变量
- ❌ 未提到虚拟变量编码
- ❌ 未提到多项逻辑回归

**优化方案（Task 3.2）**：
- 添加"变量类型识别指南"
- 添加类别变量特殊处理指南
- 添加中介分析中类别中介变量的处理方法
- 添加边界情况处理指南

**优化效果（Task 3.3）**：
- Task 1质量：93%（函数签名✅，变量命名✅，错误处理✅）
- Task 2质量：95%（虚拟变量编码✅，统计方法✅）
- 平均质量：94%（从86.5%提升）

**Execution Plan功能（Task 3.4）**：
- 生成执行顺序（拓扑排序）
- 生成数据流图（nodes + edges）
- 生成验证规则（输出文件、契约、错误处理）
- 整合task_graph和technical_specs
- 质量评分：100%

**完成时间**：2026-01-19

---

## 📊 验收标准

### 功能性
- [x] 用户输入领域关键词 → 自动生成3-5个研究假设 ✅
- [x] 假设基于6种策略生成 ✅
- [x] 假设有新颖性评分（0.6-0.9）✅
- [x] 生成的DAG任务图包含假设验证任务 ✅
- [x] 双图谱信息都被正确使用 ✅
- [x] 列名自动匹配准确率 > 85% ✅（实际100%）
- [x] Methodologist能处理Strategist蓝图 ✅
- [x] 端到端测试通过（Strategist → Methodologist）✅
- [ ] Coding Agent能生成可执行代码
- [ ] 完整流程端到端测试通过（Strategist → Methodologist → Coding Agent）

### 质量
- [x] Strategist蓝图质量 > 90% ✅（实际98.8%）
- [x] Methodologist技术规格质量 > 90% ✅（实际94%）
- [ ] Coding Agent代码质量 > 85%

### 性能
- [x] Strategist响应时间 < 30秒 ✅
- [ ] Methodologist响应时间 < 20秒
- [ ] Coding Agent响应时间 < 30秒
- [ ] 完整流程响应时间 < 2分钟

### 可维护性
- [x] 代码有完整的注释 ✅
- [x] 有完整的测试覆盖 ✅
- [x] 文档与实现一致 ✅

---

## 📝 下一步行动

### 阶段4：Coding Agent集成（待开始）

**优先级1：测试Coding Agent执行**
1. 创建端到端测试脚本（Strategist → Methodologist → Coding Agent）
2. 使用测试案例："分析量子计算领域的技术影响力驱动因素"
3. 验证Coding Agent能否正确执行Task 1和Task 2
4. 评估代码生成质量和执行成功率

**优先级2：根据测试结果决定下一步**
- 如果成功率高（>80%）：当前方式够用，继续优化细节
- 如果经常出错：分析错误原因，考虑启用execution_plan或优化Prompt

### 可选优化
- [ ] 在workflow.py中集成execution_plan生成
- [ ] 修改Coding Agent读取execution_plan
- [ ] 支持并行执行识别
- [ ] 支持错误恢复策略

---

## 📂 关键文件索引

### 核心代码
- `src/utils/causal_graph_query.py` - 因果图谱查询器（假设生成）
- `src/utils/method_graph_query.py` - 方法图谱查询器
- `src/agents/strategist.py` - Strategist Agent
- `src/agents/methodologist.py` - Methodologist Agent
- `src/core/workflow.py` - 工作流编排

### 核心测试
- `tests/test_hypothesis_generation.py` - 假设生成测试
- `tests/test_strategist_with_dual_graphs.py` - Strategist双图谱集成测试
- `tests/test_strategist_to_methodologist.py` - 端到端测试
- `tests/test_execution_plan_generation.py` - execution_plan生成测试

### 数据文件
- `sandbox/static/data/causal_ontology_extracted.json` - 因果图谱数据
- `sandbox/static/data/method_knowledge_base.json` - 方法图谱数据
- `sandbox/static/data/hypothesis_generator.json` - 假设生成策略定义

### 输出示例
- `outputs/e2e_test_blueprint.json` - Strategist生成的蓝图
- `outputs/e2e_test_task_1_spec.json` - Task 1技术规格
- `outputs/e2e_test_task_2_spec.json` - Task 2技术规格
- `outputs/execution_plan.json` - 执行计划

---

## 📈 项目里程碑

| 日期 | 里程碑 | 状态 |
|------|--------|------|
| 2026-01-19 | 阶段1：完善因果图谱查询器 | ✅ 完成 |
| 2026-01-19 | 阶段2：升级Strategist Agent | ✅ 完成 |
| 2026-01-19 | 阶段3：Methodologist Agent集成 | ✅ 完成 |
| 2026-01-20 | 项目清理（文档 + 测试） | ✅ 完成 |
| 2026-01-20 | 阶段4：Coding Agent V4.2 集成 | ✅ 完成 |

---

## 🎯 关键成果总结

1. **双图谱完整接入** ✅
   - 因果图谱：假设生成 + 变量定义
   - 方法图谱：测量方法 + 分析方法
   - 协同工作：LLM使用双图谱建议

2. **智能体质量提升** ✅
   - Strategist蓝图质量：98.8%
   - Methodologist技术规格质量：94%
   - 列名匹配准确率：100%

3. **新增功能** ✅
   - Execution Plan生成（为Coding Agent提供全局视图）
   - 分层推荐系统（核心推荐 + 备选推荐）
   - 双评分体系（新颖性 + 质量）

4. **项目结构优化** ✅
   - 文档清理（删除7个过时文档，归档3个重复文档）
   - 测试清理（整理11个测试文件）
   - 结构清晰（核心文档 + 核心测试）

5. **Coding Agent V4.2 集成** ✅
   - 端到端测试成功率：100% (2/2任务)
   - Task 1 (变量计算)：326.1s, 9次迭代
   - Task 2 (中介分析)：983.9s, 20次迭代 (Qwen)
   - 修复问题：f-string变量转义、REPL预加载df
   - 输出文件：task_1_variables.csv (624KB)

6. **Coding Agent 基模优化** ✅ (2026-01-20 晚)
   - 切换基模：Qwen → Claude (通过聚合AI代理)
   - 迭代次数：20次 → 4次 (降低80%)
   - 耗时：984s → 280s (降低71%)
   - 新增 ClaudeLLMClient 支持代理访问
   - 重写 Prompt：从"小步试错"改为"先规划后执行"
   - 成功生成结论性JSON结果

---

## 📋 阶段5：流程优化（进行中）

### 5.1 全流程评审结果

| 环节 | 评分 | 主要问题 |
|------|------|----------|
| Strategist | 85/100 | 变量定义依赖猜测，未见实际数据 |
| Methodologist | 75/100 | 缺少降级方案 |
| Coding Agent | 90/100 | Claude版本表现优秀 |

### 5.2 待优化项

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 数据预览注入 | 🔄 进行中 | 让Strategist/Methodologist看到数据结构 |
| 降级方案机制 | ⏳ 待开始 | Methodologist生成备选简化方案 |
| 变量定义验证 | ⏳ 待开始 | 自动验证变量是否准确测量概念 |

### 5.3 数据预览注入设计

```
用户请求 + 数据文件
       ↓
  DataPreview 生成
  - 列名/类型
  - 唯一值数量
  - 统计信息
  - 高基数警告
  - 关键列样例行：df.head(5)（仅保留关键列子集，长文本截断）
       ↓
  Strategist (看到预览后设计蓝图)
       ↓
  Methodologist (看到预览后细化Spec)
       ↓
  Coding Agent (执行代码)
```

### 5.4 数据预览内容（建议）

**目标**：让 Strategist/Methodologist 在制定方案前看到“结构 + 值的格式”，减少变量定义猜测。

1. **结构级信息（必须）**
   - 数据形状（行/列）
   - 列名 + dtype
   - unique_count / null_count
   - 高基数列警告（提示不适合直接做分类变量，给出前缀提取/Top-N聚合建议）

2. **值级样例（建议）**
   - 提供关键列子集的 `head(5)`
   - 关键列建议：`序号`、`公开(公告)号`、`授权日`、`IPC主分类号`、`被引用专利数量`、`引用专利数量`、`发明人`、`Topic_Label`
   - 长文本列（标题/摘要等）默认不注入；如需注入，必须截断（例如前80字）

### 5.5 明日开发任务

- [ ] DataPreview：进一步降噪（避免对摘要/标题的分隔符误报，prefix建议仅对IPC/地区等字段启用）
- [ ] Strategist：在生成 DAG prompt 中注入 DataPreview（结构信息 + 关键列 head(5)）
- [ ] Methodologist：在生成 spec prompt 中注入 DataPreview（同上）
- [ ] 评测：运行 `tests/test_full_pipeline_with_coding_v4_2.py` 对比优化前后
  - 指标：蓝图质量（任务设计是否更贴合数据）、Spec 可执行性、Coding Agent 迭代次数/耗时

---

**文档版本**: 2.1  
**最后更新**: 2026-01-20  
**维护者**: Patent Analysis Research Group
