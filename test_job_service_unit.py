#!/usr/bin/env python3
"""
Unit tests for job service functionality
"""

import asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.company import Company, User
from app.models.job import Job, Application, Candidate
from app.services.job_service import JobService
from app.schemas.job import (
    JobCreate, JobUpdate, JobSearch, JobRequirements, SkillRequirement,
    SalaryRange, LocationRequirement, JobStatus, ExperienceLevel, LocationType
)


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    """Set up test database with sample data"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test company
    company = Company(
        id=uuid4(),
        name="Test Company",
        domain="test.com",
        settings={}
    )
    db.add(company)
    db.flush()
    
    # Create test user
    user = User(
        id=uuid4(),
        company_id=company.id,
        email="test@example.com",
        password_hash="hashed_password",
        role="recruiter",
        profile={},
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.flush()
    
    # Create test candidate
    candidate = Candidate(
        id=uuid4(),
        email="candidate@example.com",
        name="Test Candidate",
        phone="+1234567890",
        parsed_data={
            "skills": [
                {"name": "Python", "confidence": 0.9, "category": "technical"},
                {"name": "FastAPI", "confidence": 0.8, "category": "technical"}
            ],
            "total_experience_years": 5
        }
    )
    db.add(candidate)
    db.commit()
    
    return db, company, user, candidate


async def test_job_crud_operations():
    """Test basic CRUD operations for jobs"""
    print("🧪 Testing Job CRUD Operations")
    print("=" * 40)
    
    db, company, user, candidate = setup_test_db()
    job_service = JobService(db)
    
    try:
        # Test 1: Create job
        print("1. Testing job creation...")
        job_data = JobCreate(
            title="Senior Python Developer",
            description="Looking for an experienced Python developer",
            requirements=JobRequirements(
                skills=[
                    SkillRequirement(
                        name="Python",
                        required=True,
                        experience_years=5,
                        proficiency_level="advanced"
                    ),
                    SkillRequirement(
                        name="FastAPI",
                        required=True,
                        experience_years=2,
                        proficiency_level="intermediate"
                    )
                ],
                experience_level=ExperienceLevel.SENIOR,
                min_experience_years=5,
                location=LocationRequirement(
                    type=LocationType.REMOTE,
                    timezone="UTC-5"
                ),
                salary=SalaryRange(
                    min_salary=90000,
                    max_salary=130000,
                    currency="USD",
                    period="yearly"
                )
            ),
            status=JobStatus.DRAFT
        )
        
        created_job = await job_service.create_job(
            job_data=job_data,
            created_by_user_id=user.id,
            company_id=company.id
        )
        
        assert created_job.title == "Senior Python Developer"
        assert created_job.status == JobStatus.DRAFT
        assert len(created_job.requirements.skills) == 2
        print(f"✅ Job created with ID: {created_job.id}")
        
        # Test 2: Get job
        print("2. Testing job retrieval...")
        retrieved_job = await job_service.get_job(
            job_id=created_job.id,
            company_id=company.id
        )
        
        assert retrieved_job.id == created_job.id
        assert retrieved_job.title == "Senior Python Developer"
        print("✅ Job retrieved successfully")
        
        # Test 3: Update job
        print("3. Testing job update...")
        update_data = JobUpdate(
            title="Senior Python Developer (Updated)",
            status=JobStatus.ACTIVE
        )
        
        updated_job = await job_service.update_job(
            job_id=created_job.id,
            job_data=update_data,
            updated_by_user_id=user.id,
            company_id=company.id
        )
        
        assert updated_job.title == "Senior Python Developer (Updated)"
        assert updated_job.status == JobStatus.ACTIVE
        print("✅ Job updated successfully")
        
        # Test 4: List jobs
        print("4. Testing job listing...")
        job_list = await job_service.list_jobs(
            page=1,
            page_size=10,
            company_id=company.id
        )
        
        assert job_list.total >= 1
        assert len(job_list.jobs) >= 1
        assert job_list.jobs[0].id == created_job.id
        print(f"✅ Listed {job_list.total} jobs")
        
        # Test 5: Search jobs
        print("5. Testing job search...")
        search_params = JobSearch(
            query="Python",
            skills=["Python"],
            page=1,
            page_size=10
        )
        
        search_results = await job_service.search_jobs(
            search_params=search_params,
            company_id=company.id
        )
        
        assert search_results.total >= 1
        assert len(search_results.jobs) >= 1
        print(f"✅ Found {search_results.total} jobs matching search")
        
        # Test 6: Change job status
        print("6. Testing job status change...")
        from app.schemas.job import JobStatusChange
        
        status_change = JobStatusChange(
            status=JobStatus.PAUSED,
            reason="Testing status change"
        )
        
        status_result = await job_service.change_job_status(
            job_id=created_job.id,
            status_change=status_change,
            changed_by_user_id=user.id,
            company_id=company.id
        )
        
        assert status_result.old_status == JobStatus.ACTIVE
        assert status_result.new_status == JobStatus.PAUSED
        print("✅ Job status changed successfully")
        
        # Test 7: Get job analytics
        print("7. Testing job analytics...")
        analytics = await job_service.get_job_analytics(
            job_id=created_job.id,
            company_id=company.id
        )
        
        assert analytics.analytics.job_id == created_job.id
        assert analytics.analytics.application_stats.total_applications == 0
        print("✅ Job analytics retrieved successfully")
        
        # Test 8: Requirements parsing
        print("8. Testing requirements parsing...")
        from app.schemas.job import JobRequirementsParseRequest
        
        parse_request = JobRequirementsParseRequest(
            job_title="Full Stack Developer",
            job_description="""
            We need a Full Stack Developer with 3+ years of experience.
            Must know React, Node.js, and PostgreSQL.
            Salary: $80,000 - $110,000 per year.
            Remote work available.
            """
        )
        
        parse_result = await job_service.parse_job_requirements(parse_request)
        
        assert parse_result.success == True
        assert parse_result.parsed_requirements is not None
        print("✅ Requirements parsing completed")
        
        # Test 9: Delete job (soft delete)
        print("9. Testing job deletion...")
        delete_result = await job_service.delete_job(
            job_id=created_job.id,
            company_id=company.id
        )
        
        assert delete_result == True
        
        # Verify job is soft deleted (status changed to closed)
        deleted_job = await job_service.get_job(
            job_id=created_job.id,
            company_id=company.id
        )
        assert deleted_job.status == JobStatus.CLOSED
        print("✅ Job soft deleted successfully")
        
        print("\n" + "=" * 40)
        print("🎉 All job service tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        db.close()


async def test_job_analytics_with_applications():
    """Test job analytics with sample applications"""
    print("\n🧪 Testing Job Analytics with Applications")
    print("=" * 40)
    
    db, company, user, candidate = setup_test_db()
    job_service = JobService(db)
    
    try:
        # Create a job
        job_data = JobCreate(
            title="Data Scientist",
            description="Looking for a data scientist",
            requirements=JobRequirements(
                skills=[
                    SkillRequirement(name="Python", required=True),
                    SkillRequirement(name="Machine Learning", required=True)
                ]
            ),
            status=JobStatus.ACTIVE
        )
        
        created_job = await job_service.create_job(
            job_data=job_data,
            created_by_user_id=user.id,
            company_id=company.id
        )
        
        # Create some applications
        for i in range(3):
            application = Application(
                job_id=created_job.id,
                candidate_id=candidate.id,
                status="applied",
                cover_letter=f"Cover letter {i+1}",
                application_data={}
            )
            db.add(application)
        
        db.commit()
        
        # Get analytics
        analytics = await job_service.get_job_analytics(
            job_id=created_job.id,
            company_id=company.id
        )
        
        assert analytics.analytics.application_stats.total_applications == 3
        assert len(analytics.recommendations) > 0
        assert len(analytics.insights) > 0
        
        print(f"✅ Analytics generated for job with {analytics.analytics.application_stats.total_applications} applications")
        print(f"   Recommendations: {len(analytics.recommendations)}")
        print(f"   Insights: {len(analytics.insights)}")
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        raise
    finally:
        db.close()


async def main():
    """Run all tests"""
    print("🚀 Starting Job Service Unit Tests")
    print("=" * 50)
    
    await test_job_crud_operations()
    await test_job_analytics_with_applications()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("🎯 Job management functionality is working correctly")


if __name__ == "__main__":
    asyncio.run(main())