#!/usr/bin/env python3
"""
Demo script for Live AI Interview System
Shows all implemented features and capabilities
"""

import asyncio
import json
import os
from datetime import datetime

# Set the API key
# Set the API key from environment variable
# os.environ['GROQ_API_KEY'] = 'your-api-key-here'

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_service import ai_service


async def demo_live_ai_interview():
    """Comprehensive demo of the Live AI Interview System"""
    
    print("🎬 PRIME Live AI Interview System Demo")
    print("=" * 60)
    print("This demo showcases the complete live AI interviewer system")
    print("with real-time conversation, sentiment analysis, and adaptive questioning.")
    print()
    
    # Demo job and candidate data
    job_context = {
        "title": "Senior Full Stack Developer",
        "company": "TechCorp Inc.",
        "description": "We're looking for a senior developer to lead our product development team.",
        "requirements": {
            "skills": ["Python", "React", "PostgreSQL", "AWS", "Docker"],
            "experience": "5+ years",
            "education": "Bachelor's in Computer Science or equivalent",
            "leadership": "Experience mentoring junior developers"
        }
    }
    
    candidate_context = {
        "name": "Sarah Chen",
        "email": "sarah.chen@email.com",
        "background": {
            "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "MongoDB"],
            "experience": [
                {
                    "company": "StartupXYZ",
                    "role": "Senior Software Engineer",
                    "duration": "3 years",
                    "achievements": ["Led team of 4 developers", "Built microservices architecture"]
                },
                {
                    "company": "TechCorp",
                    "role": "Full Stack Developer", 
                    "duration": "2 years",
                    "achievements": ["Reduced API response time by 40%", "Implemented CI/CD pipeline"]
                }
            ],
            "education": [
                {
                    "degree": "Master of Science in Computer Science",
                    "university": "Stanford University",
                    "year": "2018"
                }
            ]
        }
    }
    
    interview_config = {
        "is_trial": False,
        "max_questions": 6,
        "focus_areas": ["technical", "leadership", "cultural_fit"],
        "difficulty_adaptation": True
    }
    
    print("📋 Interview Setup:")
    print(f"   Position: {job_context['title']} at {job_context['company']}")
    print(f"   Candidate: {candidate_context['name']}")
    print(f"   Focus Areas: {', '.join(interview_config['focus_areas'])}")
    print()
    
    try:
        # 1. Initialize the interview
        print("🚀 Step 1: Initializing Live AI Interview...")
        session_result = await ai_service.start_live_ai_interview(
            job_context=job_context,
            candidate_context=candidate_context,
            interview_config=interview_config,
            is_trial=False
        )
        
        print(f"✅ Interview session started")
        print(f"   Session ID: {session_result['session_state']['session_id']}")
        print(f"   AI Model: {session_result['session_state']['model']}")
        print()
        
        print("🤖 AI Interviewer:")
        print(f"   \"{session_result['opening_question']}\"")
        print()
        
        session_state = session_result["session_state"]
        
        # 2. Simulate realistic conversation
        print("💬 Step 2: Simulating Interview Conversation...")
        print("=" * 40)
        
        # Realistic candidate responses that show different aspects
        candidate_responses = [
            # Response 1: Introduction and motivation
            "Thank you for having me! I'm really excited about this opportunity. I've been following TechCorp's growth and I'm impressed by your commitment to innovation. With my 5 years of experience in full-stack development and recent leadership experience at StartupXYZ, I believe I can contribute significantly to your product development goals. I'm particularly drawn to the technical challenges you're solving and the opportunity to mentor other developers.",
            
            # Response 2: Technical expertise
            "I have extensive experience with your tech stack. I've been working with Python for over 5 years, primarily using Django and FastAPI for backend development. On the frontend, I'm proficient in React and have built several large-scale applications. I've worked with both PostgreSQL and MongoDB, and I'm comfortable with AWS services like EC2, RDS, and Lambda. I also have experience with Docker and Kubernetes for containerization and orchestration.",
            
            # Response 3: Leadership and problem-solving
            "At StartupXYZ, I led a team of 4 developers to rebuild our legacy monolithic system into a microservices architecture. The biggest challenge was maintaining system stability while migrating live data. I implemented a phased approach with extensive testing and rollback procedures. We reduced system downtime by 80% and improved response times by 60%. I also established code review processes and mentored two junior developers who were promoted during my tenure.",
            
            # Response 4: Handling challenges
            "One of the most challenging projects was when we had a critical performance issue affecting 50,000+ users. I had to quickly diagnose the problem, which turned out to be a database query optimization issue. I implemented database indexing, query optimization, and added caching layers. I also set up monitoring and alerting to prevent similar issues. The experience taught me the importance of proactive monitoring and performance testing.",
            
            # Response 5: Career goals and cultural fit
            "I'm looking for a role where I can have greater technical impact and grow my leadership skills. I'm passionate about building scalable systems and creating positive team cultures. I believe in collaborative development, continuous learning, and knowledge sharing. I'd love to contribute to TechCorp's engineering culture and help build systems that can scale with your growth. I'm also interested in exploring AI/ML integration, which aligns with your company's direction.",
            
            # Response 6: Questions and closing
            "I'm curious about the team structure and how you approach technical decision-making. What are the biggest technical challenges the team is currently facing? Also, what opportunities are there for professional development and learning new technologies? I'm excited about the possibility of joining TechCorp and contributing to your mission."
        ]
        
        conversation_log = []
        
        for i, response in enumerate(candidate_responses, 1):
            print(f"\n🎯 Turn {i}:")
            print(f"👤 Candidate: \"{response[:100]}...\"")
            
            # Process the response
            ai_result = await ai_service.process_candidate_response_live(
                session_state=session_state,
                candidate_response=response,
                response_metadata={
                    "turn": i,
                    "timestamp": datetime.now().isoformat(),
                    "response_length": len(response)
                }
            )
            
            print(f"🤖 AI Interviewer: \"{ai_result['ai_response'][:100]}...\"")
            
            # Show analysis
            analysis = ai_result['analysis']
            print(f"📊 Analysis:")
            print(f"   • Sentiment: {analysis.get('sentiment', 'N/A')}")
            print(f"   • Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"   • Engagement: {analysis.get('engagement', 'N/A')}")
            print(f"   • Clarity: {analysis.get('clarity', 'N/A')}")
            print(f"   • Technical Depth: {analysis.get('technical_depth', 'N/A')}")
            
            # Show interview progression
            print(f"🎪 Interview Status:")
            print(f"   • Phase: {ai_result.get('interview_phase', 'ongoing')}")
            print(f"   • Should Continue: {ai_result['should_continue']}")
            
            # Log the conversation
            conversation_log.append({
                "turn": i,
                "candidate_response": response,
                "ai_response": ai_result['ai_response'],
                "analysis": analysis,
                "phase": ai_result.get('interview_phase', 'ongoing')
            })
            
            # Update session state
            session_state = ai_result["session_state"]
            
            # Check if interview should end
            if not ai_result["should_continue"]:
                print("   🏁 AI has decided to conclude the interview")
                break
            
            # Add a small delay to simulate real conversation
            await asyncio.sleep(0.5)
        
        # 3. Generate comprehensive summary
        print("\n📈 Step 3: Generating Interview Summary...")
        print("=" * 40)
        
        summary = await ai_service.generate_interview_summary(
            session_state=session_state,
            job_context=job_context
        )
        
        print("📋 INTERVIEW SUMMARY REPORT")
        print("=" * 40)
        
        # Overall assessment
        print(f"🎯 Overall Score: {summary['overall_score']:.1f}/100")
        print(f"🏆 Recommendation: {summary['recommendation'].upper().replace('_', ' ')}")
        print()
        
        # Detailed scores
        print("📊 Detailed Assessment:")
        tech_score = summary['technical_assessment']['score']
        comm_score = summary['communication_skills']['score']
        culture_score = summary['cultural_fit']['score']
        
        print(f"   • Technical Skills: {tech_score:.1f}/100")
        print(f"   • Communication: {comm_score:.1f}/100")
        print(f"   • Cultural Fit: {culture_score:.1f}/100")
        print()
        
        # Key insights
        print("💡 Key Strengths:")
        for strength in summary['key_strengths'][:5]:
            print(f"   ✅ {strength}")
        print()
        
        if summary['areas_of_concern']:
            print("⚠️  Areas of Concern:")
            for concern in summary['areas_of_concern'][:3]:
                print(f"   🔸 {concern}")
            print()
        
        # Behavioral traits
        print("🧠 Behavioral Assessment:")
        traits = summary['behavioral_traits']
        print(f"   • Teamwork: {traits['teamwork']}")
        print(f"   • Problem Solving: {traits['problem_solving']}")
        print(f"   • Adaptability: {traits['adaptability']}")
        print()
        
        # Reasoning and next steps
        print("🤔 Reasoning:")
        print(f"   {summary['reasoning']}")
        print()
        
        print("🚀 Recommended Next Steps:")
        print(f"   {summary['next_steps']}")
        print()
        
        # Interview metadata
        metadata = summary['interview_metadata']
        print("📋 Interview Details:")
        print(f"   • Duration: ~{metadata['duration_minutes']} minutes")
        print(f"   • Questions Asked: {metadata['question_count']}")
        print(f"   • AI Model Used: {metadata['model_used']}")
        print(f"   • Completed: {metadata['completed_at']}")
        print()
        
        # 4. Demonstrate trial mode
        print("🎮 Step 4: Demonstrating Trial Mode...")
        print("=" * 40)
        
        trial_session = await ai_service.start_live_ai_interview(
            job_context=job_context,
            candidate_context=candidate_context,
            interview_config={**interview_config, "is_trial": True},
            is_trial=True
        )
        
        print(f"✅ Trial mode initialized")
        print(f"   Model: {trial_session['session_state']['model']} (faster, basic responses)")
        print(f"   Opening: \"{trial_session['opening_question'][:80]}...\"")
        print()
        
        # 5. Show adaptive difficulty
        print("🎚️  Step 5: Demonstrating Adaptive Difficulty...")
        print("=" * 40)
        
        # Show how the system adapts to different candidate levels
        beginner_response = "I'm new to programming and have only done some basic Python tutorials."
        expert_response = "I've architected distributed systems handling millions of requests per second using event-driven microservices with CQRS and event sourcing patterns."
        
        for level, response in [("Beginner", beginner_response), ("Expert", expert_response)]:
            analysis = await ai_service._analyze_response_sentiment_confidence(
                response=response,
                question="Tell me about your technical experience."
            )
            
            print(f"📊 {level} Level Response Analysis:")
            print(f"   Response: \"{response[:60]}...\"")
            print(f"   Technical Depth: {analysis.get('technical_depth', 'N/A')}")
            print(f"   Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"   → System would adapt difficulty accordingly")
            print()
        
        # 6. Feature summary
        print("🌟 Step 6: Feature Summary")
        print("=" * 40)
        
        features = [
            "✅ Real-time conversational AI using Groq LLM",
            "✅ Dynamic question generation based on responses", 
            "✅ Multi-turn conversation with context memory",
            "✅ Real-time sentiment and confidence analysis",
            "✅ Adaptive difficulty adjustment based on performance",
            "✅ Comprehensive interview summary with scoring",
            "✅ Trial mode with faster model for demos",
            "✅ Behavioral trait assessment",
            "✅ Technical skill evaluation",
            "✅ Cultural fit analysis",
            "✅ Bias detection and fairness auditing",
            "✅ Explainable AI with detailed reasoning",
            "✅ WebRTC integration for video calls",
            "✅ Speech-to-text and text-to-speech support",
            "✅ Error handling and graceful degradation"
        ]
        
        print("🚀 Implemented Features:")
        for feature in features:
            print(f"   {feature}")
        print()
        
        print("🎉 Demo completed successfully!")
        print("The Live AI Interview System is fully functional and ready for production use.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the demo"""
    print("🎬 Starting Live AI Interview System Demo...")
    print()
    
    success = await demo_live_ai_interview()
    
    if success:
        print("\n" + "=" * 60)
        print("🎊 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("The Live AI Interview System demonstrates:")
        print("• Advanced conversational AI capabilities")
        print("• Real-time analysis and adaptation")
        print("• Comprehensive candidate assessment")
        print("• Production-ready implementation")
        print()
        print("Ready for integration with the frontend React components!")
        return 0
    else:
        print("\n💥 Demo failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)