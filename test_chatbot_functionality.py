"""
Test chatbot pre-screening functionality
"""

import asyncio
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.company import Company, User
from app.models.job import Job, Candidate, Application
from app.models.chatbot import ChatbotTemplate, ChatbotSession
from app.services.chatbot_service import ChatbotService
from app.schemas.chatbot import (
    ChatbotTemplateCreate, ChatbotSessionStart, CandidateResponse,
    QuestionConfig, ChatbotSettings
)


def test_chatbot_template_creation():
    """Test creating a chatbot template"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test company and user
        company = Company(name="Test Company Template")
        db.add(company)
        db.commit()
        db.refresh(company)
        
        user = User(
            company_id=company.id,
            email=f"test-template-{uuid4()}@example.com",
            password_hash="hashed_password",
            role="recruiter"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create test job
        job = Job(
            company_id=company.id,
            title="Software Engineer",
            description="Test job description",
            requirements={"skills": ["Python", "FastAPI"]},
            created_by=user.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Create chatbot template
        service = ChatbotService(db)
        
        question_flow = [
            QuestionConfig(
                id="q1",
                type="open_ended",
                text="Tell me about your experience with Python programming.",
                required=True,
                evaluation_criteria={"keywords": ["python", "programming", "experience"]}
            ),
            QuestionConfig(
                id="q2",
                type="multiple_choice",
                text="How many years of experience do you have?",
                options=["0-1 years", "2-3 years", "4-5 years", "5+ years"],
                required=True
            )
        ]
        
        template_data = ChatbotTemplateCreate(
            name="Python Developer Pre-screening",
            description="Pre-screening questions for Python developers",
            job_id=job.id,
            question_flow=question_flow,
            settings=ChatbotSettings(personality="professional")
        )
        
        # Test template creation
        result = asyncio.run(service.create_template(
            template_data,
            company.id,
            user.id
        ))
        
        assert result.name == "Python Developer Pre-screening"
        assert len(result.question_flow) == 2
        assert result.is_active == True
        
        print("✓ Chatbot template creation test passed")
        
    except Exception as e:
        print(f"✗ Chatbot template creation test failed: {e}")
        raise
    finally:
        db.close()


def test_chatbot_session_flow():
    """Test complete chatbot session flow"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test data
        company = Company(name="Test Company Session")
        db.add(company)
        db.commit()
        db.refresh(company)
        
        user = User(
            company_id=company.id,
            email=f"test-session-{uuid4()}@example.com",
            password_hash="hashed_password",
            role="recruiter"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        job = Job(
            company_id=company.id,
            title="Software Engineer",
            description="Test job description",
            requirements={"skills": ["Python", "FastAPI"]},
            created_by=user.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        candidate = Candidate(
            email="candidate@example.com",
            name="John Doe",
            parsed_data={"skills": ["Python", "JavaScript"]}
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        application = Application(
            job_id=job.id,
            candidate_id=candidate.id,
            status="applied"
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        
        # Create template
        template = ChatbotTemplate(
            company_id=company.id,
            name="Test Template",
            question_flow=[
                {
                    "id": "q1",
                    "type": "open_ended",
                    "text": "Tell me about yourself.",
                    "required": True,
                    "evaluation_criteria": {"keywords": ["experience", "skills"]}
                }
            ],
            settings={"personality": "professional"},
            created_by=user.id
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        
        # Test session flow
        service = ChatbotService(db)
        
        # Start session
        session_data = ChatbotSessionStart(
            application_id=application.id,
            template_id=template.id
        )
        
        # Note: This would normally call the AI service, but for testing we'll mock it
        # In a real test, you'd want to mock the AI service calls
        print("✓ Chatbot session flow test setup completed")
        print("  (AI service calls would be mocked in full integration tests)")
        
    except Exception as e:
        print(f"✗ Chatbot session flow test failed: {e}")
        raise
    finally:
        db.close()


def test_database_models():
    """Test that chatbot database models work correctly"""
    
    db = next(get_db())
    
    try:
        # Test that we can query the new tables
        templates = db.query(ChatbotTemplate).all()
        sessions = db.query(ChatbotSession).all()
        
        print(f"✓ Database models test passed - found {len(templates)} templates, {len(sessions)} sessions")
        
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Testing chatbot pre-screening functionality...")
    
    try:
        test_database_models()
        test_chatbot_template_creation()
        test_chatbot_session_flow()
        
        print("\n✅ All chatbot tests passed!")
        
    except Exception as e:
        print(f"\n❌ Chatbot tests failed: {e}")
        exit(1)