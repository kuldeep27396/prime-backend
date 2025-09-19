from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, or_
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import Mentor, User, MentorAvailability, Review, Session, CompanyMentor, Company
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Mentors Extended"])

# Pydantic models
class MentorResponse(BaseModel):
    id: str
    name: str
    title: str
    current_company: str
    previous_companies: Optional[List[str]]
    avatar: Optional[str]
    bio: str
    specialties: List[str]
    skills: List[str]
    languages: List[str]
    experience: int
    rating: float
    review_count: int
    hourly_rate: Optional[float]
    response_time: Optional[str]
    timezone: Optional[str]
    availability: Optional[List[Dict[str, Any]]]
    is_active: bool

class MentorAvailabilityResponse(BaseModel):
    id: str
    day_of_week: int
    start_time: str
    end_time: str
    timezone: str
    is_available: bool
    recurring: bool

class MentorSearchRequest(BaseModel):
    skills: Optional[List[str]] = []
    specialties: Optional[List[str]] = []
    companies: Optional[List[str]] = []
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    hourly_rate_max: Optional[float] = None
    rating_min: Optional[float] = None
    timezone: Optional[str] = None
    languages: Optional[List[str]] = []
    search_query: Optional[str] = ""

class ReviewResponse(BaseModel):
    id: str
    rating: int
    comment: Optional[str]
    created_at: str
    user_name: str

@router.get("/mentors/search",
            response_model=List[MentorResponse],
            summary="Search mentors with filters",
            description="Search and filter mentors based on various criteria")
async def search_mentors(
    skills: Optional[List[str]] = Query(None, description="Filter by skills"),
    specialties: Optional[List[str]] = Query(None, description="Filter by specialties"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    experience_min: Optional[int] = Query(None, description="Minimum experience in years"),
    experience_max: Optional[int] = Query(None, description="Maximum experience in years"),
    hourly_rate_max: Optional[float] = Query(None, description="Maximum hourly rate"),
    rating_min: Optional[float] = Query(None, description="Minimum rating"),
    timezone: Optional[str] = Query(None, description="Filter by timezone"),
    languages: Optional[List[str]] = Query(None, description="Filter by languages"),
    search_query: Optional[str] = Query(None, description="Search in name, title, bio"),
    limit: int = Query(10, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Search mentors with advanced filters"""
    try:
        # Build base query
        query = select(Mentor).where(Mentor.is_active == True)

        # Apply filters
        if skills:
            for skill in skills:
                query = query.where(Mentor.skills.contains([skill]))

        if specialties:
            for specialty in specialties:
                query = query.where(Mentor.specialties.contains([specialty]))

        if companies:
            # Filter mentors who worked at specified companies
            query = query.where(or_(
                Mentor.current_company.in_(companies),
                Mentor.previous_companies.contains(companies)
            ))

        if experience_min is not None:
            query = query.where(Mentor.experience >= experience_min)

        if experience_max is not None:
            query = query.where(Mentor.experience <= experience_max)

        if hourly_rate_max is not None:
            query = query.where(
                (Mentor.hourly_rate <= hourly_rate_max) | (Mentor.hourly_rate.is_(None))
            )

        if rating_min is not None:
            query = query.where(Mentor.rating >= rating_min)

        if timezone:
            query = query.where(Mentor.timezone == timezone)

        if languages:
            for language in languages:
                query = query.where(Mentor.languages.contains([language]))

        if search_query:
            search_term = f"%{search_query.lower()}%"
            query = query.where(or_(
                func.lower(Mentor.name).like(search_term),
                func.lower(Mentor.title).like(search_term),
                func.lower(Mentor.bio).like(search_term)
            ))

        # Apply pagination and ordering
        query = query.order_by(Mentor.rating.desc(), Mentor.review_count.desc())
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        mentors = result.scalars().all()

        # Convert to response format
        mentor_responses = []
        for mentor in mentors:
            mentor_responses.append(MentorResponse(
                id=str(mentor.id),
                name=mentor.name,
                title=mentor.title,
                current_company=mentor.current_company,
                previous_companies=mentor.previous_companies,
                avatar=mentor.avatar,
                bio=mentor.bio,
                specialties=mentor.specialties or [],
                skills=mentor.skills or [],
                languages=mentor.languages or [],
                experience=mentor.experience,
                rating=float(mentor.rating),
                review_count=mentor.review_count,
                hourly_rate=float(mentor.hourly_rate) if mentor.hourly_rate else None,
                response_time=mentor.response_time,
                timezone=mentor.timezone,
                availability=mentor.availability,
                is_active=mentor.is_active
            ))

        return mentor_responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search mentors: {str(e)}"
        )

@router.get("/mentors/{mentor_id}/availability",
            response_model=List[MentorAvailabilityResponse],
            summary="Get mentor availability",
            description="Retrieve mentor's availability schedule")
async def get_mentor_availability(
    mentor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Get mentor availability"""
    try:
        # Check if mentor exists
        mentor_result = await db.execute(
            select(Mentor).where(Mentor.id == uuid.UUID(mentor_id))
        )
        mentor = mentor_result.scalar_one_or_none()

        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found"
            )

        # Get mentor availability
        availability_result = await db.execute(
            select(MentorAvailability)
            .where(MentorAvailability.mentor_id == uuid.UUID(mentor_id))
            .where(MentorAvailability.is_available == True)
            .order_by(MentorAvailability.day_of_week, MentorAvailability.start_time)
        )
        availability_slots = availability_result.scalars().all()

        return [
            MentorAvailabilityResponse(
                id=str(slot.id),
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                timezone=slot.timezone,
                is_available=slot.is_available,
                recurring=slot.recurring
            )
            for slot in availability_slots
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mentor availability: {str(e)}"
        )

@router.get("/mentors/{mentor_id}/reviews",
            response_model=List[ReviewResponse],
            summary="Get mentor reviews",
            description="Retrieve reviews for a specific mentor")
async def get_mentor_reviews(
    mentor_id: str,
    limit: int = Query(10, description="Maximum number of reviews"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get mentor reviews"""
    try:
        # Check if mentor exists
        mentor_result = await db.execute(
            select(Mentor).where(Mentor.id == uuid.UUID(mentor_id))
        )
        mentor = mentor_result.scalar_one_or_none()

        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found"
            )

        # Get mentor reviews
        reviews_result = await db.execute(
            select(Review, User)
            .join(User, Review.user_id == User.id)
            .where(Review.mentor_id == uuid.UUID(mentor_id))
            .where(Review.is_public == True)
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        reviews = []
        for review, user in reviews_result:
            reviews.append(ReviewResponse(
                id=str(review.id),
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at.isoformat(),
                user_name=f"{user.first_name} {user.last_name}".strip() or "Anonymous"
            ))

        return reviews

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mentor reviews: {str(e)}"
        )

@router.get("/mentors/{mentor_id}/stats",
            response_model=Dict[str, Any],
            summary="Get mentor statistics",
            description="Get comprehensive statistics for a mentor")
async def get_mentor_stats(
    mentor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get mentor statistics"""
    try:
        # Check if mentor exists
        mentor_result = await db.execute(
            select(Mentor).where(Mentor.id == uuid.UUID(mentor_id))
        )
        mentor = mentor_result.scalar_one_or_none()

        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found"
            )

        # Get session statistics
        session_stats = await db.execute(
            select(
                func.count(Session.id).label('total_sessions'),
                func.count(Session.id).filter(Session.status == 'completed').label('completed_sessions'),
                func.avg(Session.rating).label('average_rating')
            )
            .where(Session.mentor_id == uuid.UUID(mentor_id))
        )
        stats = session_stats.first()

        # Get review distribution
        review_distribution = await db.execute(
            select(
                Review.rating,
                func.count(Review.id).label('count')
            )
            .where(Review.mentor_id == uuid.UUID(mentor_id))
            .group_by(Review.rating)
        )

        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating, count in review_distribution:
            rating_distribution[rating] = count

        return {
            "mentor_id": mentor_id,
            "total_sessions": stats.total_sessions or 0,
            "completed_sessions": stats.completed_sessions or 0,
            "average_rating": float(stats.average_rating) if stats.average_rating else 0,
            "rating_distribution": rating_distribution,
            "experience_years": mentor.experience,
            "skills_count": len(mentor.skills or []),
            "specialties_count": len(mentor.specialties or []),
            "response_time": mentor.response_time,
            "is_available": mentor.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mentor stats: {str(e)}"
        )

@router.get("/mentors/companies",
            response_model=List[Dict[str, Any]],
            summary="Get companies with mentors",
            description="Get list of companies that have mentors available")
async def get_companies_with_mentors(
    db: AsyncSession = Depends(get_db)
):
    """Get companies with mentors"""
    try:
        # Get unique companies from mentors
        result = await db.execute(
            select(
                Mentor.current_company,
                func.count(Mentor.id).label('mentor_count'),
                func.avg(Mentor.rating).label('average_rating')
            )
            .where(Mentor.is_active == True)
            .where(Mentor.current_company.isnot(None))
            .group_by(Mentor.current_company)
            .order_by(func.count(Mentor.id).desc())
        )

        companies = []
        for company_name, mentor_count, avg_rating in result:
            companies.append({
                "name": company_name,
                "mentor_count": mentor_count,
                "average_rating": float(avg_rating) if avg_rating else 0
            })

        return companies

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get companies: {str(e)}"
        )

@router.get("/mentors/skills",
            response_model=List[Dict[str, Any]],
            summary="Get available skills",
            description="Get list of available skills from all mentors")
async def get_available_skills(
    db: AsyncSession = Depends(get_db)
):
    """Get available skills"""
    try:
        # Get all skills from mentors
        result = await db.execute(
            select(Mentor.skills).where(Mentor.is_active == True)
        )

        all_skills = []
        for skills_tuple in result:
            if skills_tuple[0]:  # skills is at index 0
                all_skills.extend(skills_tuple[0])

        # Count skill frequency
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Convert to sorted list
        sorted_skills = sorted(
            [{"skill": skill, "count": count} for skill, count in skill_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )

        return sorted_skills

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skills: {str(e)}"
        )

@router.get("/mentors/specialties",
            response_model=List[Dict[str, Any]],
            summary="Get available specialties",
            description="Get list of available specialties from all mentors")
async def get_available_specialties(
    db: AsyncSession = Depends(get_db)
):
    """Get available specialties"""
    try:
        # Get all specialties from mentors
        result = await db.execute(
            select(Mentor.specialties).where(Mentor.is_active == True)
        )

        all_specialties = []
        for specialties_tuple in result:
            if specialties_tuple[0]:  # specialties is at index 0
                all_specialties.extend(specialties_tuple[0])

        # Count specialty frequency
        specialty_counts = {}
        for specialty in all_specialties:
            specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

        # Convert to sorted list
        sorted_specialties = sorted(
            [{"specialty": specialty, "count": count} for specialty, count in specialty_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )

        return sorted_specialties

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get specialties: {str(e)}"
        )