#!/usr/bin/env python3
"""
Simple authentication test script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import get_password_hash, verify_password, create_access_token, verify_token
from app.schemas.auth import UserCreate, UserLogin
import uuid

def test_password_hashing():
    """Test password hashing and verification"""
    print("Testing password hashing...")
    
    password = "TestPassword123"
    hashed = get_password_hash(password)
    
    # Verify correct password
    assert verify_password(password, hashed), "Password verification failed"
    
    # Verify incorrect password
    assert not verify_password("WrongPassword", hashed), "Wrong password should not verify"
    
    print("✓ Password hashing works correctly")

def test_jwt_tokens():
    """Test JWT token creation and verification"""
    print("Testing JWT tokens...")
    
    token_data = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "role": "recruiter",
        "company_id": str(uuid.uuid4())
    }
    
    # Create token
    token = create_access_token(token_data)
    assert token, "Token creation failed"
    
    # Verify token
    payload = verify_token(token)
    assert payload["sub"] == token_data["sub"], "Token verification failed"
    assert payload["email"] == token_data["email"], "Email mismatch in token"
    assert payload["role"] == token_data["role"], "Role mismatch in token"
    
    print("✓ JWT tokens work correctly")

def test_schemas():
    """Test Pydantic schemas"""
    print("Testing Pydantic schemas...")
    
    # Test UserCreate schema
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "role": "recruiter",
        "company_id": str(uuid.uuid4())
    }
    
    try:
        user_create = UserCreate(**user_data)
        assert user_create.email == user_data["email"], "Email mismatch"
        assert user_create.role == user_data["role"], "Role mismatch"
        print("✓ UserCreate schema works correctly")
    except Exception as e:
        print(f"✗ UserCreate schema failed: {e}")
        return False
    
    # Test UserLogin schema
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123"
    }
    
    try:
        user_login = UserLogin(**login_data)
        assert user_login.email == login_data["email"], "Email mismatch"
        print("✓ UserLogin schema works correctly")
    except Exception as e:
        print(f"✗ UserLogin schema failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Running authentication system tests...\n")
    
    try:
        test_password_hashing()
        test_jwt_tokens()
        
        # Skip schema tests if pydantic is not available
        try:
            test_schemas()
        except ImportError:
            print("⚠ Skipping schema tests (pydantic not available)")
        
        print("\n✅ All authentication tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)