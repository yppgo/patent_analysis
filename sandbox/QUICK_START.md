# 🚀 快速启动指南

## 方式1：使用 Python 服务器（推荐）

```bash
cd sandbox
python start_viewer.py
```

浏览器会自动打开，展示3个可视化界面：
1. **因果本体论浏览器** ⭐ 推荐 - 完整的25变量35路径图谱
2. **假设生成演示** - 端到端的假设生成流程
3. **因果图谱查看器** - 原始的简单图谱

## 方式2：直接打开 HTML

如果 Python 服务器有问题，可以直接在浏览器中打开：

```
sandbox/ontology_explorer.html
```

注意：某些浏览器可能会阻止本地文件加载，建议使用方式1。

## 方式3：使用其他 HTTP 服务器

### Node.js (http-server)
```bash
cd sandbox
npx http-server -p 8000
```

### Python 内置服务器
```bash
cd sandbox
python -m http.server 8000
```

然后访问: http://localhost:8000/ontology_explorer.html

## 📊 界面说明

### 因果本体论浏览器 (ontology_explorer.html)

**功能**：
- 交互式力导向图（25个节点，35条边）
- 点击节点查看详细信息
- 点击路径查看因果关系
- 搜索和筛选功能

**操作**：
- 🖱️ 拖拽节点调整位置
- 🔍 滚轮缩放画布
- 👆 点击节点/路径查看详情
- 🔎 使用搜索框快速定位

### 假设生成演示 (hypothesis_viewer.html)

**功能**：
- 6步流程演示
- 5个研究假设生成
- 完整的分析方案

**操作**：
- 点击"下一步"/"上一步"按钮导航
- 查看每个假设的新颖性评分
- 查看推荐假设和分析方案

## 🔧 故障排除

### 问题1：无法加载数据

**症状**：界面显示"无法加载数据文件"

**解决方案**：
1. 确认文件存在：
   ```bash
   ls sandbox/static/data/complete_causal_ontology.json
   ```

2. 验证JSON格式：
   ```bash
   python -m json.tool sandbox/static/data/complete_causal_ontology.json > nul
   ```

3. 测试数据加载：
   ```bash
   python sandbox/test_ontology_load.py
   ```

### 问题2：浏览器CORS错误

**症状**：控制台显示 "CORS policy" 错误

**解决方案**：
- 必须使用 HTTP 服务器，不能直接打开 HTML 文件
- 使用方式1或方式3启动服务器

### 问题3：图谱显示不完整

**症状**：只显示部分节点或路径

**解决方案**：
1. 刷新页面（Ctrl+F5 强制刷新）
2. 点击"重置视图"按钮
3. 检查浏览器控制台是否有错误

### 问题4：Python 服务器启动失败

**症状**：端口被占用

**解决方案**：
1. 修改端口号：
   编辑 `start_viewer.py`，将 `PORT = 8000` 改为其他端口

2. 或者关闭占用端口的程序：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

## 📝 数据文件说明

### 核心数据文件

1. **complete_causal_ontology.json** (完整因果本体论)
   - 25个变量
   - 35条因果路径
   - 包含理论依据和文献支持

2. **hypothesis_example.json** (假设生成示例)
   - 完整的6步流程数据
   - 5个研究假设
   - 分析方案

3. **hypothesis_generator.json** (假设生成器配置)
   - 变量池定义
   - 6种生成策略
   - 输出模板

### 文件位置

```
sandbox/
├── static/
│   └── data/
│       ├── complete_causal_ontology.json  ← 主数据文件
│       ├── hypothesis_example.json
│       ├── hypothesis_generator.json
│       ├── causal_graph.json
│       └── causal_graph_v2.json
├── ontology_explorer.html  ← 主界面
├── hypothesis_viewer.html
├── causal_graph_viewer.html
└── start_viewer.py  ← 启动脚本
```

## 🎯 使用建议

### 第一次使用

1. 先运行测试脚本确认数据正常：
   ```bash
   python sandbox/test_ontology_load.py
   ```

2. 启动服务器：
   ```bash
   python sandbox/start_viewer.py
   ```

3. 浏览器会自动打开，开始探索！

### 日常使用

- 直接运行 `python sandbox/start_viewer.py`
- 或者双击 `sandbox/start_viewer.bat` (Windows)

## 📖 更多信息

- 完整文档：`sandbox/ONTOLOGY_README.md`
- 可视化说明：`sandbox/README_VIEWER.md`
- 测试脚本：`sandbox/test_ontology_load.py`

## 💡 提示

- 首次加载可能需要几秒钟
- 建议使用 Chrome 或 Firefox 浏览器
- 如果图谱太密集，可以拖拽节点调整布局
- 使用搜索功能快速定位感兴趣的变量

---

**遇到问题？** 检查浏览器控制台（F12）查看错误信息。
