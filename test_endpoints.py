"""
Simple test endpoints without authentication for testing database connectivity
"""
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from dotenv import load_dotenv

from app.database import get_db
from app.database.models import Mentor, User

load_dotenv()

app = FastAPI(title="Test Endpoints")

@app.get("/test/mentors")
async def test_mentors(db: AsyncSession = Depends(get_db)):
    """Test mentors endpoint without authentication"""
    try:
        result = await db.execute(
            select(Mentor).where(Mentor.is_active == True).limit(10)
        )
        mentors = result.scalars().all()

        mentor_list = []
        for mentor in mentors:
            mentor_list.append({
                "id": str(mentor.id),
                "name": mentor.name,
                "title": mentor.title,
                "currentCompany": mentor.current_company,
                "experience": mentor.experience,
                "rating": float(mentor.rating),
                "hourlyRate": float(mentor.hourly_rate),
                "skills": mentor.skills or [],
                "languages": mentor.languages or []
            })

        return {
            "success": True,
            "count": len(mentor_list),
            "mentors": mentor_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test/users")
async def test_users(db: AsyncSession = Depends(get_db)):
    """Test users endpoint without authentication"""
    try:
        result = await db.execute(select(User))
        users = result.scalars().all()

        user_list = []
        for user in users:
            user_list.append({
                "id": str(user.id),
                "userId": user.user_id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "role": user.role
            })

        return {
            "success": True,
            "count": len(user_list),
            "users": user_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)