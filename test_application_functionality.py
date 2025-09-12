"""
Test application and pipeline management functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.models.company import Company, User
from app.models.job import Job, Candidate, Application
from app.models.scoring import Score
from app.services.application_service import ApplicationService
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, PipelineStatusUpdate,
    ApplicationFilters, ApplicationSort, RankingWeights,
    ApplicationStatus, SortField, SortDirection
)


class TestApplicationService:
    """Test application service functionality"""

    @pytest.fixture
    def db_session(self):
        """Create a test database session"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.database import Base
        
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()

    @pytest.fixture
    def sample_data(self, db_session):
        """Create sample data for testing"""
        # Create company
        company = Company(
            id=uuid4(),
            name="Test Company",
            domain="test.com"
        )
        db_session.add(company)
        
        # Create user
        user = User(
            id=uuid4(),
            company_id=company.id,
            email="test@test.com",
            password_hash="hashed_password",
            role="recruiter"
        )
        db_session.add(user)
        
        # Create job
        job = Job(
            id=uuid4(),
            company_id=company.id,
            title="Software Engineer",
            description="Test job description",
            status="active",
            created_by=user.id
        )
        db_session.add(job)
        
        # Create candidates
        candidates = []
        for i in range(3):
            candidate = Candidate(
                id=uuid4(),
                email=f"candidate{i}@test.com",
                name=f"Candidate {i}",
                phone=f"+123456789{i}",
                parsed_data={
                    "skills": [{"name": "Python", "confidence": 0.9}],
                    "total_experience_years": i + 2
                }
            )
            candidates.append(candidate)
            db_session.add(candidate)
        
        db_session.commit()
        
        return {
            "company": company,
            "user": user,
            "job": job,
            "candidates": candidates
        }

    @pytest.mark.asyncio
    async def test_create_application(self, db_session, sample_data):
        """Test creating a new application"""
        service = ApplicationService(db_session)
        
        application_data = ApplicationCreate(
            job_id=sample_data["job"].id,
            candidate_id=sample_data["candidates"][0].id,
            cover_letter="Test cover letter",
            application_data={"source": "website"}
        )
        
        result = await service.create_application(application_data)
        
        assert result.job_id == sample_data["job"].id
        assert result.candidate_id == sample_data["candidates"][0].id
        assert result.status == ApplicationStatus.APPLIED
        assert result.cover_letter == "Test cover letter"
        assert result.candidate_name == "Candidate 0"
        assert result.job_title == "Software Engineer"

    @pytest.mark.asyncio
    async def test_create_duplicate_application(self, db_session, sample_data):
        """Test creating duplicate application raises error"""
        service = ApplicationService(db_session)
        
        # Create first application
        application_data = ApplicationCreate(
            job_id=sample_data["job"].id,
            candidate_id=sample_data["candidates"][0].id
        )
        
        await service.create_application(application_data)
        
        # Try to create duplicate
        with pytest.raises(Exception) as exc_info:
            await service.create_application(application_data)
        
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_pipeline_status(self, db_session, sample_data):
        """Test updating application pipeline status"""
        service = ApplicationService(db_session)
        
        # Create application
        application_data = ApplicationCreate(
            job_id=sample_data["job"].id,
            candidate_id=sample_data["candidates"][0].id
        )
        
        app = await service.create_application(application_data)
        
        # Update status
        status_update = PipelineStatusUpdate(
            status=ApplicationStatus.SCREENING,
            notes="Passed initial screening",
            changed_by="test_user"
        )
        
        updated_app = await service.update_pipeline_status(app.id, status_update)
        
        assert updated_app.status == ApplicationStatus.SCREENING
        assert "status_history" in updated_app.application_data
        assert len(updated_app.application_data["status_history"]) == 1
        
        history = updated_app.application_data["status_history"][0]
        assert history["from_status"] == ApplicationStatus.APPLIED
        assert history["to_status"] == ApplicationStatus.SCREENING
        assert history["notes"] == "Passed initial screening"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, db_session, sample_data):
        """Test invalid status transition raises error"""
        service = ApplicationService(db_session)
        
        # Create application
        application_data = ApplicationCreate(
            job_id=sample_data["job"].id,
            candidate_id=sample_data["candidates"][0].id
        )
        
        app = await service.create_application(application_data)
        
        # Try invalid transition (applied -> hired)
        status_update = PipelineStatusUpdate(
            status=ApplicationStatus.HIRED,
            changed_by="test_user"
        )
        
        with pytest.raises(Exception) as exc_info:
            await service.update_pipeline_status(app.id, status_update)
        
        assert "Invalid status transition" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_applications_with_filters(self, db_session, sample_data):
        """Test listing applications with filters"""
        service = ApplicationService(db_session)
        
        # Create multiple applications
        applications = []
        for i, candidate in enumerate(sample_data["candidates"]):
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id,
                cover_letter="Cover letter" if i % 2 == 0 else None
            )
            app = await service.create_application(app_data)
            applications.append(app)
        
        # Test filter by has_cover_letter
        filters = ApplicationFilters(has_cover_letter=True)
        sort = ApplicationSort()
        
        result = await service.list_applications(filters, sort, page=1, page_size=10)
        
        assert result.total == 2  # Only applications with cover letters
        assert all(app.cover_letter is not None for app in result.applications)

    @pytest.mark.asyncio
    async def test_list_applications_with_sorting(self, db_session, sample_data):
        """Test listing applications with sorting"""
        service = ApplicationService(db_session)
        
        # Create applications with different timestamps
        applications = []
        for i, candidate in enumerate(sample_data["candidates"]):
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id
            )
            app = await service.create_application(app_data)
            applications.append(app)
            
            # Simulate different creation times
            db_app = db_session.query(Application).filter(
                Application.id == app.id
            ).first()
            db_app.created_at = datetime.utcnow() - timedelta(hours=i)
            db_session.commit()
        
        # Test sorting by created_at ascending
        filters = ApplicationFilters()
        sort = ApplicationSort(
            field=SortField.CREATED_AT,
            direction=SortDirection.ASC
        )
        
        result = await service.list_applications(filters, sort, page=1, page_size=10)
        
        # Should be sorted by oldest first
        assert result.applications[0].candidate_name == "Candidate 2"
        assert result.applications[-1].candidate_name == "Candidate 0"

    @pytest.mark.asyncio
    async def test_candidate_rankings(self, db_session, sample_data):
        """Test candidate ranking with customizable weights"""
        service = ApplicationService(db_session)
        
        # Create applications
        applications = []
        for candidate in sample_data["candidates"]:
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id
            )
            app = await service.create_application(app_data)
            applications.append(app)
        
        # Add scores for each application
        for i, app in enumerate(applications):
            # Create different scores for each candidate
            scores = [
                Score(
                    application_id=app.id,
                    category="technical",
                    score=80 + i * 5,  # 80, 85, 90
                    confidence=90,
                    created_by="ai"
                ),
                Score(
                    application_id=app.id,
                    category="communication",
                    score=70 + i * 10,  # 70, 80, 90
                    confidence=85,
                    created_by="ai"
                )
            ]
            
            for score in scores:
                db_session.add(score)
        
        db_session.commit()
        
        # Test ranking with default weights
        rankings = await service.get_candidate_rankings(sample_data["job"].id)
        
        assert len(rankings) == 3
        assert rankings[0].rank == 1
        assert rankings[0].candidate_name == "Candidate 2"  # Highest scores
        assert rankings[-1].rank == 3
        assert rankings[-1].candidate_name == "Candidate 0"  # Lowest scores
        
        # Test with custom weights (favor communication over technical)
        custom_weights = RankingWeights(
            technical_weight=0.2,
            communication_weight=0.5,
            cultural_fit_weight=0.1,
            cognitive_weight=0.1,
            behavioral_weight=0.1
        )
        
        custom_rankings = await service.get_candidate_rankings(
            sample_data["job"].id, 
            custom_weights
        )
        
        # Rankings should still favor Candidate 2 but with different scores
        assert custom_rankings[0].candidate_name == "Candidate 2"
        assert custom_rankings[0].overall_score != rankings[0].overall_score

    @pytest.mark.asyncio
    async def test_application_analytics(self, db_session, sample_data):
        """Test application analytics and funnel data"""
        service = ApplicationService(db_session)
        
        # Create applications with different statuses
        statuses = [
            ApplicationStatus.APPLIED,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.HIRED,
            ApplicationStatus.REJECTED
        ]
        
        applications = []
        for i, candidate in enumerate(sample_data["candidates"]):
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id
            )
            app = await service.create_application(app_data)
            
            # Update status
            if i < len(statuses):
                db_app = db_session.query(Application).filter(
                    Application.id == app.id
                ).first()
                db_app.status = statuses[i]
                db_session.commit()
            
            applications.append(app)
        
        # Add more applications to test funnel
        for i in range(2):
            extra_candidate = Candidate(
                id=uuid4(),
                email=f"extra{i}@test.com",
                name=f"Extra {i}"
            )
            db_session.add(extra_candidate)
            db_session.commit()
            
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=extra_candidate.id
            )
            app = await service.create_application(app_data)
            applications.append(app)
        
        # Get analytics
        analytics = await service.get_application_analytics(
            job_id=sample_data["job"].id
        )
        
        assert analytics.total_applications == 5
        assert len(analytics.funnel_data) == 6  # 5 stages + rejected
        
        # Check funnel data
        applied_stage = next(
            stage for stage in analytics.funnel_data 
            if stage.stage == ApplicationStatus.APPLIED
        )
        assert applied_stage.count == 3  # 2 extra + 1 original applied
        
        # Check pipeline metrics
        assert analytics.pipeline_metrics.total_applications == 5
        assert analytics.pipeline_metrics.hired_count == 1
        assert analytics.pipeline_metrics.rejected_count == 1
        assert analytics.pipeline_metrics.active_applications == 3

    @pytest.mark.asyncio
    async def test_application_search(self, db_session, sample_data):
        """Test application search functionality"""
        service = ApplicationService(db_session)
        
        # Create applications
        for candidate in sample_data["candidates"]:
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id
            )
            await service.create_application(app_data)
        
        # Test search by candidate name
        filters = ApplicationFilters(candidate_name="Candidate 1")
        sort = ApplicationSort()
        
        result = await service.list_applications(filters, sort, page=1, page_size=10)
        
        assert result.total == 1
        assert result.applications[0].candidate_name == "Candidate 1"

    @pytest.mark.asyncio
    async def test_application_pagination(self, db_session, sample_data):
        """Test application pagination"""
        service = ApplicationService(db_session)
        
        # Create many applications
        candidates = []
        for i in range(10):
            candidate = Candidate(
                id=uuid4(),
                email=f"test{i}@test.com",
                name=f"Test Candidate {i}"
            )
            candidates.append(candidate)
            db_session.add(candidate)
        
        db_session.commit()
        
        for candidate in candidates:
            app_data = ApplicationCreate(
                job_id=sample_data["job"].id,
                candidate_id=candidate.id
            )
            await service.create_application(app_data)
        
        # Test pagination
        filters = ApplicationFilters()
        sort = ApplicationSort()
        
        # First page
        page1 = await service.list_applications(filters, sort, page=1, page_size=5)
        assert len(page1.applications) == 5
        assert page1.total == 10
        assert page1.total_pages == 2
        
        # Second page
        page2 = await service.list_applications(filters, sort, page=2, page_size=5)
        assert len(page2.applications) == 5
        assert page2.total == 10
        assert page2.total_pages == 2
        
        # Ensure different applications on different pages
        page1_ids = {app.id for app in page1.applications}
        page2_ids = {app.id for app in page2.applications}
        assert page1_ids.isdisjoint(page2_ids)


def test_application_status_enum():
    """Test application status enum values"""
    assert ApplicationStatus.APPLIED == "applied"
    assert ApplicationStatus.SCREENING == "screening"
    assert ApplicationStatus.INTERVIEWING == "interviewing"
    assert ApplicationStatus.ASSESSED == "assessed"
    assert ApplicationStatus.HIRED == "hired"
    assert ApplicationStatus.REJECTED == "rejected"


def test_ranking_weights_validation():
    """Test ranking weights validation"""
    # Valid weights
    weights = RankingWeights(
        technical_weight=0.3,
        communication_weight=0.2,
        cultural_fit_weight=0.2,
        cognitive_weight=0.15,
        behavioral_weight=0.15
    )
    assert weights.technical_weight == 0.3
    
    # Test that weights sum to 1.0 (this would be validated in the API layer)
    total = (weights.technical_weight + weights.communication_weight + 
             weights.cultural_fit_weight + weights.cognitive_weight + 
             weights.behavioral_weight)
    assert abs(total - 1.0) < 0.01


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])