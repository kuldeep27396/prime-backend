"""
Candidates API endpoints
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.company import User
from app.services.candidate_service import CandidateService
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateSearch,
    CandidateResponse, CandidateListResponse, CandidateSearchResponse,
    BulkImportResult, ApplicationCreate, ApplicationResponse
)

router = APIRouter()


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new candidate with optional resume upload"""
    
    candidate_data = CandidateCreate(
        name=name,
        email=email,
        phone=phone
    )
    
    service = CandidateService(db)
    return await service.create_candidate(candidate_data, resume_file)


@router.get("/", response_model=CandidateListResponse)
async def list_candidates(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all candidates with pagination"""
    
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters"
        )
    
    service = CandidateService(db)
    return await service.list_candidates(page, page_size)


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get candidate by ID"""
    
    service = CandidateService(db)
    return await service.get_candidate(candidate_id)


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: UUID,
    candidate_data: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update candidate information"""
    
    service = CandidateService(db)
    return await service.update_candidate(candidate_id, candidate_data)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete candidate"""
    
    # Only admins can delete candidates
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete candidates"
        )
    
    service = CandidateService(db)
    await service.delete_candidate(candidate_id)


@router.post("/search", response_model=CandidateSearchResponse)
async def search_candidates(
    search_params: CandidateSearch,
    job_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search candidates with advanced filtering and similarity matching"""
    
    service = CandidateService(db)
    return await service.search_candidates(search_params, job_id)


@router.post("/bulk-import", response_model=BulkImportResult)
async def bulk_import_candidates(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk import candidates from CSV, Excel, or JSON file"""
    
    # Only recruiters and admins can bulk import
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and administrators can bulk import candidates"
        )
    
    # Validate file type
    allowed_types = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload CSV, Excel, or JSON files."
        )
    
    # Determine file type
    file_type = "csv"
    if file.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_type = "xlsx"
    elif file.content_type == 'application/json':
        file_type = "json"
    
    # Read file content
    file_content = await file.read()
    
    service = CandidateService(db)
    return await service.bulk_import_candidates(file_content, file.filename, file_type)


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a job application for a candidate"""
    
    service = CandidateService(db)
    return await service.create_application(application_data)


@router.get("/{candidate_id}/applications", response_model=List[ApplicationResponse])
async def get_candidate_applications(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all applications for a specific candidate"""
    
    from app.models.job import Application
    
    # Verify candidate exists
    service = CandidateService(db)
    await service.get_candidate(candidate_id)  # This will raise 404 if not found
    
    # Get applications
    applications = db.query(Application).filter(
        Application.candidate_id == candidate_id
    ).all()
    
    return [
        ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            status=app.status,
            cover_letter=app.cover_letter,
            application_data=app.application_data,
            created_at=app.created_at,
            updated_at=app.updated_at
        )
        for app in applications
    ]