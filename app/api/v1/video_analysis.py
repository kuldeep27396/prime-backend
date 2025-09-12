"""
Video analysis API endpoints for proctoring and assessment
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import tempfile
import os

from app.api.deps import get_current_user, get_db
from app.models.company import User
from app.services.video_analysis_service import video_analysis_service
from pydantic import BaseModel, Field

router = APIRouter()


class VideoAnalysisRequest(BaseModel):
    """Request schema for video analysis"""
    video_url: str = Field(..., description="URL or path to the video file")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis: integrity, engagement, professionalism, comprehensive")
    cost_tier: str = Field(default="standard", description="Cost optimization tier: basic, standard, premium")


class RealTimeProctoringRequest(BaseModel):
    """Request schema for real-time proctoring"""
    frame_data: str = Field(..., description="Base64 encoded frame data")
    session_id: str = Field(..., description="Interview or assessment session ID")
    timestamp: float = Field(..., description="Timestamp of the frame")


class VideoAnalysisResponse(BaseModel):
    """Response schema for video analysis"""
    success: bool
    analysis_results: Dict[str, Any] = {}
    error: Optional[str] = None


class RealTimeProctoringResponse(BaseModel):
    """Response schema for real-time proctoring"""
    success: bool
    integrity_score: float
    engagement_score: float
    alerts: list = []
    recommendations: list = []
    error: Optional[str] = None


@router.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(
    request: VideoAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a video file for proctoring and assessment
    """
    try:
        # Validate analysis type
        valid_types = ["integrity", "engagement", "professionalism", "comprehensive"]
        if request.analysis_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis type. Must be one of: {valid_types}"
            )
        
        # Validate cost tier
        valid_tiers = ["basic", "standard", "premium"]
        if request.cost_tier not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cost tier. Must be one of: {valid_tiers}"
            )
        
        # Perform video analysis
        result = await video_analysis_service.analyze_video_file(
            video_path=request.video_url,
            analysis_type=request.analysis_type,
            cost_tier=request.cost_tier
        )
        
        return VideoAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis failed: {str(e)}"
        )


@router.post("/upload-and-analyze")
async def upload_and_analyze_video(
    file: UploadFile = File(...),
    analysis_type: str = "comprehensive",
    cost_tier: str = "standard",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and analyze a video file
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a video"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Analyze the video
            result = await video_analysis_service.analyze_video_file(
                video_path=temp_file_path,
                analysis_type=analysis_type,
                cost_tier=cost_tier
            )
            
            return VideoAnalysisResponse(**result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video upload and analysis failed: {str(e)}"
        )


@router.post("/real-time-proctoring", response_model=RealTimeProctoringResponse)
async def real_time_proctoring(
    request: RealTimeProctoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform real-time proctoring analysis on a video frame
    """
    try:
        # Prepare session context
        session_context = {
            "session_id": request.session_id,
            "user_id": str(current_user.id),
            "timestamp": request.timestamp
        }
        
        # Perform real-time analysis
        result = await video_analysis_service.real_time_proctoring(
            frame_data=request.frame_data,
            session_context=session_context
        )
        
        return RealTimeProctoringResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Real-time proctoring failed: {str(e)}"
        )


@router.get("/analysis-history/{session_id}")
async def get_analysis_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analysis history for a specific session
    """
    try:
        # In a real implementation, this would fetch from database
        # For now, return a placeholder response
        return {
            "session_id": session_id,
            "analysis_history": [],
            "summary": {
                "total_frames_analyzed": 0,
                "average_integrity_score": 0.0,
                "average_engagement_score": 0.0,
                "total_alerts": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis history: {str(e)}"
        )


@router.get("/proctoring-stats")
async def get_proctoring_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall proctoring statistics for the current user/company
    """
    try:
        # In a real implementation, this would aggregate data from database
        return {
            "total_sessions_monitored": 0,
            "integrity_violations_detected": 0,
            "average_integrity_score": 0.85,
            "average_engagement_score": 0.78,
            "most_common_violations": [
                {"type": "looking_away", "count": 0},
                {"type": "multiple_people", "count": 0},
                {"type": "unauthorized_materials", "count": 0}
            ],
            "recommendations": [
                "Consider providing clearer proctoring guidelines to candidates",
                "Ensure adequate lighting requirements are communicated",
                "Review camera positioning recommendations"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve proctoring statistics: {str(e)}"
        )


@router.post("/test-vision-api")
async def test_vision_api(
    current_user: User = Depends(get_current_user)
):
    """
    Test the vision API connectivity and functionality
    """
    try:
        # Test with a simple base64 encoded test image (1x1 pixel)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        result = await video_analysis_service.real_time_proctoring(
            frame_data=test_image,
            session_context={"session_id": "test", "user_id": "test"}
        )
        
        return {
            "api_status": "operational" if result["success"] else "error",
            "test_result": result,
            "message": "Vision API test completed successfully" if result["success"] else "Vision API test failed"
        }
        
    except Exception as e:
        return {
            "api_status": "error",
            "test_result": None,
            "message": f"Vision API test failed: {str(e)}"
        }