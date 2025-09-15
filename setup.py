"""
Setup script for Prime Interviews Backend API
Run this script to initialize the database and seed sample data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.database import engine, Base
from app.database.models import *
from app.database.database import AsyncSessionLocal

async def create_tables():
    """Create all database tables"""
    try:
        print("🔧 Creating database tables...")

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

async def seed_sample_data():
    """Seed database with sample data for development"""
    print("\n🌱 Seeding sample data...")

    try:
        async with AsyncSessionLocal() as session:
            # Sample mentors data
            from app.database.models import User, Mentor
            import uuid

            # Create sample mentor user
            mentor_user = User(
                user_id="mentor_001",
                email="mentor@example.com",
                first_name="John",
                last_name="Smith",
                role="mentor"
            )
            session.add(mentor_user)
            await session.commit()
            await session.refresh(mentor_user)

            # Create sample mentor profile
            mentor = Mentor(
                user_id=mentor_user.id,
                name="John Smith",
                title="Senior Software Engineer",
                current_company="Google",
                previous_companies=["Facebook", "Apple"],
                bio="Experienced software engineer with 10 years in tech",
                specialties=["System Design", "Algorithm Interviews"],
                skills=["Python", "Java", "JavaScript", "React", "AWS"],
                languages=["English", "Spanish"],
                experience=10,
                rating=4.8,
                review_count=156,
                hourly_rate=150.0,
                response_time="Within 2 hours",
                timezone="America/New_York",
                availability=["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17"]
            )
            session.add(mentor)

            # Create another sample mentor
            mentor_user_2 = User(
                user_id="mentor_002",
                email="mentor2@example.com",
                first_name="Sarah",
                last_name="Johnson",
                role="mentor"
            )
            session.add(mentor_user_2)
            await session.commit()
            await session.refresh(mentor_user_2)

            mentor_2 = Mentor(
                user_id=mentor_user_2.id,
                name="Sarah Johnson",
                title="Staff Software Engineer",
                current_company="Meta",
                previous_companies=["Netflix", "Uber"],
                bio="Full-stack developer specializing in scalable systems",
                specialties=["Full-Stack Development", "System Architecture"],
                skills=["TypeScript", "Node.js", "React", "PostgreSQL", "Docker"],
                languages=["English"],
                experience=8,
                rating=4.9,
                review_count=89,
                hourly_rate=175.0,
                response_time="Within 1 hour",
                timezone="America/Los_Angeles",
                availability=["Monday 10-18", "Wednesday 10-18", "Friday 10-18"]
            )
            session.add(mentor_2)

            await session.commit()
            print("✅ Sample mentors created successfully!")

    except Exception as e:
        print(f"❌ Error seeding sample data: {str(e)}")
        raise

async def main():
    """Main setup function"""
    print("🚀 Setting up Prime Interviews Backend API")
    print("=" * 50)

    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  DATABASE_URL not set. Using default PostgreSQL connection.")
        print("   Make sure your PostgreSQL server is running!")

    try:
        # Create tables
        await create_tables()

        # Seed sample data
        await seed_sample_data()

        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Set up your environment variables in .env file")
        print("2. Configure Clerk authentication keys")
        print("3. Configure SMTP settings for email service")
        print("4. Run: python -m app.main")
        print("5. Visit: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n💥 Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())