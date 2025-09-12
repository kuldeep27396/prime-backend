"""
Tests for candidate management functionality
"""

import pytest
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.job import Candidate, Application, Job
from app.models.company import Company, User
from app.schemas.candidate import CandidateCreate, CandidateSearch, ParsedResumeData
from app.services.candidate_service import CandidateService


class TestCandidateService:
    """Test candidate service functionality"""

    @pytest.fixture
    def candidate_service(self, db_session: Session):
        """Create candidate service instance"""
        return CandidateService(db_session)

    @pytest.fixture
    def sample_candidate_data(self):
        """Sample candidate data for testing"""
        return CandidateCreate(
            email="john.doe@example.com",
            name="John Doe",
            phone="+1234567890"
        )

    @pytest.fixture
    def sample_parsed_data(self):
        """Sample parsed resume data"""
        return ParsedResumeData(
            skills=[
                {"name": "Python", "confidence": 0.9, "category": "technical"},
                {"name": "JavaScript", "confidence": 0.8, "category": "technical"}
            ],
            experience=[
                {
                    "company": "Tech Corp",
                    "position": "Software Engineer",
                    "start_date": "2020-01",
                    "end_date": "2023-01",
                    "duration_months": 36,
                    "description": "Developed web applications",
                    "skills_used": ["Python", "JavaScript"]
                }
            ],
            education=[
                {
                    "institution": "University of Technology",
                    "degree": "Bachelor's",
                    "field_of_study": "Computer Science",
                    "start_date": "2016-09",
                    "end_date": "2020-05",
                    "gpa": 3.8
                }
            ],
            total_experience_years=3.0,
            summary="Experienced software engineer",
            contact_info={
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "location": "San Francisco, CA"
            }
        )

    async def test_create_candidate(self, candidate_service, sample_candidate_data):
        """Test creating a new candidate"""
        result = await candidate_service.create_candidate(sample_candidate_data)
        
        assert result.email == sample_candidate_data.email
        assert result.name == sample_candidate_data.name
        assert result.phone == sample_candidate_data.phone
        assert result.id is not None

    async def test_create_duplicate_candidate(self, candidate_service, sample_candidate_data, db_session):
        """Test creating a candidate with duplicate email"""
        # Create first candidate
        await candidate_service.create_candidate(sample_candidate_data)
        
        # Try to create duplicate
        with pytest.raises(Exception):  # Should raise HTTPException
            await candidate_service.create_candidate(sample_candidate_data)

    async def test_get_candidate(self, candidate_service, sample_candidate_data):
        """Test retrieving a candidate by ID"""
        created = await candidate_service.create_candidate(sample_candidate_data)
        retrieved = await candidate_service.get_candidate(created.id)
        
        assert retrieved.id == created.id
        assert retrieved.email == created.email
        assert retrieved.name == created.name

    async def test_get_nonexistent_candidate(self, candidate_service):
        """Test retrieving a non-existent candidate"""
        with pytest.raises(Exception):  # Should raise HTTPException
            await candidate_service.get_candidate(uuid4())

    async def test_list_candidates(self, candidate_service, db_session):
        """Test listing candidates with pagination"""
        # Create multiple candidates
        for i in range(5):
            candidate_data = CandidateCreate(
                email=f"candidate{i}@example.com",
                name=f"Candidate {i}",
                phone=f"+123456789{i}"
            )
            await candidate_service.create_candidate(candidate_data)
        
        # Test pagination
        result = await candidate_service.list_candidates(page=1, page_size=3)
        
        assert len(result.candidates) == 3
        assert result.total == 5
        assert result.page == 1
        assert result.page_size == 3
        assert result.total_pages == 2

    async def test_search_candidates_by_query(self, candidate_service, sample_candidate_data):
        """Test searching candidates by text query"""
        await candidate_service.create_candidate(sample_candidate_data)
        
        search_params = CandidateSearch(query="John", page=1, page_size=10)
        result = await candidate_service.search_candidates(search_params)
        
        assert len(result.candidates) == 1
        assert result.candidates[0].name == "John Doe"

    async def test_search_candidates_by_skills(self, candidate_service, db_session, sample_parsed_data):
        """Test searching candidates by skills"""
        # Create candidate with parsed data
        candidate = Candidate(
            email="skilled@example.com",
            name="Skilled Developer",
            parsed_data=sample_parsed_data.dict()
        )
        db_session.add(candidate)
        db_session.commit()
        
        search_params = CandidateSearch(skills=["Python"], page=1, page_size=10)
        result = await candidate_service.search_candidates(search_params)
        
        assert len(result.candidates) >= 1
        # Should find the candidate with Python skills

    async def test_bulk_import_csv(self, candidate_service):
        """Test bulk importing candidates from CSV"""
        csv_data = """email,name,phone
test1@example.com,Test User 1,+1111111111
test2@example.com,Test User 2,+2222222222
test3@example.com,Test User 3,+3333333333"""
        
        result = await candidate_service.bulk_import_candidates(
            csv_data.encode('utf-8'), 
            "candidates.csv", 
            "csv"
        )
        
        assert result.total_processed == 3
        assert result.successful_imports == 3
        assert result.failed_imports == 0
        assert len(result.imported_candidate_ids) == 3

    async def test_bulk_import_json(self, candidate_service):
        """Test bulk importing candidates from JSON"""
        json_data = [
            {"email": "json1@example.com", "name": "JSON User 1", "phone": "+1111111111"},
            {"email": "json2@example.com", "name": "JSON User 2", "phone": "+2222222222"}
        ]
        
        result = await candidate_service.bulk_import_candidates(
            json.dumps(json_data).encode('utf-8'),
            "candidates.json",
            "json"
        )
        
        assert result.total_processed == 2
        assert result.successful_imports == 2
        assert result.failed_imports == 0

    async def test_bulk_import_with_duplicates(self, candidate_service, sample_candidate_data):
        """Test bulk import handling duplicate emails"""
        # Create existing candidate
        await candidate_service.create_candidate(sample_candidate_data)
        
        # Try to import with duplicate email
        csv_data = f"""email,name,phone
{sample_candidate_data.email},Duplicate User,+9999999999
new@example.com,New User,+8888888888"""
        
        result = await candidate_service.bulk_import_candidates(
            csv_data.encode('utf-8'),
            "candidates.csv",
            "csv"
        )
        
        assert result.total_processed == 2
        assert result.successful_imports == 1
        assert result.failed_imports == 1
        assert len(result.errors) == 1

    async def test_create_application(self, candidate_service, db_session):
        """Test creating a job application"""
        # Create company, user, job, and candidate
        company = Company(name="Test Company")
        db_session.add(company)
        db_session.flush()
        
        user = User(
            company_id=company.id,
            email="recruiter@test.com",
            password_hash="hashed",
            role="recruiter"
        )
        db_session.add(user)
        db_session.flush()
        
        job = Job(
            company_id=company.id,
            title="Software Engineer",
            description="Test job",
            created_by=user.id
        )
        db_session.add(job)
        db_session.flush()
        
        candidate_data = CandidateCreate(
            email="applicant@example.com",
            name="Job Applicant"
        )
        candidate_response = await candidate_service.create_candidate(candidate_data)
        
        # Create application
        from app.schemas.candidate import ApplicationCreate
        application_data = ApplicationCreate(
            job_id=job.id,
            candidate_id=candidate_response.id,
            cover_letter="I am interested in this position"
        )
        
        result = await candidate_service.create_application(application_data)
        
        assert result.job_id == job.id
        assert result.candidate_id == candidate_response.id
        assert result.cover_letter == "I am interested in this position"
        assert result.status == "applied"

    async def test_create_duplicate_application(self, candidate_service, db_session):
        """Test creating duplicate application for same job and candidate"""
        # Setup company, user, job, and candidate
        company = Company(name="Test Company")
        db_session.add(company)
        db_session.flush()
        
        user = User(
            company_id=company.id,
            email="recruiter@test.com",
            password_hash="hashed",
            role="recruiter"
        )
        db_session.add(user)
        db_session.flush()
        
        job = Job(
            company_id=company.id,
            title="Software Engineer",
            description="Test job",
            created_by=user.id
        )
        db_session.add(job)
        db_session.flush()
        
        candidate_data = CandidateCreate(
            email="applicant@example.com",
            name="Job Applicant"
        )
        candidate_response = await candidate_service.create_candidate(candidate_data)
        
        # Create first application
        from app.schemas.candidate import ApplicationCreate
        application_data = ApplicationCreate(
            job_id=job.id,
            candidate_id=candidate_response.id
        )
        
        await candidate_service.create_application(application_data)
        
        # Try to create duplicate application
        with pytest.raises(Exception):  # Should raise HTTPException
            await candidate_service.create_application(application_data)


class TestCandidateAPI:
    """Test candidate API endpoints"""

    def test_create_candidate_endpoint(self, client: TestClient, auth_headers):
        """Test candidate creation endpoint"""
        response = client.post(
            "/api/v1/candidates/",
            data={
                "name": "API Test User",
                "email": "apitest@example.com",
                "phone": "+1234567890"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test User"
        assert data["email"] == "apitest@example.com"
        assert data["phone"] == "+1234567890"

    def test_list_candidates_endpoint(self, client: TestClient, auth_headers):
        """Test candidates listing endpoint"""
        # Create a candidate first
        client.post(
            "/api/v1/candidates/",
            data={
                "name": "List Test User",
                "email": "listtest@example.com"
            },
            headers=auth_headers
        )
        
        response = client.get("/api/v1/candidates/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_search_candidates_endpoint(self, client: TestClient, auth_headers):
        """Test candidate search endpoint"""
        # Create a candidate first
        client.post(
            "/api/v1/candidates/",
            data={
                "name": "Search Test User",
                "email": "searchtest@example.com"
            },
            headers=auth_headers
        )
        
        response = client.post(
            "/api/v1/candidates/search",
            json={
                "query": "Search Test",
                "page": 1,
                "page_size": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert len(data["candidates"]) >= 1

    def test_bulk_import_endpoint(self, client: TestClient, auth_headers):
        """Test bulk import endpoint"""
        csv_content = """email,name,phone
bulk1@example.com,Bulk User 1,+1111111111
bulk2@example.com,Bulk User 2,+2222222222"""
        
        response = client.post(
            "/api/v1/candidates/bulk-import",
            files={"file": ("candidates.csv", csv_content, "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 2
        assert data["failed_imports"] == 0

    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication"""
        response = client.get("/api/v1/candidates/")
        assert response.status_code == 401

    def test_create_application_endpoint(self, client: TestClient, auth_headers, db_session):
        """Test application creation endpoint"""
        # Setup test data
        from app.models.company import Company, User
        from app.models.job import Job
        
        company = Company(name="Test Company")
        db_session.add(company)
        db_session.flush()
        
        user = User(
            company_id=company.id,
            email="recruiter@test.com",
            password_hash="hashed",
            role="recruiter"
        )
        db_session.add(user)
        db_session.flush()
        
        job = Job(
            company_id=company.id,
            title="Software Engineer",
            description="Test job",
            created_by=user.id
        )
        db_session.add(job)
        db_session.commit()
        
        # Create candidate
        candidate_response = client.post(
            "/api/v1/candidates/",
            data={
                "name": "Application Test User",
                "email": "apptest@example.com"
            },
            headers=auth_headers
        )
        candidate_id = candidate_response.json()["id"]
        
        # Create application
        response = client.post(
            "/api/v1/candidates/applications",
            json={
                "job_id": str(job.id),
                "candidate_id": candidate_id,
                "cover_letter": "Test cover letter"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == str(job.id)
        assert data["candidate_id"] == candidate_id
        assert data["cover_letter"] == "Test cover letter"
        assert data["status"] == "applied"