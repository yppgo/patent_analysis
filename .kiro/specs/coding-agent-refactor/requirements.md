# Requirements Document

## Introduction

本文档定义了将 CodingAgentV2 从手动实现的 ReAct 模式重构为使用 LangGraph 预构建 `create_react_agent` 的需求。目标是简化代码实现、提高可维护性，同时保持现有的所有功能（代码生成、运行时测试、自动修复）。

## Glossary

- **CodingAgent**: 编码智能体，负责根据执行规格生成 Python 代码
- **ReAct Pattern**: Reasoning + Acting 模式，一种 AI agent 的设计模式，包含思考、行动、观察的循环
- **LangGraph**: LangChain 的图执行框架，用于构建复杂的 AI 工作流
- **create_react_agent**: LangGraph 提供的预构建函数，用于快速创建 ReAct agent
- **Tool**: 工具，agent 可以调用的函数，用于执行特定任务
- **Execution Spec**: 执行规格，描述需要生成的代码的详细信息
- **Runtime Testing**: 运行时测试，使用真实数据执行生成的代码以验证其正确性
- **Static Check**: 静态检查，不执行代码的情况下检查代码质量（语法、结构等）

## Requirements

### Requirement 1

**User Story:** 作为开发者，我希望使用 LangGraph 的预构建 ReAct agent，以便简化代码实现并提高可维护性。

#### Acceptance Criteria

1. WHEN the system initializes CodingAgent THEN the system SHALL use `create_react_agent` from LangGraph to build the agent
2. WHEN the agent is created THEN the system SHALL define tools that the agent can use for code generation and testing
3. WHEN the agent executes THEN the system SHALL follow the standard ReAct pattern (reasoning, tool selection, observation)
4. THE system SHALL maintain compatibility with the existing BaseAgent interface
5. THE system SHALL preserve all logging functionality from the current implementation

### Requirement 2

**User Story:** 作为开发者，我希望将代码生成、测试、检查等功能定义为独立的工具，以便 agent 可以灵活地选择和组合使用。

#### Acceptance Criteria

1. THE system SHALL define a code generation tool that accepts execution specifications and returns Python code
2. THE system SHALL define a runtime testing tool that executes generated code with test data
3. THE system SHALL define a static checking tool that validates code quality without execution
4. THE system SHALL define a code fixing tool that improves code based on identified issues
5. WHEN a tool is invoked THEN the system SHALL return structured results including success status and any errors
6. THE system SHALL ensure each tool has clear input/output schemas
7. THE system SHALL provide detailed docstrings for each tool to guide the LLM's tool selection

### Requirement 3

**User Story:** 作为开发者，我希望保留现有的运行时测试和自动修复能力，以确保生成的代码质量。

#### Acceptance Criteria

1. WHEN test data is provided THEN the system SHALL execute the generated code with the test data
2. WHEN runtime errors occur THEN the system SHALL capture the error message and make it available to the agent
3. WHEN code issues are detected THEN the system SHALL allow the agent to iterate and fix the code
4. THE system SHALL support a maximum iteration count to prevent infinite loops
5. WHEN the maximum iteration count is reached THEN the system SHALL return the best available code
6. THE system SHALL serialize execution results for storage and later use by other agents

### Requirement 4

**User Story:** 作为开发者，我希望保持与现有系统的兼容性，以便不影响其他 agent 和工作流的正常运行。

#### Acceptance Criteria

1. THE refactored CodingAgent SHALL maintain the same `process()` method signature
2. WHEN other agents call CodingAgent THEN the system SHALL return results in the same format as before
3. THE system SHALL accept the same input parameters (execution_spec, current_step, test_data)
4. THE system SHALL return the same output fields (generated_code, iteration_count, is_code_valid, code_issues, runtime_error, execution_result)
5. THE system SHALL work seamlessly with the existing WorkflowState and CodingAgentState definitions

### Requirement 5

**User Story:** 作为开发者，我希望新实现更简洁易懂，以便未来的维护和扩展。

#### Acceptance Criteria

1. THE system SHALL reduce the total lines of code compared to the current implementation
2. THE system SHALL eliminate manual state graph construction (nodes, edges, conditional edges)
3. THE system SHALL use declarative tool definitions instead of imperative node functions
4. THE system SHALL maintain clear separation between tool logic and agent orchestration
5. WHEN new capabilities are needed THEN the system SHALL allow adding new tools without modifying the agent structure

### Requirement 6

**User Story:** 作为开发者，我希望保留详细的日志记录，以便调试和监控 agent 的执行过程。

#### Acceptance Criteria

1. WHEN the agent starts processing THEN the system SHALL log the function name being generated
2. WHEN a tool is invoked THEN the system SHALL log the tool name and key parameters
3. WHEN a tool completes THEN the system SHALL log the result status (success/failure)
4. WHEN runtime errors occur THEN the system SHALL log the error details
5. WHEN the agent completes THEN the system SHALL log the total iteration count and final status
6. THE system SHALL use emoji indicators (🤔, ⚡, 🧪, 👀, 🔄) for visual clarity in logs

### Requirement 7

**User Story:** 作为开发者，我希望新实现能够处理边界情况和错误，以确保系统的健壮性。

#### Acceptance Criteria

1. WHEN test data is None or empty THEN the system SHALL skip runtime testing and proceed with static checks only
2. WHEN code generation fails THEN the system SHALL return an error message and allow retry
3. WHEN code execution raises an exception THEN the system SHALL capture the exception and provide it to the agent for fixing
4. WHEN the LLM returns malformed responses THEN the system SHALL handle parsing errors gracefully
5. WHEN required libraries are missing THEN the system SHALL provide mock implementations to allow code execution
6. WHEN serialization of execution results fails THEN the system SHALL return a simplified representation

### Requirement 8

**User Story:** 作为开发者，我希望能够轻松测试重构后的 CodingAgent，以验证其功能正确性。

#### Acceptance Criteria

1. THE system SHALL provide unit tests for each individual tool
2. THE system SHALL provide integration tests that verify the complete agent workflow
3. THE system SHALL include tests that compare outputs with the original implementation
4. WHEN tests are run THEN the system SHALL verify that all existing test cases still pass
5. THE system SHALL include tests for edge cases (no test data, runtime errors, max iterations)
