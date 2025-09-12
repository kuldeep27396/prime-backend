"""
Simple test for admin models and basic functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_admin_models():
    """Test admin models can be imported and instantiated"""
    try:
        from app.models.admin import (
            Role, UserRole, CompanyBranding, Template, 
            ReviewComment, DataExportRequest, PermissionType
        )
        from app.models.company import Company, User
        
        print("✓ All admin models imported successfully")
        
        # Test PermissionType enum
        permissions = [p.value for p in PermissionType]
        print(f"✓ Found {len(permissions)} permission types")
        print(f"  Sample permissions: {permissions[:5]}")
        
        # Test model instantiation (without database)
        company_id = "550e8400-e29b-41d4-a716-446655440000"
        
        role = Role(
            company_id=company_id,
            name="Test Role",
            description="Test role description",
            permissions=[PermissionType.JOB_READ.value, PermissionType.CANDIDATE_READ.value]
        )
        print(f"✓ Created role: {role.name}")
        
        branding = CompanyBranding(
            company_id=company_id,
            primary_color="#3B82F6",
            secondary_color="#64748B"
        )
        print(f"✓ Created branding with colors: {branding.primary_color}, {branding.secondary_color}")
        
        template = Template(
            company_id=company_id,
            name="Test Template",
            type="interview",
            content={"questions": [{"text": "Tell me about yourself"}]}
        )
        print(f"✓ Created template: {template.name}")
        
        comment = ReviewComment(
            resource_type="candidate",
            resource_id="550e8400-e29b-41d4-a716-446655440001",
            content="Great candidate!",
            author_id="550e8400-e29b-41d4-a716-446655440002"
        )
        print(f"✓ Created review comment: {comment.content}")
        
        export_request = DataExportRequest(
            company_id=company_id,
            export_type="candidates",
            format="csv",
            requested_by="550e8400-e29b-41d4-a716-446655440002"
        )
        print(f"✓ Created export request: {export_request.export_type}")
        
        print("\n🎉 All admin models work correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing admin models: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_schemas():
    """Test admin schemas can be imported"""
    try:
        from app.schemas.admin import (
            RoleCreate, RoleResponse, CompanyBrandingUpdate,
            TemplateCreate, ReviewCommentCreate, DataExportCreate
        )
        
        print("✓ All admin schemas imported successfully")
        
        # Test schema validation
        role_data = RoleCreate(
            name="Test Role",
            description="Test description",
            permissions=["job:read", "candidate:read"]
        )
        print(f"✓ Created role schema: {role_data.name}")
        
        branding_data = CompanyBrandingUpdate(
            primary_color="#3B82F6",
            logo_url="https://example.com/logo.png"
        )
        print(f"✓ Created branding schema with color: {branding_data.primary_color}")
        
        template_data = TemplateCreate(
            name="Test Template",
            type="interview",
            content={"questions": []}
        )
        print(f"✓ Created template schema: {template_data.name}")
        
        print("\n🎉 All admin schemas work correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing admin schemas: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_permission_system():
    """Test the permission system logic"""
    try:
        from app.models.admin import Role, PermissionType
        
        # Create a role with permissions
        role = Role(
            company_id="550e8400-e29b-41d4-a716-446655440000",
            name="Recruiter",
            permissions=[
                PermissionType.JOB_READ.value,
                PermissionType.CANDIDATE_READ.value,
                PermissionType.INTERVIEW_CONDUCT.value
            ]
        )
        
        # Test permission checking
        assert role.has_permission(PermissionType.JOB_READ.value)
        assert role.has_permission(PermissionType.CANDIDATE_READ.value)
        assert not role.has_permission(PermissionType.ADMIN_SETTINGS.value)
        
        print("✓ Permission checking works correctly")
        
        # Test adding/removing permissions
        role.add_permission(PermissionType.ANALYTICS_VIEW.value)
        assert role.has_permission(PermissionType.ANALYTICS_VIEW.value)
        print("✓ Adding permissions works correctly")
        
        role.remove_permission(PermissionType.ANALYTICS_VIEW.value)
        assert not role.has_permission(PermissionType.ANALYTICS_VIEW.value)
        print("✓ Removing permissions works correctly")
        
        print("\n🎉 Permission system works correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing permission system: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing PRIME Admin Features\n")
    
    success = True
    success &= test_admin_models()
    print()
    success &= test_admin_schemas()
    print()
    success &= test_permission_system()
    
    if success:
        print("\n✅ All admin feature tests passed!")
    else:
        print("\n❌ Some admin feature tests failed!")
        sys.exit(1)