"""
Live interview orchestration service for managing real-time interviews
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import asyncio
import json
import logging
from enum import Enum

from app.core.database import get_db
from app.core.websocket import connection_manager, MessageType, WebSocketMessage
from app.models.interview import Interview, InterviewResponse
from app.models.job import Application
from app.models.company import User
from app.services.notification_service import NotificationService, MessageService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class InterviewState(str, Enum):
    """Interview states"""
    WAITING = "waiting"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class InterviewOrchestrator:
    """Orchestrates live interviews with real-time communication"""
    
    def __init__(self):
        self.active_interviews: Dict[str, Dict[str, Any]] = {}
        self.ai_service = AIService()
    
    async def start_interview(
        self,
        interview_id: str,
        interviewer_id: str,
        candidate_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Start a live interview session"""
        try:
            # Get interview details
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Initialize interview session
            session_data = {
                "interview_id": interview_id,
                "interviewer_id": interviewer_id,
                "candidate_id": candidate_id,
                "state": InterviewState.WAITING,
                "start_time": datetime.utcnow(),
                "participants": [interviewer_id, candidate_id],
                "room_id": f"interview_{interview_id}",
                "webrtc_room": f"prime-interview-{interview_id}",
                "daily_room_url": None,
                "conversation_history": [],
                "current_question": None,
                "question_index": 0,
                "metadata": {
                    "interview_type": interview.type,
                    "template_id": interview.template_id,
                    "application_id": interview.application_id
                }
            }
            
            self.active_interviews[interview_id] = session_data
            
            # Create WebSocket room for interview
            for participant_id in session_data["participants"]:
                connection_manager.join_room(participant_id, session_data["room_id"])
            
            # Update interview status in database
            interview.status = "in_progress"
            interview.started_at = datetime.utcnow()
            db.commit()
            
            # Notify participants
            await NotificationService.notify_interview_starting(
                interview_id=interview_id,
                participants=session_data["participants"],
                db=db
            )
            
            # Send initial interview data to participants
            await self._broadcast_interview_update(interview_id, {
                "action": "interview_started",
                "session_data": {
                    "interview_id": interview_id,
                    "room_id": session_data["room_id"],
                    "webrtc_room": session_data["webrtc_room"],
                    "state": session_data["state"],
                    "participants": session_data["participants"]
                }
            })
            
            logger.info(f"Interview {interview_id} started successfully")
            return session_data
            
        except Exception as e:
            logger.error(f"Error starting interview {interview_id}: {e}")
            await self._handle_interview_error(interview_id, str(e))
            raise
    
    async def join_interview(
        self,
        interview_id: str,
        user_id: str,
        connection_type: str = "webrtc"
    ) -> Dict[str, Any]:
        """Handle participant joining an interview"""
        try:
            if interview_id not in self.active_interviews:
                raise ValueError(f"Interview {interview_id} not found or not active")
            
            session = self.active_interviews[interview_id]
            
            if user_id not in session["participants"]:
                raise ValueError(f"User {user_id} not authorized for interview {interview_id}")
            
            # Add user to WebSocket room
            connection_manager.join_room(user_id, session["room_id"])
            
            # Update session state
            if session["state"] == InterviewState.WAITING:
                session["state"] = InterviewState.CONNECTING
            
            # Broadcast join event
            await self._broadcast_interview_update(interview_id, {
                "action": "participant_joined",
                "user_id": user_id,
                "connection_type": connection_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # If this is an AI interview, start the conversation
            if session["metadata"]["interview_type"] == "live_ai":
                await self._start_ai_conversation(interview_id, user_id)
            
            logger.info(f"User {user_id} joined interview {interview_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error joining interview {interview_id}: {e}")
            raise
    
    async def handle_webrtc_signal(
        self,
        interview_id: str,
        sender_id: str,
        signal_type: str,
        signal_data: Any
    ):
        """Handle WebRTC signaling between participants"""
        try:
            if interview_id not in self.active_interviews:
                logger.warning(f"Received signal for inactive interview {interview_id}")
                return
            
            session = self.active_interviews[interview_id]
            
            # Relay signal to other participants
            await MessageService.send_interview_signal(
                interview_id=interview_id,
                sender_id=sender_id,
                signal_type=signal_type,
                signal_data=signal_data
            )
            
            # Handle specific signal types
            if signal_type == "connection_established":
                if session["state"] == InterviewState.CONNECTING:
                    session["state"] = InterviewState.CONNECTED
                    await self._broadcast_interview_update(interview_id, {
                        "action": "connection_established",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif signal_type == "connection_failed":
                logger.warning(f"WebRTC connection failed for interview {interview_id}")
                await self._handle_connection_fallback(interview_id)
            
            logger.debug(f"WebRTC signal relayed: {signal_type} for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error handling WebRTC signal: {e}")
    
    async def send_chat_message(
        self,
        interview_id: str,
        sender_id: str,
        message: str,
        message_type: str = "text"
    ):
        """Send chat message during interview"""
        try:
            if interview_id not in self.active_interviews:
                raise ValueError(f"Interview {interview_id} not active")
            
            session = self.active_interviews[interview_id]
            room_id = session["room_id"]
            
            # Add message to conversation history
            message_data = {
                "sender_id": sender_id,
                "message": message,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            session["conversation_history"].append(message_data)
            
            # Broadcast message to room
            await MessageService.send_chat_message(
                room_id=room_id,
                sender_id=sender_id,
                message=message,
                message_type=message_type
            )
            
            logger.info(f"Chat message sent in interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
    
    async def pause_interview(self, interview_id: str, user_id: str):
        """Pause an active interview"""
        try:
            if interview_id not in self.active_interviews:
                raise ValueError(f"Interview {interview_id} not active")
            
            session = self.active_interviews[interview_id]
            session["state"] = InterviewState.PAUSED
            session["paused_at"] = datetime.utcnow()
            
            await self._broadcast_interview_update(interview_id, {
                "action": "interview_paused",
                "paused_by": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Interview {interview_id} paused by user {user_id}")
            
        except Exception as e:
            logger.error(f"Error pausing interview: {e}")
    
    async def resume_interview(self, interview_id: str, user_id: str):
        """Resume a paused interview"""
        try:
            if interview_id not in self.active_interviews:
                raise ValueError(f"Interview {interview_id} not active")
            
            session = self.active_interviews[interview_id]
            session["state"] = InterviewState.IN_PROGRESS
            session["resumed_at"] = datetime.utcnow()
            
            await self._broadcast_interview_update(interview_id, {
                "action": "interview_resumed",
                "resumed_by": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Interview {interview_id} resumed by user {user_id}")
            
        except Exception as e:
            logger.error(f"Error resuming interview: {e}")
    
    async def end_interview(
        self,
        interview_id: str,
        ended_by: str,
        db: Session
    ):
        """End an active interview"""
        try:
            if interview_id not in self.active_interviews:
                logger.warning(f"Attempting to end inactive interview {interview_id}")
                return
            
            session = self.active_interviews[interview_id]
            session["state"] = InterviewState.COMPLETED
            session["end_time"] = datetime.utcnow()
            
            # Update database
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if interview:
                interview.status = "completed"
                interview.completed_at = datetime.utcnow()
                interview.metadata = json.dumps({
                    **json.loads(interview.metadata or "{}"),
                    "conversation_history": session["conversation_history"],
                    "duration_minutes": (session["end_time"] - session["start_time"]).total_seconds() / 60
                })
                db.commit()
            
            # Notify participants
            await NotificationService.notify_interview_completed(
                interview_id=interview_id,
                participants=session["participants"],
                db=db
            )
            
            # Broadcast end event
            await self._broadcast_interview_update(interview_id, {
                "action": "interview_ended",
                "ended_by": ended_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Clean up WebSocket rooms
            for participant_id in session["participants"]:
                connection_manager.leave_room(participant_id, session["room_id"])
            
            # Remove from active interviews
            del self.active_interviews[interview_id]
            
            logger.info(f"Interview {interview_id} ended successfully")
            
        except Exception as e:
            logger.error(f"Error ending interview {interview_id}: {e}")
    
    async def _start_ai_conversation(self, interview_id: str, candidate_id: str):
        """Start AI conversation for live AI interviews"""
        try:
            session = self.active_interviews[interview_id]
            
            # Generate first question using AI service
            first_question = await self.ai_service.generate_interview_question(
                job_context="Software Engineer",  # This would come from the job details
                conversation_history=[],
                question_type="opening"
            )
            
            session["current_question"] = first_question
            session["state"] = InterviewState.IN_PROGRESS
            
            # Send first question to candidate
            await self._broadcast_interview_update(interview_id, {
                "action": "ai_question",
                "question": first_question,
                "question_index": session["question_index"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"AI conversation started for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error starting AI conversation: {e}")
    
    async def handle_candidate_response(
        self,
        interview_id: str,
        candidate_id: str,
        response: str,
        response_type: str = "text"
    ):
        """Handle candidate response in AI interview"""
        try:
            if interview_id not in self.active_interviews:
                return
            
            session = self.active_interviews[interview_id]
            
            # Add response to conversation history
            response_data = {
                "speaker": "candidate",
                "content": response,
                "type": response_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            session["conversation_history"].append(response_data)
            
            # Generate next question or follow-up
            next_question = await self.ai_service.generate_follow_up_question(
                conversation_history=session["conversation_history"],
                current_response=response
            )
            
            if next_question:
                session["current_question"] = next_question
                session["question_index"] += 1
                
                # Send next question
                await self._broadcast_interview_update(interview_id, {
                    "action": "ai_question",
                    "question": next_question,
                    "question_index": session["question_index"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                # Interview completed
                await self.end_interview(interview_id, "ai_system", next(get_db()))
            
        except Exception as e:
            logger.error(f"Error handling candidate response: {e}")
    
    async def _handle_connection_fallback(self, interview_id: str):
        """Handle WebRTC connection failure by switching to Daily.co"""
        try:
            session = self.active_interviews[interview_id]
            
            # Create Daily.co room (this would call Daily.co API)
            daily_room_url = f"https://prime.daily.co/interview-{interview_id}"
            session["daily_room_url"] = daily_room_url
            
            # Notify participants to switch to Daily.co
            await self._broadcast_interview_update(interview_id, {
                "action": "switch_to_daily",
                "daily_room_url": daily_room_url,
                "message": "Switching to backup video service for better connection",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Switched interview {interview_id} to Daily.co fallback")
            
        except Exception as e:
            logger.error(f"Error handling connection fallback: {e}")
    
    async def _broadcast_interview_update(self, interview_id: str, update_data: Dict[str, Any]):
        """Broadcast update to all interview participants"""
        try:
            if interview_id not in self.active_interviews:
                return
            
            session = self.active_interviews[interview_id]
            room_id = session["room_id"]
            
            message = WebSocketMessage(
                type=MessageType.INTERVIEW_STATUS,
                data={
                    "interview_id": interview_id,
                    **update_data
                }
            )
            
            await connection_manager.broadcast_to_room(room_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting interview update: {e}")
    
    async def _handle_interview_error(self, interview_id: str, error_message: str):
        """Handle interview errors"""
        try:
            if interview_id in self.active_interviews:
                session = self.active_interviews[interview_id]
                session["state"] = InterviewState.ERROR
                session["error_message"] = error_message
                
                await self._broadcast_interview_update(interview_id, {
                    "action": "interview_error",
                    "error": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.error(f"Interview {interview_id} error: {error_message}")
            
        except Exception as e:
            logger.error(f"Error handling interview error: {e}")
    
    def get_active_interviews(self) -> List[str]:
        """Get list of active interview IDs"""
        return list(self.active_interviews.keys())
    
    def get_interview_session(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get interview session data"""
        return self.active_interviews.get(interview_id)
    
    def is_interview_active(self, interview_id: str) -> bool:
        """Check if interview is active"""
        return interview_id in self.active_interviews


# Global orchestrator instance
interview_orchestrator = InterviewOrchestrator()