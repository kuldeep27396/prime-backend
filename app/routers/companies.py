"""
Company Management Router
B2B client company registration and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import uuid

from app.database import get_db
from app.database.models import Company, Job, Candidate, User, CompanyAnalytics
from app.schemas.company import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyWithStats,
    CompanyStats, CompanyCreateResponse, SuccessResponse
)
from app.auth.clerk_auth import get_current_user

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.post("",
            response_model=CompanyCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register a new company",
            description="Register a new B2B client company on the platform")
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register a new company"""
    try:
        # Check if company email already exists
        existing = await db.execute(
            select(Company).where(Company.email == company_data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A company with this email already exists"
            )
        
        # Create company
        company = Company(
            name=company_data.name,
            email=company_data.email,
            website=company_data.website,
            industry=company_data.industry,
            company_size=company_data.company_size,
            description=company_data.description,
            headquarters=company_data.headquarters,
            billing_email=company_data.billing_email or company_data.email,
            plan_type="free",
            credits_remaining=2,  # Free tier: 2 interviews
            credits_used=0
        )
        
        db.add(company)
        await db.commit()
        await db.refresh(company)
        
        # Link current user as company admin
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.company_id = company.id
            user.role = "company_admin"
            await db.commit()
        
        # Create analytics record
        analytics = CompanyAnalytics(company_id=company.id)
        db.add(analytics)
        await db.commit()
        
        return CompanyCreateResponse(
            success=True,
            message="Company registered successfully",
            company=CompanyResponse(
                id=str(company.id),
                name=company.name,
                email=company.email,
                website=company.website,
                industry=company.industry,
                company_size=company.company_size,
                description=company.description,
                headquarters=company.headquarters,
                logo_url=company.logo_url,
                plan_type=company.plan_type,
                credits_remaining=company.credits_remaining,
                credits_used=company.credits_used,
                is_active=company.is_active,
                onboarding_completed=company.onboarding_completed,
                created_at=company.created_at,
                updated_at=company.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company: {str(e)}"
        )


@router.get("/me",
           response_model=CompanyWithStats,
           summary="Get current user's company",
           description="Get the company associated with the current authenticated user")
async def get_my_company(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's company with stats"""
    try:
        # Get user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No company associated with this user"
            )
        
        # Get company
        company_result = await db.execute(
            select(Company).where(Company.id == user.company_id)
        )
        company = company_result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Get stats
        stats = await _get_company_stats(db, company.id)
        
        return CompanyWithStats(
            id=str(company.id),
            name=company.name,
            email=company.email,
            website=company.website,
            industry=company.industry,
            company_size=company.company_size,
            description=company.description,
            headquarters=company.headquarters,
            logo_url=company.logo_url,
            plan_type=company.plan_type,
            credits_remaining=company.credits_remaining,
            credits_used=company.credits_used,
            is_active=company.is_active,
            onboarding_completed=company.onboarding_completed,
            created_at=company.created_at,
            updated_at=company.updated_at,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company: {str(e)}"
        )


@router.get("/{company_id}",
           response_model=CompanyWithStats,
           summary="Get company by ID",
           description="Get company details and statistics by ID")
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get company by ID"""
    try:
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Verify user has access to this company
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != company_id and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )
        
        stats = await _get_company_stats(db, company.id)
        
        return CompanyWithStats(
            id=str(company.id),
            name=company.name,
            email=company.email,
            website=company.website,
            industry=company.industry,
            company_size=company.company_size,
            description=company.description,
            headquarters=company.headquarters,
            logo_url=company.logo_url,
            plan_type=company.plan_type,
            credits_remaining=company.credits_remaining,
            credits_used=company.credits_used,
            is_active=company.is_active,
            onboarding_completed=company.onboarding_completed,
            created_at=company.created_at,
            updated_at=company.updated_at,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company: {str(e)}"
        )


@router.patch("/{company_id}",
             response_model=SuccessResponse,
             summary="Update company details",
             description="Update company profile information")
async def update_company(
    company_id: str,
    update_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update company details"""
    try:
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != company_id and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )
        
        # Get company
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(company, key):
                setattr(company, key, value)
        
        await db.commit()
        
        return SuccessResponse(
            success=True,
            message="Company updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update company: {str(e)}"
        )


@router.get("/{company_id}/stats",
           response_model=CompanyStats,
           summary="Get company statistics",
           description="Get detailed statistics for a company")
async def get_company_stats(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get company statistics"""
    try:
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != company_id and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )
        
        # Get company to check credits
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return await _get_company_stats(db, uuid.UUID(company_id))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def _get_company_stats(db: AsyncSession, company_id: uuid.UUID) -> CompanyStats:
    """Get company statistics"""
    # Get job counts
    jobs_result = await db.execute(
        select(
            func.count(Job.id).label('total'),
            func.count(Job.id).filter(Job.status == 'active').label('active')
        ).where(Job.company_id == company_id)
    )
    jobs_stats = jobs_result.first()
    
    # Get candidate counts
    candidates_result = await db.execute(
        select(func.count(Candidate.id))
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.company_id == company_id)
    )
    total_candidates = candidates_result.scalar() or 0
    
    # Get interview and shortlist counts
    shortlisted_result = await db.execute(
        select(func.count(Candidate.id))
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(and_(Job.company_id == company_id, Candidate.shortlisted == True))
    )
    total_shortlisted = shortlisted_result.scalar() or 0
    
    # Get company credits
    company_result = await db.execute(
        select(Company.credits_remaining, Company.credits_used)
        .where(Company.id == company_id)
    )
    credits = company_result.first()
    
    return CompanyStats(
        total_jobs=jobs_stats.total if jobs_stats else 0,
        active_jobs=jobs_stats.active if jobs_stats else 0,
        total_candidates=total_candidates,
        total_interviews=0,  # TODO: Count from ai_interview_sessions
        total_shortlisted=total_shortlisted,
        credits_remaining=credits.credits_remaining if credits else 0,
        credits_used=credits.credits_used if credits else 0
    )
