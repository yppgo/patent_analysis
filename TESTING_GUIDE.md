# 测试指南

本项目包含以下测试文件，用于验证系统的不同功能模块。

## 主要测试文件

### 1. test_full_system_with_real_data.py ⭐ **推荐**
**完整的 4 Agent 协作测试**

- **测试范围**: Strategist → Methodologist → CodingAgent V4.1 → Reviewer
- **数据源**: 真实专利数据（50条样本）
- **功能**:
  - 完整工作流测试
  - 真实数据分析
  - 生成最终报告
  - 保存所有中间结果
- **输出目录**: `outputs/`
- **运行命令**: `python test_full_system_with_real_data.py`

**适用场景**: 
- 验证完整系统功能
- 端到端测试
- 生成实际分析报告

**主要输出文件**:
- `outputs/final_report.md` - 最终分析报告 ⭐
- `outputs/verification_result.json` - 验证结果
- `outputs/step_*.py` - 生成的分析代码
- `outputs/step_*_results.csv` - 分析结果数据

---

### 2. test_strategist_coding_simple.py
**Strategist + CodingAgent 简单测试**

- **测试范围**: Strategist → CodingAgent V4.1
- **数据源**: 真实专利数据
- **功能**:
  - 测试战略规划
  - 测试代码生成
  - 不包含 Methodologist 和 Reviewer
- **运行命令**: `python test_strategist_coding_simple.py`

**适用场景**:
- 快速测试 Strategist 和 CodingAgent
- 调试代码生成逻辑
- 不需要完整报告

---

### 3. test_v4_1_complete.py
**CodingAgent V4.1 完整功能测试**

- **测试范围**: CodingAgent V4.1 的所有功能
- **数据源**: Mock 数据
- **功能**:
  - 测试代码生成
  - 测试执行规格解析
  - 测试错误处理和重试
  - 测试文件保存
- **运行命令**: `python test_v4_1_complete.py`

**适用场景**:
- 测试 CodingAgent 的核心功能
- 验证代码生成质量
- 调试执行逻辑

---

### 4. test_v4_1_quick.py
**CodingAgent V4.1 快速测试**

- **测试范围**: CodingAgent V4.1 基础功能
- **数据源**: Mock 数据
- **功能**:
  - 快速验证代码提取
  - 测试基本的代码生成
  - 轻量级测试
- **运行命令**: `python test_v4_1_quick.py`

**适用场景**:
- 快速验证 CodingAgent 是否正常工作
- 开发过程中的快速测试
- CI/CD 流水线

---

## 测试输出

### 主要输出目录

```
outputs/
├── final_report.md            # 最终分析报告 ⭐
├── verification_result.json   # 验证结果
├── blueprint.json             # 战略蓝图
├── execution_specs.json       # 执行规格
├── code_metadata.json         # 代码元数据
├── analysis_results.json      # 分析结果汇总
├── generated_code_*.py        # 生成的代码副本
│
├── step_1.py                  # 步骤1代码
├── step_1_topic_results.csv   # 步骤1结果
├── step_1_lda_model.pkl       # 步骤1模型
├── step_2.py                  # 步骤2代码
├── step_2_outlier_results.csv # 步骤2结果
├── step_2_abod_model.pkl      # 步骤2模型
├── step_3.py                  # 步骤3代码
└── step_3_keywords_results.csv # 步骤3结果
```

---

## 推荐测试流程

### 开发阶段
1. 使用 `test_v4_1_quick.py` 快速验证基础功能
2. 使用 `test_v4_1_complete.py` 验证完整功能
3. 使用 `test_strategist_coding_simple.py` 测试集成

### 发布前
1. 运行 `test_full_system_with_real_data.py` 进行完整测试
2. 检查 `outputs/final_report.md` 确认报告质量
3. 验证所有 CSV 结果文件

---

## 常见问题

### Q: 测试卡住不动？
A: 可能是 LLM 调用超时，检查网络连接和 API 配置。

### Q: 代码生成失败？
A: 检查 `outputs/` 目录下的生成代码，查看错误信息。

### Q: 报告没有包含实际数据？
A: 确保 CSV 文件已生成，Reviewer 会自动读取这些文件。

### Q: 步骤执行失败但继续运行？
A: 系统会尝试继续执行后续步骤，最终在报告中标注失败的步骤。

---

## 版本历史

- **V4.1**: 文件基础架构，独立脚本执行
- **V4.0**: 函数基础架构
- **V3.0**: 早期版本（已废弃）
