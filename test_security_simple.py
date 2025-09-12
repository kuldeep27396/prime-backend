"""
Simple test for security features
"""

import asyncio
from datetime import datetime
from app.services.security_service import security_service


def test_encryption_decryption():
    """Test basic encryption and decryption"""
    test_data = "sensitive information"
    
    # Encrypt data
    encrypted = security_service.encrypt_sensitive_data(test_data)
    print(f"Original: {test_data}")
    print(f"Encrypted: {encrypted[:50]}...")
    
    # Decrypt data
    decrypted = security_service.decrypt_sensitive_data(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == test_data
    print("✓ Encryption/Decryption test passed")


def test_pii_hashing():
    """Test PII data hashing"""
    test_email = "user@example.com"
    
    hash1 = security_service.hash_pii_data(test_email)
    hash2 = security_service.hash_pii_data(test_email)
    
    print(f"Original: {test_email}")
    print(f"Hash: {hash1}")
    
    # Same input should produce same hash
    assert hash1 == hash2
    
    # Hash should be different from original
    assert hash1 != test_email
    
    # Hash should be consistent length (SHA-256)
    assert len(hash1) == 64
    
    print("✓ PII hashing test passed")


async def test_browser_environment_validation():
    """Test browser environment validation logic"""
    # Mock database session
    class MockDB:
        def add(self, obj): pass
        def commit(self): pass
        def refresh(self, obj): pass
    
    db = MockDB()
    
    # Test clean environment
    clean_environment = {
        "extensions": [],
        "developer_tools_open": False,
        "multiple_monitors": False,
        "webdriver_detected": False
    }
    
    result = await security_service.validate_browser_environment(
        db=db,
        interview_id="test-interview-id",
        environment_data=clean_environment
    )
    
    print(f"Clean environment result: {result}")
    assert result["valid"] is True
    assert result["risk_score"] == 0
    assert len(result["issues"]) == 0
    
    # Test suspicious environment
    suspicious_environment = {
        "extensions": ["screen_recorder", "automation"],
        "developer_tools_open": True,
        "multiple_monitors": True,
        "webdriver_detected": True
    }
    
    result = await security_service.validate_browser_environment(
        db=db,
        interview_id="test-interview-id",
        environment_data=suspicious_environment
    )
    
    print(f"Suspicious environment result: {result}")
    assert result["valid"] is False
    assert result["risk_score"] > 50
    assert len(result["issues"]) > 0
    
    print("✓ Browser environment validation test passed")


def main():
    """Run all tests"""
    print("Running security feature tests...\n")
    
    try:
        test_encryption_decryption()
        print()
        
        test_pii_hashing()
        print()
        
        asyncio.run(test_browser_environment_validation())
        print()
        
        print("🎉 All security tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()