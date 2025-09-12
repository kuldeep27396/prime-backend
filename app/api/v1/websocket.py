"""
WebSocket API endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional, Dict, Any
import json
import logging

from app.core.websocket import connection_manager, MessageType, WebSocketMessage, NotificationService
from app.core.security import decode_access_token
from app.api.deps import get_current_user
from app.models.company import User

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_user_from_token(token: str) -> Optional[User]:
    """Extract user from WebSocket token"""
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        # In a real implementation, you would fetch the user from database
        # For now, we'll create a minimal user object
        user = User()
        user.id = user_id
        return user
        
    except Exception as e:
        logger.error(f"Error decoding WebSocket token: {e}")
        return None


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: Optional[str] = None):
    """Main WebSocket endpoint for real-time communication"""
    
    # Authenticate user if token provided
    authenticated_user = None
    if token:
        authenticated_user = await get_user_from_token(token)
        if not authenticated_user or str(authenticated_user.id) != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Connect user
    await connection_manager.connect(
        websocket, 
        user_id,
        metadata={
            "authenticated": authenticated_user is not None,
            "user_type": getattr(authenticated_user, 'role', 'anonymous') if authenticated_user else 'anonymous'
        }
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await handle_client_message(user_id, message_data)
                
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Invalid JSON format"}
                )
                await connection_manager.send_personal_message(user_id, error_message)
                
            except Exception as e:
                logger.error(f"Error handling message from user {user_id}: {e}")
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Internal server error"}
                )
                await connection_manager.send_personal_message(user_id, error_message)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await connection_manager.disconnect(user_id)


async def handle_client_message(user_id: str, message_data: Dict[str, Any]):
    """Handle incoming messages from clients"""
    
    message_type = message_data.get("type")
    data = message_data.get("data", {})
    
    if message_type == "join_room":
        # Join a room for group communication
        room_id = data.get("room_id")
        if room_id:
            connection_manager.join_room(user_id, room_id)
            
            # Notify room about new user
            room_message = WebSocketMessage(
                type=MessageType.SYSTEM_ALERT,
                data={
                    "message": f"User {user_id} joined the room",
                    "user_id": user_id,
                    "action": "user_joined"
                },
                sender_id=user_id
            )
            await connection_manager.broadcast_to_room(room_id, room_message, exclude_user=user_id)
    
    elif message_type == "leave_room":
        # Leave a room
        room_id = data.get("room_id")
        if room_id:
            connection_manager.leave_room(user_id, room_id)
            
            # Notify room about user leaving
            room_message = WebSocketMessage(
                type=MessageType.SYSTEM_ALERT,
                data={
                    "message": f"User {user_id} left the room",
                    "user_id": user_id,
                    "action": "user_left"
                },
                sender_id=user_id
            )
            await connection_manager.broadcast_to_room(room_id, room_message, exclude_user=user_id)
    
    elif message_type == "chat_message":
        # Send chat message to room
        room_id = data.get("room_id")
        message = data.get("message")
        
        if room_id and message:
            chat_message = WebSocketMessage(
                type=MessageType.CHAT_MESSAGE,
                data={
                    "room_id": room_id,
                    "message": message,
                    "sender_id": user_id
                },
                sender_id=user_id
            )
            await connection_manager.broadcast_to_room(room_id, chat_message, exclude_user=user_id)
    
    elif message_type == "interview_signal":
        # Handle interview-specific signaling (WebRTC, etc.)
        interview_id = data.get("interview_id")
        signal_type = data.get("signal_type")
        signal_data = data.get("signal_data")
        
        if interview_id and signal_type:
            # Broadcast signal to interview room
            room_id = f"interview_{interview_id}"
            signal_message = WebSocketMessage(
                type=MessageType.INTERVIEW_STATUS,
                data={
                    "interview_id": interview_id,
                    "signal_type": signal_type,
                    "signal_data": signal_data,
                    "sender_id": user_id
                },
                sender_id=user_id
            )
            await connection_manager.broadcast_to_room(room_id, signal_message, exclude_user=user_id)
    
    elif message_type == "heartbeat_response":
        # Client responding to heartbeat - no action needed
        logger.debug(f"Heartbeat response from user {user_id}")
    
    else:
        # Unknown message type
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": f"Unknown message type: {message_type}"}
        )
        await connection_manager.send_personal_message(user_id, error_message)


# REST API endpoints for WebSocket management
@router.get("/connections")
async def get_active_connections(current_user: User = Depends(get_current_user)):
    """Get information about active WebSocket connections"""
    
    # Only allow admin users to view connections
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {
        "total_connections": connection_manager.get_connection_count(),
        "connected_users": connection_manager.get_connected_users(),
        "rooms": {room_id: users for room_id, users in connection_manager.rooms.items()}
    }


@router.post("/notify/{user_id}")
async def send_notification_to_user(
    user_id: str,
    notification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Send a notification to a specific user"""
    
    title = notification_data.get("title", "Notification")
    message = notification_data.get("message", "")
    notification_type = notification_data.get("type", "info")
    action_url = notification_data.get("action_url")
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    await NotificationService.send_notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        action_url=action_url
    )
    
    return {"status": "notification_sent", "user_id": user_id}


@router.post("/broadcast")
async def broadcast_system_alert(
    alert_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Broadcast a system-wide alert"""
    
    # Only allow admin users to broadcast
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    message = alert_data.get("message", "")
    alert_type = alert_data.get("type", "info")
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    await NotificationService.broadcast_system_alert(
        message=message,
        alert_type=alert_type,
        exclude_user=str(current_user.id)
    )
    
    return {"status": "alert_broadcasted", "message": message}


@router.post("/interview/{interview_id}/notify")
async def notify_interview_participants(
    interview_id: str,
    notification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Notify interview participants about status changes"""
    
    status_update = notification_data.get("status", "")
    participants = notification_data.get("participants", [])
    details = notification_data.get("details", {})
    
    if not status_update or not participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status and participants are required"
        )
    
    await NotificationService.notify_interview_status_change(
        interview_id=interview_id,
        status=status_update,
        participants=participants,
        details=details
    )
    
    return {
        "status": "participants_notified",
        "interview_id": interview_id,
        "participants_count": len(participants)
    }