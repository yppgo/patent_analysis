import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from urllib.parse import quote

# 读取Excel获取第一个有效DOI
df = pd.read_excel('毕业设计/savedrecs (1).xls')
valid_dois = df[df['DOI'].notna()]
print(f'有效DOI数量: {len(valid_dois)}/{len(df)}')

if len(valid_dois) == 0:
    print("没有有效的DOI")
    exit()

test_doi = str(valid_dois.iloc[0]['DOI']).strip()
test_title = str(valid_dois.iloc[0]['Article Title'])
print(f'\n测试DOI: {test_doi}')
print(f'标题: {test_title}')

# 设置Chrome WebDriver
driver_path = "毕业设计/chromedriver-win64/chromedriver.exe"
if not os.path.exists(driver_path):
    print(f"ChromeDriver不存在: {driver_path}")
    exit()

chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# chrome_options.add_argument('--headless=new')  # 先不用无头模式，方便调试

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
    # 测试多个Sci-Hub镜像
    mirrors = [
        "https://sci-hub.st",
        "https://sci-hub.se",
        "https://sci-hub.ru",
        "https://sci-hub.ee",
    ]
    
    for mirror in mirrors:
        print(f"\n尝试镜像: {mirror}")
        encoded_doi = quote(test_doi, safe='')
        url = f"{mirror}/{encoded_doi}"
        
        try:
            driver.get(url)
            time.sleep(5)
            
            # 检查页面标题
            print(f"页面标题: {driver.title}")
            
            # 查找PDF链接
            try:
                pdf_element = driver.find_element(By.CSS_SELECTOR, "iframe[src*='.pdf'], embed[src*='.pdf']")
                pdf_url = pdf_element.get_attribute("src")
                print(f"✅ 找到PDF链接: {pdf_url}")
                
                # 访问PDF触发下载
                driver.get(pdf_url)
                print("等待下载...")
                time.sleep(10)
                
                # 检查下载目录
                files = os.listdir(download_dir)
                pdf_files = [f for f in files if f.endswith('.pdf')]
                print(f"下载目录中的PDF文件: {pdf_files}")
                
                if pdf_files:
                    print(f"✅ 下载成功！文件: {pdf_files[-1]}")
                    break
                else:
                    print("❌ 未找到下载的PDF文件")
            except Exception as e:
                print(f"❌ 未找到PDF链接: {e}")
                
        except Exception as e:
            print(f"❌ 访问失败: {e}")
    
finally:
    driver.quit()
    print("\n浏览器已关闭")
