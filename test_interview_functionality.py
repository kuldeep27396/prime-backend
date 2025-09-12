"""
Test interview template and management functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.company import Company, User
from app.models.job import Job, Candidate, Application
from app.models.interview import InterviewTemplate, Interview
from app.services.interview_service import InterviewService
from app.schemas.interview import (
    InterviewTemplateCreate, InterviewTemplateUpdate,
    InterviewCreate, InterviewUpdate, QuestionBankFilter
)


class TestInterviewService:
    """Test interview service functionality"""

    @pytest.fixture
    def db_session(self):
        """Create database session for testing"""
        db = next(get_db())
        yield db
        db.close()

    @pytest.fixture
    def test_company(self, db_session):
        """Create test company"""
        company = Company(
            name="Test Company",
            domain="test.com",
            settings={}
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)
        return company

    @pytest.fixture
    def test_user(self, db_session, test_company):
        """Create test user"""
        import uuid
        user = User(
            company_id=test_company.id,
            email=f"test-{uuid.uuid4()}@test.com",
            password_hash="hashed_password",
            role="recruiter",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def test_job(self, db_session, test_company, test_user):
        """Create test job"""
        job = Job(
            company_id=test_company.id,
            title="Software Engineer",
            description="Test job description",
            requirements={"skills": ["Python", "FastAPI"]},
            status="active",
            created_by=test_user.id
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def test_candidate(self, db_session):
        """Create test candidate"""
        import uuid
        candidate = Candidate(
            email=f"candidate-{uuid.uuid4()}@test.com",
            name="Test Candidate",
            phone="+1234567890",
            parsed_data={"skills": ["Python", "JavaScript"]}
        )
        db_session.add(candidate)
        db_session.commit()
        db_session.refresh(candidate)
        return candidate

    @pytest.fixture
    def test_application(self, db_session, test_job, test_candidate):
        """Create test application"""
        application = Application(
            job_id=test_job.id,
            candidate_id=test_candidate.id,
            status="applied",
            cover_letter="Test cover letter"
        )
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)
        return application

    @pytest.fixture
    def interview_service(self, db_session):
        """Create interview service instance"""
        return InterviewService(db_session)

    @pytest.mark.asyncio
    async def test_create_interview_template(self, interview_service, test_company, test_user):
        """Test creating interview template"""
        template_data = InterviewTemplateCreate(
            name="Technical Interview",
            description="Technical assessment for software engineers",
            type="technical",
            questions=[
                {
                    "id": "q1",
                    "type": "technical",
                    "category": "coding",
                    "content": "Implement a binary search algorithm",
                    "expected_duration": 1800,
                    "difficulty": "medium",
                    "tags": ["algorithms", "python"],
                    "metadata": {"points": 10}
                },
                {
                    "id": "q2",
                    "type": "technical",
                    "category": "system_design",
                    "content": "Design a URL shortener service",
                    "expected_duration": 2400,
                    "difficulty": "hard",
                    "tags": ["system_design", "scalability"],
                    "metadata": {"points": 15}
                }
            ],
            settings={
                "time_limit": 3600,
                "allow_code_execution": True,
                "recording_enabled": True
            }
        )

        result = await interview_service.create_template(
            template_data=template_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        assert result.name == "Technical Interview"
        assert result.description == "Technical assessment for software engineers"
        assert result.type == "technical"
        assert len(result.questions) == 2
        assert result.questions[0]["content"] == "Implement a binary search algorithm"
        assert result.settings["time_limit"] == 3600

    @pytest.mark.asyncio
    async def test_get_interview_templates(self, interview_service, test_company, test_user):
        """Test getting paginated interview templates"""
        # Create multiple templates
        for i in range(5):
            template_data = InterviewTemplateCreate(
                name=f"Template {i}",
                description=f"Description {i}",
                type="one_way" if i % 2 == 0 else "live_ai",
                questions=[],
                settings={}
            )
            await interview_service.create_template(
                template_data=template_data,
                company_id=test_company.id,
                user_id=test_user.id
            )

        # Test pagination
        result = await interview_service.get_templates(
            company_id=test_company.id,
            page=1,
            size=3
        )

        assert len(result["templates"]) == 3
        assert result["total"] == 5
        assert result["has_next"] is True

        # Test filtering by type
        result = await interview_service.get_templates(
            company_id=test_company.id,
            template_type="one_way"
        )

        assert len(result["templates"]) == 3  # 0, 2, 4
        for template in result["templates"]:
            assert template.type == "one_way"

    @pytest.mark.asyncio
    async def test_update_interview_template(self, interview_service, test_company, test_user):
        """Test updating interview template"""
        # Create template
        template_data = InterviewTemplateCreate(
            name="Original Template",
            description="Original description",
            type="one_way",
            questions=[],
            settings={}
        )

        template = await interview_service.create_template(
            template_data=template_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        # Update template
        update_data = InterviewTemplateUpdate(
            name="Updated Template",
            description="Updated description",
            questions=[
                {
                    "id": "q1",
                    "type": "behavioral",
                    "category": "communication",
                    "content": "Tell me about a challenging project",
                    "expected_duration": 300,
                    "difficulty": "easy",
                    "tags": ["behavioral"],
                    "metadata": {}
                }
            ]
        )

        updated_template = await interview_service.update_template(
            template_id=template.id,
            template_data=update_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        assert updated_template.name == "Updated Template"
        assert updated_template.description == "Updated description"
        assert len(updated_template.questions) == 1
        assert updated_template.questions[0]["content"] == "Tell me about a challenging project"

    @pytest.mark.asyncio
    async def test_create_interview(self, interview_service, test_company, test_user, test_application):
        """Test creating interview"""
        # Create template first
        template_data = InterviewTemplateCreate(
            name="Live AI Interview",
            description="AI-conducted interview",
            type="live_ai",
            questions=[],
            settings={}
        )

        template = await interview_service.create_template(
            template_data=template_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        # Create interview
        interview_data = InterviewCreate(
            application_id=test_application.id,
            template_id=template.id,
            type="live_ai",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            interview_metadata={"ai_model": "llama-3.1-70b"}
        )

        result = await interview_service.create_interview(
            interview_data=interview_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        assert result.application_id == test_application.id
        assert result.template_id == template.id
        assert result.type == "live_ai"
        assert result.status == "scheduled"
        assert result.interview_metadata["ai_model"] == "llama-3.1-70b"

    @pytest.mark.asyncio
    async def test_get_question_bank(self, interview_service, test_company, test_user):
        """Test getting question bank with filtering"""
        # Create templates with different question types
        template_data_1 = InterviewTemplateCreate(
            name="Technical Template",
            type="technical",
            questions=[
                {
                    "id": "tech1",
                    "type": "technical",
                    "category": "coding",
                    "content": "Write a sorting algorithm",
                    "difficulty": "medium",
                    "tags": ["algorithms", "python"]
                },
                {
                    "id": "tech2",
                    "type": "technical",
                    "category": "system_design",
                    "content": "Design a cache system",
                    "difficulty": "hard",
                    "tags": ["system_design", "caching"]
                }
            ],
            settings={}
        )

        template_data_2 = InterviewTemplateCreate(
            name="Behavioral Template",
            type="one_way",
            questions=[
                {
                    "id": "behav1",
                    "type": "behavioral",
                    "category": "leadership",
                    "content": "Describe a time you led a team",
                    "difficulty": "easy",
                    "tags": ["leadership", "teamwork"]
                }
            ],
            settings={}
        )

        await interview_service.create_template(
            template_data=template_data_1,
            company_id=test_company.id,
            user_id=test_user.id
        )

        await interview_service.create_template(
            template_data=template_data_2,
            company_id=test_company.id,
            user_id=test_user.id
        )

        # Test getting all questions
        filters = QuestionBankFilter()
        result = await interview_service.get_question_bank(
            company_id=test_company.id,
            filters=filters
        )

        assert result["total"] == 3
        assert len(result["questions"]) == 3
        assert "technical" in result["types"]
        assert "behavioral" in result["types"]
        assert "coding" in result["categories"]
        assert "leadership" in result["categories"]

        # Test filtering by type
        filters = QuestionBankFilter(type="technical")
        result = await interview_service.get_question_bank(
            company_id=test_company.id,
            filters=filters
        )

        assert result["total"] == 2
        for question in result["questions"]:
            assert question["type"] == "technical"

        # Test filtering by difficulty
        filters = QuestionBankFilter(difficulty="hard")
        result = await interview_service.get_question_bank(
            company_id=test_company.id,
            filters=filters
        )

        assert result["total"] == 1
        assert result["questions"][0]["content"] == "Design a cache system"

        # Test search functionality
        filters = QuestionBankFilter(search="sorting")
        result = await interview_service.get_question_bank(
            company_id=test_company.id,
            filters=filters
        )

        assert result["total"] == 1
        assert "sorting" in result["questions"][0]["content"].lower()

    @pytest.mark.asyncio
    async def test_customize_template_for_role(self, interview_service, test_company, test_user):
        """Test customizing template for specific role"""
        # Create base template
        template_data = InterviewTemplateCreate(
            name="Base Template",
            type="technical",
            questions=[
                {
                    "id": "q1",
                    "type": "technical",
                    "category": "coding",
                    "content": "Implement a function",
                    "difficulty": "medium",
                    "tags": ["programming"]
                }
            ],
            settings={}
        )

        template = await interview_service.create_template(
            template_data=template_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        # Customize for senior role
        role_requirements = {
            "role_title": "Senior Software Engineer",
            "seniority_level": "senior",
            "required_skills": ["python", "architecture"]
        }

        customized_template = await interview_service.customize_template_for_role(
            template_id=template.id,
            role_requirements=role_requirements,
            company_id=test_company.id
        )

        assert "Senior Software Engineer" in customized_template.name
        assert customized_template.questions[0]["difficulty"] == "hard"
        assert "python" in customized_template.questions[0]["tags"]
        assert "architecture" in customized_template.questions[0]["tags"]
        assert customized_template.settings["customized_for_role"] == "Senior Software Engineer"

    @pytest.mark.asyncio
    async def test_template_analytics(self, interview_service, test_company, test_user, test_application):
        """Test getting template analytics"""
        # Create template
        template_data = InterviewTemplateCreate(
            name="Analytics Template",
            type="one_way",
            questions=[
                {
                    "id": "q1",
                    "type": "behavioral",
                    "category": "communication",
                    "content": "Tell me about yourself",
                    "difficulty": "easy",
                    "tags": ["introduction"]
                }
            ],
            settings={}
        )

        template = await interview_service.create_template(
            template_data=template_data,
            company_id=test_company.id,
            user_id=test_user.id
        )

        # Create some interviews using this template
        for i in range(3):
            interview_data = InterviewCreate(
                application_id=test_application.id,
                template_id=template.id,
                type="one_way",
                interview_metadata={}
            )

            interview = await interview_service.create_interview(
                interview_data=interview_data,
                company_id=test_company.id,
                user_id=test_user.id
            )

            # Mark some as completed
            if i < 2:
                interview_update = InterviewUpdate(
                    status="completed",
                    started_at=datetime.utcnow() - timedelta(hours=1),
                    completed_at=datetime.utcnow()
                )
                await interview_service.update_interview(
                    interview_id=interview.id,
                    interview_data=interview_update,
                    company_id=test_company.id,
                    user_id=test_user.id
                )

        # Get analytics
        analytics = await interview_service.get_template_analytics(
            template_id=template.id,
            company_id=test_company.id
        )

        assert analytics.template_name == "Analytics Template"
        assert analytics.total_interviews == 3
        assert analytics.completed_interviews == 2
        assert analytics.average_completion_rate == 2/3
        assert analytics.average_duration is not None
        assert len(analytics.question_analytics) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])