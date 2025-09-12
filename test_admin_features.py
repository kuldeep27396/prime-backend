"""
Test script for enterprise admin features
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.admin_service import AdminService
from app.models.company import Company, User
from app.models.admin import Role, PermissionType
import uuid


async def test_admin_features():
    """Test the admin features"""
    db = SessionLocal()
    
    try:
        # Create a test company
        company = Company(
            name="Test Company",
            domain="test.com",
            settings={}
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        
        print(f"✓ Created test company: {company.name}")
        
        # Create admin service
        admin_service = AdminService(db)
        
        # Create default roles
        roles = admin_service.create_default_roles(company.id)
        print(f"✓ Created {len(roles)} default roles")
        
        # Create a custom role
        custom_role = admin_service.create_role(
            company_id=company.id,
            name="Senior Recruiter",
            description="Senior recruiter with advanced permissions",
            permissions=[
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
            ],
            created_by=uuid.uuid4()  # Mock user ID
        )
        print(f"✓ Created custom role: {custom_role.name}")
        
        # Test branding
        branding = admin_service.update_company_branding(
            company_id=company.id,
            branding_data={
                "primary_color": "#3B82F6",
                "secondary_color": "#64748B",
                "accent_color": "#10B981",
                "logo_url": "https://example.com/logo.png"
            },
            updated_by=uuid.uuid4()
        )
        print(f"✓ Updated company branding")
        
        # Test template creation
        template = admin_service.create_template(
            company_id=company.id,
            name="Technical Interview Template",
            template_type="interview",
            content={
                "questions": [
                    {
                        "id": "1",
                        "text": "Explain your experience with Python",
                        "type": "open_ended",
                        "time_limit": 300
                    },
                    {
                        "id": "2", 
                        "text": "Write a function to reverse a string",
                        "type": "coding",
                        "time_limit": 600
                    }
                ],
                "time_limit": 1800
            },
            created_by=uuid.uuid4(),
            description="Standard technical interview for software engineers",
            category="technical"
        )
        print(f"✓ Created template: {template.name}")
        
        # Test analytics
        analytics = admin_service.get_company_analytics(company.id)
        print(f"✓ Retrieved company analytics")
        print(f"  - Total jobs: {analytics['overview']['total_jobs']}")
        print(f"  - Total candidates: {analytics['overview']['total_candidates']}")
        print(f"  - Hire rate: {analytics['overview']['hire_rate']:.1%}")
        
        # Test export request
        export_request = admin_service.create_export_request(
            company_id=company.id,
            export_type="candidates",
            format="csv",
            filters={"status": "active"},
            requested_by=uuid.uuid4()
        )
        print(f"✓ Created export request: {export_request.export_type}")
        
        print("\n🎉 All admin features tested successfully!")
        
    except Exception as e:
        print(f"❌ Error testing admin features: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_admin_features())