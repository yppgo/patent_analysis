# Design Document

## Overview

本设计文档描述了如何将 CodingAgentV2 从手动实现的 ReAct 模式重构为使用 LangGraph 的 `create_react_agent` 预构建函数。重构的核心思想是将原有的节点函数（think, act, test, observe, reflect）转换为独立的工具（tools），让 LangGraph 的 ReAct agent 自动管理工具的选择和调用。

### Key Benefits

1. **代码简化**: 从 ~500 行减少到 ~300 行
2. **更标准**: 使用 LangGraph 的标准 ReAct 实现
3. **更灵活**: 通过添加工具轻松扩展功能
4. **更智能**: LLM 自动决定工具调用顺序和时机

## Architecture

### Current Architecture (Manual ReAct)

```
CodingAgentV2
├── _build_react_workflow()
│   ├── StateGraph(CodingAgentState)
│   ├── add_node("think", _think_node)
│   ├── add_node("act", _act_node)
│   ├── add_node("test", _test_node)
│   ├── add_node("observe", _observe_node)
│   ├── add_node("reflect", _reflect_node)
│   └── add_conditional_edges(...)
└── process(input_data)
    └── workflow.invoke(initial_state)
```

**问题**:
- 手动管理状态转换
- 固定的执行顺序（think → act → test → observe → reflect）
- 难以添加新功能
- 大量样板代码

### New Architecture (LangGraph ReAct Agent)

```
CodingAgentV3
├── _create_tools()
│   ├── generate_code_tool
│   ├── test_code_tool
│   ├── check_code_tool
│   └── analyze_error_tool
├── _build_agent()
│   └── create_react_agent(llm, tools, state_modifier)
└── process(input_data)
    └── agent.invoke(initial_state)
```

**优势**:
- LangGraph 自动管理状态和工具调用
- LLM 动态决定工具使用顺序
- 工具可以独立测试和复用
- 易于添加新工具

## Components and Interfaces

### 1. CodingAgentV3 Class

```python
class CodingAgentV3(BaseAgent):
    """
    编码智能体 V3 - 基于 LangGraph create_react_agent
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=3, logger=None):
        super().__init__("CodingAgentV3", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理执行规格，生成高质量代码
        
        保持与 V2 相同的接口
        """
        pass
    
    def _create_tools(self) -> List[Tool]:
        """创建 agent 可用的工具列表"""
        pass
    
    def _build_agent(self) -> CompiledGraph:
        """使用 create_react_agent 构建 agent"""
        pass
```

### 2. Tools Definition

#### Tool 1: generate_code

**Purpose**: 根据执行规格生成 Python 代码

**Input Schema**:
```python
{
    "execution_spec": Dict[str, Any],  # 执行规格
    "previous_code": str,              # 上一次生成的代码（可选）
    "issues_to_fix": List[str]         # 需要修复的问题（可选）
}
```

**Output Schema**:
```python
{
    "code": str,                       # 生成的代码
    "success": bool,                   # 是否成功
    "message": str                     # 说明信息
}
```

**Implementation**:
- 构建 prompt，包含执行规格和需要修复的问题
- 调用 LLM 生成代码
- 提取代码块，移除 import 语句
- 返回结构化结果

#### Tool 2: test_code

**Purpose**: 使用真实数据执行代码并返回结果

**Input Schema**:
```python
{
    "code": str,                       # 要测试的代码
    "function_name": str,              # 函数名
    "test_data": Any                   # 测试数据
}
```

**Output Schema**:
```python
{
    "success": bool,                   # 是否成功执行
    "result": Dict[str, Any],          # 执行结果（序列化后）
    "error": str                       # 错误信息（如果有）
}
```

**Implementation**:
- 准备执行环境（导入必要的库）
- 使用 exec() 执行代码
- 调用指定函数并传入测试数据
- 序列化执行结果
- 捕获并返回任何异常

#### Tool 3: check_code

**Purpose**: 静态检查代码质量（不执行代码）

**Input Schema**:
```python
{
    "code": str,                       # 要检查的代码
    "function_name": str               # 期望的函数名
}
```

**Output Schema**:
```python
{
    "is_valid": bool,                  # 代码是否有效
    "issues": List[str]                # 发现的问题列表
}
```

**Implementation**:
- 检查代码长度
- 检查函数定义是否存在
- 检查是否有 return 语句
- 检查是否有错误处理
- 检查是否有类型注解
- 使用 compile() 检查语法错误

#### Tool 4: analyze_error

**Purpose**: 分析错误并提供修复建议

**Input Schema**:
```python
{
    "code": str,                       # 有问题的代码
    "error": str,                      # 错误信息
    "error_type": str                  # 错误类型（runtime/static）
}
```

**Output Schema**:
```python
{
    "analysis": str,                   # 错误分析
    "suggestions": List[str]           # 修复建议
}
```

**Implementation**:
- 构建 prompt，包含代码和错误信息
- 调用 LLM 分析错误原因
- 提取修复建议
- 返回结构化分析结果

### 3. State Management

使用 LangGraph 的 `MessagesState` 作为基础，扩展添加我们需要的字段：

```python
class ReactAgentState(MessagesState):
    """
    ReAct Agent 的状态
    
    继承 MessagesState 以支持 LangGraph 的消息管理
    """
    # 输入
    execution_spec: Dict[str, Any]
    current_step: Dict[str, Any]
    test_data: Any
    
    # 代码生成过程
    generated_code: str
    code_issues: List[str]
    runtime_error: str
    execution_result: Optional[Dict[str, Any]]
    
    # 控制
    iteration_count: int
    is_code_valid: bool
```

### 4. Agent Configuration

```python
def _build_agent(self) -> CompiledGraph:
    """构建 ReAct agent"""
    
    # 创建系统提示
    system_message = """你是一个专业的 Python 代码生成专家。

你的任务是根据执行规格生成高质量的 Python 代码，并确保代码能够正确运行。

你有以下工具可用：
1. generate_code: 生成 Python 代码
2. test_code: 使用真实数据测试代码
3. check_code: 静态检查代码质量
4. analyze_error: 分析错误并提供修复建议

工作流程：
1. 首先使用 generate_code 生成初始代码
2. 使用 check_code 进行静态检查
3. 如果有测试数据，使用 test_code 进行运行时测试
4. 如果发现问题，使用 analyze_error 分析错误
5. 根据分析结果，重新使用 generate_code 生成改进的代码
6. 重复上述过程，直到代码通过所有检查或达到最大迭代次数

注意事项：
- 最多迭代 {max_iterations} 次
- 优先修复运行时错误
- 确保代码有完整的错误处理
- 使用 df.iloc[i] 而不是 df.loc[i] 访问行
"""
    
    # 创建 state modifier（用于注入系统消息）
    def state_modifier(state: ReactAgentState) -> List[BaseMessage]:
        messages = [SystemMessage(content=system_message)]
        messages.extend(state.get("messages", []))
        return messages
    
    # 使用 create_react_agent 创建 agent
    agent = create_react_agent(
        model=self.llm,
        tools=self.tools,
        state_modifier=state_modifier,
        state_schema=ReactAgentState
    )
    
    return agent
```

## Data Models

### Tool Input/Output Models

使用 Pydantic 定义工具的输入输出模型，确保类型安全：

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class GenerateCodeInput(BaseModel):
    """代码生成工具输入"""
    execution_spec: Dict[str, Any] = Field(description="执行规格")
    previous_code: Optional[str] = Field(default=None, description="上一次生成的代码")
    issues_to_fix: Optional[List[str]] = Field(default=None, description="需要修复的问题")

class GenerateCodeOutput(BaseModel):
    """代码生成工具输出"""
    code: str = Field(description="生成的代码")
    success: bool = Field(description="是否成功")
    message: str = Field(description="说明信息")

class TestCodeInput(BaseModel):
    """代码测试工具输入"""
    code: str = Field(description="要测试的代码")
    function_name: str = Field(description="函数名")
    test_data: Any = Field(description="测试数据")

class TestCodeOutput(BaseModel):
    """代码测试工具输出"""
    success: bool = Field(description="是否成功执行")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")

class CheckCodeInput(BaseModel):
    """代码检查工具输入"""
    code: str = Field(description="要检查的代码")
    function_name: str = Field(description="期望的函数名")

class CheckCodeOutput(BaseModel):
    """代码检查工具输出"""
    is_valid: bool = Field(description="代码是否有效")
    issues: List[str] = Field(description="发现的问题列表")

class AnalyzeErrorInput(BaseModel):
    """错误分析工具输入"""
    code: str = Field(description="有问题的代码")
    error: str = Field(description="错误信息")
    error_type: str = Field(description="错误类型（runtime/static）")

class AnalyzeErrorOutput(BaseModel):
    """错误分析工具输出"""
    analysis: str = Field(description="错误分析")
    suggestions: List[str] = Field(description="修复建议")
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After reviewing all testable criteria from the prework, I've identified the following groups:

**Group 1: Output Structure Properties** (2.5, 4.2, 4.4)
- These all relate to ensuring consistent output structure
- Can be combined into a single comprehensive property about output format

**Group 2: Error Handling Properties** (3.2, 7.2, 7.3)
- All about capturing and handling errors
- Can be combined into a property about error capture and propagation

**Group 3: Logging Properties** (6.2, 6.3, 6.4)
- All about logging tool invocations and results
- Can be combined into a single property about logging completeness

**Unique Properties to Keep**:
- 3.1: Code execution with test data
- 3.4: Maximum iteration count enforcement
- 3.6: Serialization of execution results

**Edge Cases** (7.1, 7.4, 7.5, 7.6):
- These are important but will be handled by property test generators
- Not separate properties, but scenarios to include in test generation

**Examples** (4.1, 4.3, 4.5, 3.5, 6.1, 6.5):
- Interface compatibility and specific scenarios
- Will be covered by unit tests, not property tests

### Correctness Properties

Property 1: Consistent Output Structure
*For any* valid execution specification and test data, when the agent completes processing, the output SHALL contain all required fields: generated_code (string), iteration_count (integer), is_code_valid (boolean), code_issues (list), runtime_error (string), and execution_result (dict or None).
**Validates: Requirements 2.5, 4.2, 4.4**

Property 2: Code Execution with Test Data
*For any* valid execution specification and non-empty test data, when the agent processes the request, the system SHALL attempt to execute the generated code with the provided test data.
**Validates: Requirements 3.1**

Property 3: Error Capture and Propagation
*For any* code that raises an exception during execution, the system SHALL capture the exception message and include it in the runtime_error field of the output, allowing the agent to use this information for fixing.
**Validates: Requirements 3.2, 7.2, 7.3**

Property 4: Maximum Iteration Enforcement
*For any* execution specification, regardless of code quality or errors, the system SHALL never exceed the configured max_iterations value, ensuring the process terminates.
**Validates: Requirements 3.4**

Property 5: Execution Result Serialization
*For any* successful code execution that returns a result, the system SHALL serialize the result into a JSON-compatible format that preserves the essential information (type, shape, sample data for large objects).
**Validates: Requirements 3.6**

Property 6: Tool Invocation Logging
*For any* tool invocation during agent execution, the system SHALL log the tool name, and when the tool completes, SHALL log the result status (success or failure).
**Validates: Requirements 6.2, 6.3, 6.4**

## Error Handling

### Error Categories

1. **LLM Errors**
   - Malformed JSON responses
   - Missing required fields
   - Invalid code syntax
   - **Handling**: Parse with try-except, provide default values, log warnings

2. **Code Execution Errors**
   - Runtime exceptions (IndexError, KeyError, etc.)
   - Missing dependencies
   - Timeout errors
   - **Handling**: Capture exception, serialize error message, pass to agent for fixing

3. **Tool Invocation Errors**
   - Invalid tool arguments
   - Tool execution failures
   - **Handling**: Return error in tool output, allow agent to retry with corrected arguments

4. **State Management Errors**
   - Missing required state fields
   - Type mismatches
   - **Handling**: Validate state before processing, provide sensible defaults

### Error Recovery Strategy

```python
def _safe_tool_execution(tool_func, *args, **kwargs):
    """
    安全执行工具，捕获所有异常
    """
    try:
        return tool_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### Iteration Control

```python
def _check_iteration_limit(state: ReactAgentState) -> bool:
    """
    检查是否达到迭代限制
    """
    iteration_count = state.get("iteration_count", 0)
    if iteration_count >= self.max_iterations:
        logger.warning(f"Reached max iterations ({self.max_iterations})")
        return True
    return False
```

## Testing Strategy

### Unit Testing

**Tool Tests** - 每个工具独立测试：

1. **test_generate_code_tool**
   - 测试正常代码生成
   - 测试带修复建议的代码生成
   - 测试 LLM 返回格式错误的处理

2. **test_test_code_tool**
   - 测试成功执行的代码
   - 测试运行时错误的捕获
   - 测试缺少测试数据的情况
   - 测试结果序列化

3. **test_check_code_tool**
   - 测试有效代码的检查
   - 测试各种代码问题的检测（缺少函数、缺少return、语法错误等）

4. **test_analyze_error_tool**
   - 测试运行时错误分析
   - 测试静态错误分析
   - 测试 LLM 返回格式错误的处理

**Integration Tests** - 完整流程测试：

1. **test_simple_code_generation**
   - 简单的执行规格，一次生成成功

2. **test_code_with_runtime_error**
   - 第一次生成有运行时错误，第二次修复成功

3. **test_max_iterations**
   - 强制达到最大迭代次数，验证返回最佳代码

4. **test_no_test_data**
   - 没有测试数据，只进行静态检查

### Property-Based Testing

使用 **Hypothesis** 库进行属性测试。

**Property Test 1: Output Structure Consistency**
```python
from hypothesis import given, strategies as st

@given(
    execution_spec=st.fixed_dictionaries({
        'function_name': st.text(min_size=1),
        'description': st.text(),
        'parameters': st.lists(st.text())
    }),
    test_data=st.one_of(st.none(), st.just(pd.DataFrame({'col': [1, 2, 3]})))
)
def test_output_structure_consistency(execution_spec, test_data):
    """
    Property: 输出结构一致性
    Feature: coding-agent-refactor, Property 1
    """
    agent = CodingAgentV3(llm_client, test_data)
    result = agent.process({
        'execution_spec': execution_spec,
        'current_step': {},
        'test_data': test_data
    })
    
    # 验证所有必需字段存在
    assert 'generated_code' in result
    assert 'iteration_count' in result
    assert 'is_code_valid' in result
    assert 'code_issues' in result
    assert 'runtime_error' in result
    assert 'execution_result' in result
    
    # 验证字段类型
    assert isinstance(result['generated_code'], str)
    assert isinstance(result['iteration_count'], int)
    assert isinstance(result['is_code_valid'], bool)
    assert isinstance(result['code_issues'], list)
    assert isinstance(result['runtime_error'], str)
```

**Property Test 2: Maximum Iteration Enforcement**
```python
@given(
    execution_spec=st.fixed_dictionaries({
        'function_name': st.text(min_size=1),
        'description': st.text()
    }),
    max_iterations=st.integers(min_value=1, max_value=5)
)
def test_max_iteration_enforcement(execution_spec, max_iterations):
    """
    Property: 最大迭代次数强制执行
    Feature: coding-agent-refactor, Property 4
    """
    agent = CodingAgentV3(llm_client, max_iterations=max_iterations)
    result = agent.process({
        'execution_spec': execution_spec,
        'current_step': {},
        'test_data': None
    })
    
    # 验证迭代次数不超过最大值
    assert result['iteration_count'] <= max_iterations
```

**Property Test 3: Error Capture**
```python
@given(
    code_with_error=st.text(min_size=10)
)
def test_error_capture(code_with_error):
    """
    Property: 错误捕获
    Feature: coding-agent-refactor, Property 3
    """
    # 创建一个会产生错误的执行规格
    execution_spec = {
        'function_name': 'buggy_func',
        'description': 'A function that will fail'
    }
    
    # Mock LLM to return buggy code
    with patch.object(llm_client, 'invoke', return_value=code_with_error):
        agent = CodingAgentV3(llm_client, test_data=pd.DataFrame({'col': [1]}))
        result = agent.process({
            'execution_spec': execution_spec,
            'current_step': {},
            'test_data': pd.DataFrame({'col': [1]})
        })
        
        # 如果代码执行失败，应该捕获错误
        if not result['is_code_valid']:
            assert len(result['runtime_error']) > 0 or len(result['code_issues']) > 0
```

**Property Test 4: Serialization**
```python
@given(
    result_data=st.one_of(
        st.dictionaries(st.text(), st.integers()),
        st.lists(st.floats()),
        st.just(pd.DataFrame({'a': [1, 2, 3]}))
    )
)
def test_serialization(result_data):
    """
    Property: 执行结果序列化
    Feature: coding-agent-refactor, Property 5
    """
    agent = CodingAgentV3(llm_client)
    serialized = agent._serialize_result(result_data)
    
    # 验证序列化结果是 JSON 兼容的
    import json
    try:
        json.dumps(serialized)
        assert True
    except (TypeError, ValueError):
        assert False, "Serialized result is not JSON-compatible"
```

### Comparison Testing

创建对比测试，确保 V3 与 V2 的行为一致：

```python
def test_v2_v3_compatibility():
    """
    对比测试：V3 应该产生与 V2 相同格式的输出
    """
    execution_spec = {
        'function_name': 'analyze_data',
        'description': 'Analyze patent data',
        'parameters': ['df']
    }
    test_data = pd.DataFrame({'col': [1, 2, 3]})
    
    # V2
    agent_v2 = CodingAgentV2(llm_client, test_data)
    result_v2 = agent_v2.process({
        'execution_spec': execution_spec,
        'current_step': {},
        'test_data': test_data
    })
    
    # V3
    agent_v3 = CodingAgentV3(llm_client, test_data)
    result_v3 = agent_v3.process({
        'execution_spec': execution_spec,
        'current_step': {},
        'test_data': test_data
    })
    
    # 验证输出格式相同
    assert set(result_v2.keys()) == set(result_v3.keys())
    assert type(result_v2['generated_code']) == type(result_v3['generated_code'])
    assert type(result_v2['iteration_count']) == type(result_v3['iteration_count'])
```

## Implementation Notes

### Migration Path

1. **Phase 1**: 创建 CodingAgentV3，与 V2 并存
2. **Phase 2**: 在测试环境中使用 V3，对比结果
3. **Phase 3**: 逐步迁移生产环境
4. **Phase 4**: 废弃 V2

### Performance Considerations

- **Tool Overhead**: 每次工具调用都有 LLM 推理开销，但 LangGraph 的 ReAct 实现已经优化
- **State Size**: 使用 MessagesState 会保存所有消息历史，需要注意内存使用
- **Iteration Control**: 通过 max_iterations 控制，避免无限循环

### Backward Compatibility

保持以下接口不变：
- `process(input_data)` 方法签名
- 输入参数结构
- 输出字段和类型
- 与 WorkflowState 的集成

### Future Extensions

使用工具架构后，可以轻松添加：
- **optimize_code_tool**: 优化代码性能
- **document_code_tool**: 自动生成文档
- **refactor_code_tool**: 重构代码结构
- **security_check_tool**: 安全检查

只需定义新工具并添加到工具列表，无需修改 agent 结构。
