# 系统架构文档

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
├─────────────────────────────────────────────────────────────────┤
│  命令行 (main.py)  │  Python API  │  快速启动 (quick_start.py) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph 工作流层                          │
├─────────────────────────────────────────────────────────────────┤
│                     workflow.py (编排器)                         │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │ Strategist   │  →   │ Methodologist│  →   │ Coding Agent │ │
│  │   Agent      │      │    Agent     │      │      V2      │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│       ↓                      ↓                      ↓          │
│   战略蓝图              执行规格              Python 代码        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         基础设施层                               │
├─────────────────────────────────────────────────────────────────┤
│  LLM 客户端  │  Neo4j 连接器  │  日志系统  │  状态管理         │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 模块详解

### 1. Agent 层 (src/agents/)

#### BaseAgent (基类)
```python
class BaseAgent:
    """所有 Agent 的基类"""
    - name: str              # Agent 名称
    - llm: LLM              # LLM 客户端
    - logger: Logger        # 日志记录器
    
    + process(input_data)   # 处理输入
    + log(message, level)   # 记录日志
```

#### Strategist Agent (战略家)
```python
class StrategistAgent(BaseAgent):
    """理解用户意图，制定研究战略"""
    - neo4j: Neo4jConnector  # 知识图谱连接
    
    + process(input_data)
      输入: {"user_goal": str}
      输出: {"blueprint": dict, "graph_context": str}
    
    - _query_neo4j_methods()     # 查询方法
    - _generate_blueprint()       # 生成蓝图
```

**工作流程**:
```
用户目标
    ↓
查询 Neo4j 知识图谱
    ↓
检索相关方法和参数
    ↓
生成战略蓝图
    ↓
{
  "research_objective": "...",
  "analysis_logic_chains": [
    {
      "step_id": 1,
      "objective": "...",
      "method": "...",
      "implementation_config": {...}
    }
  ]
}
```

#### Methodologist Agent (方法论家)
```python
class MethodologistAgent(BaseAgent):
    """将战略蓝图转化为技术执行规格"""
    
    + process(input_data)
      输入: {"step": dict}
      输出: {"execution_spec": dict}
    
    + process_multiple(steps)    # 批量处理
    - _generate_execution_spec() # 生成规格
    - validate_spec()            # 验证规格
```

**工作流程**:
```
战略蓝图中的步骤
    ↓
解析 implementation_config
    ↓
将自然语言转化为代码逻辑
    ↓
生成执行规格
    ↓
{
  "function_name": "...",
  "function_signature": "...",
  "required_libraries": [...],
  "processing_steps": [...],
  "input_specification": {...},
  "output_specification": {...}
}
```

#### Coding Agent V2 (执行者)
```python
class CodingAgentV2(BaseAgent):
    """生成高质量、可运行的 Python 代码"""
    - test_data: DataFrame       # 测试数据
    - max_iterations: int        # 最大迭代次数
    - workflow: CompiledGraph    # ReAct 工作流
    
    + process(input_data)
      输入: {"execution_spec": dict, "test_data": DataFrame}
      输出: {"generated_code": str, "is_code_valid": bool}
    
    - _build_react_workflow()    # 构建 ReAct 工作流
    - _think_node()              # 思考节点
    - _act_node()                # 行动节点
    - _test_node()               # 测试节点
    - _observe_node()            # 观察节点
    - _reflect_node()            # 反思节点
```

**ReAct 工作流**:
```
┌─────────────────────────────────────────────────────┐
│                  ReAct 循环                          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐     │
│  │Think │ → │ Act  │ → │ Test │ → │Observe│     │
│  │思考  │    │行动  │    │测试  │    │观察  │     │
│  └──────┘    └──────┘    └──────┘    └──────┘     │
│                                          ↓          │
│                                     ┌──────┐       │
│                                     │Reflect│      │
│                                     │反思  │       │
│                                     └──────┘       │
│                                          ↓          │
│                                   是否继续？        │
│                                    ↙      ↘        │
│                                  是         否      │
│                                  ↓          ↓       │
│                              回到Think    结束      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2. 核心层 (src/core/)

#### State (状态定义)
```python
class CodingAgentState(TypedDict):
    """Coding Agent 的状态"""
    execution_spec: Dict[str, Any]
    current_step: Dict[str, Any]
    test_data: Any
    thought: str
    action: str
    observation: str
    generated_code: str
    code_issues: List[str]
    runtime_error: str
    iteration_count: int
    is_code_valid: bool

class WorkflowState(TypedDict):
    """完整工作流的状态"""
    user_goal: str
    test_data: Any
    blueprint: Dict[str, Any]
    graph_context: str
    execution_specs: List[Dict[str, Any]]
    generated_codes: List[str]
    code_metadata: List[Dict[str, Any]]
```

#### Workflow (工作流编排)
```python
def build_full_workflow(strategist, methodologist, coding_agent):
    """构建完整的三 Agent 协作工作流"""
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("methodologist", methodologist_node)
    workflow.add_node("coding", coding_node)
    
    # 设置流程
    workflow.set_entry_point("strategist")
    workflow.add_edge("strategist", "methodologist")
    workflow.add_edge("methodologist", "coding")
    workflow.add_edge("coding", END)
    
    return workflow.compile()
```

**数据流**:
```
user_goal
    ↓
[Strategist Node]
    ↓
blueprint + graph_context
    ↓
[Methodologist Node]
    ↓
execution_specs
    ↓
[Coding Node]
    ↓
generated_codes + code_metadata
```

### 3. 工具层 (src/utils/)

#### LLM Client
```python
def get_llm_client():
    """获取 LLM 客户端"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    
    if provider == "openai":
        return ChatOpenAI(...)
    elif provider == "dashscope":
        return ChatTongyi(...)
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
```

**支持的提供商**:
- OpenAI (GPT-4, GPT-3.5)
- DashScope (Qwen-Max, Qwen-Plus)
- 可扩展到其他提供商

#### Neo4j Connector
```python
class Neo4jConnector:
    """Neo4j 知识图谱连接器"""
    
    + query_methods(keywords)    # 查询方法
    + get_method_details(name)   # 获取方法详情
    + close()                    # 关闭连接
```

**知识图谱结构**:
```
(Method)
  - name: str
  - category: str
  - description: str
  - parameters: dict
  - use_cases: list
  
(Method)-[:REQUIRES]->(Library)
(Method)-[:SUITABLE_FOR]->(Task)
(Method)-[:RELATED_TO]->(Method)
```

## 🔄 数据流详解

### 完整流程

```
1. 用户输入
   "分析专利数据中的技术空白"
   
2. Strategist Agent
   ├─ 查询 Neo4j: "技术空白", "异常检测"
   ├─ 检索方法: ABOD, Isolation Forest, ...
   └─ 生成蓝图:
      {
        "research_objective": "识别技术空白",
        "analysis_logic_chains": [
          {
            "step_id": 1,
            "objective": "检测异常专利",
            "method": "ABOD",
            "implementation_config": {
              "algorithm": "ABOD",
              "n_neighbors": 5
            }
          }
        ]
      }

3. Methodologist Agent
   ├─ 解析步骤 1
   ├─ 提取配置: ABOD, n_neighbors=5
   └─ 生成规格:
      {
        "function_name": "detect_technology_gaps",
        "required_libraries": ["pyod", "pandas"],
        "processing_steps": [
          {
            "step_number": 1,
            "description": "数据预处理",
            "code_logic": "标准化特征"
          },
          {
            "step_number": 2,
            "description": "ABOD 检测",
            "code_logic": "使用 ABOD 算法"
          }
        ]
      }

4. Coding Agent V2
   ├─ Think: 分析任务需求
   ├─ Act: 生成代码
   ├─ Test: 运行时测试
   ├─ Observe: 检查质量
   ├─ Reflect: 决定是否改进
   └─ 输出代码:
      def detect_technology_gaps(df: pd.DataFrame) -> Dict[str, Any]:
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

5. 输出结果
   ├─ blueprint.json
   ├─ execution_specs.json
   ├─ generated_code_1.py
   └─ code_metadata.json
```

## 🎯 设计原则

### 1. 单一职责原则
- 每个 Agent 只负责一个明确的任务
- Strategist: 战略规划
- Methodologist: 技术转化
- Coding Agent: 代码生成

### 2. 开闭原则
- 对扩展开放：可以添加新的 Agent
- 对修改封闭：不需要修改现有代码

### 3. 依赖倒置原则
- 依赖抽象（BaseAgent）而不是具体实现
- 使用接口（LLM Client）而不是具体类

### 4. 接口隔离原则
- 每个 Agent 只暴露必要的接口
- process() 方法统一接口

### 5. 里氏替换原则
- 所有 Agent 都可以替换为 BaseAgent
- 保证多态性

## 🔧 扩展点

### 添加新的 Agent

```python
class OptimizerAgent(BaseAgent):
    """代码优化 Agent"""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        code = input_data.get('code', '')
        
        # 优化代码
        optimized_code = self._optimize_code(code)
        
        return {
            'optimized_code': optimized_code,
            'improvements': [...]
        }
```

### 添加新的 LLM 提供商

```python
# 在 llm_client.py 中
def get_llm_client():
    provider = os.getenv("LLM_PROVIDER")
    
    if provider == "anthropic":
        return ChatAnthropic(...)
    elif provider == "google":
        return ChatGoogleGenerativeAI(...)
```

### 添加新的知识源

```python
class WikipediaConnector:
    """Wikipedia 知识连接器"""
    
    def query_methods(self, keywords):
        # 从 Wikipedia 检索方法
        pass
```

## 📊 性能优化

### 1. 并行执行
```python
# 并行处理多个步骤
with ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(methodologist.process, {'step': step})
        for step in steps
    ]
    results = [f.result() for f in futures]
```

### 2. 缓存机制
```python
# 缓存 LLM 响应
@lru_cache(maxsize=100)
def cached_llm_invoke(prompt):
    return llm.invoke(prompt)
```

### 3. 增量更新
```python
# 只重新生成修改的部分
if code_changed:
    regenerate_code()
else:
    use_cached_code()
```

## 🔒 安全考虑

### 1. 代码执行安全
```python
# 使用受限的执行环境
exec_globals = {
    'pd': pd,
    'np': np,
    '__builtins__': safe_builtins
}
exec(code, exec_globals)
```

### 2. API Key 保护
```python
# 从环境变量读取
api_key = os.getenv("OPENAI_API_KEY")

# 不在日志中显示
logger.info(f"API Key: {api_key[:8]}...")
```

### 3. 输入验证
```python
# 验证用户输入
if not user_goal or len(user_goal) > 1000:
    raise ValueError("无效的用户目标")
```

## 📈 监控和日志

### 日志级别
- DEBUG: 详细的调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

### 监控指标
- Agent 执行时间
- LLM API 调用次数
- 代码生成成功率
- 运行时测试通过率

---

**版本**: 2.0.0  
**最后更新**: 2025-12-18  
**维护者**: Patent-DeepScientist Team
