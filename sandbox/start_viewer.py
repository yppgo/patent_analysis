#!/usr/bin/env python3
"""
简单的 HTTP 服务器，用于查看因果图谱可视化界面
运行方式: python start_viewer.py
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000

# 切换到 sandbox 目录
os.chdir(Path(__file__).parent)

Handler = http.server.SimpleHTTPRequestHandler

print(f"🚀 启动本地服务器...")
print(f"📍 服务地址: http://localhost:{PORT}")
print(f"📂 工作目录: {os.getcwd()}")
print(f"\n可用的可视化界面:")
print(f"  1. 因果本体论浏览器: http://localhost:{PORT}/ontology_explorer.html ⭐ 推荐")
print(f"  2. 假设生成演示: http://localhost:{PORT}/hypothesis_viewer.html")
print(f"  3. 因果图谱查看器: http://localhost:{PORT}/causal_graph_viewer.html")
print(f"\n按 Ctrl+C 停止服务器\n")

# 自动打开假设生成演示
webbrowser.open(f'http://localhost:{PORT}/hypothesis_viewer.html')

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ 服务器已停止")
