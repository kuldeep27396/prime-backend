"""
Enterprise admin service for multi-tenant management and advanced features
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import uuid
import json
import csv
import io
import zipfile

from app.models.company import Company, User
from app.models.admin import (
    Role, UserRole, CompanyBranding, Template, ReviewComment, 
    DataExportRequest, PermissionType
)
from app.models.job import Job
from app.models.interview import Interview, Application
from app.core.exceptions import ValidationError, NotFoundError, PermissionError


class AdminService:
    """Service for enterprise admin operations"""

    def __init__(self, db: Session):
        self.db = db

    # Role and Permission Management
    def create_role(self, company_id: uuid.UUID, name: str, description: str, 
                   permissions: List[str], created_by: uuid.UUID) -> Role:
        """Create a new role with permissions"""
        # Validate permissions
        valid_permissions = [p.value for p in PermissionType]
        invalid_permissions = [p for p in permissions if p not in valid_permissions]
        if invalid_permissions:
            raise ValidationError(f"Invalid permissions: {invalid_permissions}")

        # Check if role name already exists in company
        existing_role = self.db.query(Role).filter(
            and_(Role.company_id == company_id, Role.name == name)
        ).first()
        if existing_role:
            raise ValidationError(f"Role '{name}' already exists")

        role = Role(
            company_id=company_id,
            name=name,
            description=description,
            permissions=permissions
        )
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        # Log the action
        self._log_admin_action(created_by, "role_created", "role", str(role.id), {
            "role_name": name,
            "permissions_count": len(permissions)
        })
        
        return role

    def update_role(self, role_id: uuid.UUID, name: Optional[str] = None,
                   description: Optional[str] = None, permissions: Optional[List[str]] = None,
                   updated_by: uuid.UUID = None) -> Role:
        """Update role details and permissions"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError("Role not found")

        if role.is_system_role:
            raise PermissionError("Cannot modify system role")

        if name:
            role.name = name
        if description is not None:
            role.description = description
        if permissions is not None:
            # Validate permissions
            valid_permissions = [p.value for p in PermissionType]
            invalid_permissions = [p for p in permissions if p not in valid_permissions]
            if invalid_permissions:
                raise ValidationError(f"Invalid permissions: {invalid_permissions}")
            role.permissions = permissions

        self.db.commit()
        self.db.refresh(role)
        
        if updated_by:
            self._log_admin_action(updated_by, "role_updated", "role", str(role.id), {
                "role_name": role.name
            })
        
        return role

    def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID,
                           granted_by: uuid.UUID, expires_at: Optional[datetime] = None,
                           resource_type: Optional[str] = None,
                           resource_id: Optional[str] = None) -> UserRole:
        """Assign role to user"""
        # Check if assignment already exists
        existing = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.resource_type == resource_type,
                UserRole.resource_id == resource_id
            )
        ).first()
        
        if existing:
            raise ValidationError("Role already assigned to user")

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by,
            expires_at=expires_at,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        
        self._log_admin_action(granted_by, "role_assigned", "user", str(user_id), {
            "role_id": str(role_id),
            "expires_at": expires_at.isoformat() if expires_at else None
        })
        
        return user_role

    def revoke_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID,
                             revoked_by: uuid.UUID) -> bool:
        """Revoke role from user"""
        user_role = self.db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        
        if not user_role:
            raise NotFoundError("Role assignment not found")

        self.db.delete(user_role)
        self.db.commit()
        
        self._log_admin_action(revoked_by, "role_revoked", "user", str(user_id), {
            "role_id": str(role_id)
        })
        
        return True

    def get_user_permissions(self, user_id: uuid.UUID) -> List[str]:
        """Get all permissions for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        return user.get_permissions()

    # Company Branding Management
    def update_company_branding(self, company_id: uuid.UUID, branding_data: Dict[str, Any],
                               updated_by: uuid.UUID) -> CompanyBranding:
        """Update company branding configuration"""
        branding = self.db.query(CompanyBranding).filter(
            CompanyBranding.company_id == company_id
        ).first()
        
        if not branding:
            branding = CompanyBranding(company_id=company_id)
            self.db.add(branding)

        # Update branding fields
        for field, value in branding_data.items():
            if hasattr(branding, field):
                setattr(branding, field, value)

        self.db.commit()
        self.db.refresh(branding)
        
        self._log_admin_action(updated_by, "branding_updated", "company", str(company_id), {
            "updated_fields": list(branding_data.keys())
        })
        
        return branding

    def verify_custom_domain(self, company_id: uuid.UUID, domain: str) -> bool:
        """Verify custom domain ownership (mock implementation)"""
        # In production, this would verify DNS records or SSL certificates
        branding = self.db.query(CompanyBranding).filter(
            CompanyBranding.company_id == company_id
        ).first()
        
        if branding and branding.custom_domain == domain:
            branding.domain_verified = True
            self.db.commit()
            return True
        
        return False

    # Template Library Management
    def create_template(self, company_id: Optional[uuid.UUID], name: str, 
                       template_type: str, content: Dict[str, Any],
                       created_by: uuid.UUID, **kwargs) -> Template:
        """Create a new template"""
        template = Template(
            company_id=company_id,
            name=name,
            type=template_type,
            content=content,
            created_by=created_by,
            **kwargs
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        self._log_admin_action(created_by, "template_created", "template", str(template.id), {
            "template_name": name,
            "template_type": template_type
        })
        
        return template

    def get_templates(self, company_id: Optional[uuid.UUID] = None, 
                     template_type: Optional[str] = None,
                     include_public: bool = True) -> List[Template]:
        """Get templates for company or public templates"""
        query = self.db.query(Template)
        
        if company_id:
            if include_public:
                query = query.filter(
                    or_(Template.company_id == company_id, Template.is_public == True)
                )
            else:
                query = query.filter(Template.company_id == company_id)
        else:
            query = query.filter(Template.is_public == True)
        
        if template_type:
            query = query.filter(Template.type == template_type)
        
        return query.order_by(Template.is_featured.desc(), Template.usage_count.desc()).all()

    def clone_template(self, template_id: uuid.UUID, company_id: uuid.UUID,
                      cloned_by: uuid.UUID, new_name: Optional[str] = None) -> Template:
        """Clone a template for company use"""
        original = self.db.query(Template).filter(Template.id == template_id).first()
        if not original:
            raise NotFoundError("Template not found")

        # Check if user can access this template
        if original.company_id and original.company_id != company_id and not original.is_public:
            raise PermissionError("Cannot access this template")

        cloned = Template(
            company_id=company_id,
            name=new_name or f"{original.name} (Copy)",
            description=original.description,
            type=original.type,
            category=original.category,
            content=original.content.copy(),
            template_metadata=original.template_metadata.copy(),
            parent_template_id=template_id,
            created_by=cloned_by
        )
        
        self.db.add(cloned)
        self.db.commit()
        self.db.refresh(cloned)
        
        # Update usage count of original
        original.usage_count += 1
        self.db.commit()
        
        return cloned

    # Collaborative Review System
    def add_review_comment(self, resource_type: str, resource_id: uuid.UUID,
                          content: str, author_id: uuid.UUID,
                          parent_comment_id: Optional[uuid.UUID] = None,
                          rating: Optional[int] = None,
                          tags: Optional[List[str]] = None,
                          is_private: bool = False) -> ReviewComment:
        """Add a review comment"""
        # Determine thread ID
        thread_id = parent_comment_id
        if parent_comment_id:
            parent = self.db.query(ReviewComment).filter(
                ReviewComment.id == parent_comment_id
            ).first()
            if parent:
                thread_id = parent.thread_id or parent.id

        comment = ReviewComment(
            resource_type=resource_type,
            resource_id=resource_id,
            content=content,
            author_id=author_id,
            parent_comment_id=parent_comment_id,
            thread_id=thread_id,
            rating=rating,
            tags=tags or [],
            is_private=is_private
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        return comment

    def get_review_comments(self, resource_type: str, resource_id: uuid.UUID,
                           user_id: Optional[uuid.UUID] = None) -> List[ReviewComment]:
        """Get review comments for a resource"""
        query = self.db.query(ReviewComment).filter(
            and_(
                ReviewComment.resource_type == resource_type,
                ReviewComment.resource_id == resource_id
            )
        )
        
        # Filter private comments
        if user_id:
            query = query.filter(
                or_(
                    ReviewComment.is_private == False,
                    ReviewComment.author_id == user_id
                )
            )
        else:
            query = query.filter(ReviewComment.is_private == False)
        
        return query.order_by(ReviewComment.created_at.asc()).all()

    # Data Export and Reporting
    def create_export_request(self, company_id: uuid.UUID, export_type: str,
                             format: str, filters: Dict[str, Any],
                             requested_by: uuid.UUID) -> DataExportRequest:
        """Create a data export request"""
        export_request = DataExportRequest(
            company_id=company_id,
            export_type=export_type,
            format=format,
            filters=filters,
            requested_by=requested_by,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Expire in 7 days
        )
        
        self.db.add(export_request)
        self.db.commit()
        self.db.refresh(export_request)
        
        # Queue background job to process export
        # In production, this would use Celery
        self._process_export_request(export_request.id)
        
        return export_request

    def _process_export_request(self, export_request_id: uuid.UUID):
        """Process data export request (mock implementation)"""
        export_request = self.db.query(DataExportRequest).filter(
            DataExportRequest.id == export_request_id
        ).first()
        
        if not export_request:
            return

        try:
            export_request.status = "processing"
            self.db.commit()

            # Generate export data based on type
            if export_request.export_type == "candidates":
                data = self._export_candidates(export_request.company_id, export_request.filters)
            elif export_request.export_type == "interviews":
                data = self._export_interviews(export_request.company_id, export_request.filters)
            elif export_request.export_type == "analytics":
                data = self._export_analytics(export_request.company_id, export_request.filters)
            else:
                raise ValueError(f"Unknown export type: {export_request.export_type}")

            # Convert to requested format
            file_content = self._convert_export_format(data, export_request.format)
            
            # In production, upload to blob storage
            export_request.file_url = f"/api/v1/admin/exports/{export_request.id}/download"
            export_request.file_size = len(file_content)
            export_request.status = "completed"
            export_request.completed_at = datetime.utcnow()
            
        except Exception as e:
            export_request.status = "failed"
            export_request.error_message = str(e)
            export_request.retry_count += 1
        
        self.db.commit()

    def _export_candidates(self, company_id: uuid.UUID, filters: Dict[str, Any]) -> List[Dict]:
        """Export candidate data"""
        # Mock implementation - in production, this would query actual candidate data
        return [
            {
                "id": str(uuid.uuid4()),
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
        ]

    def _export_interviews(self, company_id: uuid.UUID, filters: Dict[str, Any]) -> List[Dict]:
        """Export interview data"""
        # Mock implementation
        return [
            {
                "id": str(uuid.uuid4()),
                "candidate_name": "John Doe",
                "position": "Software Engineer",
                "status": "completed",
                "score": 85,
                "conducted_at": datetime.utcnow().isoformat()
            }
        ]

    def _export_analytics(self, company_id: uuid.UUID, filters: Dict[str, Any]) -> List[Dict]:
        """Export analytics data"""
        # Mock implementation
        return [
            {
                "metric": "total_candidates",
                "value": 150,
                "period": "last_30_days"
            },
            {
                "metric": "interview_completion_rate",
                "value": 0.85,
                "period": "last_30_days"
            }
        ]

    def _convert_export_format(self, data: List[Dict], format: str) -> bytes:
        """Convert data to requested format"""
        if format == "json":
            return json.dumps(data, indent=2).encode('utf-8')
        elif format == "csv":
            if not data:
                return b""
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue().encode('utf-8')
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_company_analytics(self, company_id: uuid.UUID, 
                             date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Get comprehensive company analytics"""
        # Mock implementation - in production, this would calculate real metrics
        return {
            "overview": {
                "total_jobs": 25,
                "total_candidates": 150,
                "total_interviews": 89,
                "hire_rate": 0.12
            },
            "funnel": {
                "applications": 150,
                "screening": 89,
                "interviews": 45,
                "offers": 18,
                "hires": 12
            },
            "performance": {
                "avg_time_to_hire": 21,  # days
                "interview_completion_rate": 0.85,
                "candidate_satisfaction": 4.2,
                "cost_per_hire": 2500
            },
            "trends": {
                "applications_trend": [120, 135, 150],  # Last 3 months
                "hire_rate_trend": [0.10, 0.11, 0.12]
            }
        }

    def _log_admin_action(self, user_id: uuid.UUID, action: str, 
                         resource_type: str, resource_id: str, 
                         details: Dict[str, Any]):
        """Log admin action for audit trail"""
        from app.models.audit import AuditLog
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        
        self.db.add(audit_log)
        # Don't commit here - let the calling method handle it

    # System Management
    def create_default_roles(self, company_id: uuid.UUID) -> List[Role]:
        """Create default roles for a new company"""
        default_roles = [
            {
                "name": "Admin",
                "description": "Full system access",
                "permissions": [p.value for p in PermissionType],
                "is_system_role": True
            },
            {
                "name": "Recruiter",
                "description": "Recruitment and candidate management",
                "permissions": [
                    PermissionType.JOB_CREATE.value,
                    PermissionType.JOB_READ.value,
                    PermissionType.JOB_UPDATE.value,
                    PermissionType.CANDIDATE_CREATE.value,
                    PermissionType.CANDIDATE_READ.value,
                    PermissionType.CANDIDATE_UPDATE.value,
                    PermissionType.INTERVIEW_CREATE.value,
                    PermissionType.INTERVIEW_READ.value,
                    PermissionType.INTERVIEW_CONDUCT.value,
                    PermissionType.ANALYTICS_VIEW.value
                ]
            },
            {
                "name": "Interviewer",
                "description": "Interview and assessment access",
                "permissions": [
                    PermissionType.CANDIDATE_READ.value,
                    PermissionType.INTERVIEW_READ.value,
                    PermissionType.INTERVIEW_CONDUCT.value,
                    PermissionType.ASSESSMENT_READ.value,
                    PermissionType.ASSESSMENT_GRADE.value
                ]
            }
        ]
        
        created_roles = []
        for role_data in default_roles:
            role = Role(
                company_id=company_id,
                **role_data
            )
            self.db.add(role)
            created_roles.append(role)
        
        self.db.commit()
        return created_roles