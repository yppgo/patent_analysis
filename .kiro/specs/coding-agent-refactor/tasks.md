# Implementation Plan

- [-] 1. 创建工具定义和数据模型



  - 创建 Pydantic 模型定义所有工具的输入输出
  - 实现 4 个核心工具函数（generate_code, test_code, check_code, analyze_error）
  - 为每个工具添加详细的 docstring 以指导 LLM
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [-] 1.1 编写工具单元测试

  - **Property 1: 输出结构一致性**
  - **Validates: Requirements 2.5**

- [ ] 2. 实现 CodingAgentV3 核心类
  - 创建 `src/agents/coding_agent_v3.py` 文件
  - 实现 `__init__` 方法，初始化工具和 agent
  - 实现 `_create_tools()` 方法，创建工具列表
  - 实现 `_build_agent()` 方法，使用 `create_react_agent` 构建 agent
  - 保持继承 BaseAgent 以维持接口兼容性
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3. 实现 process 方法和状态管理
  - 实现 `process(input_data)` 方法，保持与 V2 相同的签名
  - 创建 ReactAgentState 状态类
  - 实现状态初始化和转换逻辑
  - 实现结果提取和格式化
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.1 编写属性测试：输出结构一致性
  - **Property 1: 输出结构一致性**
  - **Validates: Requirements 2.5, 4.2, 4.4**

- [ ] 4. 实现代码生成工具
  - 实现 `generate_code` 工具函数
  - 构建代码生成 prompt，包含执行规格和修复建议
  - 实现代码提取逻辑（移除 markdown 标记和 import 语句）
  - 添加错误处理和日志记录
  - _Requirements: 2.1, 2.5, 6.2, 6.3_

- [ ] 4.1 编写单元测试：代码生成工具
  - 测试正常代码生成
  - 测试带修复建议的代码生成
  - 测试 LLM 返回格式错误的处理
  - _Requirements: 2.1, 7.4_

- [ ] 5. 实现代码测试工具
  - 实现 `test_code` 工具函数
  - 实现 `_prepare_execution_environment()` 辅助方法
  - 实现代码执行逻辑（使用 exec）
  - 实现异常捕获和错误消息提取
  - 实现 `_serialize_result()` 方法处理各种数据类型
  - _Requirements: 2.2, 2.5, 3.1, 3.2, 3.6, 6.2, 6.3, 6.4_

- [ ] 5.1 编写属性测试：代码执行与测试数据
  - **Property 2: 代码执行与测试数据**
  - **Validates: Requirements 3.1**

- [ ] 5.2 编写属性测试：错误捕获和传播
  - **Property 3: 错误捕获和传播**
  - **Validates: Requirements 3.2, 7.2, 7.3**

- [ ] 5.3 编写属性测试：执行结果序列化
  - **Property 5: 执行结果序列化**
  - **Validates: Requirements 3.6**

- [ ] 5.4 编写单元测试：代码测试工具
  - 测试成功执行的代码
  - 测试运行时错误的捕获
  - 测试缺少测试数据的情况（边界情况）
  - 测试结果序列化
  - _Requirements: 2.2, 3.1, 3.2, 7.1_

- [ ] 6. 实现代码检查工具
  - 实现 `check_code` 工具函数
  - 实现静态检查逻辑（函数定义、return 语句、错误处理、类型注解）
  - 实现语法检查（使用 compile）
  - 添加日志记录
  - _Requirements: 2.3, 2.5, 6.2, 6.3_

- [ ] 6.1 编写单元测试：代码检查工具
  - 测试有效代码的检查
  - 测试各种代码问题的检测
  - _Requirements: 2.3_

- [ ] 7. 实现错误分析工具
  - 实现 `analyze_error` 工具函数
  - 构建错误分析 prompt
  - 实现 LLM 调用和响应解析
  - 提取修复建议
  - 添加错误处理和日志记录
  - _Requirements: 2.4, 2.5, 6.2, 6.3_

- [ ] 7.1 编写单元测试：错误分析工具
  - 测试运行时错误分析
  - 测试静态错误分析
  - 测试 LLM 返回格式错误的处理
  - _Requirements: 2.4, 7.4_

- [ ] 8. 实现迭代控制和日志记录
  - 在 agent 配置中添加迭代计数逻辑
  - 实现最大迭代次数检查
  - 添加详细的日志记录（使用 emoji 指示器）
  - 实现日志记录工具调用和完成
  - _Requirements: 3.4, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8.1 编写属性测试：最大迭代次数强制执行
  - **Property 4: 最大迭代次数强制执行**
  - **Validates: Requirements 3.4**

- [ ] 8.2 编写属性测试：工具调用日志记录
  - **Property 6: 工具调用日志记录**
  - **Validates: Requirements 6.2, 6.3, 6.4**

- [ ] 8.3 编写单元测试：迭代控制
  - 测试达到最大迭代次数的情况
  - 测试日志记录功能
  - _Requirements: 3.4, 3.5, 6.1, 6.5_

- [ ] 9. 实现边界情况处理
  - 处理 test_data 为 None 或空的情况
  - 处理代码生成失败的情况
  - 处理 LLM 返回格式错误的情况
  - 处理缺少依赖库的情况（mock 实现）
  - 处理序列化失败的情况
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 9.1 编写边界情况测试
  - 测试无测试数据的情况
  - 测试代码生成失败的情况
  - 测试 LLM 格式错误的情况
  - 测试缺少依赖的情况
  - 测试序列化失败的情况
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 10. 集成测试和对比测试
  - 创建集成测试脚本 `test_coding_agent_v3.py`
  - 测试简单代码生成流程
  - 测试带运行时错误的修复流程
  - 测试最大迭代次数场景
  - 测试无测试数据场景
  - _Requirements: 8.4_

- [ ] 10.1 编写对比测试：V2 vs V3
  - 对比相同输入下 V2 和 V3 的输出格式
  - 验证输出字段一致性
  - 验证类型一致性
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.3_

- [ ] 11. 更新工作流集成
  - 在 `src/core/workflow.py` 中添加 V3 选项
  - 创建配置开关允许选择 V2 或 V3
  - 更新文档说明如何切换版本
  - _Requirements: 4.5_

- [ ] 12. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，询问用户是否有问题

- [ ] 13. 文档和清理
  - 更新 README 说明 V3 的改进
  - 添加迁移指南
  - 添加工具扩展示例
  - 标记 V2 为 deprecated（如果 V3 稳定）
  - _Requirements: 5.5_
