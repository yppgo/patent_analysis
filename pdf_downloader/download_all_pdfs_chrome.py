import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from urllib.parse import quote
import requests

def setup_chrome_driver():
    """设置Chrome WebDriver"""
    # 检查chromedriver.exe是否存在
    driver_paths = [
        "chromedriver-win64/chromedriver.exe",  # 在chromedriver-win64文件夹中
        "chromedriver.exe",  # 在当前目录
    ]
    
    driver_path = None
    for path in driver_paths:
        if os.path.exists(path):
            driver_path = path
            break
    
    if not driver_path:
        print("未找到chromedriver.exe文件")
        print("请确保已下载并安装了与您的Chrome浏览器版本匹配的ChromeDriver")
        print("可以从以下网址下载:")
        print("https://chromedriver.chromium.org/")
        return None
    
    try:
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless=new')  # 使用新的无头模式
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置下载目录
        download_dir = os.path.abspath("downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 设置下载首选项
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True  # 禁用浏览器PDF查看器，直接下载
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 创建WebDriver服务
        service = Service(driver_path)
        
        # 创建WebDriver实例
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print(f"Chrome WebDriver已初始化，使用驱动: {driver_path}")
        return driver
    except Exception as e:
        print(f"创建Chrome WebDriver时出错: {e}")
        return None

def download_pdf_from_doi(doi, driver, download_dir="downloads", timeout=30):
    """通过DOI下载PDF"""
    try:
        # 确保下载目录存在
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # 构造Sci-Hub URL
        encoded_doi = quote(doi, safe='')
        url = f"https://sci-hub.se/{encoded_doi}"
        
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 等待页面加载
        wait = WebDriverWait(driver, timeout)
        time.sleep(3)
        
        # 尝试多种方式获取PDF链接
        pdf_url = None
        
        # 方法1: 查找iframe中的PDF链接
        try:
            iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            src = iframe.get_attribute("src")
            if src and (src.endswith(".pdf") or "pdf" in src):
                pdf_url = src
        except:
            pass
        
        # 方法2: 查找直接的PDF链接
        if not pdf_url:
            try:
                pdf_element = driver.find_element(By.CSS_SELECTOR, "embed[src*='.pdf'], object[data*='.pdf'], a[href*='.pdf']")
                pdf_url = pdf_element.get_attribute("src") or pdf_element.get_attribute("data") or pdf_element.get_attribute("href")
            except:
                pass
        
        # 方法3: 查找包含PDF的按钮并点击
        if not pdf_url:
            try:
                pdf_button = driver.find_element(By.XPATH, "//button[contains(text(), 'PDF')] | //a[contains(text(), 'PDF')]")
                pdf_button.click()
                time.sleep(3)
                pdf_url = driver.current_url
            except:
                pass
        
        # 方法4: 查找页面上的下载链接
        if not pdf_url:
            try:
                # 查找可能的下载链接
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and (".pdf" in href.lower() or "download" in href.lower()):
                        pdf_url = href
                        break
            except:
                pass
        
        if pdf_url:
            print(f"找到PDF链接: {pdf_url}")
            
            # 如果是相对路径，构造完整URL
            if pdf_url.startswith("//"):
                pdf_url = "https:" + pdf_url
            elif pdf_url.startswith("/"):
                # 从当前页面URL获取基础URL
                from urllib.parse import urlparse
                base_url = urlparse(driver.current_url)
                pdf_url = f"{base_url.scheme}://{base_url.netloc}{pdf_url}"
            
            # 访问PDF链接以触发下载
            driver.get(pdf_url)
            time.sleep(8)  # 等待下载完成
            return True
        else:
            print("未找到有效的PDF链接，尝试直接下载")
            # 尝试使用requests下载
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                
                # 检查是否是PDF内容
                if response.headers.get('content-type', '').startswith('application/pdf'):
                    # 创建文件名
                    filename = f"{doi.replace('/', '_')}.pdf"
                    file_path = os.path.join(download_dir, filename)
                    
                    # 保存文件
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"PDF文件已保存: {file_path}")
                    return True
            except Exception as e:
                print(f"使用requests下载时出错: {e}")
            
            print("未找到有效的PDF链接")
            return False
            
    except Exception as e:
        print(f"下载PDF时出错: {e}")
        return False

def main():
    """主函数"""
    # 读取Excel文件
    try:
        df = pd.read_excel('savedrecs (2).xls')
        print(f"成功读取Excel文件，共{len(df)}行数据")
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return
    
    # 设置Chrome WebDriver
    driver = setup_chrome_driver()
    if not driver:
        print("无法设置Chrome WebDriver，程序退出")
        return
    
    # 统计下载情况
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    try:
        # 遍历DOI并下载PDF
        for index, row in df.iterrows():
            doi = row.get('DOI')
            if doi and str(doi).strip() != '' and str(doi).strip() != 'nan':
                doi = str(doi).strip()
                print(f"\n正在处理第{index+1}行，DOI: {doi}")
                
                # 检查是否已经下载过
                expected_filename = f"{doi.replace('/', '_')}.pdf"
                if os.path.exists(os.path.join("downloads", expected_filename)):
                    print(f"DOI {doi} 已经下载过，跳过")
                    skip_count += 1
                    continue
                
                success = download_pdf_from_doi(doi, driver)
                if success:
                    print(f"DOI {doi} 下载成功")
                    success_count += 1
                else:
                    print(f"DOI {doi} 下载失败")
                    fail_count += 1
                
                # 添加延迟以避免过于频繁的请求
                time.sleep(3)
            else:
                print(f"第{index+1}行没有有效的DOI")
                skip_count += 1
                
            # 每处理50个DOI后稍作休息
            if (index + 1) % 50 == 0:
                print(f"\n已处理 {index + 1} 个DOI，休息5秒...")
                time.sleep(5)
                
    finally:
        # 关闭浏览器
        driver.quit()
        print("Chrome WebDriver已关闭")
    
    # 输出统计信息
    print(f"\n处理完成!")
    print(f"成功下载: {success_count} 个")
    print(f"下载失败: {fail_count} 个")
    print(f"跳过处理: {skip_count} 个")
    print(f"总计处理: {success_count + fail_count + skip_count} 个")

if __name__ == "__main__":
    main()