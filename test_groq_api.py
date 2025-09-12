#!/usr/bin/env python3
"""
Simple test to verify Groq API connection
"""

import asyncio
import httpx
import json
import os

async def test_groq_api():
    """Test basic Groq API connection"""
    
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    print(f"🔑 Using API key: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple test request
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print("📡 Making request to Groq API...")
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message = result["choices"][0]["message"]["content"]
                print(f"✅ Success! AI response: {message}")
                return True
            else:
                print(f"❌ Error response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_groq_api())
    if success:
        print("🎉 Groq API connection successful!")
    else:
        print("💥 Groq API connection failed!")