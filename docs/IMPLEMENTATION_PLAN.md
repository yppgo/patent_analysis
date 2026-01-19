# 双图谱接入执行方案

## 📋 项目目标

将因果图谱和方法图谱完整接入到Strategist Agent中，实现从用户输入到DAG任务图的自动生成。

## 🎯 核心问题

### 当前状态
1. ✅ 因果图谱数据已准备（causal_ontology_extracted.json，30变量135路径）
2. ✅ 方法图谱已在Neo4j中（66篇论文）
3. ✅ 变量映射器已实现（24/30变量已映射）
4. ✅ CausalGraphQuery基础查询功能已实现
5. ❌ **缺失**：完整的假设生成流程（6种策略）
6. ❌ **缺失**：Strategist中的双图谱协同调用
7. ❌ **缺失**：端到端测试验证

### 目标状态
- 用户输入领域关键词 → 系统自动生成研究假设 → 生成完整的DAG任务图
- 假设生成基于6种策略（理论迁移、路径探索、边界条件、中介机制、反事实推理、交互效应）
- 双图谱协同工作（因果图谱提供假设，方法图谱提供方法）

---

## 📅 执行计划（分3个阶段）

### 阶段1：完善因果图谱查询器（2-3天）

**目标**：将CausalGraphQuery升级为完整的假设生成器（基于sandbox的6种策略）

#### Task 1.1：实现6种假设生成策略
**文件**：`src/utils/causal_graph_query.py`

**需要实现的方法**：
```python
class CausalGraphQuery:
    # 已有方法（保持不变）
    def suggest_hypotheses(self, user_goal, top_k=5)  # 简单版本
    
    # 新增方法
    def generate_hypotheses_v2(self, user_input: Dict) -> Dict:
        """
        完整的6步假设生成流程
        
        Args:
            user_input: {
                "domain": "量子计算",
                "intent": "技术趋势分析"
            }
        
        Returns:
            {
                "step1_input": {...},
                "step2_analysis": {...},
                "step3_matching": {...},
                "step4_literature": {...},
                "step5_hypotheses": [...],
                "step6_recommendation": {...}
            }
        """
        pass
    
    def _strategy_theory_transfer(self, matched_vars) -> List[Dict]:
        """策略1：理论迁移"""
        pass
    
    def _strategy_path_exploration(self, matched_vars) -> List[Dict]:
        """策略2：路径探索（未探索路径）"""
        pass
    
    def _strategy_boundary_condition(self, matched_vars) -> List[Dict]:
        """策略3：边界条件（调节效应）"""
        pass
    
    def _strategy_mediation(self, matched_vars) -> List[Dict]:
        """策略4：中介机制"""
        pass
    
    def _strategy_counterfactual(self, matched_vars) -> List[Dict]:
        """策略5：反事实推理"""
        pass
    
    def _strategy_interaction(self, matched_vars) -> List[Dict]:
        """策略6：交互效应"""
        pass
    
    def _calculate_novelty_score(self, hypothesis: Dict) -> float:
        """计算新颖性评分（0.6-0.9）"""
        pass
```

**参考**：
- `sandbox/static/data/hypothesis_generator.json` - 策略定义
- `sandbox/static/data/hypothesis_example.json` - 输出示例

**验收标准**：
- [ ] 6种策略都能生成假设
- [ ] 新颖性评分合理（0.6-0.9）
- [ ] 输出格式与sandbox示例一致

---

#### Task 1.2：实现变量匹配逻辑
**文件**：`src/utils/causal_graph_query.py`

**需要实现**：
```python
def match_variables(self, keywords: List[str]) -> Dict:
    """
    根据关键词匹配相关变量
    
    Returns:
        {
            "independent_vars": [V01, V03, V04, ...],  # 自变量
            "dependent_vars": [V16, V17, V19, ...],    # 因变量
            "mediator_vars": [V09, V10, V11, ...],     # 中介变量
            "moderator_vars": [V22, V23, V24, ...]     # 调节变量
        }
    """
    pass
```

**验收标准**：
- [ ] 能正确区分4种变量类型
- [ ] 匹配准确率 > 80%

---

#### Task 1.3：实现文献检查逻辑
**文件**：`src/utils/causal_graph_query.py`

**需要实现**：
```python
def check_literature(self, source_var: str, target_var: str) -> Dict:
    """
    检查某条因果路径的文献支持情况
    
    Returns:
        {
            "is_validated": True/False,
            "evidence_count": 14,
            "is_exploratory": False,
            "novelty_potential": 0.3  # 已充分研究
        }
    """
    pass
```

**验收标准**：
- [ ] 能区分已验证路径和探索性路径
- [ ] 新颖性潜力评分合理

---

#### Task 1.4：创建测试脚本
**文件**：`test_hypothesis_generation.py`

**测试内容**：
```python
# 测试1：6种策略都能生成假设
def test_all_strategies():
    query = CausalGraphQuery()
    result = query.generate_hypotheses_v2({
        "domain": "量子计算",
        "intent": "技术趋势分析"
    })
    assert len(result['step5_hypotheses']) >= 5
    assert all(h['novelty_score'] >= 0.6 for h in result['step5_hypotheses'])

# 测试2：变量匹配准确性
def test_variable_matching():
    query = CausalGraphQuery()
    matched = query.match_variables(["研发投资", "技术影响力"])
    assert "V03_rd_investment" in matched['independent_vars']
    assert "V16_tech_impact" in matched['dependent_vars']

# 测试3：文献检查
def test_literature_check():
    query = CausalGraphQuery()
    result = query.check_literature("V03_rd_investment", "V16_tech_impact")
    assert result['is_validated'] == True
    assert result['evidence_count'] > 10
```

**验收标准**：
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 80%

---

### 阶段2：升级Strategist Agent（3-4天）

**目标**：将完整的假设生成流程集成到Strategist中，增强列名匹配能力

#### Task 2.1：修改Strategist的process方法
**文件**：`src/agents/strategist.py`

**修改点**：
```python
def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    # 原有流程
    user_goal = input_data.get('user_goal', '')
    keywords = self._extract_keywords(user_goal)
    
    # 新增：完整的假设生成流程
    if self.causal_graph:  # 如果有因果图谱
        hypothesis_result = self.causal_graph.generate_hypotheses_v2({
            "domain": extract_domain(user_goal),
            "intent": extract_intent(user_goal)
        })
        
        # 将假设结果传递给后续流程
        recommended_hypotheses = hypothesis_result['step6_recommendation']
    
    # 原有流程：方法图谱检索
    graph_context, retrieved_cases = self._retrieve_from_graph(keywords)
    
    # 新增：整合假设和方法
    blueprint = self._generate_dag_with_hypotheses(
        user_goal=user_goal,
        hypotheses=recommended_hypotheses,
        methods=retrieved_cases,
        available_columns=available_columns
    )
    
    return {
        'blueprint': blueprint,
        'hypotheses': recommended_hypotheses,
        'graph_context': graph_context
    }
```

**验收标准**：
- [ ] 能正确调用假设生成器
- [ ] 假设和方法能正确整合

---

#### Task 2.2：增强Strategist的列名匹配能力
**文件**：`src/agents/strategist.py`

**修改_describe_columns_semantics方法**：
```python
def _describe_columns_semantics(self, columns: List[str]) -> str:
    """
    增强版：不仅提供语义，还提供与理论变量的对应关系
    """
    descriptions = []
    descriptions.append("【实际列名】→【语义说明】→【对应理论变量】")
    descriptions.append("")
    
    # 扩展语义映射，包含理论变量提示
    semantic_map = {
        '被引用专利': '被引用专利（前向引文，用于计算技术影响力 V16_tech_impact）',
        '被引用专利数量': '被引用次数（技术影响力的直接度量 V16_tech_impact）',
        'IPC分类号': '国际专利分类号（技术多样性 V09_tech_diversity、技术广度 V14_tech_breadth）',
        '申请(专利权)人': '申请人（企业规模 V02_firm_size、研发投资 V03_rd_investment）',
        '发明人': '发明人（研发效率 V13_rd_efficiency、国际合作 V04_international_collab）',
        '引用专利': '引用专利（后向引文，科学关联度 V10_science_linkage）',
        ...
    }
    
    for col in columns:
        semantic = semantic_map.get(col, f"未知语义，请根据列名推断用途")
        descriptions.append(f"  '{col}' → {semantic}")
    
    return "\n".join(descriptions)
```

**验收标准**：
- [ ] 列名语义说明包含理论变量提示
- [ ] LLM能正确匹配列名和变量

---

#### Task 2.3：修改Strategist的Prompt
**文件**：`src/agents/strategist.py`

**修改_generate_dag_blueprint的Prompt**：
```python
prompt = f"""
用户目标: {user_goal}

【因果图谱 - 推荐的研究假设】
{format_hypotheses(recommended_hypotheses)}

假设1 (新颖性: 0.85): 国际合作强度 → 技术影响力
  - 策略: 路径探索（未充分研究）
  - 变量: V04_international_collab → V16_tech_impact
  - 变量定义:
    * V04: 涉及外国发明人的专利占比
    * V16: 专利的被引用次数
  - 理论依据: 全球创新网络理论
  - 文献支持: 3篇（探索性）

假设2 (新颖性: 0.75): 研发投资 → 技术多样性 → 技术影响力
  - 策略: 中介机制
  - 变量: V03_rd_investment → V09_tech_diversity → V16_tech_impact
  - 变量定义:
    * V03: 人均专利产出（代理研发投资）
    * V09: IPC分类的多样性（Shannon熵）
    * V16: 被引用次数
  - 理论依据: 开放式创新理论
  - 文献支持: 8篇

【方法图谱 - 相关分析案例】
{format_methods(retrieved_cases)}

案例1: "A patent analysis of..."
  - 使用数据: ["前向引文", "IPC分类号", "申请人"]
  - 步骤1: 数据收集
  - 步骤2: 计算技术多样性（Shannon熵）
  - 步骤3: 引文分析
  - 步骤4: 回归分析

【当前数据可用列名及语义】
{columns_semantic}

⚠️ 重要提示：
1. 根据变量定义，从【当前数据可用列名】中选择最合适的列
2. 参考【方法图谱】中的数据使用方式
3. 例如：
   - V16_tech_impact（被引用次数）→ 选择"被引用专利数量"列
   - V09_tech_diversity（IPC多样性）→ 选择"IPC分类号"列
   - V04_international_collab（外国发明人占比）→ 选择"发明人"列，需要解析国籍

请基于以上信息生成DAG任务图，确保：
1. 每个任务明确使用哪些列（从实际列名中选择）
2. 说明如何计算每个变量
3. 任务之间的依赖关系清晰
"""
```

**验收标准**：
- [ ] Prompt包含完整的假设信息和变量定义
- [ ] Prompt包含方法案例和数据使用方式
- [ ] Prompt明确要求从实际列名中选择
- [ ] LLM能正确理解并整合

---

#### Task 2.4：创建端到端测试
**文件**：`test_strategist_with_dual_graphs.py`

**测试内容**：
```python
def test_strategist_with_causal_graph():
    """测试Strategist能正确使用因果图谱"""
    strategist = StrategistAgent(
        llm_client=llm,
        neo4j_connector=neo4j,
        causal_graph=CausalGraphQuery()  # 新增
    )
    
    result = strategist.process({
        "user_goal": "分析量子计算领域的技术趋势",
        "use_dag": True
    })
    
    # 验证假设生成
    assert 'hypotheses' in result
    assert len(result['hypotheses']) >= 3
    
    # 验证DAG任务图
    assert 'task_graph' in result['blueprint']
    assert len(result['blueprint']['task_graph']) >= 3
    
    # 验证任务包含假设验证
    tasks = result['blueprint']['task_graph']
    hypothesis_tasks = [t for t in tasks if 'hypothesis' in t.get('description', '').lower()]
    assert len(hypothesis_tasks) >= 1
    
    # 验证列名选择正确
    for task in tasks:
        config = task.get('implementation_config', {})
        if 'columns_to_load' in config:
            # 确保使用的列名在实际数据中存在
            assert all(col in available_columns for col in config['columns_to_load'])

def test_column_matching():
    """测试列名匹配的准确性"""
    # 测试LLM能否正确匹配：
    # V16_tech_impact → "被引用专利数量"
    # V09_tech_diversity → "IPC分类号"
    pass

def test_dual_graph_integration():
    """测试双图谱协同工作"""
    # 测试因果图谱和方法图谱的信息都被使用
    pass
```

**验收标准**：
- [ ] 端到端测试通过
- [ ] 生成的DAG任务图包含假设验证任务
- [ ] 列名选择正确（在实际数据中存在）
- [ ] 双图谱信息都被正确使用

---

### 阶段3：系统集成测试（2-3天）

**目标**：验证整个系统端到端工作

#### Task 4.1：创建完整的集成测试
**文件**：`test_full_system_integration.py`

**测试场景**：
```python
def test_scenario_1_data_security():
    """场景1：数据安全领域技术趋势分析"""
    user_input = "分析数据安全领域的技术趋势"
    
    # 执行完整流程
    result = run_full_pipeline(user_input)
    
    # 验证输出
    assert 'hypotheses' in result
    assert 'task_graph' in result
    assert 'methods' in result
    
    # 验证假设质量
    hypotheses = result['hypotheses']
    assert len(hypotheses) >= 3
    assert all(h['novelty_score'] >= 0.6 for h in hypotheses)
    
    # 验证任务图质量
    tasks = result['task_graph']
    assert len(tasks) >= 3
    assert any('hypothesis' in t.get('description', '') for t in tasks)

def test_scenario_2_quantum_computing():
    """场景2：量子计算领域技术空白识别"""
    pass

def test_scenario_3_ai_competition():
    """场景3：人工智能领域竞争格局分析"""
    pass
```

**验收标准**：
- [ ] 3个场景测试全部通过
- [ ] 每个场景生成合理的假设和任务图
- [ ] 执行时间 < 60秒

---

#### Task 4.2：性能测试
**文件**：`test_performance.py`

**测试内容**：
```python
def test_response_time():
    """测试响应时间"""
    times = []
    for i in range(10):
        start = time.time()
        result = strategist.process({"user_goal": "..."})
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    assert avg_time < 30  # 平均响应时间 < 30秒

def test_hypothesis_quality():
    """测试假设质量"""
    result = strategist.process({"user_goal": "..."})
    hypotheses = result['hypotheses']
    
    # 新颖性评分分布合理
    scores = [h['novelty_score'] for h in hypotheses]
    assert max(scores) >= 0.8  # 至少有一个高新颖性假设
    assert min(scores) >= 0.6  # 所有假设都有一定新颖性
```

**验收标准**：
- [ ] 响应时间 < 30秒
- [ ] 假设质量评分合理

---

#### Task 4.3：文档更新
**文件**：`docs/COMPLETE_SYSTEM_WORKFLOW.md`

**更新内容**：
- 补充完整的假设生成流程（6种策略）
- 更新Strategist的工作流程图
- 添加实际运行示例

**验收标准**：
- [ ] 文档与实际实现一致
- [ ] 包含完整的使用示例

---

## 📊 进度跟踪

### 阶段1：完善因果图谱查询器
- [ ] Task 1.1：实现6种假设生成策略
- [ ] Task 1.2：实现变量匹配逻辑
- [ ] Task 1.3：实现文献检查逻辑
- [ ] Task 1.4：创建测试脚本

### 阶段2：升级Strategist Agent
- [ ] Task 2.1：修改Strategist的process方法
- [ ] Task 2.2：增强Strategist的列名匹配能力
- [ ] Task 2.3：修改Strategist的Prompt
- [ ] Task 2.4：创建端到端测试

### 阶段3：系统集成测试
- [ ] Task 3.1：创建完整的集成测试
- [ ] Task 3.2：性能测试
- [ ] Task 3.3：文档更新

---

## 🎯 验收标准（总体）

### 功能性
- [ ] 用户输入领域关键词 → 自动生成3-5个研究假设
- [ ] 假设基于6种策略生成
- [ ] 假设有新颖性评分（0.6-0.9）
- [ ] 生成的DAG任务图包含假设验证任务
- [ ] 双图谱信息都被正确使用
- [ ] 列名自动匹配准确率 > 85%

### 性能
- [ ] 响应时间 < 30秒
- [ ] 假设生成准确率 > 80%
- [ ] 列名匹配准确率 > 85%

### 可维护性
- [ ] 代码有完整的注释
- [ ] 有完整的测试覆盖
- [ ] 文档与实现一致

---

## 📝 下一步行动

### 立即开始（今天）
1. 阅读sandbox中的假设生成示例
2. 设计6种策略的实现方案
3. 开始实现Task 1.1

### 本周目标
- 完成阶段1（完善因果图谱查询器）
- 开始阶段2（升级Strategist Agent）

### 下周目标
- 完成阶段2
- 完成阶段3（系统集成测试）

---

## 🔄 设计变更说明

### 删除阶段3（变量映射器）的原因

1. **Strategist已有列名匹配能力**
   - 当前Strategist已经能读取实际数据列名
   - 已经提供列名的语义说明
   - LLM可以自己推理和匹配

2. **方法图谱已提供数据字段信息**
   - 方法图谱记录了论文使用的数据字段
   - 可以作为参考和提示

3. **减少系统复杂度**
   - 变量映射器增加了一层抽象
   - 维护成本高（30个变量需要手动维护）
   - 灵活性差（数据列名变化需要更新映射）

4. **增强Strategist更实用**
   - 让Strategist的Prompt包含变量定义
   - 让Strategist的Prompt包含列名语义提示
   - LLM自己推理匹配，更灵活

### 新的设计思路

**核心理念**：让LLM自己理解和匹配，而不是预定义映射

**实现方式**：
1. 因果图谱提供：变量定义、测量方式
2. 方法图谱提供：数据字段使用案例
3. Strategist提供：实际列名和语义说明
4. LLM推理：选择最合适的列名和计算方法

**优势**：
- 更灵活：适应不同的数据源
- 更智能：LLM理解语义相似性
- 更易维护：不需要维护映射表
- 更可扩展：新变量不需要预定义

---

**文档版本**: 2.0  
**创建日期**: 2026-01-19  
**修改日期**: 2026-01-19  
**预计完成时间**: 2026-01-27（8天）
