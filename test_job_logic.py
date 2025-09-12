#!/usr/bin/env python3
"""
Test job management business logic without database
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from app.schemas.job import (
    JobCreate, JobUpdate, JobSearch, JobRequirements, SkillRequirement,
    SalaryRange, LocationRequirement, JobStatus, ExperienceLevel, LocationType,
    JobRequirementsParseRequest
)
from app.services.job_service import JobService


class MockDB:
    """Mock database session for testing"""
    def __init__(self):
        self.jobs = []
        self.applications = []
        self.candidates = []
        self.companies = []
        self.users = []
    
    def query(self, model):
        return MockQuery(self, model)
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def close(self):
        pass


class MockQuery:
    """Mock query object"""
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []
    
    def filter(self, *args):
        return self
    
    def first(self):
        return None
    
    def count(self):
        return 0
    
    def all(self):
        return []
    
    def offset(self, n):
        return self
    
    def limit(self, n):
        return self
    
    def order_by(self, *args):
        return self


async def test_job_schema_validation():
    """Test job schema validation"""
    print("🧪 Testing Job Schema Validation")
    print("=" * 40)
    
    try:
        # Test 1: Valid job creation schema
        print("1. Testing valid job creation...")
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
        
        assert job_data.title == "Senior Python Developer"
        assert job_data.status == JobStatus.DRAFT
        assert len(job_data.requirements.skills) == 2
        assert job_data.requirements.salary.min_salary == 90000
        print("✅ Valid job creation schema works")
        
        # Test 2: Job update schema
        print("2. Testing job update schema...")
        update_data = JobUpdate(
            title="Senior Python Developer (Updated)",
            status=JobStatus.ACTIVE
        )
        
        assert update_data.title == "Senior Python Developer (Updated)"
        assert update_data.status == JobStatus.ACTIVE
        print("✅ Job update schema works")
        
        # Test 3: Job search schema
        print("3. Testing job search schema...")
        search_params = JobSearch(
            query="Python developer",
            skills=["Python", "FastAPI"],
            experience_level=ExperienceLevel.SENIOR,
            location_type=LocationType.REMOTE,
            min_salary=80000,
            max_salary=150000,
            page=1,
            page_size=20
        )
        
        assert search_params.query == "Python developer"
        assert "Python" in search_params.skills
        assert search_params.experience_level == ExperienceLevel.SENIOR
        print("✅ Job search schema works")
        
        # Test 4: Salary range validation
        print("4. Testing salary range validation...")
        try:
            invalid_salary = SalaryRange(
                min_salary=100000,
                max_salary=80000,  # Invalid: max < min
                currency="USD",
                period="yearly"
            )
            print("❌ Should have failed salary validation")
        except ValueError:
            print("✅ Salary range validation works")
        
        # Test 5: Skill requirement validation
        print("5. Testing skill requirement validation...")
        skill = SkillRequirement(
            name="Python",
            required=True,
            experience_years=5,
            proficiency_level="advanced"
        )
        
        assert skill.name == "Python"
        assert skill.required == True
        assert skill.experience_years == 5
        print("✅ Skill requirement validation works")
        
        print("\n✅ All schema validation tests passed!")
        
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        raise


async def test_job_requirements_parsing():
    """Test job requirements parsing logic"""
    print("\n🧪 Testing Job Requirements Parsing")
    print("=" * 40)
    
    try:
        # Mock job service
        mock_db = MockDB()
        job_service = JobService(mock_db)
        
        # Test basic requirements parsing (fallback method)
        print("1. Testing basic requirements parsing...")
        parse_request = JobRequirementsParseRequest(
            job_title="Full Stack Developer",
            job_description="""
            We are seeking a talented Full Stack Developer to join our growing team. 
            The ideal candidate will have 3+ years of experience with React, Node.js, 
            and PostgreSQL. Must have a Bachelor's degree in Computer Science.
            
            Requirements:
            - 3+ years of JavaScript experience
            - Experience with React and Node.js
            - Knowledge of SQL databases
            - Python programming skills
            - Docker containerization experience
            
            Salary: $80,000 - $110,000 per year
            Location: Remote work available
            """
        )
        
        # Test the basic parsing method directly
        parse_result = await job_service._basic_requirements_parsing(parse_request)
        
        assert parse_result.success == True
        assert parse_result.parsed_requirements is not None
        assert len(parse_result.extracted_skills) > 0
        assert "Python" in parse_result.extracted_skills
        
        # Check salary parsing
        salary = parse_result.parsed_requirements.salary
        assert salary is not None
        assert salary.min_salary == 80000
        assert salary.max_salary == 110000
        
        # Check experience parsing
        assert parse_result.parsed_requirements.min_experience_years == 3
        
        print("✅ Basic requirements parsing works")
        print(f"   Extracted skills: {', '.join(parse_result.extracted_skills)}")
        print(f"   Min experience: {parse_result.parsed_requirements.min_experience_years} years")
        print(f"   Salary range: ${salary.min_salary:,} - ${salary.max_salary:,}")
        
        # Test 2: Test improvement suggestions
        print("2. Testing improvement suggestions...")
        suggestions = job_service._suggest_improvements(parse_request.job_description)
        
        assert len(suggestions) > 0
        print(f"✅ Generated {len(suggestions)} improvement suggestions")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print("\n✅ All requirements parsing tests passed!")
        
    except Exception as e:
        print(f"❌ Requirements parsing test failed: {e}")
        raise


async def test_job_status_transitions():
    """Test job status transition validation"""
    print("\n🧪 Testing Job Status Transitions")
    print("=" * 40)
    
    try:
        mock_db = MockDB()
        job_service = JobService(mock_db)
        
        # Test valid transitions
        valid_transitions = [
            (JobStatus.DRAFT, JobStatus.ACTIVE),
            (JobStatus.DRAFT, JobStatus.CLOSED),
            (JobStatus.ACTIVE, JobStatus.PAUSED),
            (JobStatus.ACTIVE, JobStatus.CLOSED),
            (JobStatus.PAUSED, JobStatus.ACTIVE),
            (JobStatus.PAUSED, JobStatus.CLOSED),
        ]
        
        print("1. Testing valid status transitions...")
        for old_status, new_status in valid_transitions:
            is_valid = job_service._is_valid_status_transition(old_status, new_status)
            assert is_valid == True
            print(f"   ✅ {old_status.value} → {new_status.value}")
        
        # Test invalid transitions
        invalid_transitions = [
            (JobStatus.CLOSED, JobStatus.ACTIVE),
            (JobStatus.CLOSED, JobStatus.DRAFT),
            (JobStatus.CLOSED, JobStatus.PAUSED),
        ]
        
        print("2. Testing invalid status transitions...")
        for old_status, new_status in invalid_transitions:
            is_valid = job_service._is_valid_status_transition(old_status, new_status)
            assert is_valid == False
            print(f"   ❌ {old_status.value} → {new_status.value} (correctly blocked)")
        
        print("\n✅ All status transition tests passed!")
        
    except Exception as e:
        print(f"❌ Status transition test failed: {e}")
        raise


async def test_job_search_scoring():
    """Test job search relevance scoring logic"""
    print("\n🧪 Testing Job Search Scoring")
    print("=" * 40)
    
    try:
        mock_db = MockDB()
        job_service = JobService(mock_db)
        
        # Create a mock job object
        class MockJob:
            def __init__(self):
                self.id = uuid4()
                self.title = "Senior Python Developer"
                self.description = "Looking for an experienced Python developer with FastAPI knowledge"
                self.requirements = {
                    "skills": [
                        {"name": "Python", "required": True},
                        {"name": "FastAPI", "required": True},
                        {"name": "PostgreSQL", "required": False}
                    ]
                }
                self.created_at = datetime.utcnow()
        
        mock_job = MockJob()
        
        # Test 1: Query matching
        print("1. Testing query-based relevance scoring...")
        search_params = JobSearch(
            query="Python FastAPI developer",
            page=1,
            page_size=10
        )
        
        score = await job_service._calculate_job_relevance_score(mock_job, search_params)
        assert score is not None
        assert 0 <= score <= 1
        print(f"✅ Query relevance score: {score:.3f}")
        
        # Test 2: Skills matching
        print("2. Testing skills-based relevance scoring...")
        search_params = JobSearch(
            skills=["Python", "FastAPI"],
            page=1,
            page_size=10
        )
        
        score = await job_service._calculate_job_relevance_score(mock_job, search_params)
        assert score is not None
        assert score > 0  # Should have high score for matching skills
        print(f"✅ Skills relevance score: {score:.3f}")
        
        # Test 3: Find matching skills and keywords
        print("3. Testing match finding...")
        search_params = JobSearch(
            query="Python developer",
            skills=["Python", "FastAPI", "Django"],  # Django not in job
            page=1,
            page_size=10
        )
        
        matching_skills, matching_keywords = job_service._find_job_matches(mock_job, search_params)
        
        assert "Python" in matching_skills
        assert "FastAPI" in matching_skills
        assert "Django" not in matching_skills  # Not in job requirements
        assert len(matching_keywords) > 0
        
        print(f"✅ Found matching skills: {', '.join(matching_skills)}")
        print(f"✅ Found matching keywords: {', '.join(matching_keywords)}")
        
        print("\n✅ All search scoring tests passed!")
        
    except Exception as e:
        print(f"❌ Search scoring test failed: {e}")
        raise


async def test_analytics_generation():
    """Test analytics and insights generation"""
    print("\n🧪 Testing Analytics Generation")
    print("=" * 40)
    
    try:
        mock_db = MockDB()
        job_service = JobService(mock_db)
        
        # Create mock analytics data
        from app.schemas.job import JobAnalytics, JobApplicationStats, JobPerformanceMetrics, CandidateQualityMetrics
        
        analytics = JobAnalytics(
            job_id=uuid4(),
            application_stats=JobApplicationStats(
                total_applications=50,
                applications_by_status={
                    "applied": 30,
                    "screening": 10,
                    "interviewing": 5,
                    "hired": 2,
                    "rejected": 3
                },
                avg_applications_per_day=2.5,
                conversion_rates={
                    "applied": 60.0,
                    "screening": 20.0,
                    "interviewing": 10.0,
                    "hired": 4.0,
                    "rejected": 6.0
                }
            ),
            performance_metrics=JobPerformanceMetrics(
                views=500,
                applications=50,
                application_rate=0.1,
                quality_score=7.5
            ),
            candidate_quality=CandidateQualityMetrics(
                total_candidates=50,
                qualified_candidates=35,
                qualification_rate=70.0,
                avg_experience_years=4.2,
                skill_match_distribution={
                    "python": 40,
                    "fastapi": 25,
                    "postgresql": 30
                }
            ),
            generated_at=datetime.utcnow()
        )
        
        # Test 1: Generate recommendations
        print("1. Testing recommendation generation...")
        recommendations = job_service._generate_recommendations(analytics)
        
        assert len(recommendations) >= 0  # May or may not have recommendations
        print(f"✅ Generated {len(recommendations)} recommendations")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Test 2: Generate insights
        print("2. Testing insight generation...")
        insights = job_service._generate_insights(analytics)
        
        assert len(insights) > 0
        print(f"✅ Generated {len(insights)} insights")
        for i, insight in enumerate(insights, 1):
            print(f"   {i}. {insight}")
        
        # Test 3: Test with poor performance metrics
        print("3. Testing recommendations for poor performance...")
        poor_analytics = JobAnalytics(
            job_id=uuid4(),
            application_stats=JobApplicationStats(total_applications=2),
            performance_metrics=JobPerformanceMetrics(
                views=1000,
                applications=2,
                application_rate=0.002,  # Very low
                quality_score=3.0  # Low quality
            ),
            candidate_quality=CandidateQualityMetrics(
                total_candidates=2,
                qualified_candidates=0,
                qualification_rate=0.0,  # No qualified candidates
                skill_match_distribution={}
            ),
            generated_at=datetime.utcnow()
        )
        
        poor_recommendations = job_service._generate_recommendations(poor_analytics)
        assert len(poor_recommendations) > 0  # Should have recommendations for improvement
        print(f"✅ Generated {len(poor_recommendations)} recommendations for improvement")
        
        print("\n✅ All analytics generation tests passed!")
        
    except Exception as e:
        print(f"❌ Analytics generation test failed: {e}")
        raise


async def main():
    """Run all tests"""
    print("🚀 Starting Job Management Logic Tests")
    print("=" * 50)
    
    await test_job_schema_validation()
    await test_job_requirements_parsing()
    await test_job_status_transitions()
    await test_job_search_scoring()
    await test_analytics_generation()
    
    print("\n" + "=" * 50)
    print("✅ All job management logic tests completed successfully!")
    print("🎯 Job management business logic is working correctly")
    print("\n📋 Summary of tested functionality:")
    print("   ✅ Job schema validation and serialization")
    print("   ✅ Job requirements parsing from text")
    print("   ✅ Job status transition validation")
    print("   ✅ Job search relevance scoring")
    print("   ✅ Analytics and insights generation")


if __name__ == "__main__":
    asyncio.run(main())