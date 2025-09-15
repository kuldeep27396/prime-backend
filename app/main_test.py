"""
Test version of main.py that doesn't require database connection
"""
from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Prime Interviews API",
    description="Comprehensive backend service for interview scheduling and management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mock data for testing
MOCK_USERS = {
    "user_123": {
        "id": str(uuid.uuid4()),
        "userId": "user_123",
        "email": "user@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "role": "candidate",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
}

MOCK_MENTORS = [
    {
        "id": str(uuid.uuid4()),
        "name": "Sarah Johnson",
        "title": "Senior Software Engineer",
        "currentCompany": "Google",
        "previousCompanies": ["Facebook", "Apple"],
        "avatar": "https://example.com/avatar1.jpg",
        "bio": "Experienced software engineer with 8+ years in tech",
        "specialties": ["System Design", "Algorithm Interviews"],
        "skills": ["Python", "JavaScript", "React", "AWS"],
        "languages": ["English", "Spanish"],
        "experience": 8,
        "rating": 4.8,
        "reviewCount": 142,
        "hourlyRate": 150.0,
        "responseTime": "Within 2 hours",
        "timezone": "America/New_York",
        "availability": ["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17"],
        "isActive": True,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Mike Chen",
        "title": "Staff Software Engineer",
        "currentCompany": "Meta",
        "previousCompanies": ["Netflix", "Uber"],
        "avatar": "https://example.com/avatar2.jpg",
        "bio": "Full-stack developer specializing in scalable systems",
        "specialties": ["Full-Stack Development", "System Architecture"],
        "skills": ["TypeScript", "Node.js", "PostgreSQL", "Docker"],
        "languages": ["English", "Mandarin"],
        "experience": 10,
        "rating": 4.9,
        "reviewCount": 98,
        "hourlyRate": 175.0,
        "responseTime": "Within 1 hour",
        "timezone": "America/Los_Angeles",
        "availability": ["Monday 10-18", "Wednesday 10-18", "Friday 10-18"],
        "isActive": True,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
]

MOCK_SESSIONS = []

# Simple auth simulation
def get_mock_user():
    return MOCK_USERS["user_123"]

# Schemas
class UserCreate(BaseModel):
    userId: str
    email: EmailStr
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    profileImage: Optional[str] = None
    role: str = "candidate"
    experience: Optional[str] = None
    skills: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None

class SessionCreate(BaseModel):
    mentorId: str
    sessionType: str
    scheduledAt: datetime
    duration: int = Field(ge=15, le=480)
    meetingType: str = "video"
    recordSession: bool = False
    specialRequests: Optional[str] = None
    participantEmail: Optional[str] = None
    participantName: Optional[str] = None

# Routes
@app.get("/")
def read_root():
    return {
        "message": "Prime Interviews API v2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "mock_mode",
        "email_service": "configured" if os.getenv("SMTP_HOST") else "not_configured"
    }

# User endpoints
@app.post("/api/users")
def create_user(user_data: UserCreate):
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "userId": user_data.userId,
        "email": user_data.email,
        "firstName": user_data.firstName,
        "lastName": user_data.lastName,
        "role": user_data.role,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    MOCK_USERS[user_data.userId] = user

    return {
        "success": True,
        "message": "User created successfully",
        "data": {"user": user}
    }

@app.get("/api/users/{user_id}")
def get_user_profile(user_id: str):
    user = MOCK_USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "profile": user,
        "sessionHistory": [],
        "skillAssessments": [
            {"skill": "Python", "score": 85, "assessedAt": datetime.now().isoformat()},
            {"skill": "JavaScript", "score": 78, "assessedAt": datetime.now().isoformat()}
        ],
        "favorites": [],
        "preferences": {
            "recentSearches": ["React", "Python"],
            "favoriteTopics": ["Web Development"],
            "timezone": "America/New_York"
        }
    }

@app.get("/api/users/{user_id}/analytics")
def get_user_analytics(user_id: str):
    user = MOCK_USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "stats": {
            "totalInterviews": 12,
            "completedCount": 8,
            "upcomingCount": 4,
            "averageScore": 4.2,
            "totalHoursSpent": 16
        },
        "progressData": [
            {"month": "2024-01", "score": 3.8, "interviews": 3},
            {"month": "2024-02", "score": 4.0, "interviews": 5},
            {"month": "2024-03", "score": 4.2, "interviews": 4}
        ],
        "skillAssessments": [
            {"skill": "Python", "score": 85, "assessedAt": datetime.now().isoformat()},
            {"skill": "JavaScript", "score": 78, "assessedAt": datetime.now().isoformat()}
        ],
        "upcomingInterviews": [
            {
                "id": str(uuid.uuid4()),
                "mentorName": "Sarah Johnson",
                "company": "Google",
                "title": "System Design Interview",
                "scheduledAt": "2024-01-20T14:00:00Z",
                "type": "System Design",
                "difficulty": "Medium"
            }
        ],
        "recentActivity": [
            {
                "type": "session_completed",
                "description": "Completed mock interview with Sarah Johnson",
                "date": datetime.now().isoformat(),
                "metadata": {"rating": 4}
            }
        ]
    }

# Mentor endpoints
@app.get("/api/mentors")
def get_mentors(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    skills: Optional[str] = Query(None),
    companies: Optional[str] = Query(None),
    rating_min: Optional[float] = Query(None, ge=0, le=5),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    experience_min: Optional[int] = Query(None, ge=0),
    languages: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    # Apply basic filtering
    filtered_mentors = MOCK_MENTORS.copy()

    if skills:
        skill_list = [s.strip() for s in skills.split(',')]
        filtered_mentors = [m for m in filtered_mentors
                           if any(skill in m['skills'] for skill in skill_list)]

    if companies:
        company_list = [c.strip() for c in companies.split(',')]
        filtered_mentors = [m for m in filtered_mentors
                           if m['currentCompany'] in company_list or
                           any(c in (m['previousCompanies'] or []) for c in company_list)]

    if rating_min:
        filtered_mentors = [m for m in filtered_mentors if m['rating'] >= rating_min]

    if price_min:
        filtered_mentors = [m for m in filtered_mentors if m['hourlyRate'] >= price_min]

    if price_max:
        filtered_mentors = [m for m in filtered_mentors if m['hourlyRate'] <= price_max]

    if experience_min:
        filtered_mentors = [m for m in filtered_mentors if m['experience'] >= experience_min]

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_mentors = filtered_mentors[start:end]

    return {
        "mentors": paginated_mentors,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(filtered_mentors),
            "totalPages": (len(filtered_mentors) + limit - 1) // limit
        },
        "filters": {
            "availableSkills": ["Python", "JavaScript", "React", "AWS", "TypeScript", "Node.js", "PostgreSQL", "Docker"],
            "availableCompanies": ["Google", "Meta", "Facebook", "Apple", "Netflix", "Uber"],
            "availableLanguages": ["English", "Spanish", "Mandarin"],
            "priceRange": {"min": 50, "max": 300},
            "experienceRange": {"min": 0, "max": 15}
        }
    }

@app.get("/api/mentors/{mentor_id}")
def get_mentor_detail(mentor_id: str):
    mentor = next((m for m in MOCK_MENTORS if m['id'] == mentor_id), None)
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    # Add reviews and availability data
    mentor_detail = mentor.copy()
    mentor_detail.update({
        "reviews": [
            {
                "id": str(uuid.uuid4()),
                "userId": "user_123",
                "userName": "John D.",
                "rating": 5,
                "comment": "Excellent mentor! Very helpful with system design concepts.",
                "date": datetime.now().isoformat(),
                "sessionType": "System Design"
            }
        ],
        "upcomingSlots": ["2024-01-20T10:00:00Z", "2024-01-20T14:00:00Z", "2024-01-21T09:00:00Z"],
        "isAvailable": True
    })

    return mentor_detail

# Session endpoints
@app.post("/api/sessions")
def create_session(session_data: SessionCreate, current_user: dict = Depends(get_mock_user)):
    session_id = str(uuid.uuid4())
    mentor = next((m for m in MOCK_MENTORS if m['id'] == session_data.mentorId), None)
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    session = {
        "id": session_id,
        "userId": current_user["id"],
        "mentorId": session_data.mentorId,
        "sessionType": session_data.sessionType,
        "scheduledAt": session_data.scheduledAt.isoformat(),
        "duration": session_data.duration,
        "meetingType": session_data.meetingType,
        "meetingLink": f"https://meet.prime-interviews.com/room/{session_id}",
        "status": "pending",
        "recordSession": session_data.recordSession,
        "specialRequests": session_data.specialRequests,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }

    MOCK_SESSIONS.append(session)

    return {
        "success": True,
        "session": session,
        "emailSent": True
    }

@app.get("/api/sessions")
def get_user_sessions(
    status_filter: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_mock_user)
):
    user_sessions = [s for s in MOCK_SESSIONS if s["userId"] == current_user["id"]]

    if status_filter:
        if status_filter == "upcoming":
            user_sessions = [s for s in user_sessions if s["status"] in ["pending", "confirmed"]]
        else:
            user_sessions = [s for s in user_sessions if s["status"] == status_filter]

    # Add mentor details
    sessions_with_mentors = []
    for session in user_sessions:
        mentor = next((m for m in MOCK_MENTORS if m['id'] == session['mentorId']), None)
        if mentor:
            session_with_mentor = session.copy()
            session_with_mentor.update({
                "mentorName": mentor["name"],
                "mentorAvatar": mentor["avatar"],
                "mentorCompany": mentor["currentCompany"]
            })
            sessions_with_mentors.append(session_with_mentor)

    return {
        "sessions": sessions_with_mentors,
        "stats": {
            "totalSessions": len(user_sessions),
            "completedSessions": len([s for s in user_sessions if s["status"] == "completed"]),
            "upcomingSessions": len([s for s in user_sessions if s["status"] in ["pending", "confirmed"]]),
            "averageRating": 4.2,
            "totalHours": 8
        }
    }

@app.patch("/api/sessions/{session_id}")
def update_session(session_id: str, update_data: dict):
    session = next((s for s in MOCK_SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.update(update_data)
    session["updatedAt"] = datetime.now().isoformat()

    return {"success": True, "message": "Session updated successfully"}

# Video room endpoints
@app.post("/api/rooms")
def create_video_room(room_data: dict):
    room_id = str(uuid.uuid4())
    return {
        "roomId": room_id,
        "roomUrl": f"https://meet.prime-interviews.com/room/{room_id}",
        "participantToken": f"participant_{uuid.uuid4()}",
        "mentorToken": f"mentor_{uuid.uuid4()}",
        "expiresAt": "2024-01-20T23:59:59Z"
    }

@app.get("/api/rooms/{room_id}/status")
def get_room_status(room_id: str):
    return {
        "roomId": room_id,
        "status": "active",
        "participants": [
            {
                "name": "John Doe",
                "role": "participant",
                "joinedAt": datetime.now().isoformat(),
                "isActive": True
            }
        ],
        "recordingUrl": None,
        "duration": None
    }

# Email endpoint (keep existing)
from app.email_service import email_service

class EmailRequest(BaseModel):
    to: EmailStr
    toName: Optional[str] = None
    subject: str
    html: str

@app.post("/api/send-email")
async def send_email(email_request: EmailRequest):
    if not email_service.is_configured():
        raise HTTPException(status_code=500, detail="Email service not configured")

    success = await email_service.send_email(
        to_email=email_request.to,
        to_name=email_request.toName,
        subject=email_request.subject,
        html_content=email_request.html
    )

    return {"success": success, "message": "Email sent successfully" if success else "Failed to send email"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)