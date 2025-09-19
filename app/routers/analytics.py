from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta

from app.database import get_db
from app.database.models import User, Session, Mentor, UserAnalytics, SessionAnalytics, SkillProgression, SkillAssessment, Review, Company
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Analytics"])

# Pydantic models
class UserAnalyticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_rating: float
    total_time_spent_minutes: int
    skills_improved: Optional[List[Dict[str, Any]]]
    companies_interviewed_with: Optional[List[str]]
    streak_days: int
    last_activity_at: str
    completion_rate: float

class SessionAnalyticsResponse(BaseModel):
    session_id: str
    performance_score: Optional[int]
    technical_score: Optional[int]
    communication_score: Optional[int]
    problem_solving_score: Optional[int]
    feedback_summary: Optional[str]
    key_improvements: Optional[List[str]]
    strengths: Optional[List[str]]

class SkillProgressionResponse(BaseModel):
    skill: str
    initial_score: int
    current_score: int
    improvement_percentage: float
    assessments_count: int
    last_assessed_at: str
    next_recommended_assessment: Optional[str]

class PlatformStatsResponse(BaseModel):
    total_users: int
    total_mentors: int
    total_sessions: int
    total_companies: int
    average_rating: float
    popular_skills: List[Dict[str, Any]]
    top_companies: List[Dict[str, Any]]
    session_growth: List[Dict[str, Any]]

class PerformanceMetricsResponse(BaseModel):
    weekly_progress: Dict[str, float]
    skill_distribution: Dict[str, int]
    company_distribution: Dict[str, int]
    session_types: Dict[str, int]
    improvement_areas: List[str]

@router.get("/analytics/user/{user_id}",
            response_model=UserAnalyticsResponse,
            summary="Get user analytics",
            description="Get comprehensive analytics for a specific user")
async def get_user_analytics(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user analytics"""
    try:
        # Verify user has access to this data
        if current_user["sub"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user analytics
        analytics_result = await db.execute(
            select(UserAnalytics).where(UserAnalytics.user_id == user.id)
        )
        analytics = analytics_result.scalar_one_or_none()

        # Calculate completion rate
        completion_rate = 0
        if analytics and analytics.total_sessions > 0:
            completion_rate = (analytics.completed_sessions / analytics.total_sessions) * 100

        # Create default analytics if not exists
        if not analytics:
            analytics = UserAnalytics(user_id=user.id)
            db.add(analytics)
            await db.commit()

        return UserAnalyticsResponse(
            total_sessions=analytics.total_sessions,
            completed_sessions=analytics.completed_sessions,
            average_rating=float(analytics.average_rating),
            total_time_spent_minutes=analytics.total_time_spent_minutes,
            skills_improved=analytics.skills_improved,
            companies_interviewed_with=analytics.companies_interviewed_with,
            streak_days=analytics.streak_days,
            last_activity_at=analytics.last_activity_at.isoformat(),
            completion_rate=completion_rate
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user analytics: {str(e)}"
        )

@router.get("/analytics/skills/{user_id}",
            response_model=List[SkillProgressionResponse],
            summary="Get skill progression",
            description="Get skill progression tracking for a user")
async def get_skill_progression(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get skill progression"""
    try:
        # Verify user has access to this data
        if current_user["sub"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get skill progression
        progression_result = await db.execute(
            select(SkillProgression)
            .where(SkillProgression.user_id == user.id)
            .order_by(SkillProgression.current_score.desc())
        )
        progressions = progression_result.scalars().all()

        return [
            SkillProgressionResponse(
                skill=progression.skill,
                initial_score=progression.initial_score,
                current_score=progression.current_score,
                improvement_percentage=float(progression.improvement_percentage) if progression.improvement_percentage else 0,
                assessments_count=progression.assessments_count,
                last_assessed_at=progression.last_assessed_at.isoformat(),
                next_recommended_assessment=progression.next_recommended_assessment.isoformat() if progression.next_recommended_assessment else None
            )
            for progression in progressions
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill progression: {str(e)}"
        )

@router.get("/analytics/sessions/{user_id}",
            response_model=List[SessionAnalyticsResponse],
            summary="Get session analytics",
            description="Get detailed session analytics for a user")
async def get_session_analytics(
    user_id: str,
    limit: int = Query(10, description="Maximum number of sessions"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get session analytics"""
    try:
        # Verify user has access to this data
        if current_user["sub"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get session analytics
        analytics_result = await db.execute(
            select(SessionAnalytics)
            .where(SessionAnalytics.user_id == user.id)
            .order_by(SessionAnalytics.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        session_analytics = analytics_result.scalars().all()

        return [
            SessionAnalyticsResponse(
                session_id=str(analytics.session_id),
                performance_score=analytics.performance_score,
                technical_score=analytics.technical_score,
                communication_score=analytics.communication_score,
                problem_solving_score=analytics.problem_solving_score,
                feedback_summary=analytics.feedback_summary,
                key_improvements=analytics.key_improvements,
                strengths=analytics.strengths
            )
            for analytics in session_analytics
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session analytics: {str(e)}"
        )

@router.get("/analytics/performance/{user_id}",
            response_model=PerformanceMetricsResponse,
            summary="Get performance metrics",
            description="Get detailed performance metrics for a user")
async def get_performance_metrics(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance metrics"""
    try:
        # Verify user has access to this data
        if current_user["sub"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get sessions in date range
        sessions_result = await db.execute(
            select(Session)
            .where(Session.user_id == user.id)
            .where(Session.scheduled_at >= start_date)
            .where(Session.scheduled_at <= end_date)
        )
        sessions = sessions_result.scalars().all()

        # Calculate weekly progress
        weekly_progress = {}
        for i in range(4):
            week_start = end_date - timedelta(weeks=i+1)
            week_end = end_date - timedelta(weeks=i)

            week_sessions = [s for s in sessions if week_start <= s.scheduled_at <= week_end]
            weekly_progress[f"Week {i+1}"] = len(week_sessions)

        # Get skill assessments
        skills_result = await db.execute(
            select(SkillAssessment)
            .where(SkillAssessment.user_id == user.id)
            .where(SkillAssessment.assessed_at >= start_date)
        )
        skill_assessments = skills_result.scalars().all()

        # Calculate skill distribution
        skill_distribution = {}
        for assessment in skill_assessments:
            skill_level = "Beginner" if assessment.score < 60 else "Intermediate" if assessment.score < 80 else "Advanced"
            skill_distribution[skill_level] = skill_distribution.get(skill_level, 0) + 1

        # Get company distribution from sessions
        company_distribution = {}
        for session in sessions:
            if session.mentor:
                company = session.mentor.current_company
                if company:
                    company_distribution[company] = company_distribution.get(company, 0) + 1

        # Get session types
        session_types = {}
        for session in sessions:
            session_types[session.session_type] = session_types.get(session.session_type, 0) + 1

        # Identify improvement areas based on low scores
        improvement_areas = []
        for assessment in skill_assessments:
            if assessment.score < 60:
                improvement_areas.append(assessment.skill)

        return PerformanceMetricsResponse(
            weekly_progress=weekly_progress,
            skill_distribution=skill_distribution,
            company_distribution=company_distribution,
            session_types=session_types,
            improvement_areas=list(set(improvement_areas))
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/analytics/platform/stats",
            response_model=PlatformStatsResponse,
            summary="Get platform statistics",
            description="Get platform-wide statistics and analytics")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get platform statistics"""
    try:
        # Get basic counts
        user_count = await db.execute(select(func.count(User.id)))
        mentor_count = await db.execute(select(func.count(Mentor.id)))
        session_count = await db.execute(select(func.count(Session.id)))
        company_count = await db.execute(select(func.count(Company.id)))

        # Get average rating
        avg_rating = await db.execute(
            select(func.avg(Session.rating))
            .where(Session.rating.isnot(None))
        )

        # Get popular skills from mentors
        skills_result = await db.execute(select(Mentor.skills).where(Mentor.skills.isnot(None)))
        all_skills = []
        for skills_tuple in skills_result:
            if skills_tuple[0]:
                all_skills.extend(skills_tuple[0])

        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        popular_skills = [
            {"skill": skill, "count": count}
            for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Get top companies
        companies_result = await db.execute(
            select(
                Mentor.current_company,
                func.count(Mentor.id).label('mentor_count')
            )
            .where(Mentor.current_company.isnot(None))
            .group_by(Mentor.current_company)
            .order_by(func.count(Mentor.id).desc())
            .limit(10)
        )

        top_companies = [
            {"name": company, "mentor_count": count}
            for company, count in companies_result
        ]

        # Get session growth over last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        sessions_result = await db.execute(
            select(
                func.date(Session.scheduled_at).label('date'),
                func.count(Session.id).label('count')
            )
            .where(Session.scheduled_at >= start_date)
            .where(Session.scheduled_at <= end_date)
            .group_by(func.date(Session.scheduled_at))
            .order_by(func.date(Session.scheduled_at))
        )

        session_growth = [
            {"date": date.strftime("%Y-%m-%d"), "count": count}
            for date, count in sessions_result
        ]

        return PlatformStatsResponse(
            total_users=user_count.scalar() or 0,
            total_mentors=mentor_count.scalar() or 0,
            total_sessions=session_count.scalar() or 0,
            total_companies=company_count.scalar() or 0,
            average_rating=float(avg_rating.scalar() or 0),
            popular_skills=popular_skills,
            top_companies=top_companies,
            session_growth=session_growth
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform stats: {str(e)}"
        )

@router.get("/analytics/trends",
            response_model=Dict[str, Any],
            summary="Get platform trends",
            description="Get platform trends and insights")
async def get_platform_trends(
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get platform trends"""
    try:
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get session trends
        session_trends = await db.execute(
            select(
                func.date(Session.scheduled_at).label('date'),
                func.count(Session.id).label('count'),
                func.avg(Session.rating).label('avg_rating')
            )
            .where(Session.scheduled_at >= start_date)
            .where(Session.scheduled_at <= end_date)
            .group_by(func.date(Session.scheduled_at))
            .order_by(func.date(Session.scheduled_at))
        )

        # Get user registration trends
        user_trends = await db.execute(
            select(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            )
            .where(User.created_at >= start_date)
            .where(User.created_at <= end_date)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )

        # Get popular session types
        session_types = await db.execute(
            select(
                Session.session_type,
                func.count(Session.id).label('count')
            )
            .where(Session.created_at >= start_date)
            .group_by(Session.session_type)
            .order_by(func.count(Session.id).desc())
        )

        # Get top performing mentors
        top_mentors = await db.execute(
            select(
                Mentor.name,
                func.count(Session.id).label('session_count'),
                func.avg(Session.rating).label('avg_rating')
            )
            .join(Session, Mentor.id == Session.mentor_id)
            .where(Session.created_at >= start_date)
            .group_by(Mentor.id, Mentor.name)
            .order_by(func.count(Session.id).desc(), func.avg(Session.rating).desc())
            .limit(10)
        )

        return {
            "session_trends": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "count": count,
                    "avg_rating": float(avg_rating) if avg_rating else 0
                }
                for date, count, avg_rating in session_trends
            ],
            "user_trends": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "count": count
                }
                for date, count in user_trends
            ],
            "popular_session_types": [
                {
                    "type": session_type,
                    "count": count
                }
                for session_type, count in session_types
            ],
            "top_mentors": [
                {
                    "name": name,
                    "session_count": session_count,
                    "avg_rating": float(avg_rating) if avg_rating else 0
                }
                for name, session_count, avg_rating in top_mentors
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform trends: {str(e)}"
        )