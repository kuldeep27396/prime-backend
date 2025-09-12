"""
Test application API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.schemas.application import ApplicationStatus


def test_application_api_endpoints():
    """Test application API endpoints are properly registered"""
    client = TestClient(app)
    
    # Test that the API docs include our application endpoints
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test that the OpenAPI spec includes our endpoints
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec.get("paths", {})
    
    # Check that our application endpoints are registered
    expected_paths = [
        "/api/v1/applications/",
        "/api/v1/applications/{application_id}",
        "/api/v1/applications/{application_id}/status",
        "/api/v1/applications/jobs/{job_id}/rankings",
        "/api/v1/applications/analytics/overview",
        "/api/v1/applications/bulk/status-update",
        "/api/v1/applications/search",
        "/api/v1/applications/dashboard/metrics"
    ]
    
    for path in expected_paths:
        assert path in paths, f"Path {path} not found in OpenAPI spec"
    
    print("All application API endpoints are properly registered!")


def test_application_schemas_in_openapi():
    """Test that application schemas are included in OpenAPI spec"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    components = openapi_spec.get("components", {})
    schemas = components.get("schemas", {})
    
    # Check that our application schemas are included
    expected_schemas = [
        "ApplicationCreate",
        "ApplicationUpdate", 
        "ApplicationResponse",
        "ApplicationListResponse",
        "PipelineStatusUpdate",
        "CandidateRanking",
        "RankingWeights",
        "ApplicationAnalytics",
        "ApplicationFilters",
        "ApplicationSort",
        "ApplicationStatus",
        "SortField",
        "SortDirection"
    ]
    
    for schema_name in expected_schemas:
        assert schema_name in schemas, f"Schema {schema_name} not found in OpenAPI spec"
    
    print("All application schemas are properly included in OpenAPI spec!")


def test_application_status_enum_values():
    """Test that ApplicationStatus enum values are correct"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    schemas = openapi_spec["components"]["schemas"]
    
    # Check ApplicationStatus enum values
    app_status_schema = schemas.get("ApplicationStatus")
    assert app_status_schema is not None
    
    expected_values = ["applied", "screening", "interviewing", "assessed", "hired", "rejected"]
    actual_values = app_status_schema.get("enum", [])
    
    for value in expected_values:
        assert value in actual_values, f"ApplicationStatus enum missing value: {value}"
    
    print("ApplicationStatus enum values are correct!")


def test_api_endpoint_methods():
    """Test that API endpoints have correct HTTP methods"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    # Test specific endpoint methods
    endpoint_methods = {
        "/api/v1/applications/": ["get", "post"],
        "/api/v1/applications/{application_id}": ["get", "put"],
        "/api/v1/applications/{application_id}/status": ["patch"],
        "/api/v1/applications/jobs/{job_id}/rankings": ["get"],
        "/api/v1/applications/analytics/overview": ["get"],
        "/api/v1/applications/bulk/status-update": ["post"],
        "/api/v1/applications/search": ["post"],
        "/api/v1/applications/dashboard/metrics": ["get"]
    }
    
    for path, expected_methods in endpoint_methods.items():
        path_spec = paths.get(path, {})
        actual_methods = list(path_spec.keys())
        
        for method in expected_methods:
            assert method in actual_methods, f"Method {method} not found for path {path}"
    
    print("All API endpoints have correct HTTP methods!")


def test_request_response_schemas():
    """Test that endpoints have proper request/response schemas"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    # Test POST /api/v1/applications/
    create_endpoint = paths["/api/v1/applications/"]["post"]
    
    # Check request body schema
    request_body = create_endpoint.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema_ref = json_content.get("schema", {}).get("$ref", "")
    assert "ApplicationCreate" in schema_ref
    
    # Check response schema
    responses = create_endpoint.get("responses", {})
    success_response = responses.get("201", {})
    response_content = success_response.get("content", {})
    response_json = response_content.get("application/json", {})
    response_schema_ref = response_json.get("schema", {}).get("$ref", "")
    assert "ApplicationResponse" in response_schema_ref
    
    print("Request/response schemas are properly configured!")


def test_query_parameters():
    """Test that endpoints have proper query parameters"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    # Test GET /api/v1/applications/ query parameters
    list_endpoint = paths["/api/v1/applications/"]["get"]
    parameters = list_endpoint.get("parameters", [])
    
    # Check for pagination parameters
    param_names = [param["name"] for param in parameters]
    expected_params = ["page", "page_size", "job_id", "candidate_id", "status"]
    
    for param in expected_params:
        assert param in param_names, f"Query parameter {param} not found"
    
    # Test rankings endpoint query parameters
    rankings_endpoint = paths["/api/v1/applications/jobs/{job_id}/rankings"]["get"]
    rankings_params = rankings_endpoint.get("parameters", [])
    rankings_param_names = [param["name"] for param in rankings_params]
    
    weight_params = ["technical_weight", "communication_weight", "cultural_fit_weight", 
                    "cognitive_weight", "behavioral_weight"]
    
    for param in weight_params:
        assert param in rankings_param_names, f"Weight parameter {param} not found"
    
    print("Query parameters are properly configured!")


def test_error_responses():
    """Test that endpoints define proper error responses"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    # Test that endpoints define error responses
    create_endpoint = paths["/api/v1/applications/"]["post"]
    responses = create_endpoint.get("responses", {})
    
    # Should have error responses defined
    assert "422" in responses  # Validation error
    
    # Test GET endpoint
    get_endpoint = paths["/api/v1/applications/{application_id}"]["get"]
    get_responses = get_endpoint.get("responses", {})
    
    assert "404" in get_responses or "422" in get_responses  # Not found or validation error
    
    print("Error responses are properly defined!")


def test_authentication_requirements():
    """Test that endpoints require authentication"""
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    # Check that endpoints have security requirements
    create_endpoint = paths["/api/v1/applications/"]["post"]
    security = create_endpoint.get("security", [])
    
    # Should have some form of security requirement
    # (The exact security scheme depends on the auth implementation)
    assert len(security) > 0 or "security" in openapi_spec, "Endpoints should require authentication"
    
    print("Authentication requirements are configured!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])