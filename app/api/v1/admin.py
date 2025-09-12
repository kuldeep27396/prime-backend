"""
Enterprise admin API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_db, get_current_active_user, require_admin
from app.models.company import User
from app.services.admin_service import AdminService
from app.schemas.admin import (
    RoleCreate, RoleUpdate, RoleResponse, UserRoleAssignment,
    CompanyBrandingUpdate, CompanyBrandingResponse,
    TemplateCreate, TemplateResponse, TemplateClone,
    ReviewCommentCreate, ReviewCommentResponse,
    DataExportCreate, DataExportResponse,
    CompanyAnalyticsResponse
)

router = APIRouter(prefix="/admin", tags=["admin"])


# Role Management
@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new role with permissions"""
    admin_service = AdminService(db)
    
    try:
        role = admin_service.create_role(
            company_id=current_user.company_id,
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            created_by=current_user.id
        )
        return role
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all roles for the company"""
    from app.models.admin import Role
    
    roles = db.query(Role).filter(Role.company_id == current_user.company_id).all()
    return roles


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update role details and permissions"""
    admin_service = AdminService(db)
    
    try:
        role = admin_service.update_role(
            role_id=role_id,
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            updated_by=current_user.id
        )
        return role
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: uuid.UUID,
    assignment: UserRoleAssignment,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign role to user"""
    admin_service = AdminService(db)
    
    try:
        user_role = admin_service.assign_role_to_user(
            user_id=user_id,
            role_id=assignment.role_id,
            granted_by=current_user.id,
            expires_at=assignment.expires_at,
            resource_type=assignment.resource_type,
            resource_id=assignment.resource_id
        )
        return {"message": "Role assigned successfully", "id": str(user_role.id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}/roles/{role_id}")
async def revoke_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Revoke role from user"""
    admin_service = AdminService(db)
    
    try:
        admin_service.revoke_role_from_user(
            user_id=user_id,
            role_id=role_id,
            revoked_by=current_user.id
        )
        return {"message": "Role revoked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all permissions for a user"""
    admin_service = AdminService(db)
    
    try:
        permissions = admin_service.get_user_permissions(user_id)
        return {"permissions": permissions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Company Branding
@router.get("/branding", response_model=CompanyBrandingResponse)
async def get_company_branding(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get company branding configuration"""
    from app.models.admin import CompanyBranding
    
    branding = db.query(CompanyBranding).filter(
        CompanyBranding.company_id == current_user.company_id
    ).first()
    
    if not branding:
        # Return default branding
        return CompanyBrandingResponse(
            company_id=current_user.company_id,
            logo_url=None,
            favicon_url=None,
            primary_color="#3B82F6",
            secondary_color="#64748B",
            accent_color="#10B981",
            custom_domain=None,
            domain_verified=False,
            email_header_logo=None,
            email_footer_text=None,
            custom_css=None,
            features={}
        )
    
    return branding


@router.put("/branding", response_model=CompanyBrandingResponse)
async def update_company_branding(
    branding_data: CompanyBrandingUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update company branding configuration"""
    admin_service = AdminService(db)
    
    try:
        branding = admin_service.update_company_branding(
            company_id=current_user.company_id,
            branding_data=branding_data.dict(exclude_unset=True),
            updated_by=current_user.id
        )
        return branding
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/branding/verify-domain")
async def verify_custom_domain(
    domain: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verify custom domain ownership"""
    admin_service = AdminService(db)
    
    verified = admin_service.verify_custom_domain(
        company_id=current_user.company_id,
        domain=domain
    )
    
    return {"verified": verified}


# Template Library
@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new template"""
    admin_service = AdminService(db)
    
    try:
        template = admin_service.create_template(
            company_id=current_user.company_id,
            name=template_data.name,
            template_type=template_data.type,
            content=template_data.content,
            created_by=current_user.id,
            description=template_data.description,
            category=template_data.category,
            is_public=template_data.is_public
        )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    template_type: Optional[str] = Query(None),
    include_public: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get templates for company"""
    admin_service = AdminService(db)
    
    templates = admin_service.get_templates(
        company_id=current_user.company_id,
        template_type=template_type,
        include_public=include_public
    )
    return templates


@router.post("/templates/{template_id}/clone", response_model=TemplateResponse)
async def clone_template(
    template_id: uuid.UUID,
    clone_data: TemplateClone,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clone a template for company use"""
    admin_service = AdminService(db)
    
    try:
        template = admin_service.clone_template(
            template_id=template_id,
            company_id=current_user.company_id,
            cloned_by=current_user.id,
            new_name=clone_data.new_name
        )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Collaborative Reviews
@router.post("/reviews", response_model=ReviewCommentResponse)
async def add_review_comment(
    comment_data: ReviewCommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a review comment"""
    admin_service = AdminService(db)
    
    try:
        comment = admin_service.add_review_comment(
            resource_type=comment_data.resource_type,
            resource_id=comment_data.resource_id,
            content=comment_data.content,
            author_id=current_user.id,
            parent_comment_id=comment_data.parent_comment_id,
            rating=comment_data.rating,
            tags=comment_data.tags,
            is_private=comment_data.is_private
        )
        return comment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/reviews/{resource_type}/{resource_id}", response_model=List[ReviewCommentResponse])
async def get_review_comments(
    resource_type: str,
    resource_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get review comments for a resource"""
    admin_service = AdminService(db)
    
    comments = admin_service.get_review_comments(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=current_user.id
    )
    return comments


# Data Export and Analytics
@router.post("/exports", response_model=DataExportResponse)
async def create_export_request(
    export_data: DataExportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a data export request"""
    admin_service = AdminService(db)
    
    try:
        export_request = admin_service.create_export_request(
            company_id=current_user.company_id,
            export_type=export_data.export_type,
            format=export_data.format,
            filters=export_data.filters,
            requested_by=current_user.id
        )
        return export_request
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/exports", response_model=List[DataExportResponse])
async def get_export_requests(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get export requests for company"""
    from app.models.admin import DataExportRequest
    
    exports = db.query(DataExportRequest).filter(
        DataExportRequest.company_id == current_user.company_id
    ).order_by(DataExportRequest.created_at.desc()).all()
    
    return exports


@router.get("/analytics", response_model=CompanyAnalyticsResponse)
async def get_company_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive company analytics"""
    admin_service = AdminService(db)
    
    # Parse date range if provided
    date_range = None
    if date_from and date_to:
        from datetime import datetime
        try:
            date_range = (
                datetime.fromisoformat(date_from),
                datetime.fromisoformat(date_to)
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
            )
    
    analytics = admin_service.get_company_analytics(
        company_id=current_user.company_id,
        date_range=date_range
    )
    
    return analytics


# System Management
@router.post("/system/init-company")
async def initialize_company_defaults(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Initialize default roles and settings for company"""
    admin_service = AdminService(db)
    
    try:
        roles = admin_service.create_default_roles(current_user.company_id)
        return {
            "message": "Company defaults initialized successfully",
            "roles_created": len(roles)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )