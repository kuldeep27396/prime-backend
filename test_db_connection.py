"""
Test database connection to Supabase
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

async def test_connection():
    load_dotenv()

    # Try different URL formats
    urls = [
        "postgresql://postgres:Prime27%23@ttuxkvppzbhbfksdvcjx.supabase.co:5432/postgres",
        "postgresql://postgres:Prime27%23@ttuxkvppzbhbfksdvcjx.supabase.co:6543/postgres",
        "postgres://postgres:Prime27%23@ttuxkvppzbhbfksdvcjx.supabase.co:5432/postgres",
    ]

    for i, url in enumerate(urls):
        print(f"Testing URL {i+1}: {url[:50]}...")
        try:
            conn = await asyncpg.connect(url)
            print(f"✅ Connection {i+1} successful!")

            # Test a simple query
            result = await conn.fetchval("SELECT version()")
            print(f"Database version: {result[:50]}...")

            await conn.close()
            return url
        except Exception as e:
            print(f"❌ Connection {i+1} failed: {str(e)}")

    return None

if __name__ == "__main__":
    asyncio.run(test_connection())