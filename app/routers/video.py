from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import time
import hashlib
import hmac
import json
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["Video"])

class VideoTokenRequest(BaseModel):
    room_id: str = Field(..., description="Video room ID", example="interview-room-123")
    user_id: str = Field(..., description="User ID requesting the token", example="user_123")
    role: str = Field("host", description="User role in the video call", example="host")
    duration: int = Field(3600, description="Token duration in seconds", example=3600)

class VideoTokenResponse(BaseModel):
    success: bool = Field(..., description="Whether token generation was successful")
    token: Optional[str] = Field(None, description="Generated video token")
    room_id: str = Field(..., description="Video room ID")
    app_id: Optional[str] = Field(None, description="Video app ID")
    endpoint: Optional[str] = Field(None, description="Video service endpoint")
    expires_at: Optional[str] = Field(None, description="Token expiration time")
    message: str = Field(..., description="Status message")

class VideoRoomRequest(BaseModel):
    session_id: str = Field(..., description="Associated session ID", example="session_123")
    participant_name: str = Field(..., description="Participant name", example="John Doe")
    mentor_name: str = Field(..., description="Mentor name", example="Jane Smith")
    duration: int = Field(3600, description="Room duration in seconds", example=3600)
    record_session: bool = Field(True, description="Whether to record the session")

class VideoRoomResponse(BaseModel):
    success: bool = Field(..., description="Whether room creation was successful")
    room_id: str = Field(..., description="Created room ID")
    room_code: Optional[str] = Field(None, description="Room access code")
    host_token: Optional[str] = Field(None, description="Host token")
    participant_token: Optional[str] = Field(None, description="Participant token")
    recording_enabled: bool = Field(..., description="Whether recording is enabled")
    expires_at: Optional[str] = Field(None, description="Room expiration time")
    message: str = Field(..., description="Status message")

# Video token generation endpoint
@router.post("/generate-hms-token",
            response_model=VideoTokenResponse,
            status_code=status.HTTP_200_OK,
            summary="Generate HMS video token",
            description="Generate authentication token for 100ms video service")
async def generate_hms_token(request: VideoTokenRequest):
    """Generate HMS video token"""
    try:
        # Mock HMS token generation - in production, this would use the 100ms Management API
        # For demonstration, we'll create a mock JWT-like token

        # Token payload
        current_time = int(time.time())
        expires_at = current_time + request.duration

        payload = {
            "sub": request.user_id,
            "room_id": request.room_id,
            "role": request.role,
            "iat": current_time,
            "exp": expires_at,
            "jti": str(uuid.uuid4())
        }

        # Mock token creation (in production, use proper JWT signing with HMS credentials)
        token_data = json.dumps(payload)
        mock_token = f"hms_mock_{hashlib.sha256(token_data.encode()).hexdigest()[:32]}"

        return VideoTokenResponse(
            success=True,
            token=mock_token,
            room_id=request.room_id,
            app_id="hms_app_mock",  # Mock app ID
            endpoint="https://prod-in.100ms.live",  # 100ms production endpoint
            expires_at=datetime.fromtimestamp(expires_at).isoformat(),
            message="Video token generated successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video token: {str(e)}"
        )

# Enhanced video room creation with token generation
@router.post("/video-rooms",
            response_model=VideoRoomResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create video room with tokens",
            description="Create a new video room and generate tokens for host and participant")
async def create_video_room_with_tokens(request: VideoRoomRequest):
    """Create video room with pre-generated tokens"""
    try:
        # Generate room ID
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        room_code = f"{uuid.uuid4().hex[:6].upper()}"

        # Calculate expiration
        expires_at = datetime.now() + timedelta(seconds=request.duration)

        # Generate host token
        host_token_request = VideoTokenRequest(
            room_id=room_id,
            user_id=f"host_{request.session_id}",
            role="host",
            duration=request.duration
        )
        host_token_response = await generate_hms_token(host_token_request)

        # Generate participant token
        participant_token_request = VideoTokenRequest(
            room_id=room_id,
            user_id=f"participant_{request.session_id}",
            role="guest",
            duration=request.duration
        )
        participant_token_response = await generate_hms_token(participant_token_request)

        return VideoRoomResponse(
            success=True,
            room_id=room_id,
            room_code=room_code,
            host_token=host_token_response.token,
            participant_token=participant_token_response.token,
            recording_enabled=request.record_session,
            expires_at=expires_at.isoformat(),
            message="Video room created successfully with tokens"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create video room: {str(e)}"
        )

# Get video room status
@router.get("/video-rooms/{room_id}/status",
            summary="Get video room status",
            description="Get current status and participants in a video room")
async def get_video_room_status(room_id: str):
    """Get video room status"""
    try:
        # Mock room status - in production, this would query the 100ms API
        mock_participants = [
            {
                "user_id": "host_123",
                "name": "Jane Smith",
                "role": "host",
                "joined_at": "2024-01-15T14:00:00Z",
                "status": "active"
            },
            {
                "user_id": "participant_456",
                "name": "John Doe",
                "role": "guest",
                "joined_at": "2024-01-15T14:05:00Z",
                "status": "active"
            }
        ]

        return {
            "success": True,
            "room_id": room_id,
            "status": "active",
            "participant_count": len(mock_participants),
            "participants": mock_participants,
            "recording": {
                "enabled": True,
                "status": "recording",
                "started_at": "2024-01-15T14:00:00Z",
                "duration_minutes": 5
            },
            "created_at": "2024-01-15T14:00:00Z",
            "expires_at": "2024-01-15T15:00:00Z"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video room status: {str(e)}"
        )

# Validate video token
@router.post("/validate-video-token",
            summary="Validate video token",
            description="Validate a video token and return its payload")
async def validate_video_token(token: str):
    """Validate video token"""
    try:
        # Mock token validation - in production, this would properly validate JWT tokens
        if not token.startswith("hms_mock_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

        # Extract mock token data
        token_hash = token.replace("hms_mock_", "")

        # Mock token payload
        current_time = int(time.time())
        payload = {
            "sub": "user_123",
            "room_id": "room_abc123",
            "role": "host",
            "iat": current_time - 3600,
            "exp": current_time + 3600,
            "jti": str(uuid.uuid4()),
            "valid": True
        }

        return {
            "success": True,
            "valid": True,
            "payload": payload,
            "message": "Token is valid"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate token: {str(e)}"
        )