#!/usr/bin/env python3
"""
OpenAI API接続テスト
"""

import os
from dotenv import load_dotenv

def test_openai_connection():
    """OpenAI APIの接続をテスト"""
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key found: {bool(api_key)}")
    
    if api_key:
        print(f"API Key starts with: {api_key[:20]}...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello from OpenAI'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API接続成功")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API接続失敗: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection()