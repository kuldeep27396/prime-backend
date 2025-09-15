from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional
import uuid

from app.database import get_db
from app.database.models import User, UserPreference, Session, SkillAssessment
from app.schemas.user import UserCreate, UserResponse, UserProfileResponse, UserAnalytics
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user

router = APIRouter(prefix="/api", tags=["Users"])

@router.post("/users",
            response_model=SuccessResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create or update user profile",
            description="Create or update user profile after Clerk authentication")
async def create_or_update_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create or update user profile"""
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.user_id == user_data.userId)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Update existing user
            existing_user.email = user_data.email
            existing_user.first_name = user_data.firstName
            existing_user.last_name = user_data.lastName
            existing_user.profile_image = user_data.profileImage
            existing_user.role = user_data.role
            existing_user.experience = user_data.experience

            await db.commit()
            await db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            user = User(
                user_id=user_data.userId,
                email=user_data.email,
                first_name=user_data.firstName,
                last_name=user_data.lastName,
                profile_image=user_data.profileImage,
                role=user_data.role,
                experience=user_data.experience
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Handle preferences if provided
        if user_data.preferences:
            pref_result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user.id)
            )
            existing_pref = pref_result.scalar_one_or_none()

            if existing_pref:
                # Update preferences
                existing_pref.recent_searches = user_data.preferences.get('recentSearches', [])
                existing_pref.favorite_topics = user_data.preferences.get('favoriteTopics', [])
                existing_pref.timezone = user_data.preferences.get('timezone')
            else:
                # Create preferences
                preference = UserPreference(
                    user_id=user.id,
                    recent_searches=user_data.preferences.get('recentSearches', []),
                    favorite_topics=user_data.preferences.get('favoriteTopics', []),
                    timezone=user_data.preferences.get('timezone')
                )
                db.add(preference)

            await db.commit()

        return SuccessResponse(
            message="User profile created/updated successfully",
            data={
                "user": {
                    "id": str(user.id),
                    "userId": user.user_id,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "role": user.role,
                    "createdAt": user.created_at.isoformat(),
                    "updatedAt": user.updated_at.isoformat()
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update user: {str(e)}"
        )

@router.get("/users/{user_id}",
           response_model=UserProfileResponse,
           summary="Get user profile and session history",
           description="Get complete user profile including session history and preferences")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user profile with complete information"""
    try:
        # Verify user exists and get profile
        result = await db.execute(
            select(User)
            .options(selectinload(User.preferences))
            .where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get session history
        session_result = await db.execute(
            select(Session)
            .where(Session.user_id == user.id)
            .order_by(Session.scheduled_at.desc())
        )
        sessions = session_result.scalars().all()

        session_history = []
        for session in sessions:
            session_history.append({
                "id": str(session.id),
                "mentorId": str(session.mentor_id),
                "date": session.scheduled_at.isoformat(),
                "duration": session.duration,
                "type": session.session_type,
                "rating": session.rating,
                "feedback": session.feedback
            })

        # Get skill assessments
        skill_result = await db.execute(
            select(SkillAssessment)
            .where(SkillAssessment.user_id == user.id)
            .order_by(SkillAssessment.assessed_at.desc())
        )
        skills = skill_result.scalars().all()

        skill_assessments = []
        for skill in skills:
            skill_assessments.append({
                "skill": skill.skill,
                "score": skill.score,
                "assessedAt": skill.assessed_at.isoformat()
            })

        # Get preferences
        preferences = None
        if user.preferences:
            preferences = {
                "recentSearches": user.preferences.recent_searches or [],
                "favoriteTopics": user.preferences.favorite_topics or [],
                "timezone": user.preferences.timezone
            }

        return UserProfileResponse(
            profile=UserResponse(
                id=str(user.id),
                userId=user.user_id,
                email=user.email,
                firstName=user.first_name,
                lastName=user.last_name,
                profileImage=user.profile_image,
                role=user.role,
                experience=user.experience,
                createdAt=user.created_at,
                updatedAt=user.updated_at
            ),
            sessionHistory=session_history,
            skillAssessments=skill_assessments,
            favorites=[],  # TODO: Implement favorites functionality
            preferences=preferences
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.get("/users/{user_id}/analytics",
           response_model=UserAnalytics,
           summary="Get user analytics and dashboard data",
           description="Get comprehensive analytics data for user dashboard")
async def get_user_analytics(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user analytics data"""
    try:
        # Verify user exists
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get session statistics
        stats_result = await db.execute(
            select(
                func.count(Session.id).label('total_interviews'),
                func.count(Session.id).filter(Session.status == 'completed').label('completed_count'),
                func.count(Session.id).filter(Session.status == 'pending').label('upcoming_count'),
                func.avg(Session.rating).filter(Session.rating.isnot(None)).label('average_score'),
                func.sum(Session.duration).filter(Session.status == 'completed').label('total_hours')
            )
            .where(Session.user_id == user.id)
        )
        stats = stats_result.first()

        # Get progress data (mock data for now - implement actual logic)
        progress_data = [
            {"month": "2024-01", "score": 3.5, "interviews": 5},
            {"month": "2024-02", "score": 4.0, "interviews": 7},
            {"month": "2024-03", "score": 4.2, "interviews": 8}
        ]

        # Get skill assessments
        skill_result = await db.execute(
            select(SkillAssessment)
            .where(SkillAssessment.user_id == user.id)
            .order_by(SkillAssessment.assessed_at.desc())
            .limit(10)
        )
        skills = skill_result.scalars().all()

        skill_assessments = []
        for skill in skills:
            skill_assessments.append({
                "skill": skill.skill,
                "score": skill.score,
                "assessedAt": skill.assessed_at.isoformat()
            })

        # Get upcoming interviews
        upcoming_result = await db.execute(
            select(Session)
            .where(
                and_(
                    Session.user_id == user.id,
                    Session.status.in_(['pending', 'confirmed'])
                )
            )
            .order_by(Session.scheduled_at)
            .limit(5)
        )
        upcoming_sessions = upcoming_result.scalars().all()

        upcoming_interviews = []
        for session in upcoming_sessions:
            upcoming_interviews.append({
                "id": str(session.id),
                "mentorName": "Mentor Name",  # TODO: Join with mentor table
                "company": "Company",  # TODO: Join with mentor table
                "title": session.session_type,
                "scheduledAt": session.scheduled_at.isoformat(),
                "type": session.session_type,
                "difficulty": "Medium"  # TODO: Implement difficulty system
            })

        # Recent activity (mock data)
        recent_activity = [
            {
                "type": "session_completed",
                "description": "Completed interview with Senior Engineer",
                "date": "2024-01-15T10:00:00Z",
                "metadata": {"rating": 4}
            }
        ]

        return UserAnalytics(
            stats={
                "totalInterviews": stats.total_interviews or 0,
                "completedCount": stats.completed_count or 0,
                "upcomingCount": stats.upcoming_count or 0,
                "averageScore": float(stats.average_score or 0),
                "totalHoursSpent": int((stats.total_hours or 0) / 60)  # Convert minutes to hours
            },
            progressData=progress_data,
            skillAssessments=skill_assessments,
            upcomingInterviews=upcoming_interviews,
            recentActivity=recent_activity
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user analytics: {str(e)}"
        )