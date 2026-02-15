# 安装与运行说明（当前版本）

## 1. 创建并激活虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

## 2. 安装依赖

```bash
pip install -r config/requirements.txt
```

## 3. 配置 `.env`

在项目根目录创建 `.env`：

```env
# 默认 Agent（Strategist/Methodologist/Reviewer）
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_key
DASHSCOPE_MODEL=qwen3-max

# Coding Agent（可选单独配置）
CODING_LLM_PROVIDER=anthropic
CODING_ANTHROPIC_API_KEY=your_key
CODING_ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
# 可选：CODING_ANTHROPIC_BASE_URL=...
```

> 说明：`CODING_` 前缀配置会只作用于 Coding Agent。

## 4. 运行方式

### 单次端到端测试

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py
```

### 四方案对比实验（D/A/B/C）

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py --compare
```

### 仅运行纯 LLM 基线（D_baseline0）

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_full_pipeline_with_coding_v4_2.py --baseline0
```

### 实验量化评估（自动指标 + LLM-as-Judge）

```bash
# 全量评估
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py

# 仅自动化指标
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py --auto-only

# 仅 LLM 评分
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/evaluate_experiments.py --llm-only
```

输出文件位于 `outputs/`，包含 `experiment_*.json`、`experiment_summary.json`、`evaluation_*.json`。

## 5. 常见问题

### PowerShell 无法激活虚拟环境

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 控制台出现中文编码问题

运行前加：

```bash
PYTHONIOENCODING=utf-8
```

### 依赖安装慢

```bash
pip install -r config/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 6. 当前有效文档

- `README.md`
- `docs/PROJECT_OVERVIEW.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/项目进展记录.md`
