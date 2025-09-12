"""
Standalone test for security features without full app dependencies
"""

import hashlib
import os
from cryptography.fernet import Fernet


class SimpleSecurityService:
    """Simplified security service for testing"""
    
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def hash_pii_data(self, data: str) -> str:
        """Hash PII data for anonymization"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_browser_environment(self, environment_data: dict) -> dict:
        """Validate browser environment for security"""
        security_issues = []
        risk_score = 0
        
        # Check for suspicious extensions
        extensions = environment_data.get("extensions", [])
        suspicious_extensions = [
            "screen_recorder", "remote_desktop", "automation", 
            "developer_tools", "proxy", "vpn"
        ]
        
        for ext in extensions:
            if any(sus in ext.lower() for sus in suspicious_extensions):
                security_issues.append(f"Suspicious extension detected: {ext}")
                risk_score += 20
        
        # Check browser integrity
        if environment_data.get("developer_tools_open"):
            security_issues.append("Developer tools detected")
            risk_score += 30
        
        if environment_data.get("multiple_monitors"):
            security_issues.append("Multiple monitors detected")
            risk_score += 10
        
        # Check for automation tools
        if environment_data.get("webdriver_detected"):
            security_issues.append("Automation tools detected")
            risk_score += 50
        
        # Determine severity
        if risk_score >= 50:
            severity = "critical"
        elif risk_score >= 30:
            severity = "high"
        elif risk_score >= 10:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "valid": risk_score < 50,
            "risk_score": risk_score,
            "issues": security_issues,
            "severity": severity
        }


def test_encryption_decryption():
    """Test basic encryption and decryption"""
    service = SimpleSecurityService()
    test_data = "sensitive information"
    
    # Encrypt data
    encrypted = service.encrypt_sensitive_data(test_data)
    print(f"Original: {test_data}")
    print(f"Encrypted: {encrypted[:50]}...")
    
    # Decrypt data
    decrypted = service.decrypt_sensitive_data(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == test_data
    print("✓ Encryption/Decryption test passed")


def test_pii_hashing():
    """Test PII data hashing"""
    service = SimpleSecurityService()
    test_email = "user@example.com"
    
    hash1 = service.hash_pii_data(test_email)
    hash2 = service.hash_pii_data(test_email)
    
    print(f"Original: {test_email}")
    print(f"Hash: {hash1}")
    
    # Same input should produce same hash
    assert hash1 == hash2
    
    # Hash should be different from original
    assert hash1 != test_email
    
    # Hash should be consistent length (SHA-256)
    assert len(hash1) == 64
    
    print("✓ PII hashing test passed")


def test_browser_environment_validation():
    """Test browser environment validation logic"""
    service = SimpleSecurityService()
    
    # Test clean environment
    clean_environment = {
        "extensions": [],
        "developer_tools_open": False,
        "multiple_monitors": False,
        "webdriver_detected": False
    }
    
    result = service.validate_browser_environment(clean_environment)
    
    print(f"Clean environment result: {result}")
    assert result["valid"] is True
    assert result["risk_score"] == 0
    assert len(result["issues"]) == 0
    assert result["severity"] == "low"
    
    # Test suspicious environment
    suspicious_environment = {
        "extensions": ["screen_recorder", "automation"],
        "developer_tools_open": True,
        "multiple_monitors": True,
        "webdriver_detected": True
    }
    
    result = service.validate_browser_environment(suspicious_environment)
    
    print(f"Suspicious environment result: {result}")
    assert result["valid"] is False
    assert result["risk_score"] > 50
    assert len(result["issues"]) > 0
    assert result["severity"] in ["high", "critical"]
    
    print("✓ Browser environment validation test passed")


def test_security_scoring():
    """Test security risk scoring"""
    service = SimpleSecurityService()
    
    # Test various risk levels
    test_cases = [
        {
            "name": "No Risk",
            "data": {
                "extensions": [],
                "developer_tools_open": False,
                "multiple_monitors": False,
                "webdriver_detected": False
            },
            "expected_risk": 0,
            "expected_severity": "low"
        },
        {
            "name": "Low Risk",
            "data": {
                "extensions": [],
                "developer_tools_open": False,
                "multiple_monitors": True,
                "webdriver_detected": False
            },
            "expected_risk": 10,
            "expected_severity": "medium"
        },
        {
            "name": "High Risk",
            "data": {
                "extensions": ["screen_recorder"],
                "developer_tools_open": True,
                "multiple_monitors": False,
                "webdriver_detected": False
            },
            "expected_risk": 50,  # 20 (extension) + 30 (dev tools)
            "expected_severity": "critical"
        },
        {
            "name": "Critical Risk",
            "data": {
                "extensions": ["screen_recorder", "automation"],
                "developer_tools_open": True,
                "multiple_monitors": True,
                "webdriver_detected": True
            },
            "expected_risk": 130,  # 20+20 (extensions) + 30 (dev tools) + 10 (monitors) + 50 (webdriver)
            "expected_severity": "critical"
        }
    ]
    
    for test_case in test_cases:
        result = service.validate_browser_environment(test_case["data"])
        print(f"{test_case['name']}: Risk Score = {result['risk_score']}, Severity = {result['severity']}")
        
        assert result["risk_score"] == test_case["expected_risk"]
        assert result["severity"] == test_case["expected_severity"]
    
    print("✓ Security scoring test passed")


def main():
    """Run all tests"""
    print("Running standalone security feature tests...\n")
    
    try:
        test_encryption_decryption()
        print()
        
        test_pii_hashing()
        print()
        
        test_browser_environment_validation()
        print()
        
        test_security_scoring()
        print()
        
        print("🎉 All security tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()