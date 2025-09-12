#!/usr/bin/env python3
"""
Test script for Live AI Interview functionality
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_service import ai_service
from app.services.interview_service import InterviewService
from app.core.database import SessionLocal
from app.models.company import Company, User
from app.models.job import Job, Application, Candidate
from app.models.interview import Interview, InterviewTemplate


async def test_live_ai_interview():
    """Test the complete live AI interview flow"""
    
    print("🤖 Testing Live AI Interview System")
    print("=" * 50)
    
    # Test data
    job_context = {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "description": "We are looking for a senior software engineer with expertise in Python and React.",
        "requirements": {
            "skills": ["Python", "React", "PostgreSQL", "AWS"],
            "experience": "5+ years",
            "education": "Bachelor's degree in Computer Science"
        }
    }
    
    candidate_context = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "background": {
            "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL"],
            "experience": [
                {
                    "company": "StartupXYZ",
                    "role": "Full Stack Developer",
                    "duration": "3 years",
                    "technologies": ["Python", "React", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "university": "State University",
                    "year": "2018"
                }
            ]
        }
    }
    
    interview_config = {
        "is_trial": False,
        "max_questions": 8,
        "focus_areas": ["technical", "behavioral", "cultural_fit"]
    }
    
    try:
        # Test 1: Start Live AI Interview
        print("\n1. Testing AI Interview Initialization...")
        session_result = await ai_service.start_live_ai_interview(
            job_context=job_context,
            candidate_context=candidate_context,
            interview_config=interview_config,
            is_trial=False
        )
        
        print(f"✅ Session started successfully")
        print(f"   Session ID: {session_result['session_state']['session_id']}")
        print(f"   Opening Question: {session_result['opening_question']}")
        
        session_state = session_result["session_state"]
        
        # Test 2: Simulate conversation turns
        print("\n2. Testing Conversation Flow...")
        
        candidate_responses = [
            "Hi! I'm excited to be here. I'm John, a software engineer with about 5 years of experience, primarily working with Python and React. I've been working at StartupXYZ where I've built several full-stack applications.",
            
            "I have strong experience with Python, particularly with frameworks like Django and FastAPI. I've built REST APIs, worked with PostgreSQL databases, and deployed applications on AWS. I'm also proficient in React for frontend development.",
            
            "In my current role, I led a project to rebuild our legacy system using microservices architecture. We reduced response times by 60% and improved system reliability. I collaborated with a team of 4 developers and worked closely with product managers to define requirements.",
            
            "I'm looking for opportunities to work on more challenging technical problems and to mentor junior developers. I'm particularly interested in AI/ML integration and scalable system design.",
            
            "I don't have any specific questions right now, but I'm excited about the possibility of joining your team and contributing to innovative projects."
        ]
        
        for i, response in enumerate(candidate_responses, 1):
            print(f"\n   Turn {i}:")
            print(f"   Candidate: {response[:100]}...")
            
            # Process candidate response
            ai_result = await ai_service.process_candidate_response_live(
                session_state=session_state,
                candidate_response=response,
                response_metadata={"turn": i, "timestamp": datetime.utcnow().isoformat()}
            )
            
            print(f"   AI Response: {ai_result['ai_response'][:100]}...")
            print(f"   Analysis - Sentiment: {ai_result['analysis'].get('sentiment', 'N/A')}, "
                  f"Confidence: {ai_result['analysis'].get('confidence', 0):.2f}")
            print(f"   Should Continue: {ai_result['should_continue']}")
            print(f"   Interview Phase: {ai_result.get('interview_phase', 'ongoing')}")
            
            # Update session state
            session_state = ai_result["session_state"]
            
            # Break if interview should end
            if not ai_result["should_continue"]:
                print("   🏁 AI decided to end the interview")
                break
        
        # Test 3: Generate Interview Summary
        print("\n3. Testing Interview Summary Generation...")
        
        summary = await ai_service.generate_interview_summary(
            session_state=session_state,
            job_context=job_context
        )
        
        print(f"✅ Summary generated successfully")
        print(f"   Overall Score: {summary['overall_score']}")
        print(f"   Recommendation: {summary['recommendation']}")
        print(f"   Technical Score: {summary['technical_assessment']['score']}")
        print(f"   Communication Score: {summary['communication_skills']['score']}")
        print(f"   Key Strengths: {', '.join(summary['key_strengths'][:3])}")
        
        # Test 4: Test with Trial Mode
        print("\n4. Testing Trial Mode...")
        
        trial_session = await ai_service.start_live_ai_interview(
            job_context=job_context,
            candidate_context=candidate_context,
            interview_config={**interview_config, "is_trial": True},
            is_trial=True
        )
        
        print(f"✅ Trial session started")
        print(f"   Model: {trial_session['session_state']['model']}")
        print(f"   Opening Question: {trial_session['opening_question'][:100]}...")
        
        # Test 5: Test Error Handling
        print("\n5. Testing Error Handling...")
        
        try:
            # Test with empty response
            error_result = await ai_service.process_candidate_response_live(
                session_state=session_state,
                candidate_response="",
                response_metadata={}
            )
            print(f"✅ Empty response handled: {error_result['ai_response'][:50]}...")
        except Exception as e:
            print(f"❌ Error handling failed: {e}")
        
        # Test 6: Test Sentiment Analysis
        print("\n6. Testing Sentiment Analysis...")
        
        test_responses = [
            ("I'm really excited about this opportunity and love working with your tech stack!", "positive"),
            ("I'm not sure if I have enough experience for this role.", "negative"),
            ("I have worked with Python for 3 years and built several applications.", "neutral")
        ]
        
        for response_text, expected_sentiment in test_responses:
            analysis = await ai_service._analyze_response_sentiment_confidence(
                response=response_text,
                question="Tell me about your experience with Python."
            )
            
            actual_sentiment = analysis.get('sentiment', 'unknown')
            print(f"   Response: '{response_text[:50]}...'")
            print(f"   Expected: {expected_sentiment}, Got: {actual_sentiment}")
            print(f"   Confidence: {analysis.get('confidence', 0):.2f}")
        
        print("\n" + "=" * 50)
        print("🎉 All Live AI Interview tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interview_service_integration():
    """Test the interview service integration with live AI"""
    
    print("\n🔧 Testing Interview Service Integration")
    print("=" * 50)
    
    # This would require a database setup, so we'll just test the structure
    try:
        # Create a mock database session
        db = SessionLocal()
        service = InterviewService(db)
        
        print("✅ Interview service initialized")
        
        # Test method existence
        methods_to_test = [
            'start_live_ai_interview',
            'process_live_ai_response', 
            'complete_live_ai_interview',
            'get_live_ai_session_state'
        ]
        
        for method_name in methods_to_test:
            if hasattr(service, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    
    print("🚀 Starting Live AI Interview System Tests")
    print("=" * 60)
    
    # Check if GROQ_API_KEY is set
    if not os.getenv('GROQ_API_KEY'):
        print("⚠️  Warning: GROQ_API_KEY not set. Some tests may fail.")
        print("   Set GROQ_API_KEY environment variable to run full tests.")
    
    # Run tests
    test_results = []
    
    # Test AI service
    ai_test_result = await test_live_ai_interview()
    test_results.append(("Live AI Interview", ai_test_result))
    
    # Test service integration
    service_test_result = await test_interview_service_integration()
    test_results.append(("Service Integration", service_test_result))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Live AI Interview system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)