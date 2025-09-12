"""
Application and pipeline management service
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, case, text
from fastapi import HTTPException, status

from app.models.job import Application, Job, Candidate
from app.models.scoring import Score
from app.models.interview import Interview
from app.models.assessment import Assessment
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ApplicationListResponse, ApplicationFilters, ApplicationSort,
    PipelineStatusUpdate, CandidateRanking, RankingWeights,
    ApplicationAnalytics, FunnelData, PipelineMetrics
)

logger = logging.getLogger(__name__)


class ApplicationStatus(str, Enum):
    """Application status enum"""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    ASSESSED = "assessed"
    HIRED = "hired"
    REJECTED = "rejected"


class SortField(str, Enum):
    """Available sort fields"""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    CANDIDATE_NAME = "candidate_name"
    JOB_TITLE = "job_title"
    OVERALL_SCORE = "overall_score"


class ApplicationService:
    """Service for application and pipeline management"""

    def __init__(self, db: Session):
        self.db = db

    async def create_application(
        self, 
        application_data: ApplicationCreate
    ) -> ApplicationResponse:
        """Create a new job application"""
        
        # Verify candidate exists
        candidate = self.db.query(Candidate).filter(
            Candidate.id == application_data.candidate_id
        ).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )

        # Verify job exists and is active
        job = self.db.query(Job).filter(
            and_(
                Job.id == application_data.job_id,
                Job.status == "active"
            )
        ).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not active"
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
            status=ApplicationStatus.APPLIED,
            cover_letter=application_data.cover_letter,
            application_data=application_data.application_data or {}
        )

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)

        return await self._to_application_response(application)

    async def get_application(self, application_id: UUID) -> ApplicationResponse:
        """Get application by ID"""
        application = self.db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return await self._to_application_response(application)

    async def update_application(
        self, 
        application_id: UUID, 
        application_data: ApplicationUpdate
    ) -> ApplicationResponse:
        """Update application information"""
        application = self.db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # Update fields
        update_data = application_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)

        application.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(application)

        return await self._to_application_response(application)

    async def update_pipeline_status(
        self, 
        application_id: UUID, 
        status_update: PipelineStatusUpdate
    ) -> ApplicationResponse:
        """Update application pipeline status with notes"""
        application = self.db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # Validate status transition
        if not self._is_valid_status_transition(application.status, status_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {application.status} to {status_update.status}"
            )

        # Update status and add notes to application data
        old_status = application.status
        application.status = status_update.status
        application.updated_at = datetime.utcnow()

        # Add status change to application data
        if 'status_history' not in application.application_data:
            application.application_data['status_history'] = []
        
        application.application_data['status_history'].append({
            'from_status': old_status,
            'to_status': status_update.status,
            'changed_at': datetime.utcnow().isoformat(),
            'changed_by': status_update.changed_by,
            'notes': status_update.notes
        })

        self.db.commit()
        self.db.refresh(application)

        return await self._to_application_response(application)

    async def list_applications(
        self,
        filters: ApplicationFilters,
        sort: ApplicationSort,
        page: int = 1,
        page_size: int = 20
    ) -> ApplicationListResponse:
        """List applications with filtering and sorting"""
        
        query = self.db.query(Application).join(Candidate).join(Job)
        
        # Apply filters
        query = self._apply_filters(query, filters)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        query = self._apply_sorting(query, sort)
        
        # Apply pagination
        offset = (page - 1) * page_size
        applications = query.offset(offset).limit(page_size).all()
        
        # Convert to response objects
        application_responses = []
        for app in applications:
            response = await self._to_application_response(app)
            application_responses.append(response)
        
        return ApplicationListResponse(
            applications=application_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            filters=filters,
            sort=sort
        )

    async def get_candidate_rankings(
        self,
        job_id: UUID,
        weights: Optional[RankingWeights] = None
    ) -> List[CandidateRanking]:
        """Get ranked candidates for a job with customizable weights"""
        
        # Verify job exists
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Use default weights if not provided
        if weights is None:
            weights = RankingWeights()

        # Get applications for the job with scores
        applications = self.db.query(Application).filter(
            Application.job_id == job_id
        ).all()

        rankings = []
        for app in applications:
            ranking = await self._calculate_candidate_ranking(app, weights)
            rankings.append(ranking)

        # Sort by overall score descending
        rankings.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Add rank positions
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1

        return rankings

    async def get_application_analytics(
        self,
        job_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> ApplicationAnalytics:
        """Get application analytics and funnel data"""
        
        # Build base query
        query = self.db.query(Application)
        
        if job_id:
            query = query.filter(Application.job_id == job_id)
        
        if company_id:
            query = query.join(Job).filter(Job.company_id == company_id)
        
        if date_from:
            query = query.filter(Application.created_at >= date_from)
        
        if date_to:
            query = query.filter(Application.created_at <= date_to)

        # Get all applications
        applications = query.all()
        
        # Calculate funnel data
        funnel_data = self._calculate_funnel_data(applications)
        
        # Calculate pipeline metrics
        pipeline_metrics = self._calculate_pipeline_metrics(applications)
        
        # Calculate time-based metrics
        applications_by_date = self._calculate_applications_by_date(applications)
        
        return ApplicationAnalytics(
            total_applications=len(applications),
            funnel_data=funnel_data,
            pipeline_metrics=pipeline_metrics,
            applications_by_date=applications_by_date,
            conversion_rates=self._calculate_conversion_rates(funnel_data),
            average_time_in_pipeline=self._calculate_average_pipeline_time(applications)
        )

    # Private helper methods

    def _apply_filters(self, query, filters: ApplicationFilters):
        """Apply filters to the query"""
        
        if filters.job_id:
            query = query.filter(Application.job_id == filters.job_id)
        
        if filters.candidate_id:
            query = query.filter(Application.candidate_id == filters.candidate_id)
        
        if filters.status:
            if isinstance(filters.status, list):
                query = query.filter(Application.status.in_(filters.status))
            else:
                query = query.filter(Application.status == filters.status)
        
        if filters.created_from:
            query = query.filter(Application.created_at >= filters.created_from)
        
        if filters.created_to:
            query = query.filter(Application.created_at <= filters.created_to)
        
        if filters.updated_from:
            query = query.filter(Application.updated_at >= filters.updated_from)
        
        if filters.updated_to:
            query = query.filter(Application.updated_at <= filters.updated_to)
        
        if filters.candidate_name:
            query = query.filter(
                Candidate.name.ilike(f"%{filters.candidate_name}%")
            )
        
        if filters.job_title:
            query = query.filter(
                Job.title.ilike(f"%{filters.job_title}%")
            )
        
        if filters.has_cover_letter is not None:
            if filters.has_cover_letter:
                query = query.filter(Application.cover_letter.isnot(None))
            else:
                query = query.filter(Application.cover_letter.is_(None))
        
        if filters.min_score is not None:
            # Filter by minimum overall score
            subquery = self.db.query(
                Score.application_id,
                func.avg(Score.score).label('avg_score')
            ).group_by(Score.application_id).subquery()
            
            query = query.join(
                subquery, 
                Application.id == subquery.c.application_id
            ).filter(subquery.c.avg_score >= filters.min_score)
        
        return query

    def _apply_sorting(self, query, sort: ApplicationSort):
        """Apply sorting to the query"""
        
        sort_column = None
        
        if sort.field == SortField.CREATED_AT:
            sort_column = Application.created_at
        elif sort.field == SortField.UPDATED_AT:
            sort_column = Application.updated_at
        elif sort.field == SortField.STATUS:
            sort_column = Application.status
        elif sort.field == SortField.CANDIDATE_NAME:
            sort_column = Candidate.name
        elif sort.field == SortField.JOB_TITLE:
            sort_column = Job.title
        elif sort.field == SortField.OVERALL_SCORE:
            # Sort by average score
            subquery = self.db.query(
                Score.application_id,
                func.avg(Score.score).label('avg_score')
            ).group_by(Score.application_id).subquery()
            
            query = query.outerjoin(
                subquery, 
                Application.id == subquery.c.application_id
            )
            sort_column = subquery.c.avg_score
        
        if sort_column is not None:
            if sort.direction == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        return query

    def _is_valid_status_transition(self, from_status: str, to_status: str) -> bool:
        """Validate if status transition is allowed"""
        
        # Define valid transitions
        valid_transitions = {
            ApplicationStatus.APPLIED: [
                ApplicationStatus.SCREENING, 
                ApplicationStatus.REJECTED
            ],
            ApplicationStatus.SCREENING: [
                ApplicationStatus.INTERVIEWING, 
                ApplicationStatus.REJECTED
            ],
            ApplicationStatus.INTERVIEWING: [
                ApplicationStatus.ASSESSED, 
                ApplicationStatus.REJECTED
            ],
            ApplicationStatus.ASSESSED: [
                ApplicationStatus.HIRED, 
                ApplicationStatus.REJECTED
            ],
            ApplicationStatus.HIRED: [],  # Final state
            ApplicationStatus.REJECTED: []  # Final state
        }
        
        return to_status in valid_transitions.get(from_status, [])

    async def _calculate_candidate_ranking(
        self, 
        application: Application, 
        weights: RankingWeights
    ) -> CandidateRanking:
        """Calculate candidate ranking with weighted scores"""
        
        # Get scores for this application
        scores = self.db.query(Score).filter(
            Score.application_id == application.id
        ).all()
        
        # Initialize score categories
        category_scores = {
            'technical': 0.0,
            'communication': 0.0,
            'cultural_fit': 0.0,
            'cognitive': 0.0,
            'behavioral': 0.0
        }
        
        # Populate scores
        for score in scores:
            if score.category in category_scores:
                category_scores[score.category] = float(score.score)
        
        # Calculate weighted overall score
        overall_score = (
            category_scores['technical'] * weights.technical_weight +
            category_scores['communication'] * weights.communication_weight +
            category_scores['cultural_fit'] * weights.cultural_fit_weight +
            category_scores['cognitive'] * weights.cognitive_weight +
            category_scores['behavioral'] * weights.behavioral_weight
        )
        
        # Get additional metrics
        interview_count = self.db.query(Interview).filter(
            Interview.application_id == application.id
        ).count()
        
        assessment_count = self.db.query(Assessment).filter(
            Assessment.application_id == application.id
        ).count()
        
        return CandidateRanking(
            application_id=application.id,
            candidate_id=application.candidate_id,
            candidate_name=application.candidate.name,
            candidate_email=application.candidate.email,
            job_id=application.job_id,
            job_title=application.job.title,
            overall_score=overall_score,
            category_scores=category_scores,
            status=application.status,
            applied_at=application.created_at,
            last_updated=application.updated_at,
            interview_count=interview_count,
            assessment_count=assessment_count,
            rank=0  # Will be set after sorting
        )

    def _calculate_funnel_data(self, applications: List[Application]) -> List[FunnelData]:
        """Calculate funnel conversion data"""
        
        status_counts = {}
        for app in applications:
            status_counts[app.status] = status_counts.get(app.status, 0) + 1
        
        # Define funnel stages in order
        funnel_stages = [
            ApplicationStatus.APPLIED,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.ASSESSED,
            ApplicationStatus.HIRED
        ]
        
        funnel_data = []
        total_applications = len(applications)
        
        for stage in funnel_stages:
            count = status_counts.get(stage, 0)
            percentage = (count / total_applications * 100) if total_applications > 0 else 0
            
            funnel_data.append(FunnelData(
                stage=stage,
                count=count,
                percentage=percentage
            ))
        
        # Add rejected as a separate category
        rejected_count = status_counts.get(ApplicationStatus.REJECTED, 0)
        rejected_percentage = (rejected_count / total_applications * 100) if total_applications > 0 else 0
        
        funnel_data.append(FunnelData(
            stage=ApplicationStatus.REJECTED,
            count=rejected_count,
            percentage=rejected_percentage
        ))
        
        return funnel_data

    def _calculate_pipeline_metrics(self, applications: List[Application]) -> PipelineMetrics:
        """Calculate pipeline performance metrics"""
        
        total_apps = len(applications)
        if total_apps == 0:
            return PipelineMetrics()
        
        # Count by status
        status_counts = {}
        for app in applications:
            status_counts[app.status] = status_counts.get(app.status, 0) + 1
        
        # Calculate metrics
        hired_count = status_counts.get(ApplicationStatus.HIRED, 0)
        rejected_count = status_counts.get(ApplicationStatus.REJECTED, 0)
        active_count = total_apps - hired_count - rejected_count
        
        hire_rate = (hired_count / total_apps) * 100
        rejection_rate = (rejected_count / total_apps) * 100
        
        # Calculate average time in each stage
        stage_times = self._calculate_average_stage_times(applications)
        
        return PipelineMetrics(
            total_applications=total_apps,
            active_applications=active_count,
            hired_count=hired_count,
            rejected_count=rejected_count,
            hire_rate=hire_rate,
            rejection_rate=rejection_rate,
            average_stage_times=stage_times
        )

    def _calculate_applications_by_date(
        self, 
        applications: List[Application]
    ) -> List[Dict[str, Any]]:
        """Calculate applications grouped by date"""
        
        date_counts = {}
        for app in applications:
            date_key = app.created_at.date().isoformat()
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
        
        return [
            {"date": date, "count": count}
            for date, count in sorted(date_counts.items())
        ]

    def _calculate_conversion_rates(self, funnel_data: List[FunnelData]) -> Dict[str, float]:
        """Calculate conversion rates between stages"""
        
        conversion_rates = {}
        
        # Find applied count as base
        applied_count = 0
        for stage in funnel_data:
            if stage.stage == ApplicationStatus.APPLIED:
                applied_count = stage.count
                break
        
        if applied_count == 0:
            return conversion_rates
        
        # Calculate conversion rates
        for stage in funnel_data:
            if stage.stage != ApplicationStatus.APPLIED and stage.stage != ApplicationStatus.REJECTED:
                rate = (stage.count / applied_count) * 100
                conversion_rates[f"applied_to_{stage.stage}"] = rate
        
        return conversion_rates

    def _calculate_average_pipeline_time(self, applications: List[Application]) -> Optional[float]:
        """Calculate average time from application to final status"""
        
        completed_apps = [
            app for app in applications 
            if app.status in [ApplicationStatus.HIRED, ApplicationStatus.REJECTED]
        ]
        
        if not completed_apps:
            return None
        
        total_days = 0
        for app in completed_apps:
            days = (app.updated_at - app.created_at).days
            total_days += days
        
        return total_days / len(completed_apps)

    def _calculate_average_stage_times(self, applications: List[Application]) -> Dict[str, float]:
        """Calculate average time spent in each stage"""
        
        stage_times = {}
        
        for app in applications:
            status_history = app.application_data.get('status_history', [])
            
            if not status_history:
                continue
            
            # Calculate time in each stage
            prev_time = app.created_at
            prev_status = ApplicationStatus.APPLIED
            
            for change in status_history:
                change_time = datetime.fromisoformat(change['changed_at'].replace('Z', '+00:00'))
                time_in_stage = (change_time - prev_time).total_seconds() / 3600  # hours
                
                if prev_status not in stage_times:
                    stage_times[prev_status] = []
                stage_times[prev_status].append(time_in_stage)
                
                prev_time = change_time
                prev_status = change['to_status']
        
        # Calculate averages
        avg_stage_times = {}
        for stage, times in stage_times.items():
            avg_stage_times[stage] = sum(times) / len(times) if times else 0
        
        return avg_stage_times

    async def _to_application_response(self, application: Application) -> ApplicationResponse:
        """Convert Application model to response schema"""
        
        # Get related data
        candidate = application.candidate
        job = application.job
        
        # Get scores
        scores = self.db.query(Score).filter(
            Score.application_id == application.id
        ).all()
        
        score_summary = {}
        overall_score = None
        
        if scores:
            category_scores = {}
            for score in scores:
                category_scores[score.category] = float(score.score)
            
            # Calculate overall score as average
            if category_scores:
                overall_score = sum(category_scores.values()) / len(category_scores)
            
            score_summary = {
                'overall_score': overall_score,
                'category_scores': category_scores,
                'score_count': len(scores)
            }
        
        # Get interview and assessment counts
        interview_count = self.db.query(Interview).filter(
            Interview.application_id == application.id
        ).count()
        
        assessment_count = self.db.query(Assessment).filter(
            Assessment.application_id == application.id
        ).count()
        
        return ApplicationResponse(
            id=application.id,
            job_id=application.job_id,
            candidate_id=application.candidate_id,
            status=application.status,
            cover_letter=application.cover_letter,
            application_data=application.application_data,
            created_at=application.created_at,
            updated_at=application.updated_at,
            # Related data
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            job_title=job.title,
            company_id=job.company_id,
            # Computed fields
            overall_score=overall_score,
            score_summary=score_summary,
            interview_count=interview_count,
            assessment_count=assessment_count,
            days_in_pipeline=(datetime.utcnow() - application.created_at).days
        )