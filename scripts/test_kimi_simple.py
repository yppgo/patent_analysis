#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 Kimi API 连接
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_kimi_connection():
    """测试 Kimi API 连接"""
    
    # 从环境变量读取配置
    api_key = os.getenv("CODING_ANTHROPIC_API_KEY")
    base_url = os.getenv("CODING_ANTHROPIC_BASE_URL")
    model = os.getenv("KIMI_MODEL", "moonshot-v1-128k")
    
    print("=" * 60)
    print("Kimi API 连接测试")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}..." if api_key else "未设置")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
    if not api_key:
        print("[ERROR] 未设置 CODING_ANTHROPIC_API_KEY")
        return
    
    try:
        # 创建客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        print("[INFO] 发送测试请求...")
        
        # 发送简单的测试请求
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "你好，请用一句话介绍你自己。"
                }
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        
        print("[OK] 连接成功！")
        print()
        print("响应内容:")
        print(result)
        print()
        print("=" * 60)
        print("✅ Kimi API 配置正确，可以正常使用")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        print()
        print("请检查:")
        print("1. CODING_ANTHROPIC_API_KEY 是否正确")
        print("2. CODING_ANTHROPIC_BASE_URL 是否正确")
        print("3. 聚合API是否支持 Kimi 模型")
        print("4. 网络连接是否正常")


if __name__ == "__main__":
    test_kimi_connection()
