import requests
import zipfile
import os
import shutil

# 获取最新的Chrome Stable版本
print("获取最新ChromeDriver版本...")
r = requests.get('https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json')
version = r.json()['channels']['Stable']['version']
print(f"最新版本: {version}")

# 构造下载URL
download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
print(f"下载地址: {download_url}")

# 下载文件
print("开始下载...")
response = requests.get(download_url, stream=True)
total_size = int(response.headers.get('content-length', 0))
downloaded = 0

zip_path = "chromedriver-win64.zip"
with open(zip_path, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

print("\n下载完成！")

# 解压文件
print("解压文件...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(".")

# 备份旧版本
old_driver_dir = "毕业设计/chromedriver-win64"
if os.path.exists(old_driver_dir):
    backup_dir = "毕业设计/chromedriver-win64.backup"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    print(f"备份旧版本到: {backup_dir}")
    shutil.move(old_driver_dir, backup_dir)

# 移动新版本
print("安装新版本...")
shutil.move("chromedriver-win64", old_driver_dir)

# 清理
os.remove(zip_path)

print(f"✅ ChromeDriver {version} 安装完成！")
print(f"位置: {old_driver_dir}/chromedriver.exe")
