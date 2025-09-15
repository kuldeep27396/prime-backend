"""
Database migration script for Prime Interviews API
Creates all required tables based on the models defined in models.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.database import engine, Base
from app.database.models import *

async def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully!")
        print("\nTables created:")
        print("- users")
        print("- mentors")
        print("- sessions")
        print("- user_preferences")
        print("- skill_assessments")
        print("- reviews")
        print("- video_rooms")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_tables())