"""
Candidate management service
"""

import json
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import pandas as pd
import io
import csv

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, Text
from sqlalchemy.sql import text
from fastapi import HTTPException, status, UploadFile
import httpx

from app.models.job import Candidate, Application, Job
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateSearch,
    CandidateResponse, CandidateListResponse, CandidateSearchResponse,
    CandidateSearchResult, BulkImportResult, ResumeParseResult,
    ParsedResumeData, ExtractedSkill, WorkExperience, Education,
    Certification, Language, ApplicationCreate, ApplicationResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CandidateService:
    """Service for candidate management operations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_candidate(
        self, 
        candidate_data: CandidateCreate,
        resume_file: Optional[UploadFile] = None
    ) -> CandidateResponse:
        """Create a new candidate with optional resume parsing"""
        
        # Check if candidate already exists
        existing_candidate = self.db.query(Candidate).filter(
            Candidate.email == candidate_data.email
        ).first()
        
        if existing_candidate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidate with this email already exists"
            )

        # Parse resume if provided
        parsed_data = ParsedResumeData()
        resume_url = None
        
        if resume_file:
            try:
                # Upload resume to storage
                resume_url = await self._upload_resume(resume_file)
                
                # Parse resume content
                resume_content = await resume_file.read()
                await resume_file.seek(0)  # Reset file pointer
                
                parse_result = await self._parse_resume(resume_content, resume_file.filename)
                if parse_result.success and parse_result.parsed_data:
                    parsed_data = parse_result.parsed_data
                    
            except Exception as e:
                logger.error(f"Error processing resume: {e}")
                # Continue without parsed data if resume processing fails

        # Create candidate
        candidate = Candidate(
            email=candidate_data.email,
            name=candidate_data.name,
            phone=candidate_data.phone,
            resume_url=resume_url,
            parsed_data=parsed_data.dict()
        )

        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)

        return self._to_candidate_response(candidate)

    async def get_candidate(self, candidate_id: UUID) -> CandidateResponse:
        """Get candidate by ID"""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        return self._to_candidate_response(candidate)

    async def update_candidate(
        self, 
        candidate_id: UUID, 
        candidate_data: CandidateUpdate
    ) -> CandidateResponse:
        """Update candidate information"""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )

        # Update fields
        update_data = candidate_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(candidate, field, value)

        candidate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)

        return self._to_candidate_response(candidate)

    async def delete_candidate(self, candidate_id: UUID) -> bool:
        """Delete candidate"""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )

        self.db.delete(candidate)
        self.db.commit()
        return True

    async def list_candidates(
        self, 
        page: int = 1, 
        page_size: int = 20
    ) -> CandidateListResponse:
        """List candidates with pagination"""
        offset = (page - 1) * page_size
        
        query = self.db.query(Candidate)
        total = query.count()
        
        candidates = query.offset(offset).limit(page_size).all()
        
        candidate_responses = [self._to_candidate_response(c) for c in candidates]
        
        return CandidateListResponse(
            candidates=candidate_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def search_candidates(
        self, 
        search_params: CandidateSearch,
        job_id: Optional[UUID] = None
    ) -> CandidateSearchResponse:
        """Search candidates with vector similarity and keyword matching"""
        
        query = self.db.query(Candidate)
        
        # Basic filters
        if search_params.experience_min is not None:
            query = query.filter(
                func.coalesce(
                    func.cast(Candidate.parsed_data['total_experience_years'], float), 0
                ) >= search_params.experience_min
            )
        
        if search_params.experience_max is not None:
            query = query.filter(
                func.coalesce(
                    func.cast(Candidate.parsed_data['total_experience_years'], float), 0
                ) <= search_params.experience_max
            )

        # Text search in name, email, and parsed data
        if search_params.query:
            search_term = f"%{search_params.query.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Candidate.name).like(search_term),
                    func.lower(Candidate.email).like(search_term),
                    func.cast(Candidate.parsed_data, Text).ilike(search_term)
                )
            )

        # Skills filter
        if search_params.skills:
            for skill in search_params.skills:
                query = query.filter(
                    func.cast(Candidate.parsed_data['skills'], Text).ilike(f'%{skill}%')
                )

        # Location filter
        if search_params.location:
            query = query.filter(
                func.cast(Candidate.parsed_data['contact_info'], Text).ilike(f'%{search_params.location}%')
            )

        # Education level filter
        if search_params.education_level:
            query = query.filter(
                func.cast(Candidate.parsed_data['education'], Text).ilike(f'%{search_params.education_level}%')
            )

        # Pagination
        total = query.count()
        offset = (search_params.page - 1) * search_params.page_size
        candidates = query.offset(offset).limit(search_params.page_size).all()

        # Convert to search results with similarity scoring
        search_results = []
        for candidate in candidates:
            similarity_score = await self._calculate_similarity_score(
                candidate, search_params, job_id
            )
            
            matching_skills, matching_keywords = self._find_matches(
                candidate, search_params
            )
            
            result = CandidateSearchResult(
                **self._to_candidate_response(candidate).dict(),
                similarity_score=similarity_score,
                matching_skills=matching_skills,
                matching_keywords=matching_keywords
            )
            search_results.append(result)

        # Sort by similarity score if available
        search_results.sort(key=lambda x: x.similarity_score or 0, reverse=True)

        return CandidateSearchResponse(
            candidates=search_results,
            total=total,
            page=search_params.page,
            page_size=search_params.page_size,
            total_pages=(total + search_params.page_size - 1) // search_params.page_size,
            search_query=search_params.query
        )

    async def bulk_import_candidates(
        self, 
        file_data: bytes, 
        filename: str, 
        file_type: str
    ) -> BulkImportResult:
        """Bulk import candidates from CSV, Excel, or JSON file"""
        
        result = BulkImportResult(
            total_processed=0,
            successful_imports=0,
            failed_imports=0,
            errors=[],
            imported_candidate_ids=[]
        )

        try:
            # Parse file based on type
            if file_type == "csv":
                candidates_data = self._parse_csv_file(file_data)
            elif file_type == "xlsx":
                candidates_data = self._parse_excel_file(file_data)
            elif file_type == "json":
                candidates_data = self._parse_json_file(file_data)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            result.total_processed = len(candidates_data)

            # Process each candidate
            for i, candidate_data in enumerate(candidates_data):
                try:
                    # Validate required fields
                    if not candidate_data.get('email') or not candidate_data.get('name'):
                        raise ValueError("Missing required fields: email and name")

                    # Check if candidate already exists
                    existing = self.db.query(Candidate).filter(
                        Candidate.email == candidate_data['email']
                    ).first()
                    
                    if existing:
                        result.errors.append({
                            'row': i + 1,
                            'email': candidate_data['email'],
                            'error': 'Candidate already exists'
                        })
                        result.failed_imports += 1
                        continue

                    # Create candidate
                    candidate = Candidate(
                        email=candidate_data['email'],
                        name=candidate_data['name'],
                        phone=candidate_data.get('phone'),
                        parsed_data=candidate_data.get('parsed_data', {})
                    )

                    self.db.add(candidate)
                    self.db.flush()  # Get ID without committing
                    
                    result.imported_candidate_ids.append(candidate.id)
                    result.successful_imports += 1

                except Exception as e:
                    result.errors.append({
                        'row': i + 1,
                        'email': candidate_data.get('email', 'Unknown'),
                        'error': str(e)
                    })
                    result.failed_imports += 1

            # Commit all successful imports
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk import failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk import failed: {str(e)}"
            )

        return result

    async def create_application(
        self, 
        application_data: ApplicationCreate
    ) -> ApplicationResponse:
        """Create a job application"""
        
        # Verify candidate exists
        candidate = self.db.query(Candidate).filter(
            Candidate.id == application_data.candidate_id
        ).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )

        # Verify job exists
        job = self.db.query(Job).filter(Job.id == application_data.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Check if application already exists
        existing_application = self.db.query(Application).filter(
            and_(
                Application.job_id == application_data.job_id,
                Application.candidate_id == application_data.candidate_id
            )
        ).first()
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists for this job and candidate"
            )

        # Create application
        application = Application(
            job_id=application_data.job_id,
            candidate_id=application_data.candidate_id,
            cover_letter=application_data.cover_letter,
            application_data=application_data.application_data
        )

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)

        return ApplicationResponse(
            id=application.id,
            job_id=application.job_id,
            candidate_id=application.candidate_id,
            status=application.status,
            cover_letter=application.cover_letter,
            application_data=application.application_data,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    # Private helper methods

    async def _parse_resume(self, file_content: bytes, filename: str) -> ResumeParseResult:
        """Parse resume using Groq API"""
        
        if not settings.GROQ_API_KEY:
            logger.warning("Groq API key not configured, skipping resume parsing")
            return ResumeParseResult(success=False, error="AI service not configured")

        try:
            # Convert file content to text (simplified - in production, use proper PDF/DOCX parsing)
            text_content = self._extract_text_from_file(file_content, filename)
            
            # Use Groq API to parse resume
            parsed_data = await self._call_groq_for_resume_parsing(text_content)
            
            return ResumeParseResult(
                success=True,
                parsed_data=parsed_data,
                confidence_score=0.8  # Mock confidence score
            )
            
        except Exception as e:
            logger.error(f"Resume parsing failed: {e}")
            return ResumeParseResult(
                success=False,
                error=str(e)
            )

    def _extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text from file (simplified implementation)"""
        try:
            # For now, assume text files. In production, use libraries like PyPDF2, python-docx
            return file_content.decode('utf-8', errors='ignore')
        except Exception:
            # Fallback for binary files
            return str(file_content)

    async def _call_groq_for_resume_parsing(self, text_content: str) -> ParsedResumeData:
        """Call Groq API to parse resume content"""
        
        prompt = f"""
        Parse the following resume and extract structured information. Return a JSON object with the following structure:
        {{
            "skills": [
                {{"name": "skill_name", "confidence": 0.9, "category": "technical"}}
            ],
            "experience": [
                {{
                    "company": "Company Name",
                    "position": "Job Title",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM",
                    "duration_months": 24,
                    "description": "Job description",
                    "skills_used": ["skill1", "skill2"]
                }}
            ],
            "education": [
                {{
                    "institution": "University Name",
                    "degree": "Bachelor's",
                    "field_of_study": "Computer Science",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM",
                    "gpa": 3.8
                }}
            ],
            "certifications": [
                {{
                    "name": "Certification Name",
                    "issuer": "Issuing Organization",
                    "issue_date": "YYYY-MM",
                    "expiry_date": "YYYY-MM"
                }}
            ],
            "languages": [
                {{"language": "English", "proficiency": "native"}}
            ],
            "total_experience_years": 5.5,
            "summary": "Professional summary",
            "contact_info": {{
                "email": "email@example.com",
                "phone": "+1234567890",
                "location": "City, State"
            }}
        }}

        Resume content:
        {text_content}
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama3-70b-8192",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed_json = json.loads(json_match.group())
                        return ParsedResumeData(**parsed_json)
                    
                raise Exception("Failed to parse JSON from Groq response")
                
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            # Return basic parsed data as fallback
            return self._basic_text_parsing(text_content)

    def _basic_text_parsing(self, text_content: str) -> ParsedResumeData:
        """Basic text parsing as fallback when AI parsing fails"""
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        
        # Extract phone numbers
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phones = re.findall(phone_pattern, text_content)
        
        # Extract common skills (basic keyword matching)
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'html', 'css', 'typescript', 'mongodb'
        ]
        
        found_skills = []
        text_lower = text_content.lower()
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(ExtractedSkill(
                    name=skill.title(),
                    confidence=0.7,
                    category="technical"
                ))

        return ParsedResumeData(
            skills=found_skills,
            contact_info={
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None
            },
            summary=text_content[:200] + "..." if len(text_content) > 200 else text_content
        )

    async def _upload_resume(self, file: UploadFile) -> str:
        """Upload resume to Vercel Blob storage"""
        # Mock implementation - in production, integrate with Vercel Blob
        # For now, return a mock URL
        return f"https://blob.vercel-storage.com/resumes/{file.filename}"

    async def _calculate_similarity_score(
        self, 
        candidate: Candidate, 
        search_params: CandidateSearch,
        job_id: Optional[UUID] = None
    ) -> Optional[float]:
        """Calculate similarity score between candidate and search criteria"""
        
        score = 0.0
        factors = 0
        
        # Query match score
        if search_params.query:
            query_lower = search_params.query.lower()
            candidate_text = f"{candidate.name} {candidate.email} {json.dumps(candidate.parsed_data)}".lower()
            
            # Simple text similarity (in production, use proper vector similarity)
            query_words = set(query_lower.split())
            candidate_words = set(candidate_text.split())
            
            if query_words:
                intersection = len(query_words.intersection(candidate_words))
                union = len(query_words.union(candidate_words))
                score += intersection / union if union > 0 else 0
                factors += 1

        # Skills match score
        if search_params.skills:
            candidate_skills = [
                skill.get('name', '').lower() 
                for skill in candidate.parsed_data.get('skills', [])
            ]
            
            matched_skills = 0
            for skill in search_params.skills:
                if any(skill.lower() in cs for cs in candidate_skills):
                    matched_skills += 1
            
            if search_params.skills:
                score += matched_skills / len(search_params.skills)
                factors += 1

        # Experience match score
        candidate_exp = candidate.parsed_data.get('total_experience_years', 0)
        if isinstance(candidate_exp, (int, float)) and candidate_exp > 0:
            if search_params.experience_min is not None or search_params.experience_max is not None:
                exp_min = search_params.experience_min or 0
                exp_max = search_params.experience_max or 50
                
                if exp_min <= candidate_exp <= exp_max:
                    score += 1.0
                else:
                    # Partial score based on how close the experience is
                    if candidate_exp < exp_min:
                        score += max(0, 1 - (exp_min - candidate_exp) / exp_min)
                    else:
                        score += max(0, 1 - (candidate_exp - exp_max) / exp_max)
                
                factors += 1

        return score / factors if factors > 0 else None

    def _find_matches(
        self, 
        candidate: Candidate, 
        search_params: CandidateSearch
    ) -> Tuple[List[str], List[str]]:
        """Find matching skills and keywords"""
        
        matching_skills = []
        matching_keywords = []
        
        candidate_skills = [
            skill.get('name', '') 
            for skill in candidate.parsed_data.get('skills', [])
        ]
        
        # Find matching skills
        if search_params.skills:
            for skill in search_params.skills:
                for candidate_skill in candidate_skills:
                    if skill.lower() in candidate_skill.lower():
                        matching_skills.append(candidate_skill)
                        break

        # Find matching keywords from query
        if search_params.query:
            query_words = search_params.query.lower().split()
            candidate_text = f"{candidate.name} {json.dumps(candidate.parsed_data)}".lower()
            
            for word in query_words:
                if len(word) > 2 and word in candidate_text:
                    matching_keywords.append(word)

        return matching_skills, matching_keywords

    def _parse_csv_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse CSV file for bulk import"""
        try:
            content = file_data.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {e}")

    def _parse_excel_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file for bulk import"""
        try:
            df = pd.read_excel(io.BytesIO(file_data))
            return df.to_dict('records')
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {e}")

    def _parse_json_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse JSON file for bulk import"""
        try:
            content = file_data.decode('utf-8')
            data = json.loads(content)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError("JSON must contain an array or object")
                
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {e}")

    def _to_candidate_response(self, candidate: Candidate) -> CandidateResponse:
        """Convert Candidate model to response schema"""
        return CandidateResponse(
            id=candidate.id,
            email=candidate.email,
            name=candidate.name,
            phone=candidate.phone,
            resume_url=candidate.resume_url,
            parsed_data=ParsedResumeData(**candidate.parsed_data) if candidate.parsed_data else ParsedResumeData(),
            created_at=candidate.created_at,
            updated_at=candidate.updated_at
        )