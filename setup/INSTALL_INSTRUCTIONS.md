# 🔧 安装说明

## Windows 用户

### 方法 1：一键运行（推荐）

直接双击以下批处理文件：

```
setup_and_run_strategist.bat
```

### 方法 2：命令行运行

```cmd
# 在项目根目录打开命令提示符
setup_and_run_strategist.bat
```

### 其他批处理脚本

```cmd
# 运行测试
run_test_strategist.bat

# 运行示例
run_example_strategist.bat
```

---

## Linux/Mac 用户

### 第一次运行

```bash
# 1. 给脚本添加执行权限
chmod +x setup_and_run_strategist.sh

# 2. 运行脚本
./setup_and_run_strategist.sh
```

### 后续运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行程序
python strategist_graph.py

# 或运行测试
python test_strategist.py

# 或运行示例
python example_strategist_usage.py
```

---

## 手动安装步骤（所有平台）

### 1. 创建虚拟环境

```bash
# Windows
python -m venv .venv

# Linux/Mac
python3 -m venv .venv
```

### 2. 激活虚拟环境

```bash
# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

编辑 `.env` 文件：

```env
DASHSCOPE_API_KEY=sk-your-api-key-here
```

### 5. 配置 Neo4j

编辑 `neo4j_config.py`：

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
}
```

### 6. 运行程序

```bash
python strategist_graph.py
```

---

## 验证安装

### 检查虚拟环境

```bash
# 应该看到 (.venv) 前缀
# Windows
where python

# Linux/Mac
which python
```

### 检查依赖

```bash
pip list | grep langgraph
pip list | grep langchain
pip list | grep neo4j
```

### 测试连接

```bash
# 测试 Neo4j
python test_neo4j_connection.py

# 测试 API Key
python test_api_key.py
```

---

## 常见问题

### Q: 虚拟环境激活失败

**Windows PowerShell 执行策略问题：**

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**或使用 CMD 代替 PowerShell**

### Q: pip 安装速度慢

使用国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 找不到 python 命令

**Windows:**
- 确保 Python 已添加到 PATH
- 或使用 `py` 命令代替 `python`

**Linux/Mac:**
- 使用 `python3` 代替 `python`

### Q: Neo4j 连接失败

1. 确保 Neo4j 服务正在运行
2. 检查端口 7687 是否开放
3. 验证用户名和密码

---

## 依赖列表

```
pdfplumber>=0.9.0
dashscope>=1.14.0
python-dotenv>=1.0.0
langgraph>=0.0.20
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.20
neo4j>=5.14.0
```

---

## 卸载

### 删除虚拟环境

```bash
# Windows
rmdir /s /q .venv

# Linux/Mac
rm -rf .venv
```

### 清理生成的文件

```bash
# Windows
del strategist_output.json
del test_strategist_results.json
del batch_strategist_results.json

# Linux/Mac
rm strategist_output.json
rm test_strategist_results.json
rm batch_strategist_results.json
```

---

## 下一步

安装完成后，请阅读：
- `QUICKSTART_STRATEGIST.md` - 快速入门
- `STRATEGIST_README.md` - 完整文档

---

**需要帮助？** 检查 `QUICKSTART_STRATEGIST.md` 中的故障排除部分。
