"""
Authentication tests
"""

import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


def test_register_user(client: TestClient, test_company):
    """Test user registration"""
    user_data = {
        "email": "newuser@test.com",
        "password": "NewPassword123",
        "role": "recruiter",
        "company_id": str(test_company.id)
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]
    assert "id" in data
    assert "password_hash" not in data  # Password should not be returned


def test_register_user_invalid_password(client: TestClient, test_company):
    """Test user registration with invalid password"""
    user_data = {
        "email": "newuser@test.com",
        "password": "weak",  # Too weak password
        "role": "recruiter",
        "company_id": str(test_company.id)
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_register_duplicate_email(client: TestClient, test_user, test_company):
    """Test registration with duplicate email"""
    user_data = {
        "email": test_user.email,  # Duplicate email
        "password": "NewPassword123",
        "role": "recruiter",
        "company_id": str(test_company.id)
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400


def test_login_success(client: TestClient, test_user):
    """Test successful login"""
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert data["user"]["email"] == test_user.email


def test_login_invalid_credentials(client: TestClient, test_user):
    """Test login with invalid credentials"""
    login_data = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user"""
    login_data = {
        "email": "nonexistent@test.com",
        "password": "somepassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_user):
    """Test getting current user info"""
    # Create access token
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role,
        "company_id": str(test_user.company_id)
    }
    access_token = create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # No credentials provided


def test_password_reset_request(client: TestClient, test_user):
    """Test password reset request"""
    reset_data = {"email": test_user.email}
    
    response = client.post("/api/v1/auth/password-reset", json=reset_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "reset_token" in data  # This should be removed in production


def test_password_reset_nonexistent_email(client: TestClient):
    """Test password reset for nonexistent email"""
    reset_data = {"email": "nonexistent@test.com"}
    
    response = client.post("/api/v1/auth/password-reset", json=reset_data)
    assert response.status_code == 200  # Should not reveal if email exists


def test_create_company(client: TestClient):
    """Test company creation"""
    company_data = {
        "name": "New Test Company",
        "domain": "newtest.com"
    }
    
    response = client.post("/api/v1/auth/companies", json=company_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == company_data["name"]
    assert data["domain"] == company_data["domain"]
    assert "id" in data


def test_health_check(client: TestClient):
    """Test authentication health check"""
    response = client.get("/api/v1/auth/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "authentication"