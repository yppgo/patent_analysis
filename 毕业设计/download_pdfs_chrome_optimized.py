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
import threading
import concurrent.futures
from typing import Optional

# 全局配置
MAX_WORKERS = 3  # 并发下载数量
PAGE_LOAD_TIMEOUT = 10  # 页面加载超时时间
DOWNLOAD_WAIT_TIME = 8  # 下载等待时间
REQUEST_DELAY = 2  # 请求间隔时间

def setup_chrome_driver():
    """设置Chrome WebDriver"""
    # 检查chromedriver.exe是否存在
    driver_paths = [
        "毕业设计/chromedriver-win64/chromedriver.exe",  # 在毕业设计/chromedriver-win64文件夹中
        "chromedriver-win64/chromedriver.exe",  # 在chromedriver-win64文件夹中
        "chromedriver.exe",  # 在当前目录
    ]
    
    driver_path = None
    for path in driver_paths:
        if os.path.exists(path):
            driver_path = path
            break
    
    if not driver_path:
        # 检查绝对路径
        absolute_path = r"c:\Users\73669\Desktop\专利分析\毕业设计\chromedriver-win64\chromedriver.exe"
        if os.path.exists(absolute_path):
            driver_path = absolute_path
    
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
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        
        # 设置下载目录为毕业设计/downloads
        download_dir = os.path.abspath("毕业设计/downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 设置下载首选项
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,  # 禁用Chrome内置PDF查看器
            "profile.default_content_setting_values.notifications": 2,  # 禁用通知
            "profile.default_content_settings.popups": 0,  # 禁用弹窗
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 添加实验性选项以禁用PDF查看器
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # 创建WebDriver服务
        service = Service(driver_path)
        
        # 创建WebDriver实例
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"Chrome WebDriver已初始化，使用驱动: {driver_path}")
        print(f"下载目录设置为: {download_dir}")
        return driver
    except Exception as e:
        print(f"创建Chrome WebDriver时出错: {e}")
        return None

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    # 移除首尾空格和点
    filename = filename.strip('. ')
    # 限制文件名长度
    if len(filename) > 150:
        filename = filename[:150]
    return filename

def wait_for_download_complete(download_dir: str, timeout: int = 30) -> bool:
    """等待下载完成"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        # 检查是否有.crdownload文件（正在下载的文件）
        downloading = any(file.endswith('.crdownload') for file in os.listdir(download_dir))
        if not downloading:
            return True
        time.sleep(1)
    return False

def download_pdf_from_doi(doi: str, title: str, driver) -> bool:
    """通过DOI下载PDF"""
    try:
        # 下载目录为毕业设计/downloads
        download_dir = os.path.abspath("毕业设计/downloads")
        
        # 如果提供了标题，使用标题作为文件名
        if title and str(title).lower() != 'nan' and str(title).strip():
            # 清理标题以用作文件名
            clean_title = sanitize_filename(str(title).strip())
            new_filename = clean_title + ".pdf"
        else:
            # 如果没有标题，先访问页面获取原始文件名
            # 构造Sci-Hub URL
            encoded_doi = quote(doi, safe='')
            url = f"https://sci-hub.se/{encoded_doi}"
            
            print(f"正在访问: {url}")
            driver.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找PDF下载链接
            pdf_url = None
            try:
                # 查找包含PDF链接的元素
                pdf_element = driver.find_element(By.CSS_SELECTOR, "iframe[src*='.pdf'], embed[src*='.pdf'], a[href*='.pdf']")
                pdf_url = pdf_element.get_attribute("src") or pdf_element.get_attribute("href")
            except:
                # 如果没找到直接的PDF链接，尝试查找按钮
                try:
                    pdf_button = driver.find_element(By.CSS_SELECTOR, "button, a[contains(text(), 'PDF')]")
                    pdf_button.click()
                    time.sleep(2)
                    pdf_url = driver.current_url
                except:
                    print("未找到PDF链接")
                    return False
            
            if pdf_url:
                # 获取原始文件名
                original_filename = pdf_url.split('/')[-1].split('?')[0]
                new_filename = original_filename
            else:
                print("未找到有效的PDF链接")
                return False
        
        # 检查文件是否已存在
        target_file_path = os.path.join(download_dir, new_filename)
        if os.path.exists(target_file_path):
            print(f"文件已存在，跳过下载: {new_filename}")
            return True
        
        # 如果文件不存在，继续下载流程
        print(f"文件不存在，开始下载: {new_filename}")
        
        # 如果之前没有访问过页面，则现在访问
        if 'url' in locals():
            # 访问PDF链接以触发下载
            driver.get(pdf_url)
        else:
            # 构造Sci-Hub URL
            encoded_doi = quote(doi, safe='')
            url = f"https://sci-hub.se/{encoded_doi}"
            
            print(f"正在访问: {url}")
            driver.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找PDF下载链接
            pdf_url = None
            try:
                # 查找包含PDF链接的元素
                pdf_element = driver.find_element(By.CSS_SELECTOR, "iframe[src*='.pdf'], embed[src*='.pdf'], a[href*='.pdf']")
                pdf_url = pdf_element.get_attribute("src") or pdf_element.get_attribute("href")
            except:
                # 如果没找到直接的PDF链接，尝试查找按钮
                try:
                    pdf_button = driver.find_element(By.CSS_SELECTOR, "button, a[contains(text(), 'PDF')]")
                    pdf_button.click()
                    time.sleep(2)
                    pdf_url = driver.current_url
                except:
                    print("未找到PDF链接")
                    return False
            
            if pdf_url:
                print(f"找到PDF链接: {pdf_url}")
                # 访问PDF链接以触发下载
                driver.get(pdf_url)
            else:
                print("未找到有效的PDF链接")
                return False
        
        # 等待下载完成
        if wait_for_download_complete(download_dir, DOWNLOAD_WAIT_TIME):
            print("下载完成")
        else:
            print("下载可能未完成")
        
        # 重命名下载的文件（如果使用了标题）
        if title and str(title).lower() != 'nan' and str(title).strip():
            # 获取原始文件名用于重命名
            original_filename = pdf_url.split('/')[-1].split('?')[0]
            rename_downloaded_file(download_dir, original_filename, new_filename)
        
        return True
            
    except Exception as e:
        print(f"下载PDF时出错: {e}")
        return False

def rename_downloaded_file(download_dir: str, original_filename: str, new_filename: str):
    """重命名下载的文件"""
    try:
        # 查找下载的文件
        download_path = os.path.join(download_dir, original_filename)
        
        # 检查文件是否存在
        if os.path.exists(download_path):
            # 构造新文件路径
            new_path = os.path.join(download_dir, new_filename)
            
            # 如果新文件名已存在，添加数字后缀
            counter = 1
            base_name, ext = os.path.splitext(new_filename)
            while os.path.exists(new_path):
                new_filename = f"{base_name}_{counter}{ext}"
                new_path = os.path.join(download_dir, new_filename)
                counter += 1
            
            # 重命名文件
            os.rename(download_path, new_path)
            print(f"文件已重命名为: {new_filename}")
        else:
            # 尝试查找部分匹配的文件
            for file in os.listdir(download_dir):
                if original_filename.split('.')[0] in file and file.endswith('.pdf'):
                    old_path = os.path.join(download_dir, file)
                    new_path = os.path.join(download_dir, new_filename)
                    
                    # 如果新文件名已存在，添加数字后缀
                    counter = 1
                    base_name, ext = os.path.splitext(new_filename)
                    while os.path.exists(new_path):
                        new_filename = f"{base_name}_{counter}{ext}"
                        new_path = os.path.join(download_dir, new_filename)
                        counter += 1
                    
                    # 重命名文件
                    os.rename(old_path, new_path)
                    print(f"文件已重命名为: {new_filename}")
                    break
            else:
                print(f"未找到下载的文件: {original_filename}")
    except Exception as e:
        print(f"重命名文件时出错: {e}")

def process_doi_batch(dois_and_titles: list) -> list:
    """处理DOI批次"""
    results = []
    
    # 为每个批次创建独立的WebDriver实例
    driver = setup_chrome_driver()
    if not driver:
        print("无法设置Chrome WebDriver")
        return [(doi, False) for doi, _ in dois_and_titles]
    
    try:
        for doi, title in dois_and_titles:
            print(f"\n正在处理DOI: {doi}")
            success = download_pdf_from_doi(doi, title, driver)
            results.append((doi, success))
            # 添加延迟以避免过于频繁的请求
            time.sleep(REQUEST_DELAY)
    finally:
        driver.quit()
        print("Chrome WebDriver已关闭")
    
    return results

def main():
    """主函数"""
    # 读取Excel文件
    try:
        df = pd.read_excel('毕业设计\savedrecs (1).xls')
        print(f"成功读取Excel文件，共{len(df)}行数据")
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return
    
    # 准备DOI和标题列表
    dois_and_titles = []
    for index, row in df.iterrows():
        doi = row.get('DOI') or row.get('doi')
        title = row.get('Title') or row.get('title') or row.get('Article Title') or row.get('article title')
        # 检查DOI是否存在且不为空
        if doi and str(doi).lower() != 'nan' and str(doi).strip():
            doi = str(doi).strip()  # 去除首尾空格
            dois_and_titles.append((doi, title))
        else:
            print(f"第{index+1}行没有有效的DOI")
    
    if not dois_and_titles:
        print("没有有效的DOI需要处理")
        return
    
    print(f"总共需要处理 {len(dois_and_titles)} 个DOI")
    
    # 分批处理DOI
    batch_size = MAX_WORKERS
    batches = [dois_and_titles[i:i + batch_size] for i in range(0, len(dois_and_titles), batch_size)]
    
    print(f"将分为 {len(batches)} 个批次处理，每批最多 {batch_size} 个DOI")
    
    # 使用线程池并发处理批次
    successful_downloads = 0
    failed_downloads = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 提交所有批次任务
        future_to_batch = {executor.submit(process_doi_batch, batch): batch for batch in batches}
        
        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                results = future.result()
                for doi, success in results:
                    if success:
                        successful_downloads += 1
                        print(f"DOI {doi} 下载成功")
                    else:
                        failed_downloads += 1
                        print(f"DOI {doi} 下载失败")
            except Exception as e:
                print(f"处理批次时出错: {e}")
                failed_downloads += len(batch)
    
    print(f"\n下载完成统计:")
    print(f"成功下载: {successful_downloads}")
    print(f"下载失败: {failed_downloads}")
    print(f"总计处理: {successful_downloads + failed_downloads}")

if __name__ == "__main__":
    main()