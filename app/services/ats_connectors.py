"""
Mock ATS connector implementations for Greenhouse, Lever, Workday, and BambooHR
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from app.services.integration_service import ATSConnector
from app.schemas.integration import ATSCandidate, ATSJob, ATSCandidateUpdate

logger = logging.getLogger(__name__)


class GreenhouseConnector(ATSConnector):
    """Mock Greenhouse ATS connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.base_url = credentials.get("base_url", "https://harvest-api.greenhouse.io/v1")
        self.api_key = credentials.get("api_key")
    
    async def authenticate(self) -> bool:
        """Mock authentication"""
        await asyncio.sleep(0.1)  # Simulate API call
        if not self.api_key:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Greenhouse"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Greenhouse rate limits"""
        return {
            "limit": 1000,
            "remaining": random.randint(500, 1000),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[ATSCandidate]:
        """Get candidates from Greenhouse"""
        await asyncio.sleep(0.2)  # Simulate API call
        
        # Mock candidate data
        mock_candidates = []
        for i in range(random.randint(5, 15)):
            candidate = ATSCandidate(
                external_id=f"gh_candidate_{i}",
                email=f"candidate{i}@example.com",
                name=f"John Doe {i}",
                phone=f"+1555000{i:04d}",
                resume_url=f"https://greenhouse.io/resumes/candidate_{i}.pdf",
                status=random.choice(["active", "hired", "rejected", "prospect"]),
                job_id=f"gh_job_{random.randint(1, 5)}",
                custom_fields={
                    "source": random.choice(["LinkedIn", "Indeed", "Referral"]),
                    "experience_years": random.randint(1, 10),
                    "salary_expectation": random.randint(50000, 150000)
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            )
            mock_candidates.append(candidate)
        
        return mock_candidates
    
    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[ATSJob]:
        """Get jobs from Greenhouse"""
        await asyncio.sleep(0.2)
        
        mock_jobs = []
        job_titles = ["Software Engineer", "Product Manager", "Data Scientist", "UX Designer", "DevOps Engineer"]
        
        for i, title in enumerate(job_titles):
            job = ATSJob(
                external_id=f"gh_job_{i+1}",
                title=title,
                description=f"We are looking for a talented {title} to join our team...",
                status=random.choice(["open", "closed", "draft"]),
                department=random.choice(["Engineering", "Product", "Design"]),
                location=random.choice(["San Francisco", "New York", "Remote"]),
                custom_fields={
                    "salary_min": random.randint(80000, 120000),
                    "salary_max": random.randint(120000, 200000),
                    "remote_ok": random.choice([True, False])
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
            )
            mock_jobs.append(job)
        
        return mock_jobs
    
    async def update_candidate(self, external_id: str, updates: ATSCandidateUpdate) -> bool:
        """Update candidate in Greenhouse"""
        await asyncio.sleep(0.1)
        logger.info(f"Updating Greenhouse candidate {external_id} with {updates.dict()}")
        return True
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create candidate in Greenhouse"""
        await asyncio.sleep(0.1)
        external_id = f"gh_candidate_{random.randint(1000, 9999)}"
        logger.info(f"Created Greenhouse candidate {external_id}")
        return external_id


class LeverConnector(ATSConnector):
    """Mock Lever ATS connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.base_url = credentials.get("base_url", "https://api.lever.co/v1")
        self.api_key = credentials.get("api_key")
    
    async def authenticate(self) -> bool:
        """Mock authentication"""
        await asyncio.sleep(0.1)
        if not self.api_key:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Lever"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Lever rate limits"""
        return {
            "limit": 500,
            "remaining": random.randint(200, 500),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[ATSCandidate]:
        """Get candidates from Lever"""
        await asyncio.sleep(0.2)
        
        mock_candidates = []
        for i in range(random.randint(3, 12)):
            candidate = ATSCandidate(
                external_id=f"lever_candidate_{i}",
                email=f"lever.candidate{i}@example.com",
                name=f"Jane Smith {i}",
                phone=f"+1555100{i:04d}",
                resume_url=f"https://lever.co/files/candidate_{i}.pdf",
                status=random.choice(["new", "contacted", "interviewed", "offer", "hired", "rejected"]),
                job_id=f"lever_job_{random.randint(1, 4)}",
                custom_fields={
                    "stage": random.choice(["Phone Screen", "Technical", "Final", "Offer"]),
                    "rating": random.randint(1, 5),
                    "notes": f"Candidate {i} interview notes"
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            )
            mock_candidates.append(candidate)
        
        return mock_candidates
    
    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[ATSJob]:
        """Get jobs from Lever"""
        await asyncio.sleep(0.2)
        
        mock_jobs = []
        job_titles = ["Senior Developer", "Marketing Manager", "Sales Representative", "HR Specialist"]
        
        for i, title in enumerate(job_titles):
            job = ATSJob(
                external_id=f"lever_job_{i+1}",
                title=title,
                description=f"Join our team as a {title}. We offer competitive compensation...",
                status=random.choice(["published", "internal", "closed"]),
                department=random.choice(["Engineering", "Marketing", "Sales", "HR"]),
                location=random.choice(["Austin", "Seattle", "Boston", "Remote"]),
                custom_fields={
                    "team": random.choice(["Frontend", "Backend", "Full Stack"]),
                    "level": random.choice(["Junior", "Mid", "Senior"]),
                    "equity": random.choice([True, False])
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
            )
            mock_jobs.append(job)
        
        return mock_jobs
    
    async def update_candidate(self, external_id: str, updates: ATSCandidateUpdate) -> bool:
        """Update candidate in Lever"""
        await asyncio.sleep(0.1)
        logger.info(f"Updating Lever candidate {external_id} with {updates.dict()}")
        return True
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create candidate in Lever"""
        await asyncio.sleep(0.1)
        external_id = f"lever_candidate_{random.randint(1000, 9999)}"
        logger.info(f"Created Lever candidate {external_id}")
        return external_id


class WorkdayConnector(ATSConnector):
    """Mock Workday ATS connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.base_url = credentials.get("base_url", "https://api.workday.com/v1")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
    
    async def authenticate(self) -> bool:
        """Mock authentication"""
        await asyncio.sleep(0.2)  # Workday auth is slower
        if not self.client_id or not self.client_secret:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Workday"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.2)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Workday rate limits"""
        return {
            "limit": 200,
            "remaining": random.randint(50, 200),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[ATSCandidate]:
        """Get candidates from Workday"""
        await asyncio.sleep(0.3)  # Workday is slower
        
        mock_candidates = []
        for i in range(random.randint(2, 8)):
            candidate = ATSCandidate(
                external_id=f"wd_candidate_{i}",
                email=f"workday.candidate{i}@company.com",
                name=f"Michael Johnson {i}",
                phone=f"+1555200{i:04d}",
                resume_url=f"https://workday.com/documents/candidate_{i}.pdf",
                status=random.choice(["applied", "screening", "interview", "offer_extended", "hired", "declined"]),
                job_id=f"wd_job_{random.randint(1, 3)}",
                custom_fields={
                    "requisition_id": f"REQ-{random.randint(1000, 9999)}",
                    "hiring_manager": f"Manager {random.randint(1, 5)}",
                    "priority": random.choice(["High", "Medium", "Low"])
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            )
            mock_candidates.append(candidate)
        
        return mock_candidates
    
    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[ATSJob]:
        """Get jobs from Workday"""
        await asyncio.sleep(0.3)
        
        mock_jobs = []
        job_titles = ["Business Analyst", "Project Manager", "Financial Analyst"]
        
        for i, title in enumerate(job_titles):
            job = ATSJob(
                external_id=f"wd_job_{i+1}",
                title=title,
                description=f"We are seeking a qualified {title} to support our growing business...",
                status=random.choice(["open", "filled", "cancelled"]),
                department=random.choice(["Business", "Finance", "Operations"]),
                location=random.choice(["Chicago", "Dallas", "Atlanta", "Remote"]),
                custom_fields={
                    "job_family": random.choice(["Professional", "Management", "Executive"]),
                    "travel_required": random.choice(["None", "25%", "50%"]),
                    "security_clearance": random.choice([True, False])
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 120)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 21))
            )
            mock_jobs.append(job)
        
        return mock_jobs
    
    async def update_candidate(self, external_id: str, updates: ATSCandidateUpdate) -> bool:
        """Update candidate in Workday"""
        await asyncio.sleep(0.2)
        logger.info(f"Updating Workday candidate {external_id} with {updates.dict()}")
        return True
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create candidate in Workday"""
        await asyncio.sleep(0.2)
        external_id = f"wd_candidate_{random.randint(1000, 9999)}"
        logger.info(f"Created Workday candidate {external_id}")
        return external_id


class BambooHRConnector(ATSConnector):
    """Mock BambooHR ATS connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.subdomain = credentials.get("subdomain")
        self.api_key = credentials.get("api_key")
        self.base_url = f"https://api.bamboohr.com/api/gateway.php/{self.subdomain}/v1"
    
    async def authenticate(self) -> bool:
        """Mock authentication"""
        await asyncio.sleep(0.1)
        if not self.subdomain or not self.api_key:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to BambooHR"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get BambooHR rate limits"""
        return {
            "limit": 300,
            "remaining": random.randint(100, 300),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[ATSCandidate]:
        """Get candidates from BambooHR"""
        await asyncio.sleep(0.2)
        
        mock_candidates = []
        for i in range(random.randint(4, 10)):
            candidate = ATSCandidate(
                external_id=f"bamboo_candidate_{i}",
                email=f"bamboo.candidate{i}@example.com",
                name=f"Sarah Wilson {i}",
                phone=f"+1555300{i:04d}",
                resume_url=f"https://bamboohr.com/files/candidate_{i}.pdf",
                status=random.choice(["new", "phone_screen", "in_person", "reference_check", "hired", "rejected"]),
                job_id=f"bamboo_job_{random.randint(1, 4)}",
                custom_fields={
                    "application_date": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "referral_source": random.choice(["Employee Referral", "Job Board", "Company Website"]),
                    "years_experience": random.randint(0, 15)
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                updated_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            )
            mock_candidates.append(candidate)
        
        return mock_candidates
    
    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[ATSJob]:
        """Get jobs from BambooHR"""
        await asyncio.sleep(0.2)
        
        mock_jobs = []
        job_titles = ["Customer Success Manager", "Operations Coordinator", "Content Writer", "QA Engineer"]
        
        for i, title in enumerate(job_titles):
            job = ATSJob(
                external_id=f"bamboo_job_{i+1}",
                title=title,
                description=f"Join our team as a {title}. We value work-life balance and growth...",
                status=random.choice(["active", "inactive", "draft"]),
                department=random.choice(["Customer Success", "Operations", "Marketing", "Engineering"]),
                location=random.choice(["Portland", "Denver", "Nashville", "Remote"]),
                custom_fields={
                    "employment_type": random.choice(["Full-time", "Part-time", "Contract"]),
                    "benefits": random.choice(["Full Benefits", "Partial Benefits", "None"]),
                    "start_date": (datetime.utcnow() + timedelta(days=random.randint(7, 60))).isoformat()
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
            )
            mock_jobs.append(job)
        
        return mock_jobs
    
    async def update_candidate(self, external_id: str, updates: ATSCandidateUpdate) -> bool:
        """Update candidate in BambooHR"""
        await asyncio.sleep(0.1)
        logger.info(f"Updating BambooHR candidate {external_id} with {updates.dict()}")
        return True
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create candidate in BambooHR"""
        await asyncio.sleep(0.1)
        external_id = f"bamboo_candidate_{random.randint(1000, 9999)}"
        logger.info(f"Created BambooHR candidate {external_id}")
        return external_id