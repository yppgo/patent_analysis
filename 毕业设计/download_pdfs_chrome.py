import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from urllib.parse import quote

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
        chrome_options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
        
        # 设置下载目录
        download_dir = os.path.abspath("downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 设置下载首选项
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 创建WebDriver服务
        service = Service(driver_path)
        
        # 创建WebDriver实例
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"Chrome WebDriver已初始化，使用驱动: {driver_path}")
        return driver
    except Exception as e:
        print(f"创建Chrome WebDriver时出错: {e}")
        return None

def download_pdf_from_doi(doi, driver, download_dir="downloads"):
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
        time.sleep(5)
        
        # 查找PDF下载链接
        try:
            # 查找包含PDF链接的元素
            pdf_element = driver.find_element("css selector", "iframe[src*='.pdf'], embed[src*='.pdf'], a[href*='.pdf']")
            pdf_url = pdf_element.get_attribute("src") or pdf_element.get_attribute("href")
        except:
            # 如果没找到直接的PDF链接，尝试查找按钮
            try:
                pdf_button = driver.find_element("css selector", "button, a[contains(text(), 'PDF')]")
                pdf_button.click()
                time.sleep(3)
                pdf_url = driver.current_url
            except:
                print("未找到PDF链接")
                return False
        
        if pdf_url:
            print(f"找到PDF链接: {pdf_url}")
            # 访问PDF链接以触发下载
            driver.get(pdf_url)
            time.sleep(10)  # 等待下载完成
            return True
        else:
            print("未找到有效的PDF链接")
            return False
            
    except Exception as e:
        print(f"下载PDF时出错: {e}")
        return False

def main():
    """主函数"""
    # 读取Excel文件
    try:
        df = pd.read_excel('毕业设计\savedrecs (2).xls')
        print(f"成功读取Excel文件，共{len(df)}行数据")
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return
    
    # 设置Chrome WebDriver
    driver = setup_chrome_driver()
    if not driver:
        print("无法设置Chrome WebDriver，程序退出")
        return
    
    try:
        # 遍历DOI并下载PDF
        for index, row in df.iterrows():
            doi = row.get('DOI') or row.get('doi')
            # 检查DOI是否存在且不为空
            if doi and str(doi).lower() != 'nan' and str(doi).strip():
                doi = str(doi).strip()  # 去除首尾空格
                print(f"\n正在处理第{index+1}行，DOI: {doi}")
                success = download_pdf_from_doi(doi, driver)
                if success:
                    print(f"DOI {doi} 下载成功")
                else:
                    print(f"DOI {doi} 下载失败")
                # 添加延迟以避免过于频繁的请求
                time.sleep(5)
            else:
                print(f"第{index+1}行没有有效的DOI")
    finally:
        # 关闭浏览器
        driver.quit()
        print("Chrome WebDriver已关闭")

if __name__ == "__main__":
    main()