"""
Check available languages in Judge0 API
"""

import httpx
import asyncio
import json


async def check_languages():
    """Check available languages in Judge0"""
    
    headers = {
        'x-rapidapi-key': "1246ea2ee8mshd398907cf74dfeep135401jsn3c98d3a7accb",
        'x-rapidapi-host': "judge0-extra-ce.p.rapidapi.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://judge0-extra-ce.p.rapidapi.com/languages",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                languages = response.json()
                print("Available languages:")
                print("=" * 50)
                
                # Filter for common languages
                common_languages = ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'typescript']
                
                for lang in languages:
                    name = lang['name'].lower()
                    if any(common in name for common in common_languages):
                        print(f"ID: {lang['id']:2d} | Name: {lang['name']}")
                
                print("\nAll languages:")
                print("=" * 50)
                for lang in languages:
                    print(f"ID: {lang['id']:2d} | Name: {lang['name']}")
                    
            else:
                print(f"Failed to get languages: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_languages())