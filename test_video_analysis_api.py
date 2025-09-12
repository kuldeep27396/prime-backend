"""
Test video analysis API endpoints
"""

import asyncio
import httpx
import json


async def test_video_analysis_api():
    """Test video analysis API endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Test data
    real_time_request = {
        "frame_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "session_id": "test-session",
        "timestamp": 1234567890.0
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code} - {response.json()}")
            
            # Test vision API test endpoint
            print("\nTesting vision API test endpoint...")
            response = await client.post(
                f"{base_url}/api/v1/video-analysis/test-vision-api",
                timeout=30
            )
            
            if response.status_code == 401:
                print("Authentication required (expected for production)")
            else:
                print(f"Vision API test: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"API Status: {result.get('api_status', 'unknown')}")
                    print(f"Message: {result.get('message', 'no message')}")
                else:
                    print(f"Error: {response.text}")
            
            # Test real-time proctoring endpoint
            print("\nTesting real-time proctoring endpoint...")
            response = await client.post(
                f"{base_url}/api/v1/video-analysis/real-time-proctoring",
                json=real_time_request,
                timeout=30
            )
            
            if response.status_code == 401:
                print("Authentication required (expected for production)")
            else:
                print(f"Real-time proctoring: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Success: {result.get('success', False)}")
                    print(f"Integrity Score: {result.get('integrity_score', 'N/A')}")
                    print(f"Engagement Score: {result.get('engagement_score', 'N/A')}")
                    print(f"Alerts: {len(result.get('alerts', []))}")
                else:
                    print(f"Error: {response.text}")
            
            # Test proctoring stats endpoint
            print("\nTesting proctoring stats endpoint...")
            response = await client.get(
                f"{base_url}/api/v1/video-analysis/proctoring-stats",
                timeout=10
            )
            
            if response.status_code == 401:
                print("Authentication required (expected for production)")
            else:
                print(f"Proctoring stats: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Total sessions: {result.get('total_sessions_monitored', 0)}")
                    print(f"Average integrity: {result.get('average_integrity_score', 'N/A')}")
                else:
                    print(f"Error: {response.text}")
            
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Testing Video Analysis API")
    print("=" * 40)
    print("Note: Make sure the FastAPI server is running on localhost:8000")
    print("Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("=" * 40)
    
    asyncio.run(test_video_analysis_api())