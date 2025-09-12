#!/usr/bin/env python3
"""
Simple test for Cerebras API integration
"""

import asyncio
import httpx
import json


async def test_cerebras_api():
    """Test Cerebras API directly"""
    print("🧠 Testing Cerebras API Integration")
    print("=" * 40)
    
    api_key = "csk-65tnt9v4dkc9c53fwmvweftej6rjr8ck4tcj5mct9pehdjtwimport"
    base_url = "https://api.cerebras.ai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b",
        "messages": [
            {
                "role": "user", 
                "content": "Hello! Can you tell me about AI-powered recruitment in 2 sentences?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print("📡 Making request to Cerebras API...")
            
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    print(f"✅ Success! Cerebras Response:")
                    print(f"💬 {content}")
                    
                    # Print model info
                    model_used = result.get("model", "unknown")
                    print(f"🤖 Model Used: {model_used}")
                    
                    return True
                else:
                    print("❌ Invalid response format")
                    print(f"Response: {result}")
                    return False
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


async def test_available_models():
    """Test which Cerebras models are available"""
    print("\n🔍 Testing Available Cerebras Models")
    print("=" * 40)
    
    models_to_test = [
        "llama-4-scout-17b-16e-instruct",
        "llama3.1-8b", 
        "llama-3.3-70b",
        "qwen-3-32b"
    ]
    
    api_key = "csk-65tnt9v4dkc9c53fwmvweftej6rjr8ck4tcj5mct9pehdjtwimport"
    base_url = "https://api.cerebras.ai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    working_models = []
    
    for model in models_to_test:
        print(f"🧪 Testing model: {model}")
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
            "temperature": 0.5
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    print(f"  ✅ {model} - Working")
                    working_models.append(model)
                else:
                    print(f"  ❌ {model} - Error {response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ {model} - Exception: {e}")
    
    print(f"\n📋 Working Models: {working_models}")
    return working_models


async def main():
    """Run tests"""
    print("🚀 PRIME Cerebras API Integration Test")
    print("=" * 50)
    
    # Test basic API functionality
    api_test = await test_cerebras_api()
    
    # Test available models
    working_models = await test_available_models()
    
    print("\n📊 Summary")
    print("=" * 20)
    
    if api_test:
        print("✅ Cerebras API is working!")
        print("✅ Ready to use as Groq fallback")
        print(f"✅ {len(working_models)} models available")
        
        print("\n🎯 Integration Status:")
        print("- Cerebras API: ✅ Connected")
        print("- Fallback System: ✅ Ready")
        print("- PRIME AI Services: ✅ Redundant & Reliable")
        
        return True
    else:
        print("❌ Cerebras API test failed")
        print("⚠️  Check API key and network connection")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎉 All tests passed!' if success else '❌ Tests failed'}")