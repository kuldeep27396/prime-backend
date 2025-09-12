"""
Simple Judge0 API test
"""

import httpx
import asyncio
import base64
import json
import time


async def simple_test():
    """Simple test of Judge0 API"""
    
    headers = {
        'x-rapidapi-key': "1246ea2ee8mshd398907cf74dfeep135401jsn3c98d3a7accb",
        'x-rapidapi-host': "judge0-extra-ce.p.rapidapi.com",
        'Content-Type': 'application/json'
    }
    
    # Simple Python code
    code = "print('Hello World')"
    
    submission_data = {
        "source_code": code,
        "language_id": 31,  # Python for ML (3.12.5)
        "stdin": "",
        "expected_output": "Hello World"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Submit code
            print("Submitting code...")
            submit_response = await client.post(
                "https://judge0-extra-ce.p.rapidapi.com/submissions",
                headers=headers,
                json=submission_data,
                timeout=30
            )
            
            print(f"Submit status: {submit_response.status_code}")
            print(f"Submit response: {submit_response.text}")
            
            if submit_response.status_code != 201:
                return
            
            submission = submit_response.json()
            token = submission["token"]
            print(f"Token: {token}")
            
            # Poll for result
            print("Polling for result...")
            for i in range(10):
                await asyncio.sleep(1)
                
                result_response = await client.get(
                    f"https://judge0-extra-ce.p.rapidapi.com/submissions/{token}",
                    headers=headers,
                    timeout=10
                )
                
                print(f"Poll {i+1} status: {result_response.status_code}")
                
                if result_response.status_code == 200:
                    result = result_response.json()
                    print(f"Status ID: {result['status']['id']}")
                    print(f"Status Description: {result['status']['description']}")
                    
                    if result["status"]["id"] not in [1, 2]:  # Not "In Queue" or "Processing"
                        print("Execution complete!")
                        print(f"Raw result: {json.dumps(result, indent=2)}")
                        
                        # Print outputs (Judge0 returns raw strings)
                        if result.get("stdout"):
                            print(f"Stdout: '{result['stdout']}'")
                        
                        if result.get("stderr"):
                            print(f"Stderr: '{result['stderr']}'")
                        
                        break
                else:
                    print(f"Poll error: {result_response.text}")
                    break
            
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(simple_test())