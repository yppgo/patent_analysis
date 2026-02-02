# 通义千问VL PDF提取测试

## 简介

使用 `qwen-vl-ocr-2025-11-20` 模型从PDF论文中提取因果关系，作为Claude的平替方案。

## 优势

- **成本低**: 通义千问价格约为Claude的1/10
- **中文能力强**: 特别适合中文专利分析
- **支持PDF**: 原生支持PDF文档理解
- **OCR能力**: 专门优化的OCR模型，能处理扫描版PDF

## 使用方法

### 1. 安装依赖

```bash
pip install dashscope
```

### 2. 配置API Key

在 `.env` 文件中设置：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 运行测试

**方式1: 指定PDF路径**
```bash
python scripts/test_qwen_vl_pdf_extraction.py path/to/your/paper.pdf
```

**方式2: 自动查找PDF**
```bash
# 将PDF放在以下任一文件夹，脚本会自动找到第一个
# - downloads/
# - data/
# - 项目根目录
python scripts/test_qwen_vl_pdf_extraction.py
```

## 输出结果

测试结果会保存到：
```
outputs/qwen_vl_test/{paper_name}_qwen_vl.json
```

结果包含：
- 论文标题和领域
- 因果关系列表
- 复杂关系（中介、调节效应）
- API调用耗时

## 与Claude版本对比

| 特性 | Claude V3 | Qwen VL OCR |
|------|-----------|-------------|
| 成本 | ~$3/1M tokens | ~$0.3/1M tokens |
| PDF支持 | ✅ 原生 | ✅ 原生 |
| 中文能力 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| OCR能力 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 并行处理 | ✅ 支持 | ✅ 可扩展 |

## 注意事项

1. **模型限制**: `qwen-vl-ocr-2025-11-20` 是专门用于OCR的模型，对于纯文本PDF可能不如 `qwen-vl-max` 效果好
2. **文件大小**: 建议PDF文件不超过20MB
3. **API限制**: 注意DashScope的调用频率限制

## 下一步

如果测试效果良好，可以：
1. 修改 `extract_causal_with_claude_v3.py` 支持Qwen模型
2. 添加批量处理功能
3. 集成到主流程中

## 故障排除

**问题**: `ImportError: No module named 'dashscope'`
- 解决: `pip install dashscope`

**问题**: `ValueError: 请设置 DASHSCOPE_API_KEY`
- 解决: 在 `.env` 文件中设置API Key

**问题**: API调用失败
- 检查: API Key是否正确，账户余额是否充足
