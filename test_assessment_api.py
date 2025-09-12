"""
Test assessment API endpoints
"""

import asyncio
import httpx
import json


async def test_assessment_api():
    """Test assessment API endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Test data
    assessment_data = {
        "application_id": "test-app-id",
        "type": "coding",
        "questions": [
            {
                "question_type": "coding",
                "title": "Simple Addition",
                "content": "Write a function that adds two numbers",
                "time_limit": 600,
                "difficulty": "easy",
                "points": 10,
                "programming_language": "python",
                "starter_code": "def add(a, b):\n    # Your code here\n    pass\n\na = int(input())\nb = int(input())\nprint(add(a, b))",
                "test_cases": [
                    {
                        "input": "5\n3",
                        "expected_output": "8",
                        "is_hidden": False
                    },
                    {
                        "input": "10\n20",
                        "expected_output": "30",
                        "is_hidden": False
                    }
                ]
            }
        ]
    }
    
    code_submission = {
        "question_id": "test-question-id",
        "code": "def add(a, b):\n    return a + b\n\na = int(input())\nb = int(input())\nprint(add(a, b))",
        "programming_language": "python"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code} - {response.json()}")
            
            # Test code execution endpoint (without auth for demo)
            print("\nTesting code execution...")
            response = await client.post(
                f"{base_url}/api/v1/assessments/execute-code",
                json=code_submission,
                timeout=30
            )
            
            if response.status_code == 401:
                print("Authentication required (expected for production)")
            else:
                print(f"Code execution: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Execution result: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {response.text}")
            
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Testing Assessment API")
    print("=" * 40)
    print("Note: Make sure the FastAPI server is running on localhost:8000")
    print("Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("=" * 40)
    
    asyncio.run(test_assessment_api())