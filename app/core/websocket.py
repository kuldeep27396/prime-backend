"""
WebSocket connection manager for real-time updates
"""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    INTERVIEW_STATUS = "interview_status"
    CANDIDATE_UPDATE = "candidate_update"
    NOTIFICATION = "notification"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_ALERT = "system_alert"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class WebSocketMessage:
    """WebSocket message structure"""
    
    def __init__(
        self,
        type: MessageType,
        data: Any,
        recipient_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.type = type
        self.data = data
        self.recipient_id = recipient_id
        self.sender_id = sender_id
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "recipient_id": self.recipient_id,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Room-based connections for group communications
        self.rooms: Dict[str, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Close existing connection if user reconnects
        if user_id in self.active_connections:
            await self.disconnect(user_id)
        
        self.active_connections[user_id] = websocket
        self.connection_metadata[user_id] = metadata or {}
        
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Send connection confirmation
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type=MessageType.SYSTEM_ALERT,
                data={"message": "Connected successfully", "status": "connected"}
            )
        )
        
        # Start heartbeat for this connection
        asyncio.create_task(self._heartbeat_loop(user_id))
    
    async def disconnect(self, user_id: str):
        """Disconnect a WebSocket connection"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket for user {user_id}: {e}")
            
            del self.active_connections[user_id]
            
            # Remove from all rooms
            for room_id in list(self.rooms.keys()):
                self.rooms[room_id].discard(user_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            
            # Clean up metadata
            self.connection_metadata.pop(user_id, None)
            
            logger.info(f"WebSocket connection closed for user {user_id}")
    
    async def send_personal_message(self, user_id: str, message: WebSocketMessage):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message.to_json())
                logger.debug(f"Message sent to user {user_id}: {message.type}")
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for user {user_id}")
                await self.disconnect(user_id)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                await self.disconnect(user_id)
    
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast a message to all users in a room"""
        if room_id not in self.rooms:
            logger.warning(f"Room {room_id} does not exist")
            return
        
        disconnected_users = []
        
        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
                
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                try:
                    await websocket.send_text(message.to_json())
                except WebSocketDisconnect:
                    disconnected_users.append(user_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
    
    async def broadcast_to_all(self, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast a message to all connected users"""
        disconnected_users = []
        
        for user_id in list(self.active_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
                
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message.to_json())
            except WebSocketDisconnect:
                disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
    
    def join_room(self, user_id: str, room_id: str):
        """Add a user to a room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        logger.info(f"User {user_id} joined room {room_id}")
    
    def leave_room(self, user_id: str, room_id: str):
        """Remove a user from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            logger.info(f"User {user_id} left room {room_id}")
    
    def get_room_users(self, room_id: str) -> List[str]:
        """Get all users in a room"""
        return list(self.rooms.get(room_id, set()))
    
    def get_connected_users(self) -> List[str]:
        """Get all connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is connected"""
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    async def _heartbeat_loop(self, user_id: str):
        """Send periodic heartbeat to maintain connection"""
        while user_id in self.active_connections:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if user_id in self.active_connections:
                    await self.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type=MessageType.HEARTBEAT,
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                    )
            except Exception as e:
                logger.error(f"Heartbeat error for user {user_id}: {e}")
                break


# Global connection manager instance
connection_manager = ConnectionManager()


class NotificationService:
    """Service for sending real-time notifications"""
    
    @staticmethod
    async def notify_interview_status_change(
        interview_id: str,
        status: str,
        participants: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        """Notify participants about interview status changes"""
        message = WebSocketMessage(
            type=MessageType.INTERVIEW_STATUS,
            data={
                "interview_id": interview_id,
                "status": status,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        for user_id in participants:
            await connection_manager.send_personal_message(user_id, message)
    
    @staticmethod
    async def notify_candidate_update(
        candidate_id: str,
        update_type: str,
        data: Dict[str, Any],
        recipients: List[str]
    ):
        """Notify about candidate updates"""
        message = WebSocketMessage(
            type=MessageType.CANDIDATE_UPDATE,
            data={
                "candidate_id": candidate_id,
                "update_type": update_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        for user_id in recipients:
            await connection_manager.send_personal_message(user_id, message)
    
    @staticmethod
    async def send_notification(
        user_id: str,
        title: str,
        message: str,
        type: str = "info",
        action_url: Optional[str] = None
    ):
        """Send a general notification to a user"""
        notification_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "title": title,
                "message": message,
                "type": type,
                "action_url": action_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await connection_manager.send_personal_message(user_id, notification_message)
    
    @staticmethod
    async def broadcast_system_alert(
        message: str,
        alert_type: str = "info",
        exclude_user: Optional[str] = None
    ):
        """Broadcast a system-wide alert"""
        alert_message = WebSocketMessage(
            type=MessageType.SYSTEM_ALERT,
            data={
                "message": message,
                "type": alert_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await connection_manager.broadcast_to_all(alert_message, exclude_user)