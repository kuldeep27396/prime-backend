from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import Session, User, Mentor, VideoRoom
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionWithMentorResponse,
    SessionListResponse, SessionStats, SessionCreateResponse, VideoRoomCreate,
    VideoRoomResponse, VideoRoomStatusResponse, ParticipantInfo
)
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user
from app.email_service import email_service

router = APIRouter(prefix="/api", tags=["Sessions"])

@router.post("/sessions",
            response_model=SessionCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create new interview session booking",
            description="Create a new interview session booking with mentor")
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create new interview session"""
    try:
        # Get user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify mentor exists and is active
        mentor_result = await db.execute(
            select(Mentor).where(
                and_(Mentor.id == session_data.mentorId, Mentor.is_active == True)
            )
        )
        mentor = mentor_result.scalar_one_or_none()

        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found or inactive"
            )

        # Check for time slot conflicts
        conflict_result = await db.execute(
            select(Session).where(
                and_(
                    Session.mentor_id == session_data.mentorId,
                    Session.scheduled_at == session_data.scheduledAt,
                    Session.status.in_(['pending', 'confirmed'])
                )
            )
        )
        conflict_session = conflict_result.scalar_one_or_none()

        if conflict_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected time slot is no longer available"
            )

        # Generate meeting link if not provided
        meeting_link = session_data.meetingLink
        if not meeting_link and session_data.meetingType == "video":
            # Generate a unique meeting room URL
            room_id = str(uuid.uuid4())
            meeting_link = f"https://meet.prime-interviews.com/room/{room_id}"

        # Create session
        session = Session(
            user_id=user.id,
            mentor_id=uuid.UUID(session_data.mentorId),
            session_type=session_data.sessionType,
            scheduled_at=session_data.scheduledAt,
            duration=session_data.duration,
            meeting_type=session_data.meetingType.value,
            meeting_link=meeting_link,
            record_session=session_data.recordSession,
            special_requests=session_data.specialRequests,
            status='pending'
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Send confirmation email
        email_sent = False
        try:
            if email_service.is_configured():
                participant_email = session_data.participantEmail or user.email
                participant_name = session_data.participantName or f"{user.first_name} {user.last_name}"

                # Create email content
                email_subject = f"Interview Confirmation: {session_data.sessionType}"
                email_html = f"""
                <h2>Interview Confirmation</h2>
                <p>Dear {participant_name},</p>
                <p>Your interview has been scheduled successfully!</p>

                <h3>Details:</h3>
                <ul>
                    <li><strong>Mentor:</strong> {mentor.name}</li>
                    <li><strong>Company:</strong> {mentor.current_company}</li>
                    <li><strong>Type:</strong> {session_data.sessionType}</li>
                    <li><strong>Date & Time:</strong> {session_data.scheduledAt.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li><strong>Duration:</strong> {session_data.duration} minutes</li>
                    <li><strong>Meeting Type:</strong> {session_data.meetingType.value}</li>
                </ul>

                {f'<p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>' if meeting_link else ''}

                <p>Best regards,<br>Prime Interviews Team</p>
                """

                email_sent = await email_service.send_email(
                    to_email=participant_email,
                    to_name=participant_name,
                    subject=email_subject,
                    html_content=email_html
                )
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")

        return SessionCreateResponse(
            success=True,
            session=SessionResponse(
                id=str(session.id),
                userId=str(session.user_id),
                mentorId=str(session.mentor_id),
                sessionType=session.session_type,
                scheduledAt=session.scheduled_at,
                duration=session.duration,
                meetingType=session.meeting_type,
                meetingLink=session.meeting_link,
                status=session.status,
                recordSession=session.record_session,
                specialRequests=session.special_requests,
                rating=session.rating,
                feedback=session.feedback,
                cancellationReason=session.cancellation_reason,
                recordingUrl=session.recording_url,
                createdAt=session.created_at,
                updatedAt=session.updated_at
            ),
            emailSent=email_sent
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions",
           response_model=SessionListResponse,
           summary="Get user's session history and upcoming sessions",
           description="Get paginated list of user's sessions with filtering")
async def get_user_sessions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    page: int = Query(1, ge=1, description="Page number"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's sessions"""
    try:
        # Get user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build query
        query = select(Session, Mentor).join(Mentor, Session.mentor_id == Mentor.id).where(Session.user_id == user.id)

        if status_filter:
            if status_filter == "upcoming":
                query = query.where(Session.status.in_(['pending', 'confirmed']))
            else:
                query = query.where(Session.status == status_filter)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(Session.scheduled_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        sessions_data = result.all()

        # Format response
        sessions = []
        for session, mentor in sessions_data:
            sessions.append(SessionWithMentorResponse(
                id=str(session.id),
                userId=str(session.user_id),
                mentorId=str(session.mentor_id),
                mentorName=mentor.name,
                mentorAvatar=mentor.avatar,
                mentorCompany=mentor.current_company,
                sessionType=session.session_type,
                scheduledAt=session.scheduled_at,
                duration=session.duration,
                meetingType=session.meeting_type,
                meetingLink=session.meeting_link,
                status=session.status,
                recordSession=session.record_session,
                specialRequests=session.special_requests,
                rating=session.rating,
                feedback=session.feedback,
                cancellationReason=session.cancellation_reason,
                recordingUrl=session.recording_url,
                createdAt=session.created_at,
                updatedAt=session.updated_at
            ))

        # Get statistics
        stats_result = await db.execute(
            select(
                func.count(Session.id).label('total_sessions'),
                func.count(Session.id).filter(Session.status == 'completed').label('completed_sessions'),
                func.count(Session.id).filter(Session.status.in_(['pending', 'confirmed'])).label('upcoming_sessions'),
                func.avg(Session.rating).filter(Session.rating.isnot(None)).label('average_rating'),
                func.sum(Session.duration).filter(Session.status == 'completed').label('total_minutes')
            )
            .where(Session.user_id == user.id)
        )
        stats = stats_result.first()

        session_stats = {
            "totalSessions": stats.total_sessions or 0,
            "completedSessions": stats.completed_sessions or 0,
            "upcomingSessions": stats.upcoming_sessions or 0,
            "averageRating": float(stats.average_rating or 0),
            "totalHours": int((stats.total_minutes or 0) / 60)
        }

        return SessionListResponse(
            sessions=sessions,
            stats=session_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )

@router.patch("/sessions/{session_id}",
             response_model=SuccessResponse,
             summary="Update session status, add feedback, or cancel",
             description="Update session details including status, rating, and feedback")
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update session"""
    try:
        # Get user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get session
        session_result = await db.execute(
            select(Session).where(
                and_(Session.id == session_id, Session.user_id == user.id)
            )
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Update fields
        update_data = {}
        if session_update.status is not None:
            update_data["status"] = session_update.status.value
        if session_update.rating is not None:
            update_data["rating"] = session_update.rating
        if session_update.feedback is not None:
            update_data["feedback"] = session_update.feedback
        if session_update.cancellationReason is not None:
            update_data["cancellation_reason"] = session_update.cancellationReason

        if update_data:
            await db.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(**update_data)
            )
            await db.commit()

        return SuccessResponse(
            message="Session updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )

@router.post("/rooms",
            response_model=VideoRoomResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create video call room for interview sessions",
            description="Create a video call room using HMS (100ms) for interview sessions")
async def create_video_room(
    room_data: VideoRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create video call room"""
    try:
        # Verify session exists and user has access
        session_result = await db.execute(
            select(Session, User).join(User, Session.user_id == User.id)
            .where(Session.id == room_data.sessionId)
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
            session_id=uuid.UUID(room_data.sessionId),
            room_url=room_url,
            participant_token=participant_token,
            mentor_token=mentor_token,
            status='active'
        )

        db.add(video_room)
        await db.commit()

        return VideoRoomResponse(
            roomId=room_id,
            roomUrl=room_url,
            participantToken=participant_token,
            mentorToken=mentor_token,
            expiresAt=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create video room: {str(e)}"
        )

@router.get("/rooms/{room_id}/status",
           response_model=VideoRoomStatusResponse,
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
            ParticipantInfo(
                name="John Doe",
                role="participant",
                joinedAt=datetime.now(),
                isActive=True
            )
        ]

        return VideoRoomStatusResponse(
            roomId=room.room_id,
            status=room.status,
            participants=participants,
            recordingUrl=room.recording_url,
            duration=room.actual_duration
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get room status: {str(e)}"
        )