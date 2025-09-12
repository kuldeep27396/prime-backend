"""
Job management service
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, Text, case
from sqlalchemy.sql import text
from fastapi import HTTPException, status
import httpx

from app.models.job import Job, Application, Candidate
from app.models.company import Company, User
from app.schemas.job import (
    JobCreate, JobUpdate, JobSearch, JobFilters, JobResponse, JobListResponse,
    JobSearchResponse, JobSearchResult, JobAnalytics, JobAnalyticsResponse,
    JobApplicationStats, JobPerformanceMetrics, CandidateQualityMetrics,
    JobBulkUpdate, JobBulkUpdateResult, JobStatusChange, JobStatusChangeResult,
    JobRequirementsParseRequest, JobRequirementsParseResult, JobRequirements,
    JobStatus, ExperienceLevel, LocationType, SalaryRange, LocationRequirement,
    SkillRequirement
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobService:
    """Service for job management operations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_job(
        self, 
        job_data: JobCreate, 
        created_by_user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> JobResponse:
        """Create a new job posting"""
        
        # Use company_id from job_data or get from user
        if not company_id and not job_data.company_id:
            user = self.db.query(User).filter(User.id == created_by_user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            company_id = user.company_id
        else:
            company_id = job_data.company_id or company_id

        # Verify company exists
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        # Create job
        job = Job(
            company_id=company_id,
            title=job_data.title,
            description=job_data.description,
            requirements=job_data.requirements.dict() if job_data.requirements else {},
            status=job_data.status.value,
            created_by=created_by_user_id
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return await self._to_job_response(job)

    async def get_job(self, job_id: UUID, company_id: Optional[UUID] = None) -> JobResponse:
        """Get job by ID"""
        query = self.db.query(Job).filter(Job.id == job_id)
        
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        job = query.first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return await self._to_job_response(job)

    async def update_job(
        self, 
        job_id: UUID, 
        job_data: JobUpdate,
        updated_by_user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> JobResponse:
        """Update job information"""
        query = self.db.query(Job).filter(Job.id == job_id)
        
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        job = query.first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Update fields
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "requirements" and value:
                setattr(job, field, value.dict() if hasattr(value, 'dict') else value)
            elif field == "status" and value:
                setattr(job, field, value.value if hasattr(value, 'value') else value)
            else:
                setattr(job, field, value)

        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)

        return await self._to_job_response(job)

    async def delete_job(
        self, 
        job_id: UUID, 
        company_id: Optional[UUID] = None
    ) -> bool:
        """Delete job (soft delete by setting status to closed)"""
        query = self.db.query(Job).filter(Job.id == job_id)
        
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        job = query.first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Soft delete by setting status to closed
        job.status = JobStatus.CLOSED.value
        job.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True

    async def list_jobs(
        self, 
        page: int = 1, 
        page_size: int = 20,
        company_id: Optional[UUID] = None,
        filters: Optional[JobFilters] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> JobListResponse:
        """List jobs with pagination and filtering"""
        
        query = self.db.query(Job)
        
        # Apply company filter
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        # Apply filters
        if filters:
            query = self._apply_job_filters(query, filters)
        
        # Apply sorting
        sort_column = getattr(Job, sort_by, Job.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        jobs = query.offset(offset).limit(page_size).all()
        
        # Convert to response objects
        job_responses = []
        for job in jobs:
            job_response = await self._to_job_response(job)
            job_responses.append(job_response)
        
        return JobListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def search_jobs(
        self, 
        search_params: JobSearch,
        company_id: Optional[UUID] = None
    ) -> JobSearchResponse:
        """Search jobs with advanced filtering and relevance scoring"""
        
        query = self.db.query(Job)
        
        # Apply company filter
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        # Apply search filters
        filters_applied = {}
        
        # Status filter
        if search_params.status:
            query = query.filter(Job.status == search_params.status.value)
            filters_applied["status"] = search_params.status.value
        
        # Company filter
        if search_params.company_id:
            query = query.filter(Job.company_id == search_params.company_id)
            filters_applied["company_id"] = str(search_params.company_id)
        
        # Created by filter
        if search_params.created_by:
            query = query.filter(Job.created_by == search_params.created_by)
            filters_applied["created_by"] = str(search_params.created_by)
        
        # Date range filter
        if search_params.date_from:
            query = query.filter(Job.created_at >= search_params.date_from)
            filters_applied["date_from"] = search_params.date_from.isoformat()
        
        if search_params.date_to:
            query = query.filter(Job.created_at <= search_params.date_to)
            filters_applied["date_to"] = search_params.date_to.isoformat()
        
        # Text search in title and description
        if search_params.query:
            search_term = f"%{search_params.query.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Job.title).like(search_term),
                    func.lower(Job.description).like(search_term),
                    func.cast(Job.requirements, Text).ilike(search_term)
                )
            )
            filters_applied["query"] = search_params.query
        
        # Skills filter
        if search_params.skills:
            for skill in search_params.skills:
                query = query.filter(
                    func.cast(Job.requirements, Text).ilike(f'%{skill}%')
                )
            filters_applied["skills"] = search_params.skills
        
        # Experience level filter
        if search_params.experience_level:
            query = query.filter(
                func.cast(Job.requirements, Text).ilike(f'%{search_params.experience_level.value}%')
            )
            filters_applied["experience_level"] = search_params.experience_level.value
        
        # Location type filter
        if search_params.location_type:
            query = query.filter(
                func.cast(Job.requirements, Text).ilike(f'%{search_params.location_type.value}%')
            )
            filters_applied["location_type"] = search_params.location_type.value
        
        # Location city filter
        if search_params.location_city:
            query = query.filter(
                func.cast(Job.requirements, Text).ilike(f'%{search_params.location_city}%')
            )
            filters_applied["location_city"] = search_params.location_city
        
        # Salary filters
        if search_params.min_salary:
            query = query.filter(
                func.cast(
                    func.json_extract_path_text(Job.requirements, 'salary', 'min_salary'), 
                    func.INTEGER
                ) >= search_params.min_salary
            )
            filters_applied["min_salary"] = search_params.min_salary
        
        if search_params.max_salary:
            query = query.filter(
                func.cast(
                    func.json_extract_path_text(Job.requirements, 'salary', 'max_salary'), 
                    func.INTEGER
                ) <= search_params.max_salary
            )
            filters_applied["max_salary"] = search_params.max_salary
        
        # Apply sorting
        sort_column = getattr(Job, search_params.sort_by, Job.created_at)
        if search_params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        jobs = query.offset(offset).limit(search_params.page_size).all()
        
        # Convert to search results with relevance scoring
        search_results = []
        for job in jobs:
            relevance_score = await self._calculate_job_relevance_score(job, search_params)
            matching_skills, matching_keywords = self._find_job_matches(job, search_params)
            
            job_response = await self._to_job_response(job)
            result = JobSearchResult(
                **job_response.dict(),
                relevance_score=relevance_score,
                matching_skills=matching_skills,
                matching_keywords=matching_keywords
            )
            search_results.append(result)
        
        # Sort by relevance score if available
        if search_params.query or search_params.skills:
            search_results.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        return JobSearchResponse(
            jobs=search_results,
            total=total,
            page=search_params.page,
            page_size=search_params.page_size,
            total_pages=(total + search_params.page_size - 1) // search_params.page_size,
            search_query=search_params.query,
            filters_applied=filters_applied
        )

    async def change_job_status(
        self, 
        job_id: UUID, 
        status_change: JobStatusChange,
        changed_by_user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> JobStatusChangeResult:
        """Change job status with audit trail"""
        
        query = self.db.query(Job).filter(Job.id == job_id)
        
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        job = query.first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        old_status = JobStatus(job.status)
        new_status = status_change.status
        
        # Validate status transition
        if not self._is_valid_status_transition(old_status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {old_status.value} to {new_status.value}"
            )
        
        # Update job status
        job.status = new_status.value
        job.updated_at = datetime.utcnow()
        self.db.commit()
        
        return JobStatusChangeResult(
            job_id=job_id,
            old_status=old_status,
            new_status=new_status,
            changed_at=job.updated_at,
            changed_by=changed_by_user_id,
            reason=status_change.reason
        )

    async def get_job_analytics(
        self, 
        job_id: UUID,
        company_id: Optional[UUID] = None
    ) -> JobAnalyticsResponse:
        """Get comprehensive job analytics"""
        
        query = self.db.query(Job).filter(Job.id == job_id)
        
        if company_id:
            query = query.filter(Job.company_id == company_id)
        
        job = query.first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get application statistics
        application_stats = await self._get_application_stats(job_id)
        
        # Get performance metrics
        performance_metrics = await self._get_performance_metrics(job_id)
        
        # Get candidate quality metrics
        candidate_quality = await self._get_candidate_quality_metrics(job_id)
        
        analytics = JobAnalytics(
            job_id=job_id,
            application_stats=application_stats,
            performance_metrics=performance_metrics,
            candidate_quality=candidate_quality,
            generated_at=datetime.utcnow()
        )
        
        # Generate recommendations and insights
        recommendations = self._generate_recommendations(analytics)
        insights = self._generate_insights(analytics)
        
        return JobAnalyticsResponse(
            analytics=analytics,
            recommendations=recommendations,
            insights=insights
        )

    async def bulk_update_jobs(
        self, 
        bulk_update: JobBulkUpdate,
        updated_by_user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> JobBulkUpdateResult:
        """Bulk update multiple jobs"""
        
        result = JobBulkUpdateResult(
            total_processed=len(bulk_update.job_ids),
            successful_updates=0,
            failed_updates=0,
            errors=[],
            updated_job_ids=[]
        )
        
        for job_id in bulk_update.job_ids:
            try:
                await self.update_job(
                    job_id=job_id,
                    job_data=bulk_update.updates,
                    updated_by_user_id=updated_by_user_id,
                    company_id=company_id
                )
                result.updated_job_ids.append(job_id)
                result.successful_updates += 1
                
            except Exception as e:
                result.errors.append({
                    'job_id': str(job_id),
                    'error': str(e)
                })
                result.failed_updates += 1
        
        return result

    async def parse_job_requirements(
        self, 
        parse_request: JobRequirementsParseRequest
    ) -> JobRequirementsParseResult:
        """Parse job requirements from job description using AI"""
        
        if not settings.GROQ_API_KEY:
            logger.warning("Groq API key not configured, using basic parsing")
            return await self._basic_requirements_parsing(parse_request)
        
        try:
            parsed_requirements = await self._call_groq_for_requirements_parsing(
                parse_request.job_description,
                parse_request.job_title
            )
            
            return JobRequirementsParseResult(
                success=True,
                parsed_requirements=parsed_requirements,
                confidence_score=0.8,
                extracted_skills=self._extract_skills_from_requirements(parsed_requirements),
                suggested_improvements=self._suggest_improvements(parse_request.job_description)
            )
            
        except Exception as e:
            logger.error(f"AI requirements parsing failed: {e}")
            return await self._basic_requirements_parsing(parse_request)

    # Private helper methods

    def _apply_job_filters(self, query, filters: JobFilters):
        """Apply job filters to query"""
        
        if filters.status:
            query = query.filter(Job.status.in_([s.value for s in filters.status]))
        
        if filters.company_id:
            query = query.filter(Job.company_id == filters.company_id)
        
        if filters.created_by:
            query = query.filter(Job.created_by == filters.created_by)
        
        if filters.skills:
            for skill in filters.skills:
                query = query.filter(
                    func.cast(Job.requirements, Text).ilike(f'%{skill}%')
                )
        
        if filters.experience_levels:
            exp_conditions = []
            for level in filters.experience_levels:
                exp_conditions.append(
                    func.cast(Job.requirements, Text).ilike(f'%{level.value}%')
                )
            query = query.filter(or_(*exp_conditions))
        
        if filters.location_types:
            loc_conditions = []
            for loc_type in filters.location_types:
                loc_conditions.append(
                    func.cast(Job.requirements, Text).ilike(f'%{loc_type.value}%')
                )
            query = query.filter(or_(*loc_conditions))
        
        if filters.salary_min:
            query = query.filter(
                func.cast(
                    func.json_extract_path_text(Job.requirements, 'salary', 'min_salary'), 
                    func.INTEGER
                ) >= filters.salary_min
            )
        
        if filters.salary_max:
            query = query.filter(
                func.cast(
                    func.json_extract_path_text(Job.requirements, 'salary', 'max_salary'), 
                    func.INTEGER
                ) <= filters.salary_max
            )
        
        if filters.date_from:
            query = query.filter(Job.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Job.created_at <= filters.date_to)
        
        return query

    async def _to_job_response(self, job: Job) -> JobResponse:
        """Convert Job model to response schema"""
        
        # Get application counts
        application_count = self.db.query(Application).filter(
            Application.job_id == job.id
        ).count()
        
        active_application_count = self.db.query(Application).filter(
            and_(
                Application.job_id == job.id,
                Application.status.in_(['applied', 'screening', 'interviewing', 'assessed'])
            )
        ).count()
        
        return JobResponse(
            id=job.id,
            company_id=job.company_id,
            title=job.title,
            description=job.description,
            requirements=JobRequirements(**job.requirements) if job.requirements else JobRequirements(),
            status=JobStatus(job.status),
            created_by=job.created_by,
            created_at=job.created_at,
            updated_at=job.updated_at,
            application_count=application_count,
            active_application_count=active_application_count
        )

    async def _calculate_job_relevance_score(
        self, 
        job: Job, 
        search_params: JobSearch
    ) -> Optional[float]:
        """Calculate relevance score for job search results"""
        
        score = 0.0
        factors = 0
        
        # Query match score
        if search_params.query:
            query_lower = search_params.query.lower()
            job_text = f"{job.title} {job.description or ''} {json.dumps(job.requirements)}".lower()
            
            query_words = set(query_lower.split())
            job_words = set(job_text.split())
            
            if query_words:
                intersection = len(query_words.intersection(job_words))
                union = len(query_words.union(job_words))
                score += intersection / union if union > 0 else 0
                factors += 1
        
        # Skills match score
        if search_params.skills:
            job_skills = []
            if job.requirements and 'skills' in job.requirements:
                job_skills = [
                    skill.get('name', '').lower() 
                    for skill in job.requirements.get('skills', [])
                ]
            
            matched_skills = 0
            for skill in search_params.skills:
                if any(skill.lower() in js for js in job_skills):
                    matched_skills += 1
            
            if search_params.skills:
                score += matched_skills / len(search_params.skills)
                factors += 1
        
        # Recency score (newer jobs get higher score)
        if job.created_at:
            days_old = (datetime.utcnow() - job.created_at).days
            recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
            score += recency_score
            factors += 1
        
        return score / factors if factors > 0 else None

    def _find_job_matches(
        self, 
        job: Job, 
        search_params: JobSearch
    ) -> Tuple[List[str], List[str]]:
        """Find matching skills and keywords for job search"""
        
        matching_skills = []
        matching_keywords = []
        
        # Find matching skills
        if search_params.skills and job.requirements:
            job_skills = []
            if 'skills' in job.requirements:
                job_skills = [
                    skill.get('name', '') 
                    for skill in job.requirements.get('skills', [])
                ]
            
            for skill in search_params.skills:
                for job_skill in job_skills:
                    if skill.lower() in job_skill.lower():
                        matching_skills.append(job_skill)
                        break
        
        # Find matching keywords from query
        if search_params.query:
            query_words = search_params.query.lower().split()
            job_text = f"{job.title} {job.description or ''}".lower()
            
            for word in query_words:
                if len(word) > 2 and word in job_text:
                    matching_keywords.append(word)
        
        return matching_skills, matching_keywords

    def _is_valid_status_transition(self, old_status: JobStatus, new_status: JobStatus) -> bool:
        """Validate job status transitions"""
        
        valid_transitions = {
            JobStatus.DRAFT: [JobStatus.ACTIVE, JobStatus.CLOSED],
            JobStatus.ACTIVE: [JobStatus.PAUSED, JobStatus.CLOSED],
            JobStatus.PAUSED: [JobStatus.ACTIVE, JobStatus.CLOSED],
            JobStatus.CLOSED: []  # Closed jobs cannot be reopened
        }
        
        return new_status in valid_transitions.get(old_status, [])

    async def _get_application_stats(self, job_id: UUID) -> JobApplicationStats:
        """Get application statistics for a job"""
        
        # Total applications
        total_applications = self.db.query(Application).filter(
            Application.job_id == job_id
        ).count()
        
        # Applications by status
        status_counts = self.db.query(
            Application.status,
            func.count(Application.id)
        ).filter(
            Application.job_id == job_id
        ).group_by(Application.status).all()
        
        applications_by_status = {status: count for status, count in status_counts}
        
        # Applications by date (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_applications = self.db.query(
            func.date(Application.created_at).label('date'),
            func.count(Application.id).label('count')
        ).filter(
            and_(
                Application.job_id == job_id,
                Application.created_at >= thirty_days_ago
            )
        ).group_by(func.date(Application.created_at)).all()
        
        applications_by_date = [
            {'date': date.isoformat(), 'count': count}
            for date, count in daily_applications
        ]
        
        # Average applications per day
        avg_applications_per_day = total_applications / 30 if total_applications > 0 else 0
        
        # Conversion rates (simplified)
        conversion_rates = {}
        if total_applications > 0:
            for status, count in applications_by_status.items():
                conversion_rates[status] = (count / total_applications) * 100
        
        return JobApplicationStats(
            total_applications=total_applications,
            applications_by_status=applications_by_status,
            applications_by_date=applications_by_date,
            avg_applications_per_day=avg_applications_per_day,
            conversion_rates=conversion_rates
        )

    async def _get_performance_metrics(self, job_id: UUID) -> JobPerformanceMetrics:
        """Get performance metrics for a job"""
        
        # Get application count
        applications = self.db.query(Application).filter(
            Application.job_id == job_id
        ).count()
        
        # Mock metrics (in production, integrate with analytics service)
        return JobPerformanceMetrics(
            views=applications * 10,  # Mock: assume 10 views per application
            applications=applications,
            application_rate=0.1 if applications > 0 else 0,  # Mock: 10% conversion
            time_to_fill=None,  # Would calculate based on hire date
            quality_score=7.5,  # Mock quality score
            source_breakdown={
                'direct': applications // 2,
                'referral': applications // 3,
                'job_board': applications - (applications // 2) - (applications // 3)
            }
        )

    async def _get_candidate_quality_metrics(self, job_id: UUID) -> CandidateQualityMetrics:
        """Get candidate quality metrics for a job"""
        
        # Get candidates who applied to this job
        candidates_query = self.db.query(Candidate).join(Application).filter(
            Application.job_id == job_id
        )
        
        total_candidates = candidates_query.count()
        
        if total_candidates == 0:
            return CandidateQualityMetrics()
        
        candidates = candidates_query.all()
        
        # Calculate metrics
        qualified_candidates = 0
        total_experience = 0
        experience_count = 0
        skill_counts = defaultdict(int)
        education_counts = defaultdict(int)
        
        for candidate in candidates:
            parsed_data = candidate.parsed_data or {}
            
            # Count as qualified if has relevant skills or experience
            if parsed_data.get('skills') or parsed_data.get('experience'):
                qualified_candidates += 1
            
            # Experience metrics
            exp_years = parsed_data.get('total_experience_years')
            if exp_years and isinstance(exp_years, (int, float)):
                total_experience += exp_years
                experience_count += 1
            
            # Skill distribution
            for skill in parsed_data.get('skills', []):
                skill_name = skill.get('name', '').lower()
                if skill_name:
                    skill_counts[skill_name] += 1
            
            # Education distribution
            for education in parsed_data.get('education', []):
                degree = education.get('degree', '').lower()
                if degree:
                    education_counts[degree] += 1
        
        return CandidateQualityMetrics(
            total_candidates=total_candidates,
            qualified_candidates=qualified_candidates,
            qualification_rate=(qualified_candidates / total_candidates) * 100,
            avg_experience_years=total_experience / experience_count if experience_count > 0 else None,
            skill_match_distribution=dict(skill_counts),
            education_distribution=dict(education_counts)
        )

    def _generate_recommendations(self, analytics: JobAnalytics) -> List[str]:
        """Generate recommendations based on job analytics"""
        
        recommendations = []
        
        # Application rate recommendations
        if analytics.performance_metrics.application_rate < 0.05:
            recommendations.append(
                "Consider improving job title and description to attract more candidates"
            )
        
        # Qualification rate recommendations
        if analytics.candidate_quality.qualification_rate < 50:
            recommendations.append(
                "Review job requirements - they might be too strict or unclear"
            )
        
        # Skills recommendations
        if len(analytics.candidate_quality.skill_match_distribution) < 3:
            recommendations.append(
                "Consider adding more specific skill requirements to attract qualified candidates"
            )
        
        return recommendations

    def _generate_insights(self, analytics: JobAnalytics) -> List[str]:
        """Generate insights based on job analytics"""
        
        insights = []
        
        # Application trends
        if analytics.application_stats.total_applications > 0:
            insights.append(
                f"Received {analytics.application_stats.total_applications} applications with "
                f"{analytics.application_stats.avg_applications_per_day:.1f} applications per day on average"
            )
        
        # Candidate quality
        if analytics.candidate_quality.avg_experience_years:
            insights.append(
                f"Candidates have an average of {analytics.candidate_quality.avg_experience_years:.1f} "
                f"years of experience"
            )
        
        # Top skills
        if analytics.candidate_quality.skill_match_distribution:
            top_skill = max(
                analytics.candidate_quality.skill_match_distribution.items(),
                key=lambda x: x[1]
            )
            insights.append(f"Most common skill among applicants: {top_skill[0]} ({top_skill[1]} candidates)")
        
        return insights

    async def _call_groq_for_requirements_parsing(
        self, 
        job_description: str, 
        job_title: Optional[str] = None
    ) -> JobRequirements:
        """Call Groq API to parse job requirements"""
        
        prompt = f"""
        Parse the following job description and extract structured requirements. Return a JSON object with this structure:
        {{
            "skills": [
                {{"name": "Python", "required": true, "experience_years": 3, "proficiency_level": "advanced"}}
            ],
            "experience_level": "mid",
            "min_experience_years": 3,
            "education_level": "bachelor",
            "location": {{
                "type": "remote",
                "city": null,
                "state": null,
                "country": null,
                "timezone": null,
                "travel_required": false
            }},
            "salary": {{
                "min_salary": 80000,
                "max_salary": 120000,
                "currency": "USD",
                "period": "yearly"
            }},
            "additional_requirements": ["Must have portfolio", "Strong communication skills"]
        }}

        Job Title: {job_title or 'Not provided'}
        Job Description:
        {job_description}
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
                        "max_tokens": 1500
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
                        return JobRequirements(**parsed_json)
                    
                raise Exception("Failed to parse JSON from Groq response")
                
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    async def _basic_requirements_parsing(
        self, 
        parse_request: JobRequirementsParseRequest
    ) -> JobRequirementsParseResult:
        """Basic requirements parsing as fallback"""
        
        description = parse_request.job_description.lower()
        
        # Extract common skills
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'html', 'css', 'typescript', 'mongodb'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill in description:
                found_skills.append(SkillRequirement(
                    name=skill.title(),
                    required=True,
                    proficiency_level='intermediate'
                ))
        
        # Extract experience requirements
        exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', description)
        min_experience_years = int(exp_match.group(1)) if exp_match else None
        
        # Extract salary information
        salary_match = re.search(r'\$(\d+)(?:,(\d+))?\s*(?:-\s*\$(\d+)(?:,(\d+))?)?', description)
        salary = None
        if salary_match:
            min_sal = int(salary_match.group(1) + (salary_match.group(2) or ''))
            max_sal = int(salary_match.group(3) + (salary_match.group(4) or '')) if salary_match.group(3) else None
            salary = {
                'min_salary': min_sal,
                'max_salary': max_sal,
                'currency': 'USD',
                'period': 'yearly'
            }
        
        # Determine location type
        location_type = 'onsite'
        if 'remote' in description:
            location_type = 'remote'
        elif 'hybrid' in description:
            location_type = 'hybrid'
        
        requirements = JobRequirements(
            skills=found_skills,
            min_experience_years=min_experience_years,
            location=LocationRequirement(type=LocationType(location_type)) if location_type else None,
            salary=SalaryRange(**salary) if salary else None
        )
        
        return JobRequirementsParseResult(
            success=True,
            parsed_requirements=requirements,
            confidence_score=0.6,
            extracted_skills=[skill.name for skill in found_skills],
            suggested_improvements=[
                "Consider adding more specific skill requirements",
                "Specify experience level more clearly",
                "Include salary range for better candidate attraction"
            ]
        )

    def _extract_skills_from_requirements(self, requirements: JobRequirements) -> List[str]:
        """Extract skill names from requirements"""
        return [skill.name for skill in requirements.skills] if requirements.skills else []

    def _suggest_improvements(self, job_description: str) -> List[str]:
        """Suggest improvements for job description"""
        
        suggestions = []
        
        if len(job_description) < 200:
            suggestions.append("Consider adding more details about the role and responsibilities")
        
        if 'salary' not in job_description.lower():
            suggestions.append("Including salary range can attract more qualified candidates")
        
        if 'benefit' not in job_description.lower():
            suggestions.append("Mention benefits and perks to make the position more attractive")
        
        if 'remote' not in job_description.lower() and 'office' not in job_description.lower():
            suggestions.append("Clarify work location (remote, hybrid, or on-site)")
        
        return suggestions