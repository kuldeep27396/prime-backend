#!/usr/bin/env python3
"""
Database setup and test script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.company import Company, User
from app.services.auth_service import AuthService
from app.schemas.auth import CompanyCreate, UserCreate
from sqlalchemy.orm import sessionmaker
import uuid

def setup_database():
    """Create database tables"""
    print("Setting up database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    print("Testing database operations...")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test auth service
        auth_service = AuthService(db)
        
        # Create a test company
        company_data = CompanyCreate(
            name="Test Company",
            domain="test.com"
        )
        company = auth_service.create_company(company_data)
        print(f"✓ Created company: {company.name}")
        
        # Create a test user
        user_data = UserCreate(
            email="admin@test.com",
            password="AdminPassword123",
            role="admin",
            company_id=company.id
        )
        user = auth_service.create_user(user_data)
        print(f"✓ Created user: {user.email}")
        
        # Test authentication
        authenticated_user = auth_service.authenticate_user("admin@test.com", "AdminPassword123")
        assert authenticated_user is not None, "Authentication failed"
        print("✓ User authentication works")
        
        # Test token creation
        token_data = auth_service.create_access_token_for_user(authenticated_user)
        assert "access_token" in token_data, "Token creation failed"
        print("✓ Token creation works")
        
        # Clean up
        db.delete(user)
        db.delete(company)
        db.commit()
        print("✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Database operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Run database setup and tests"""
    print("Running database setup and tests...\n")
    
    try:
        # Setup database
        if not setup_database():
            return False
        
        # Test database operations
        if not test_database_operations():
            return False
        
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)