"""
Simple API test for interview endpoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_interview_endpoints_exist():
    """Test that interview endpoints are properly registered"""
    
    # Test that the endpoints exist (should return 401 for unauthenticated requests)
    response = client.get("/api/v1/interviews/templates")
    print(f"Templates endpoint status: {response.status_code}")
    assert response.status_code in [401, 403, 422]  # Unauthorized, Forbidden, or validation error
    
    response = client.get("/api/v1/interviews/")
    print(f"Interviews endpoint status: {response.status_code}")
    assert response.status_code in [401, 403, 422]  # Unauthorized, Forbidden, or validation error
    
    response = client.get("/api/v1/interviews/question-bank")
    print(f"Question bank endpoint status: {response.status_code}")
    assert response.status_code in [401, 403, 422]  # Unauthorized, Forbidden, or validation error
    
    print("✅ Interview endpoints are properly registered!")


def test_api_structure():
    """Test that the API structure is correct"""
    
    # Test OpenAPI docs include our endpoints
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    
    # Check that our interview endpoints are in the spec
    paths = openapi_spec.get("paths", {})
    assert "/api/v1/interviews/templates" in paths
    assert "/api/v1/interviews/" in paths
    assert "/api/v1/interviews/question-bank" in paths
    
    print("✅ API structure test passed!")


if __name__ == "__main__":
    test_interview_endpoints_exist()
    test_api_structure()
    print("🎉 All API tests passed!")