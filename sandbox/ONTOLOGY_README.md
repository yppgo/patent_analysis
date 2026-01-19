# 完整因果本体论 - Complete Causal Ontology

## 📊 数据概览

### 规模统计
- **变量总数**: 25个
- **因果路径**: 35条
- **已验证路径**: 28条
- **探索性路径**: 7条

### 变量分类
- **输入变量** (8个): 外生变量，因果链起点
- **中介变量** (7个): 传递因果效应
- **结果变量** (6个): 研究的最终目标
- **调节变量** (4个): 改变因果关系强度

### 路径类型
- **直接效应**: 25条
- **调节效应**: 4条
- **中介效应**: 2条
- **交互效应**: 2条
- **反馈回路**: 2条

## 🎯 核心特点

### 1. 完整性
涵盖专利分析领域的三大维度：
- **技术创新维度**: 跨界度、科学关联度、知识重组等
- **组织能力维度**: 研发效率、技术广度/深度等
- **市场表现维度**: 影响力、商业价值、市场份额等

### 2. 理论基础扎实
每个变量都有：
- 明确的理论依据（如开放式创新理论、资源基础理论）
- 关键学者引用（如 Fleming 2001, Chesbrough 2003）
- 核心论点说明

### 3. 可操作性强
每个变量都包含：
- **测量指标**: 具体的计算方法
- **数据来源**: 从哪里获取数据
- **计算公式**: 如何计算

### 4. 实证支撑
每条因果路径都标注：
- **验证状态**: 已验证 vs 探索性
- **文献数量**: 支持该路径的论文数
- **代表性文献**: 关键论文引用
- **验证领域**: 在哪些技术领域验证过

## 📚 变量详解

### 输入变量 (Input Variables)

| ID | 变量名 | 测量指标 | 理论依据 |
|----|--------|----------|----------|
| V01 | 技术投入强度 | patent_count | 资源基础理论 |
| V02 | 企业规模 | applicant_total_patents | 规模经济理论 |
| V03 | 研发投资强度 | rd_intensity | 创新投入产出理论 |
| V04 | 国际合作强度 | foreign_coinventor_ratio | 全球创新网络理论 |
| V05 | 产学研合作 | university_collab_ratio | 三螺旋模型 |
| V06 | 先验经验 | historical_patent_count | 学习曲线理论 |
| V07 | 政策支持 | government_funded_ratio | 创新政策理论 |
| V08 | 市场竞争强度 | herfindahl_index | 竞争理论 |

### 中介变量 (Mediator Variables)

| ID | 变量名 | 测量指标 | 理论依据 |
|----|--------|----------|----------|
| V09 | 技术跨界度 | ipc_entropy | 开放式创新理论 |
| V10 | 科学关联度 | npl_ratio | 科学-技术关联理论 |
| V11 | 知识重组度 | new_combination_ratio | 重组创新理论 |
| V12 | 技术迭代速度 | tct | 技术生命周期理论 |
| V13 | 研发效率 | patent_per_inventor | 创新生产函数 |
| V14 | 技术广度 | ipc_class_count | 技术能力理论 |
| V15 | 技术深度 | ipc_concentration | 专业化理论 |

### 结果变量 (Outcome Variables)

| ID | 变量名 | 测量指标 | 理论依据 |
|----|--------|----------|----------|
| V16 | 技术影响力 | forward_citations | 引文分析理论 |
| V17 | 技术突破性 | disruptive_index | 颠覆性创新理论 |
| V18 | 技术独立性 | domestic_citation_ratio | 技术主权理论 |
| V19 | 商业价值 | maintenance_years | 专利价值理论 |
| V20 | 市场份额 | patent_share | 市场竞争理论 |
| V21 | 许可收益 | licensing_income | 知识产权商业化理论 |

### 调节变量 (Moderator Variables)

| ID | 变量名 | 测量指标 | 作用 |
|----|--------|----------|------|
| V22 | 技术成熟度 | patent_growth_rate | 影响创新模式 |
| V23 | 产业类型 | industry_category | 不同产业创新模式不同 |
| V24 | 组织类型 | applicant_type | 组织特征影响创新行为 |
| V25 | 地理位置 | applicant_country | 地理集聚促进知识溢出 |

## 🔗 核心因果路径

### 高证据支持路径（文献数 > 10）

1. **P10**: 技术跨界度 → 技术影响力 (18篇文献)
   - 效应: 正向，大
   - 机制: 跨界融合产生突破性创新
   - 验证领域: ICT, Biotech, Materials, Chemistry

2. **P19**: 技术影响力 → 商业价值 (20篇文献)
   - 效应: 正向，大
   - 机制: 影响力高的技术更有商业价值
   - 验证领域: 所有领域

3. **P06**: 产学研合作 → 科学关联度 (15篇文献)
   - 效应: 正向，大
   - 机制: 产学研合作强化科学基础
   - 验证领域: Biotech, Pharma, Materials

4. **P12**: 科学关联度 → 技术影响力 (14篇文献)
   - 效应: 正向，中
   - 机制: 科学基础支撑长期影响力
   - 验证领域: Pharma, Chemistry, Materials

### 探索性路径（创新机会）

1. **P05**: 国际合作强度 → 技术影响力
   - 新颖性: 高
   - 理由: 文献中该路径研究不足

2. **P22**: 技术投入强度 → 技术独立性 (倒U型)
   - 新颖性: 高
   - 理由: 理论推导，缺乏实证验证

3. **P23**: 国际合作强度 → 技术独立性 (负向)
   - 新颖性: 高
   - 理由: 反直觉假设，具有政策意义

4. **P32**: 技术跨界度 × 科学关联度 → 技术影响力
   - 新颖性: 高
   - 理由: 交互效应未被充分研究

## 🎨 可视化界面

### 启动方式
```bash
cd sandbox
python start_viewer.py
```

### 界面功能

1. **交互式力导向图**
   - 节点: 25个变量，按类别着色
   - 连线: 35条因果路径，按验证状态着色
   - 拖拽: 可自由调整节点位置
   - 缩放: 支持放大缩小

2. **详细信息面板**
   - 点击节点: 查看变量定义、测量方式、理论依据
   - 点击路径: 查看效应类型、作用机制、实证证据
   - 自动显示: 输入/输出路径、调节/中介作用

3. **筛选和搜索**
   - 按变量类别筛选
   - 按路径类型筛选（已验证/探索性）
   - 关键词搜索

4. **统计概览**
   - 顶部显示: 变量总数、路径总数、验证状态
   - 图例: 变量类型颜色说明

## 💡 使用场景

### 1. 研究假设生成
- 浏览已验证路径 → 理论迁移到新领域
- 发现探索性路径 → 填补文献空白
- 查看调节/中介效应 → 揭示作用机制

### 2. 文献综述
- 快速了解领域内的核心因果关系
- 查看每条路径的代表性文献
- 识别研究热点和空白

### 3. 研究设计
- 选择合适的变量和测量指标
- 了解变量的理论依据
- 设计因果推断研究

### 4. 教学演示
- 展示专利分析领域的知识体系
- 说明因果推断的基本概念
- 演示如何从理论到实证

## 🔧 扩展方向

### 短期（1-2周）
1. 补充更多变量（目标: 40个）
2. 增加路径数量（目标: 50条）
3. 完善文献引用（每条路径至少3篇）

### 中期（1个月）
1. 集成到 Strategist Agent
2. 实现自动假设生成
3. 连接真实专利数据验证

### 长期（3个月）
1. 构建动态更新机制（从新文献中提取）
2. 添加领域特异性路径（如AI、生物医药）
3. 开发假设验证工具（自动运行回归分析）

## 📖 参考文献

### 核心理论
- Chesbrough, H. (2003). Open Innovation. Harvard Business School Press.
- Fleming, L. (2001). Recombinant uncertainty in technological search. Management Science.
- Narin, F., et al. (1997). The increasing linkage between technology and science. Research Policy.
- Trajtenberg, M. (1990). A penny for your quotes: Patent citations and the value of innovations. RAND Journal of Economics.

### 方法论
- Ahmadpoor, M., & Jones, B. F. (2017). The dual frontier: Patented inventions and prior scientific advance. Science.
- Arts, S., & Fleming, L. (2018). Paradise of novelty—or loss of human capital? Research Policy.
- Harhoff, D., et al. (1999). Citation frequency and the value of patented inventions. Review of Economics and Statistics.

## 🎓 致谢

本因果本体论基于专利计量学领域30年的研究积累，整合了来自 Research Policy, Management Science, Strategic Management Journal 等顶级期刊的核心发现。

---

**版本**: 3.0 Complete Edition  
**最后更新**: 2025-01-12  
**维护者**: Patent Analysis Research Group
