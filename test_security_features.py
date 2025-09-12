"""
Test security and compliance features
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import get_db, engine
from app.models.company import Company, User
from app.models.interview import Interview
from app.models.audit import AuditLog, ProctoringEvent, SecurityAlert, ComplianceLog, DataRetentionPolicy
from app.services.security_service import security_service
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base
    
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///./test_security.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_company(db_session):
    """Create a test company"""
    company = Company(
        name="Test Company",
        domain="test.com",
        settings={}
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company):
    """Create a test user"""
    user = User(
        company_id=test_company.id,
        email="test@test.com",
        password_hash="hashed_password",
        role="admin",
        profile={"name": "Test User"},
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    token = create_access_token(data={"sub": test_user.email, "user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestSecurityService:
    """Test security service functionality"""
    
    @pytest.mark.asyncio
    async def test_log_user_action(self, db_session, test_user):
        """Test audit logging"""
        # Mock request object
        mock_request = Mock()
        mock_request.headers = {"User-Agent": "Test Browser"}
        mock_request.client.host = "127.0.0.1"
        
        audit_log = await security_service.log_user_action(
            db=db_session,
            user_id=str(test_user.id),
            action="test_action",
            resource_type="test_resource",
            resource_id="test_id",
            details={"test": "data"},
            request=mock_request
        )
        
        assert audit_log.user_id == test_user.id
        assert audit_log.action == "test_action"
        assert audit_log.resource_type == "test_resource"
        assert audit_log.resource_id == "test_id"
        assert audit_log.details == {"test": "data"}
        assert audit_log.user_agent == "Test Browser"
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, db_session):
        """Test security event logging"""
        # Create a test interview
        interview = Interview(
            application_id="test-app-id",
            template_id="test-template-id",
            type="live_ai",
            status="in_progress"
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)
        
        event = await security_service.log_security_event(
            db=db_session,
            interview_id=str(interview.id),
            event_type="face_detection",
            severity="high",
            details={"faces_detected": 2}
        )
        
        assert event.interview_id == interview.id
        assert event.event_type == "face_detection"
        assert event.severity == "high"
        assert event.details == {"faces_detected": 2}
    
    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption"""
        test_data = "sensitive information"
        
        # Encrypt data
        encrypted = security_service.encrypt_sensitive_data(test_data)
        assert encrypted != test_data
        
        # Decrypt data
        decrypted = security_service.decrypt_sensitive_data(encrypted)
        assert decrypted == test_data
    
    def test_hash_pii_data(self):
        """Test PII data hashing"""
        test_email = "user@example.com"
        
        hash1 = security_service.hash_pii_data(test_email)
        hash2 = security_service.hash_pii_data(test_email)
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from original
        assert hash1 != test_email
        
        # Hash should be consistent length
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string
    
    @pytest.mark.asyncio
    async def test_anonymize_user_data(self, db_session, test_user):
        """Test user data anonymization"""
        original_email = test_user.email
        
        result = await security_service.anonymize_user_data(
            db=db_session,
            user_id=str(test_user.id)
        )
        
        # Refresh user from database
        db_session.refresh(test_user)
        
        assert result["status"] == "anonymized"
        assert test_user.email != original_email
        assert test_user.email.startswith("anonymized_")
        assert test_user.profile["name"] == "Anonymized User"
        assert "anonymized_at" in test_user.profile
    
    @pytest.mark.asyncio
    async def test_validate_browser_environment(self, db_session):
        """Test browser environment validation"""
        # Create a test interview
        interview = Interview(
            application_id="test-app-id",
            template_id="test-template-id",
            type="live_ai",
            status="in_progress"
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)
        
        # Test with suspicious environment
        environment_data = {
            "extensions": ["screen_recorder", "automation_tool"],
            "developer_tools_open": True,
            "multiple_monitors": True,
            "webdriver_detected": False
        }
        
        result = await security_service.validate_browser_environment(
            db=db_session,
            interview_id=str(interview.id),
            environment_data=environment_data
        )
        
        assert not result["valid"]
        assert result["risk_score"] > 50
        assert len(result["issues"]) > 0
        assert result["severity"] in ["high", "critical"]
    
    @pytest.mark.asyncio
    async def test_apply_data_retention_policy(self, db_session, test_user):
        """Test data retention policy application"""
        # Create old audit logs
        old_date = datetime.utcnow() - timedelta(days=8*365)  # 8 years old
        old_audit_log = AuditLog(
            user_id=test_user.id,
            action="old_action",
            created_at=old_date
        )
        db_session.add(old_audit_log)
        
        # Create recent audit log
        recent_audit_log = AuditLog(
            user_id=test_user.id,
            action="recent_action"
        )
        db_session.add(recent_audit_log)
        db_session.commit()
        
        # Apply retention policy
        result = await security_service.apply_data_retention_policy(db_session)
        
        assert result["audit_logs_deleted"] >= 1
        
        # Verify old log is deleted and recent log remains
        remaining_logs = db_session.query(AuditLog).all()
        actions = [log.action for log in remaining_logs]
        assert "recent_action" in actions


class TestSecurityAPI:
    """Test security API endpoints"""
    
    def test_create_audit_log(self, auth_headers):
        """Test audit log creation endpoint"""
        response = client.post(
            "/api/v1/security/audit-log",
            params={
                "action": "test_action",
                "resource_type": "test_resource",
                "resource_id": "test_id"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged"
        assert "audit_log_id" in data
    
    def test_get_audit_logs(self, auth_headers):
        """Test audit logs retrieval endpoint"""
        response = client.get(
            "/api/v1/security/audit-logs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_log_security_event(self, auth_headers):
        """Test security event logging endpoint"""
        event_data = {
            "interview_id": "test-interview-id",
            "event_type": "face_detection",
            "severity": "medium",
            "details": {"test": "data"}
        }
        
        response = client.post(
            "/api/v1/security/security-event",
            json=event_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "face_detection"
        assert data["severity"] == "medium"
    
    def test_validate_browser_environment(self, auth_headers):
        """Test browser environment validation endpoint"""
        environment_data = {
            "interview_id": "test-interview-id",
            "environment_data": {
                "extensions": ["adblock"],
                "developer_tools_open": False,
                "multiple_monitors": False,
                "webdriver_detected": False
            }
        }
        
        response = client.post(
            "/api/v1/security/validate-browser-environment",
            json=environment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "risk_score" in data
        assert "issues" in data
        assert "severity" in data
    
    def test_get_security_dashboard(self, auth_headers):
        """Test security dashboard endpoint"""
        response = client.get(
            "/api/v1/security/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "security_events" in data
        assert "audit_logs" in data
        assert "period_days" in data
    
    def test_create_data_retention_policy(self, auth_headers):
        """Test data retention policy creation"""
        policy_data = {
            "data_type": "audit_logs",
            "retention_days": 2555,  # 7 years
            "auto_delete": True,
            "encryption_required": False
        }
        
        response = client.post(
            "/api/v1/security/data-retention-policy",
            json=policy_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data_type"] == "audit_logs"
        assert data["retention_days"] == 2555
        assert data["auto_delete"] is True
    
    def test_log_compliance_action(self, auth_headers):
        """Test compliance action logging"""
        compliance_data = {
            "subject_id": "test-user-id",
            "action": "data_export",
            "legal_basis": "GDPR Article 20",
            "details": {"export_format": "JSON"},
            "requested_by": "user@example.com"
        }
        
        response = client.post(
            "/api/v1/security/compliance-action",
            json=compliance_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "data_export"
        assert data["legal_basis"] == "GDPR Article 20"
        assert data["subject_id"] == "test-user-id"


class TestBrowserEnvironmentValidation:
    """Test browser environment validation logic"""
    
    @pytest.mark.asyncio
    async def test_clean_environment(self, db_session):
        """Test validation of clean browser environment"""
        interview = Interview(
            application_id="test-app-id",
            template_id="test-template-id",
            type="live_ai",
            status="in_progress"
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)
        
        clean_environment = {
            "extensions": [],
            "developer_tools_open": False,
            "multiple_monitors": False,
            "webdriver_detected": False
        }
        
        result = await security_service.validate_browser_environment(
            db=db_session,
            interview_id=str(interview.id),
            environment_data=clean_environment
        )
        
        assert result["valid"] is True
        assert result["risk_score"] == 0
        assert len(result["issues"]) == 0
        assert result["severity"] == "low"
    
    @pytest.mark.asyncio
    async def test_suspicious_environment(self, db_session):
        """Test validation of suspicious browser environment"""
        interview = Interview(
            application_id="test-app-id",
            template_id="test-template-id",
            type="live_ai",
            status="in_progress"
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)
        
        suspicious_environment = {
            "extensions": ["screen_recorder", "remote_desktop", "automation"],
            "developer_tools_open": True,
            "multiple_monitors": True,
            "webdriver_detected": True
        }
        
        result = await security_service.validate_browser_environment(
            db=db_session,
            interview_id=str(interview.id),
            environment_data=suspicious_environment
        )
        
        assert result["valid"] is False
        assert result["risk_score"] >= 50
        assert len(result["issues"]) > 0
        assert result["severity"] in ["high", "critical"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])