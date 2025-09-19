from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import User, UserProfile, UserAnalytics, SkillProgression, SkillAssessment, UserPreference, Session
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user
from pydantic import BaseModel, EmailStr, Field
from typing import List
from sqlalchemy import desc

router = APIRouter(prefix="/api", tags=["User Management"])

# Pydantic models for request/response
class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_image: Optional[str]
    role: str
    experience: Optional[str]

    # Extended profile data
    target_companies: Optional[List[str]]
    focus_areas: Optional[List[str]]
    preferred_interview_types: Optional[List[str]]
    years_of_experience: Optional[int]
    current_role: Optional[str]
    current_company: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    resume_url: Optional[str]
    bio: Optional[str]
    created_at: str
    updated_at: str

class UserAnalyticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_rating: float
    total_time_spent_minutes: int
    skills_improved: Optional[List[Dict[str, Any]]]
    companies_interviewed_with: Optional[List[str]]
    streak_days: int
    last_activity_at: str

class SkillAssessmentResponse(BaseModel):
    id: str
    skill: str
    score: int
    level: str
    last_tested: str
    badge: str

class SessionSummary(BaseModel):
    id: str
    mentor_name: str
    session_type: str
    scheduled_at: str
    duration_minutes: int
    status: str
    rating: Optional[float]
    feedback: Optional[str]

class DashboardData(BaseModel):
    user_profile: UserProfileResponse
    analytics: UserAnalyticsResponse
    recent_sessions: List[SessionSummary]
    upcoming_sessions: List[SessionSummary]
    skills: List[SkillAssessmentResponse]
    quick_stats: Dict[str, Any]

class UserPreferencesUpdate(BaseModel):
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    theme: Optional[str] = None
    notification_settings: Optional[Dict[str, Any]] = None

class UserProfileUpdate(BaseModel):
    target_companies: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    preferred_interview_types: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    bio: Optional[str] = None

@router.get("/users/me",
            response_model=UserProfileResponse,
            summary="Get current user profile",
            description="Retrieve the current user's profile information")
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current user profile"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        return UserProfileResponse(
            id=str(user.id),
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image=user.profile_image,
            role=user.role,
            experience=user.experience,
            target_companies=profile.target_companies if profile else [],
            focus_areas=profile.focus_areas if profile else [],
            preferred_interview_types=profile.preferred_interview_types if profile else [],
            years_of_experience=profile.years_of_experience if profile else None,
            current_role=profile.current_role if profile else None,
            current_company=profile.current_company if profile else None,
            location=profile.location if profile else None,
            linkedin_url=profile.linkedin_url if profile else None,
            github_url=profile.github_url if profile else None,
            portfolio_url=profile.portfolio_url if profile else None,
            resume_url=profile.resume_url if profile else None,
            bio=profile.bio if profile else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.get("/users/me/analytics",
            response_model=UserAnalyticsResponse,
            summary="Get user analytics",
            description="Retrieve user's performance analytics and statistics")
async def get_user_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user analytics"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
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

        if not analytics:
            # Create default analytics if not exists
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
            last_activity_at=analytics.last_activity_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user analytics: {str(e)}"
        )

@router.get("/users/me/skills",
            response_model=List[SkillAssessmentResponse],
            summary="Get user skill assessments",
            description="Retrieve user's skill assessment history and scores")
async def get_user_skills(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user skills"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get skill assessments
        skills_result = await db.execute(
            select(SkillAssessment)
            .where(SkillAssessment.user_id == user.id)
            .order_by(SkillAssessment.assessed_at.desc())
        )
        skills = skills_result.scalars().all()

        # Map scores to levels and badges
        def get_level_and_badge(score):
            if score >= 80:
                return "Advanced", "🟩"
            elif score >= 60:
                return "Intermediate", "🟨"
            elif score >= 40:
                return "Beginner", "🟧"
            else:
                return "Novice", "🟥"

        return [
            SkillAssessmentResponse(
                id=str(skill.id),
                skill=skill.skill,
                score=skill.score,
                level=get_level_and_badge(skill.score)[0],
                last_tested=skill.assessed_at.strftime("%Y-%m-%d"),
                badge=get_level_and_badge(skill.score)[1]
            )
            for skill in skills
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user skills: {str(e)}"
        )

@router.patch("/users/me/preferences",
               response_model=SuccessResponse,
               summary="Update user preferences",
               description="Update user's preferences and settings")
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get or create user preferences
        pref_result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        user_pref = pref_result.scalar_one_or_none()

        if not user_pref:
            user_pref = UserPreference(user_id=user.id)
            db.add(user_pref)

        # Update preferences
        update_data = preferences.dict(exclude_unset=True)
        if update_data:
            await db.execute(
                update(UserPreference)
                .where(UserPreference.user_id == user.id)
                .values(**update_data)
            )
            await db.commit()

        return SuccessResponse(
            success=True,
            message="User preferences updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

@router.patch("/users/me/profile",
               response_model=SuccessResponse,
               summary="Update user profile",
               description="Update user's extended profile information")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get or create user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)

        # Update profile
        update_data = profile_data.dict(exclude_unset=True)
        if update_data:
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user.id)
                .values(**update_data)
            )
            await db.commit()

        return SuccessResponse(
            success=True,
            message="User profile updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )

class SkillAssessmentRequest(BaseModel):
    skill: str = Field(..., description="Skill name")
    score: int = Field(..., ge=0, le=100, description="Score (0-100)")
    session_id: Optional[str] = Field(None, description="Associated session ID")

@router.post("/users/me/skills",
              response_model=SkillAssessmentResponse,
              summary="Add skill assessment",
              description="Add a new skill assessment for the user")
async def add_skill_assessment(
    request: SkillAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add skill assessment"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Create skill assessment
        assessment = SkillAssessment(
            user_id=user.id,
            skill=request.skill,
            score=request.score,
            session_id=uuid.UUID(request.session_id) if request.session_id else None
        )
        db.add(assessment)
        await db.commit()

        # Get level and badge
        def get_level_and_badge(score):
            if score >= 80:
                return "Advanced", "🟩"
            elif score >= 60:
                return "Intermediate", "🟨"
            elif score >= 40:
                return "Beginner", "🟧"
            else:
                return "Novice", "🟥"

        level, badge = get_level_and_badge(request.score)

        return SkillAssessmentResponse(
            id=str(assessment.id),
            skill=assessment.skill,
            score=assessment.score,
            level=level,
            last_tested=assessment.assessed_at.strftime("%Y-%m-%d"),
            badge=badge
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add skill assessment: {str(e)}"
        )

@router.get("/users/me/dashboard",
            response_model=DashboardData,
            summary="Get user dashboard data",
            description="Retrieve comprehensive dashboard data for the current user")
async def get_user_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user dashboard data"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        user_profile = UserProfileResponse(
            id=str(user.id),
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image=user.profile_image,
            role=user.role,
            experience=user.experience,
            target_companies=profile.target_companies if profile else [],
            focus_areas=profile.focus_areas if profile else [],
            preferred_interview_types=profile.preferred_interview_types if profile else [],
            years_of_experience=profile.years_of_experience if profile else None,
            current_role=profile.current_role if profile else None,
            current_company=profile.current_company if profile else None,
            location=profile.location if profile else None,
            linkedin_url=profile.linkedin_url if profile else None,
            github_url=profile.github_url if profile else None,
            portfolio_url=profile.portfolio_url if profile else None,
            resume_url=profile.resume_url if profile else None,
            bio=profile.bio if profile else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )

        # Get user analytics
        analytics_result = await db.execute(
            select(UserAnalytics).where(UserAnalytics.user_id == user.id)
        )
        analytics = analytics_result.scalar_one_or_none()

        if not analytics:
            analytics = UserAnalytics(user_id=user.id)
            db.add(analytics)
            await db.commit()

        user_analytics = UserAnalyticsResponse(
            total_sessions=analytics.total_sessions,
            completed_sessions=analytics.completed_sessions,
            average_rating=float(analytics.average_rating),
            total_time_spent_minutes=analytics.total_time_spent_minutes,
            skills_improved=analytics.skills_improved,
            companies_interviewed_with=analytics.companies_interviewed_with,
            streak_days=analytics.streak_days,
            last_activity_at=analytics.last_activity_at.isoformat()
        )

        # Get recent sessions
        recent_sessions_result = await db.execute(
            select(Session)
            .where(Session.user_id == user.id)
            .order_by(desc(Session.scheduled_at))
            .limit(5)
        )
        recent_sessions = recent_sessions_result.scalars().all()

        recent_session_summaries = []
        for session in recent_sessions:
            recent_session_summaries.append(SessionSummary(
                id=str(session.id),
                mentor_name=f"{session.mentor.first_name} {session.mentor.last_name}",
                session_type=session.session_type,
                scheduled_at=session.scheduled_at.isoformat(),
                duration_minutes=session.duration_minutes,
                status=session.status,
                rating=session.rating,
                feedback=session.feedback
            ))

        # Get upcoming sessions
        upcoming_sessions_result = await db.execute(
            select(Session)
            .where(
                and_(
                    Session.user_id == user.id,
                    Session.status.in_(['scheduled', 'confirmed']),
                    Session.scheduled_at > datetime.now()
                )
            )
            .order_by(Session.scheduled_at)
            .limit(5)
        )
        upcoming_sessions = upcoming_sessions_result.scalars().all()

        upcoming_session_summaries = []
        for session in upcoming_sessions:
            upcoming_session_summaries.append(SessionSummary(
                id=str(session.id),
                mentor_name=f"{session.mentor.first_name} {session.mentor.last_name}",
                session_type=session.session_type,
                scheduled_at=session.scheduled_at.isoformat(),
                duration_minutes=session.duration_minutes,
                status=session.status,
                rating=session.rating,
                feedback=session.feedback
            ))

        # Get skills
        skills_result = await db.execute(
            select(SkillAssessment)
            .where(SkillAssessment.user_id == user.id)
            .order_by(desc(SkillAssessment.assessed_at))
            .limit(10)
        )
        skills = skills_result.scalars().all()

        def get_level_and_badge(score):
            if score >= 80:
                return "Advanced", "🟩"
            elif score >= 60:
                return "Intermediate", "🟨"
            elif score >= 40:
                return "Beginner", "🟧"
            else:
                return "Novice", "🟥"

        skill_assessments = []
        for skill in skills:
            level, badge = get_level_and_badge(skill.score)
            skill_assessments.append(SkillAssessmentResponse(
                id=str(skill.id),
                skill=skill.skill,
                score=skill.score,
                level=level,
                last_tested=skill.assessed_at.strftime("%Y-%m-%d"),
                badge=badge
            ))

        # Quick stats
        quick_stats = {
            "completion_rate": round((analytics.completed_sessions / analytics.total_sessions * 100) if analytics.total_sessions > 0 else 0, 1),
            "average_session_duration": round(analytics.total_time_spent_minutes / analytics.completed_sessions) if analytics.completed_sessions > 0 else 0,
            "total_mentors_interviewed": len(set(s.mentor_id for s in recent_sessions if s.mentor_id)),
            "skill_improvement_rate": len([s for s in skills if s.score >= 60]),
            "active_streak": analytics.streak_days
        }

        return DashboardData(
            user_profile=user_profile,
            analytics=user_analytics,
            recent_sessions=recent_session_summaries,
            upcoming_sessions=upcoming_session_summaries,
            skills=skill_assessments,
            quick_stats=quick_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user dashboard: {str(e)}"
        )