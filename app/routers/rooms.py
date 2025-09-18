from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import VideoRoom, Session, User
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user

router = APIRouter(prefix="/api", tags=["Video Rooms"])

@router.post("/rooms",
            response_model=dict,
            status_code=status.HTTP_201_CREATED,
            summary="Create video call room for interview sessions",
            description="Create a video call room using HMS (100ms) for interview sessions")
async def create_video_room(
    room_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create video call room"""
    try:
        # Verify session exists and user has access
        session_result = await db.execute(
            select(Session, User).join(User, Session.user_id == User.id)
            .where(Session.id == room_data.get("sessionId"))
        )
        session_data = session_result.first()

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session, user = session_data

        # Generate room ID and tokens (mock implementation)
        room_id = str(uuid.uuid4())
        room_url = f"https://meet.prime-interviews.com/room/{room_id}"
        participant_token = f"participant_{uuid.uuid4()}"
        mentor_token = f"mentor_{uuid.uuid4()}"
        expires_at = datetime.now().replace(hour=23, minute=59, second=59)

        # Create video room record
        video_room = VideoRoom(
            room_id=room_id,
            session_id=uuid.UUID(room_data.get("sessionId")),
            room_url=room_url,
            participant_token=participant_token,
            mentor_token=mentor_token,
            status='active'
        )

        db.add(video_room)
        await db.commit()

        return {
            "roomId": room_id,
            "roomUrl": room_url,
            "participantToken": participant_token,
            "mentorToken": mentor_token,
            "expiresAt": expires_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create video room: {str(e)}"
        )

@router.get("/rooms/{room_id}/status",
           response_model=dict,
           summary="Get room status and participants",
           description="Get current status of video call room and participant information")
async def get_room_status(
    room_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get video room status"""
    try:
        # Get room
        room_result = await db.execute(
            select(VideoRoom).where(VideoRoom.room_id == room_id)
        )
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )

        # Mock participants data (in real implementation, this would come from HMS API)
        participants = [
            {
                "name": "John Doe",
                "role": "participant",
                "joinedAt": datetime.now().isoformat(),
                "isActive": True
            }
        ]

        return {
            "roomId": room.room_id,
            "status": room.status,
            "participants": participants,
            "recordingUrl": room.recording_url,
            "duration": room.actual_duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get room status: {str(e)}"
        )