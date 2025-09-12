#!/usr/bin/env python3
"""
Test Cerebras API integration as fallback for Groq
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import GroqAIService, CerebrasAIService


async def test_cerebras_direct():
    """Test Cerebras API directly"""
    print("\n🧠 Testing Cerebras API Direct Integration")
    print("=" * 50)
    
    try:
        cerebras_service = CerebrasAIService()
        
        # Test basic chat completion
        data = {
            "model": "llama-3.3-70b",
            "messages": [
                {"role": "user", "content": "Hello! Can you tell me about AI recruitment?"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = await cerebras_service._make_request("chat/completions", data)
        
        if response and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Cerebras API Response: {content[:200]}...")
            return True
        else:
            print("❌ Invalid response format from Cerebras")
            return False
            
    except Exception as e:
        print(f"❌ Cerebras API test failed: {e}")
        return False


async def test_groq_with_cerebras_fallback():
    """Test Groq service with Cerebras fallback"""
    print("\n🔄 Testing Groq with Cerebras Fallback")
    print("=" * 50)
    
    try:
        # Initialize service (will use fallback if Groq fails)
        ai_service = GroqAIService()
        
        # Test chatbot response generation
        conversation_history = [
            {"sender": "user", "content": "Hi, I'm interested in a software engineer position"}
        ]
        
        question_config = {
            "personality": "professional",
            "type": "experience"
        }
        
        candidate_context = {
            "name": "Test Candidate",
            "role": "Software Engineer"
        }
        
        response = await ai_service.generate_chatbot_response(
            conversation_history=conversation_history,
            question_config=question_config,
            candidate_context=candidate_context,
            is_trial=True
        )
        
        print(f"✅ AI Service Response: {response[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ AI Service test failed: {e}")
        return False


async def test_live_interview_with_fallback():
    """Test live interview functionality with fallback"""
    print("\n🎥 Testing Live Interview with Fallback")
    print("=" * 50)
    
    try:
        ai_service = GroqAIService()
        
        job_context = {
            "title": "Senior Software Engineer",
            "company": "PRIME",
            "requirements": {
                "skills": ["Python", "React", "AI/ML"],
                "experience": "5+ years"
            }
        }
        
        candidate_context = {
            "name": "Test Candidate",
            "background": {
                "experience": "Software development",
                "skills": ["Python", "JavaScript"]
            }
        }
        
        interview_config = {
            "duration": 30,
            "focus_areas": ["technical", "behavioral"]
        }
        
        result = await ai_service.start_live_ai_interview(
            job_context=job_context,
            candidate_context=candidate_context,
            interview_config=interview_config,
            is_trial=True
        )
        
        if result and "opening_question" in result:
            print(f"✅ Live Interview Started: {result['opening_question'][:150]}...")
            return True
        else:
            print("❌ Failed to start live interview")
            return False
            
    except Exception as e:
        print(f"❌ Live interview test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 PRIME AI Service Integration Tests")
    print("Testing Groq API with Cerebras Fallback")
    print("=" * 60)
    
    test_results = []
    
    # Test Cerebras directly
    cerebras_result = await test_cerebras_direct()
    test_results.append(("Cerebras Direct", cerebras_result))
    
    # Test Groq with fallback
    groq_fallback_result = await test_groq_with_cerebras_fallback()
    test_results.append(("Groq with Cerebras Fallback", groq_fallback_result))
    
    # Test live interview
    live_interview_result = await test_live_interview_with_fallback()
    test_results.append(("Live Interview with Fallback", live_interview_result))
    
    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("\n🎉 All AI integration tests passed!")
        print("✅ Cerebras API is working as a reliable fallback for Groq")
        print("✅ Your PRIME platform now has redundant AI services")
    else:
        print(f"\n⚠️  {len(test_results) - passed} test(s) failed")
        print("Check your API keys and network connection")
    
    return passed == len(test_results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)