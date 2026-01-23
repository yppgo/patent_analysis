"""查询聚合API支持的Claude模型"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CODING_ANTHROPIC_API_KEY')
if not api_key or api_key.startswith('sk-Aq8'):
    print("请输入你的聚合API Key:")
    api_key = input().strip()

base_url = "https://api.juheai.top/v1"

print(f"查询 {base_url} 的可用模型...")
print("=" * 80)

try:
    response = requests.get(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if 'data' in data:
            models = data['data']
            claude_models = [m for m in models if 'claude' in m.get('id', '').lower()]
            
            print(f"\nClaude模型 ({len(claude_models)}个):\n")
            for model in sorted(claude_models, key=lambda x: x.get('id', '')):
                print(f"  • {model.get('id', 'N/A')}")
        else:
            print("响应:", data)
    else:
        print(f"失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"错误: {e}")
