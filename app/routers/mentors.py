from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid

from app.database import get_db
from app.database.models import Mentor, User, Review, Session
from app.schemas.mentor import (
    MentorListResponse, MentorResponse, MentorDetailResponse,
    MentorFilters, PaginationResponse, FilterOptions, ReviewResponse
)
from app.schemas.common import ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user_optional

router = APIRouter(prefix="/api", tags=["Mentors"])

@router.get("/mentors",
           response_model=MentorListResponse,
           summary="Get paginated list of mentors with filtering",
           description="Get a paginated list of mentors with advanced filtering options")
async def get_mentors(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    companies: Optional[str] = Query(None, description="Comma-separated companies"),
    rating_min: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    experience_min: Optional[int] = Query(None, ge=0, description="Minimum experience years"),
    languages: Optional[str] = Query(None, description="Comma-separated languages"),
    search: Optional[str] = Query(None, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get paginated list of mentors with filtering"""
    try:
        # Build base query
        query = select(Mentor).where(Mentor.is_active == True)
        count_query = select(func.count()).select_from(Mentor).where(Mentor.is_active == True)

        # Apply filters
        conditions = []

        if skills:
            skill_list = [skill.strip() for skill in skills.split(',')]
            # PostgreSQL JSONB array contains any of the skills
            for skill in skill_list:
                conditions.append(
                    text("mentors.skills @> :skill").bindparam(skill=f'["{skill}"]')
                )

        if companies:
            company_list = [company.strip() for company in companies.split(',')]
            company_conditions = []
            for company in company_list:
                company_conditions.extend([
                    Mentor.current_company.ilike(f"%{company}%"),
                    text("mentors.previous_companies @> :company").bindparam(company=f'["{company}"]')
                ])
            if company_conditions:
                conditions.append(or_(*company_conditions))

        if rating_min is not None:
            conditions.append(Mentor.rating >= rating_min)

        if price_min is not None:
            conditions.append(Mentor.hourly_rate >= price_min)

        if price_max is not None:
            conditions.append(Mentor.hourly_rate <= price_max)

        if experience_min is not None:
            conditions.append(Mentor.experience >= experience_min)

        if languages:
            language_list = [lang.strip() for lang in languages.split(',')]
            for language in language_list:
                conditions.append(
                    text("mentors.languages @> :language").bindparam(language=f'["{language}"]')
                )

        if search:
            search_conditions = [
                Mentor.name.ilike(f"%{search}%"),
                Mentor.title.ilike(f"%{search}%"),
                Mentor.bio.ilike(f"%{search}%"),
                Mentor.current_company.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Order by rating and review count
        query = query.order_by(Mentor.rating.desc(), Mentor.review_count.desc())

        # Execute query
        result = await db.execute(query)
        mentors = result.scalars().all()

        # Convert to response format
        mentor_responses = []
        for mentor in mentors:
            mentor_responses.append(MentorResponse(
                id=str(mentor.id),
                userId=str(mentor.user_id),
                name=mentor.name,
                title=mentor.title,
                currentCompany=mentor.current_company,
                previousCompanies=mentor.previous_companies or [],
                avatar=mentor.avatar,
                bio=mentor.bio,
                specialties=mentor.specialties or [],
                skills=mentor.skills or [],
                languages=mentor.languages or [],
                experience=mentor.experience,
                rating=float(mentor.rating),
                reviewCount=mentor.review_count,
                hourlyRate=float(mentor.hourly_rate),
                responseTime=mentor.response_time,
                timezone=mentor.timezone,
                availability=mentor.availability or [],
                isActive=mentor.is_active,
                createdAt=mentor.created_at,
                updatedAt=mentor.updated_at
            ))

        # Calculate pagination
        total_pages = (total + limit - 1) // limit

        # Get filter options (aggregated data)
        filter_options = await get_filter_options(db)

        return MentorListResponse(
            mentors=mentor_responses,
            pagination=PaginationResponse(
                page=page,
                limit=limit,
                total=total,
                totalPages=total_pages
            ),
            filters=filter_options
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch mentors: {str(e)}"
        )

@router.get("/mentors/{mentor_id}",
           response_model=MentorDetailResponse,
           summary="Get detailed mentor profile",
           description="Get detailed mentor profile including reviews and availability")
async def get_mentor_detail(
    mentor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get detailed mentor profile"""
    try:
        # Get mentor with reviews
        result = await db.execute(
            select(Mentor)
            .options(selectinload(Mentor.reviews))
            .where(and_(Mentor.id == mentor_id, Mentor.is_active == True))
        )
        mentor = result.scalar_one_or_none()

        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found"
            )

        # Get reviews with user information
        reviews_result = await db.execute(
            select(Review, User)
            .join(User, Review.user_id == User.id)
            .where(and_(Review.mentor_id == mentor.id, Review.is_public == True))
            .order_by(Review.created_at.desc())
            .limit(10)
        )
        reviews_data = reviews_result.all()

        reviews = []
        for review, user in reviews_data:
            reviews.append(ReviewResponse(
                id=str(review.id),
                userId=str(review.user_id),
                userName=f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else "Anonymous",
                rating=review.rating,
                comment=review.comment,
                date=review.created_at,
                sessionType="Interview"  # TODO: Get from session
            ))

        # TODO: Implement upcoming slots logic
        upcoming_slots = ["2024-01-20T10:00:00Z", "2024-01-20T14:00:00Z"]

        # TODO: Implement availability check
        is_available = True

        return MentorDetailResponse(
            id=str(mentor.id),
            userId=str(mentor.user_id),
            name=mentor.name,
            title=mentor.title,
            currentCompany=mentor.current_company,
            previousCompanies=mentor.previous_companies or [],
            avatar=mentor.avatar,
            bio=mentor.bio,
            specialties=mentor.specialties or [],
            skills=mentor.skills or [],
            languages=mentor.languages or [],
            experience=mentor.experience,
            rating=float(mentor.rating),
            reviewCount=mentor.review_count,
            hourlyRate=float(mentor.hourly_rate),
            responseTime=mentor.response_time,
            timezone=mentor.timezone,
            availability=mentor.availability or [],
            isActive=mentor.is_active,
            createdAt=mentor.created_at,
            updatedAt=mentor.updated_at,
            reviews=reviews,
            upcomingSlots=upcoming_slots,
            isAvailable=is_available
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch mentor details: {str(e)}"
        )

async def get_filter_options(db: AsyncSession) -> FilterOptions:
    """Get available filter options for mentors"""
    try:
        # Get unique skills (aggregated from JSONB)
        skills_result = await db.execute(
            text("SELECT DISTINCT jsonb_array_elements_text(skills) as skill FROM mentors WHERE is_active = true AND skills IS NOT NULL")
        )
        available_skills = [row.skill for row in skills_result]

        # Get unique companies
        companies_result = await db.execute(
            select(Mentor.current_company)
            .where(and_(Mentor.is_active == True, Mentor.current_company.isnot(None)))
            .distinct()
        )
        available_companies = [row.current_company for row in companies_result]

        # Get unique languages
        languages_result = await db.execute(
            text("SELECT DISTINCT jsonb_array_elements_text(languages) as language FROM mentors WHERE is_active = true AND languages IS NOT NULL")
        )
        available_languages = [row.language for row in languages_result]

        # Get price range
        price_result = await db.execute(
            select(
                func.min(Mentor.hourly_rate).label('min_price'),
                func.max(Mentor.hourly_rate).label('max_price')
            )
            .where(Mentor.is_active == True)
        )
        price_range = price_result.first()

        # Get experience range
        exp_result = await db.execute(
            select(
                func.min(Mentor.experience).label('min_exp'),
                func.max(Mentor.experience).label('max_exp')
            )
            .where(Mentor.is_active == True)
        )
        experience_range = exp_result.first()

        return FilterOptions(
            availableSkills=sorted(available_skills) if available_skills else [],
            availableCompanies=sorted(available_companies) if available_companies else [],
            availableLanguages=sorted(available_languages) if available_languages else [],
            priceRange={
                "min": float(price_range.min_price or 0),
                "max": float(price_range.max_price or 500)
            },
            experienceRange={
                "min": int(experience_range.min_exp or 0),
                "max": int(experience_range.max_exp or 20)
            }
        )

    except Exception as e:
        # Return default options if query fails
        return FilterOptions(
            availableSkills=[],
            availableCompanies=[],
            availableLanguages=[],
            priceRange={"min": 0, "max": 500},
            experienceRange={"min": 0, "max": 20}
        )