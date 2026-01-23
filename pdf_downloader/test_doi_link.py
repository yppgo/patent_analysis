import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os

# 读取Excel
df = pd.read_excel('毕业设计/savedrecs (1).xls')
valid_data = df[df['DOI Link'].notna()]
print(f'有效DOI Link数量: {len(valid_data)}/{len(df)}')

if len(valid_data) == 0:
    print("没有有效的DOI Link")
    exit()

test_doi_link = str(valid_data.iloc[0]['DOI Link']).strip()
test_title = str(valid_data.iloc[0]['Article Title'])
print(f'\n测试DOI Link: {test_doi_link}')
print(f'标题: {test_title}')

# 设置Chrome WebDriver
driver_path = "毕业设计/chromedriver-win64/chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

download_dir = os.path.abspath("毕业设计/downloads")
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True,
}
chrome_options.add_experimental_option("prefs", prefs)

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # 方法1: 直接访问DOI Link（会重定向到出版商网站）
    print(f"\n方法1: 直接访问DOI Link")
    print(f"访问: {test_doi_link}")
    driver.get(test_doi_link)
    time.sleep(5)
    print(f"重定向后的URL: {driver.current_url}")
    print(f"页面标题: {driver.title}")
    
    # 检查是否能找到PDF下载链接
    try:
        # 常见的PDF下载按钮选择器
        pdf_selectors = [
            "a[href*='.pdf']",
            "a[contains(text(), 'PDF')]",
            "a[contains(text(), 'Download')]",
            ".pdf-download",
            "#pdf-link",
        ]
        
        for selector in pdf_selectors:
            try:
                pdf_link = driver.find_element(By.CSS_SELECTOR, selector)
                pdf_url = pdf_link.get_attribute("href")
                print(f"找到PDF链接: {pdf_url}")
                break
            except:
                continue
    except:
        print("未在出版商网站找到PDF下载链接（可能需要订阅）")
    
    # 方法2: 用DOI Link通过Sci-Hub下载
    print(f"\n方法2: 通过Sci-Hub使用DOI Link")
    sci_hub_url = f"https://sci-hub.ee/{test_doi_link}"
    print(f"访问: {sci_hub_url}")
    driver.get(sci_hub_url)
    time.sleep(5)
    
    print(f"页面标题: {driver.title}")
    
    # 查找PDF链接
    try:
        pdf_element = driver.find_element(By.CSS_SELECTOR, "iframe[src*='.pdf'], embed[src*='.pdf']")
        pdf_url = pdf_element.get_attribute("src")
        print(f"✅ 找到PDF链接: {pdf_url}")
        
        # 下载PDF
        driver.get(pdf_url)
        print("等待下载...")
        time.sleep(10)
        
        # 检查下载
        files = os.listdir(download_dir)
        pdf_files = [f for f in files if f.endswith('.pdf')]
        print(f"下载目录中的PDF文件: {pdf_files}")
        
        if len(pdf_files) > 1:
            print(f"✅ 下载成功！新文件: {pdf_files[-1]}")
        else:
            print("可能已下载或下载失败")
    except Exception as e:
        print(f"❌ 未找到PDF链接: {e}")
    
finally:
    driver.quit()
    print("\n浏览器已关闭")
