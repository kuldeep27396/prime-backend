#!/usr/bin/env python3
"""
Test script for job management functionality
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123"


async def test_job_management():
    """Test job management CRUD operations"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Job Management Functionality")
        print("=" * 50)
        
        # Step 1: Login to get authentication token
        print("1. Authenticating user...")
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        print("✅ Authentication successful")
        
        # Step 2: Create a new job
        print("\n2. Creating a new job...")
        job_data = {
            "title": "Senior Python Developer",
            "description": "We are looking for an experienced Python developer to join our team. The ideal candidate will have strong experience with FastAPI, SQLAlchemy, and modern web development practices.",
            "requirements": {
                "skills": [
                    {
                        "name": "Python",
                        "required": True,
                        "experience_years": 5,
                        "proficiency_level": "advanced"
                    },
                    {
                        "name": "FastAPI",
                        "required": True,
                        "experience_years": 2,
                        "proficiency_level": "intermediate"
                    },
                    {
                        "name": "SQLAlchemy",
                        "required": True,
                        "experience_years": 3,
                        "proficiency_level": "intermediate"
                    }
                ],
                "experience_level": "senior",
                "min_experience_years": 5,
                "education_level": "bachelor",
                "location": {
                    "type": "remote",
                    "timezone": "UTC-5",
                    "travel_required": False
                },
                "salary": {
                    "min_salary": 90000,
                    "max_salary": 130000,
                    "currency": "USD",
                    "period": "yearly"
                },
                "additional_requirements": [
                    "Strong problem-solving skills",
                    "Experience with microservices architecture",
                    "Excellent communication skills"
                ]
            },
            "status": "draft"
        }
        
        create_response = await client.post(
            f"{BASE_URL}/api/v1/jobs/",
            json=job_data,
            headers=headers
        )
        
        if create_response.status_code != 201:
            print(f"❌ Job creation failed: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return
        
        created_job = create_response.json()
        job_id = created_job["id"]
        print(f"✅ Job created successfully with ID: {job_id}")
        print(f"   Title: {created_job['title']}")
        print(f"   Status: {created_job['status']}")
        
        # Step 3: Get the created job
        print(f"\n3. Retrieving job {job_id}...")
        get_response = await client.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=headers
        )
        
        if get_response.status_code != 200:
            print(f"❌ Job retrieval failed: {get_response.status_code}")
            print(f"Response: {get_response.text}")
            return
        
        retrieved_job = get_response.json()
        print("✅ Job retrieved successfully")
        print(f"   Title: {retrieved_job['title']}")
        print(f"   Skills: {len(retrieved_job['requirements']['skills'])} skills required")
        
        # Step 4: Update the job
        print(f"\n4. Updating job {job_id}...")
        update_data = {
            "title": "Senior Python Developer (Updated)",
            "status": "active",
            "requirements": {
                "skills": [
                    {
                        "name": "Python",
                        "required": True,
                        "experience_years": 5,
                        "proficiency_level": "advanced"
                    },
                    {
                        "name": "FastAPI",
                        "required": True,
                        "experience_years": 2,
                        "proficiency_level": "intermediate"
                    },
                    {
                        "name": "Docker",
                        "required": False,
                        "experience_years": 1,
                        "proficiency_level": "beginner"
                    }
                ],
                "experience_level": "senior",
                "min_experience_years": 5,
                "education_level": "bachelor",
                "location": {
                    "type": "hybrid",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA",
                    "travel_required": False
                },
                "salary": {
                    "min_salary": 100000,
                    "max_salary": 140000,
                    "currency": "USD",
                    "period": "yearly"
                }
            }
        }
        
        update_response = await client.put(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            json=update_data,
            headers=headers
        )
        
        if update_response.status_code != 200:
            print(f"❌ Job update failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return
        
        updated_job = update_response.json()
        print("✅ Job updated successfully")
        print(f"   New title: {updated_job['title']}")
        print(f"   New status: {updated_job['status']}")
        print(f"   Location type: {updated_job['requirements']['location']['type']}")
        
        # Step 5: List jobs
        print("\n5. Listing jobs...")
        list_response = await client.get(
            f"{BASE_URL}/api/v1/jobs/?page=1&page_size=10",
            headers=headers
        )
        
        if list_response.status_code != 200:
            print(f"❌ Job listing failed: {list_response.status_code}")
            print(f"Response: {list_response.text}")
            return
        
        job_list = list_response.json()
        print(f"✅ Jobs listed successfully")
        print(f"   Total jobs: {job_list['total']}")
        print(f"   Jobs on this page: {len(job_list['jobs'])}")
        
        # Step 6: Search jobs
        print("\n6. Searching jobs...")
        search_response = await client.get(
            f"{BASE_URL}/api/v1/jobs/search?query=Python&skills=Python&skills=FastAPI",
            headers=headers
        )
        
        if search_response.status_code != 200:
            print(f"❌ Job search failed: {search_response.status_code}")
            print(f"Response: {search_response.text}")
            return
        
        search_results = search_response.json()
        print(f"✅ Job search completed")
        print(f"   Found {search_results['total']} jobs matching criteria")
        if search_results['jobs']:
            first_result = search_results['jobs'][0]
            print(f"   First result: {first_result['title']}")
            if first_result.get('matching_skills'):
                print(f"   Matching skills: {', '.join(first_result['matching_skills'])}")
        
        # Step 7: Change job status
        print(f"\n7. Changing job status to paused...")
        status_change_response = await client.patch(
            f"{BASE_URL}/api/v1/jobs/{job_id}/status",
            json={
                "status": "paused",
                "reason": "Pausing to review applications"
            },
            headers=headers
        )
        
        if status_change_response.status_code != 200:
            print(f"❌ Status change failed: {status_change_response.status_code}")
            print(f"Response: {status_change_response.text}")
            return
        
        status_result = status_change_response.json()
        print("✅ Job status changed successfully")
        print(f"   From: {status_result['old_status']} → To: {status_result['new_status']}")
        print(f"   Reason: {status_result['reason']}")
        
        # Step 8: Get job analytics
        print(f"\n8. Getting job analytics...")
        analytics_response = await client.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}/analytics",
            headers=headers
        )
        
        if analytics_response.status_code != 200:
            print(f"❌ Analytics retrieval failed: {analytics_response.status_code}")
            print(f"Response: {analytics_response.text}")
            return
        
        analytics = analytics_response.json()
        print("✅ Job analytics retrieved successfully")
        print(f"   Total applications: {analytics['analytics']['application_stats']['total_applications']}")
        print(f"   Performance score: {analytics['analytics']['performance_metrics']['quality_score']}")
        if analytics['recommendations']:
            print(f"   Recommendations: {len(analytics['recommendations'])} suggestions")
        
        # Step 9: Test requirements parsing
        print("\n9. Testing job requirements parsing...")
        parse_request = {
            "job_title": "Full Stack Developer",
            "job_description": """
            We are seeking a talented Full Stack Developer to join our growing team. 
            The ideal candidate will have 3+ years of experience with React, Node.js, 
            and PostgreSQL. Must have a Bachelor's degree in Computer Science or related field.
            
            Responsibilities:
            - Develop and maintain web applications
            - Work with REST APIs and microservices
            - Collaborate with design and product teams
            
            Requirements:
            - 3+ years of JavaScript experience
            - Experience with React and Node.js
            - Knowledge of SQL databases
            - Strong problem-solving skills
            - Excellent communication skills
            
            Salary: $80,000 - $110,000 per year
            Location: Remote work available
            """
        }
        
        parse_response = await client.post(
            f"{BASE_URL}/api/v1/jobs/parse-requirements",
            json=parse_request,
            headers=headers
        )
        
        if parse_response.status_code != 200:
            print(f"❌ Requirements parsing failed: {parse_response.status_code}")
            print(f"Response: {parse_response.text}")
            return
        
        parse_result = parse_response.json()
        print("✅ Job requirements parsed successfully")
        print(f"   Success: {parse_result['success']}")
        print(f"   Confidence: {parse_result.get('confidence_score', 'N/A')}")
        if parse_result.get('extracted_skills'):
            print(f"   Extracted skills: {', '.join(parse_result['extracted_skills'])}")
        
        # Step 10: Clean up - delete the job
        print(f"\n10. Cleaning up - deleting job {job_id}...")
        delete_response = await client.delete(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=headers
        )
        
        if delete_response.status_code != 204:
            print(f"❌ Job deletion failed: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return
        
        print("✅ Job deleted successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All job management tests completed successfully!")
        print("✅ CRUD operations working")
        print("✅ Search and filtering working")
        print("✅ Status management working")
        print("✅ Analytics working")
        print("✅ Requirements parsing working")


if __name__ == "__main__":
    asyncio.run(test_job_management())