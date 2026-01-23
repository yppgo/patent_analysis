import pandas as pd
import requests
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

download_dir = "毕业设计/downloads"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 测试多个Sci-Hub镜像（2025年1月可用镜像）
mirrors = [
    "https://sci-hub.wf",
    "https://sci-hub.st",
    "https://sci-hub.se", 
    "https://sci-hub.ru",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

for mirror in mirrors:
    print(f"\n尝试镜像: {mirror}")
    encoded_doi = quote(test_doi, safe='')
    url = f"{mirror}/{encoded_doi}"
    
    try:
        print(f"访问: {url}")
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查是否直接返回PDF
            if response.headers.get('content-type', '').startswith('application/pdf'):
                filename = f"{test_doi.replace('/', '_')}.pdf"
                filepath = os.path.join(download_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"✅ 直接下载成功: {filepath}")
                break
            else:
                # 解析HTML查找PDF链接
                content = response.text
                
                # 查找PDF链接的几种模式
                import re
                pdf_patterns = [
                    r'<iframe[^>]+src="([^"]+\.pdf[^"]*)"',
                    r'<embed[^>]+src="([^"]+\.pdf[^"]*)"',
                    r'href="([^"]+\.pdf[^"]*)"',
                    r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
                ]
                
                pdf_url = None
                for pattern in pdf_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        pdf_url = match.group(1)
                        break
                
                if pdf_url:
                    # 处理相对路径
                    if pdf_url.startswith('//'):
                        pdf_url = 'https:' + pdf_url
                    elif pdf_url.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        pdf_url = f"{parsed.scheme}://{parsed.netloc}{pdf_url}"
                    
                    print(f"找到PDF链接: {pdf_url}")
                    
                    # 下载PDF
                    pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
                    if pdf_response.status_code == 200:
                        filename = f"{test_doi.replace('/', '_')}.pdf"
                        filepath = os.path.join(download_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"✅ 下载成功: {filepath}")
                        print(f"文件大小: {len(pdf_response.content) / 1024:.2f} KB")
                        break
                    else:
                        print(f"❌ PDF下载失败，状态码: {pdf_response.status_code}")
                else:
                    print("❌ 未在页面中找到PDF链接")
                    # 打印部分HTML内容用于调试
                    print(f"页面内容前500字符: {content[:500]}")
        else:
            print(f"❌ 访问失败，状态码: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n测试完成")
