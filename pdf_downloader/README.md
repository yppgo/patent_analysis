# PDF 下载工具

本目录包含用于下载学术论文 PDF 的工具脚本。

## 📁 文件说明

### 主要下载脚本

- **`download_pdfs_chrome.py`** - 基础版 Chrome 自动化下载脚本
- **`download_pdfs_chrome_optimized.py`** - 优化版下载脚本（推荐使用）
- **`download_all_pdfs_chrome.py`** - 批量下载所有 PDF

### 辅助工具

- **`download_chromedriver.py`** - 自动下载和配置 ChromeDriver
- **`test_doi_link.py`** - 测试 DOI 链接解析
- **`test_download.py`** - 下载功能测试
- **`test_download_simple.py`** - 简化版下载测试

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install selenium webdriver-manager openpyxl pandas
```

### 2. 准备 ChromeDriver

运行自动下载脚本：
```bash
python download_chromedriver.py
```

或手动下载并配置 ChromeDriver 到系统 PATH。

### 3. 运行下载脚本

**推荐使用优化版**：
```bash
python download_pdfs_chrome_optimized.py
```

**批量下载**：
```bash
python download_all_pdfs_chrome.py
```

## 📋 输入数据格式

脚本通常需要一个 Excel 文件（如 `savedrecs.xls`），包含以下列：
- DOI 或论文链接
- 论文标题
- 其他元数据

## 📂 目录结构

```
pdf_downloader/
├── downloads/              # 已下载的 PDF 文件
├── chromedriver-win64/     # ChromeDriver 可执行文件
├── chromedriver-win64.backup/  # ChromeDriver 备份
├── savedrecs (1).xls       # 示例数据文件
└── *.py                    # 下载脚本
```

下载的 PDF 文件默认保存到：
- `downloads/` - 下载的 PDF 文件
- `downloads_selenium/` - Selenium 下载的临时文件

## ⚠️ 注意事项

1. **版权合规**：仅用于学术研究目的，遵守版权法规
2. **访问限制**：某些期刊可能需要机构访问权限
3. **下载速度**：建议设置合理的延迟，避免被封禁
4. **ChromeDriver 版本**：确保 ChromeDriver 版本与 Chrome 浏览器版本匹配

## 🔧 故障排除

### ChromeDriver 版本不匹配
```bash
python download_chromedriver.py
```

### 下载失败
- 检查网络连接
- 确认 DOI 链接有效
- 检查是否需要机构访问权限

### 浏览器无法启动
- 确认 Chrome 浏览器已安装
- 检查 ChromeDriver 路径配置

## 📝 开发说明

如需修改下载逻辑：
1. 优先修改 `download_pdfs_chrome_optimized.py`
2. 使用 `test_download_simple.py` 进行测试
3. 确保错误处理和日志记录完善
