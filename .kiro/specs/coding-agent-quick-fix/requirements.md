# Requirements Document

## Introduction

本规格旨在快速修复 CodingAgentV3 中的两个核心问题，提高代码生成的成功率。当前系统在生成代码时遇到类型导入错误和函数参数依赖问题，导致成功率为 0%。

## Glossary

- **CodingAgentV3**: 负责根据执行规格生成可执行代码的智能体
- **Methodologist**: 负责生成执行规格（函数签名和参数）的智能体
- **执行规格**: 包含函数名、参数、算法等信息的规范
- **运行时测试**: 使用真实数据测试生成的代码是否可执行

## Requirements

### Requirement 1

**User Story:** 作为系统开发者，我希望生成的代码能够正确导入所需的类型，以便代码可以通过静态检查和运行时测试

#### Acceptance Criteria

1. WHEN CodingAgentV3 生成使用 Tuple、List、Dict 等类型的代码 THEN 系统应自动添加 `from typing import` 导入语句
2. WHEN 生成的代码需要类型注解 THEN 系统应确保所有使用的类型都已正确导入
3. WHEN 代码通过静态检查 THEN 系统应确保没有 `name 'Tuple' is not defined` 类型的错误

### Requirement 2

**User Story:** 作为系统开发者，我希望生成的函数是自包含的，不依赖外部参数，以便可以直接使用测试数据进行测试

#### Acceptance Criteria

1. WHEN Methodologist 生成需要额外参数的函数规格（如 keyword_network、criteria_weights）THEN 系统应将这些参数的构建逻辑包含在函数内部
2. WHEN CodingAgentV3 生成函数代码 THEN 函数应只接受 DataFrame 作为输入参数
3. WHEN 运行时测试执行 THEN 测试应能够仅使用 test_data 成功调用函数
4. WHEN 函数需要额外的数据结构 THEN 函数应在内部从 DataFrame 构建这些数据结构

### Requirement 3

**User Story:** 作为系统开发者，我希望限制可使用的外部库，以便生成的代码不会因为缺少依赖而失败

#### Acceptance Criteria

1. WHEN Methodologist 生成执行规格 THEN 系统应只使用 pandas、numpy、sklearn 等已安装的库
2. WHEN 执行规格包含库信息 THEN 系统应验证这些库是否可用
3. WHEN 生成的代码导入外部库 THEN 系统应确保这些库在环境中已安装
