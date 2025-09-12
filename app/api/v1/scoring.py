"""
Scoring API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.company import User
from app.services.scoring_service import ScoringService, ScoringAnalytics
from app.models.job import Application

router = APIRouter()
scoring_service = ScoringService()


class ScoreCalculationRequest(BaseModel):
    application_id: str
    force_recalculate: bool = False


class BiasDetectionRequest(BaseModel):
    application_ids: List[str]
    demographic_data: Optional[dict] = None


class RankingRequest(BaseModel):
    application_ids: List[str]
    job_id: Optional[str] = None


class ConfidenceIntervalRequest(BaseModel):
    application_id: str
    confidence_level: float = 0.95


class PerformancePredictionRequest(BaseModel):
    application_id: str
    prediction_horizon_days: int = 180


@router.post("/calculate")
async def calculate_scores(
    request: ScoreCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate comprehensive AI scores for a candidate"""
    
    try:
        # Verify user has access to this application
        application = db.query(Application).filter(
            Application.id == request.application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.job.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate scores
        scores = await scoring_service.calculate_comprehensive_scores(
            request.application_id,
            db,
            request.force_recalculate
        )
        
        return {
            "success": True,
            "data": scores
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-detection")
async def detect_bias(
    request: BiasDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect potential bias in scoring across candidates"""
    
    try:
        # Verify user has access to these applications
        applications = db.query(Application).filter(
            Application.id.in_(request.application_ids)
        ).all()
        
        if not applications:
            raise HTTPException(status_code=404, detail="No applications found")
        
        # Check company access
        for app in applications:
            if app.job.company_id != current_user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Perform bias detection
        bias_analysis = await scoring_service.detect_bias_in_scores(
            request.application_ids,
            db,
            request.demographic_data
        )
        
        return {
            "success": True,
            "data": bias_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ranking")
async def generate_ranking(
    request: RankingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comparative ranking with percentiles"""
    
    try:
        # Verify user has access to these applications
        applications = db.query(Application).filter(
            Application.id.in_(request.application_ids)
        ).all()
        
        if not applications:
            raise HTTPException(status_code=404, detail="No applications found")
        
        # Check company access
        for app in applications:
            if app.job.company_id != current_user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate ranking
        ranking = await scoring_service.generate_comparative_ranking(
            request.application_ids,
            db,
            request.job_id
        )
        
        return {
            "success": True,
            "data": ranking
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confidence-intervals")
async def calculate_confidence_intervals(
    request: ConfidenceIntervalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate confidence intervals for scores"""
    
    try:
        # Verify user has access to this application
        application = db.query(Application).filter(
            Application.id == request.application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.job.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate confidence intervals
        intervals = await scoring_service.calculate_confidence_intervals(
            request.application_id,
            db,
            request.confidence_level
        )
        
        return {
            "success": True,
            "data": intervals
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance-prediction")
async def predict_performance(
    request: PerformancePredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict candidate's future performance based on historical patterns"""
    
    try:
        # Verify user has access to this application
        application = db.query(Application).filter(
            Application.id == request.application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.job.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Predict performance
        prediction = await scoring_service.predict_historical_performance(
            request.application_id,
            db,
            request.prediction_horizon_days
        )
        
        return {
            "success": True,
            "data": prediction
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/{application_id}")
async def get_application_scores(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scores for a specific application"""
    
    try:
        # Verify user has access to this application
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.job.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get existing scores
        from app.models.scoring import Score
        scores = db.query(Score).filter(
            Score.application_id == application_id
        ).all()
        
        if not scores:
            # Calculate scores if they don't exist
            score_data = await scoring_service.calculate_comprehensive_scores(
                application_id, db
            )
            return {
                "success": True,
                "data": score_data
            }
        
        # Format existing scores
        formatted_scores = await scoring_service._format_score_response(scores, application)
        
        return {
            "success": True,
            "data": formatted_scores
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trends")
async def get_scoring_trends(
    time_period_days: int = Query(30, description="Time period in days for trend analysis"),
    job_id: Optional[str] = Query(None, description="Filter by specific job"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scoring trends over time"""
    
    try:
        from app.models.scoring import Score
        from app.models.job import Job
        
        # Build query
        query = db.query(Score).join(Application).join(Job).filter(
            Job.company_id == current_user.company_id,
            Score.created_by == 'ai'
        )
        
        if job_id:
            query = query.filter(Job.id == job_id)
        
        scores = query.all()
        
        # Calculate trends
        trends = ScoringAnalytics.calculate_score_trends(scores, time_period_days)
        
        return {
            "success": True,
            "data": trends
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/correlations")
async def get_category_correlations(
    job_id: Optional[str] = Query(None, description="Filter by specific job"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get correlations between scoring categories"""
    
    try:
        from app.models.job import Job
        
        # Build query
        query = db.query(Application).join(Job).filter(
            Job.company_id == current_user.company_id
        )
        
        if job_id:
            query = query.filter(Job.id == job_id)
        
        applications = query.limit(1000).all()  # Limit for performance
        
        # Calculate correlations
        correlations = ScoringAnalytics.calculate_category_correlations(applications, db)
        
        return {
            "success": True,
            "data": correlations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_scoring_summary(
    job_id: Optional[str] = Query(None, description="Filter by specific job"),
    days_back: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive scoring analytics summary"""
    
    try:
        from app.models.scoring import Score
        from app.models.job import Job
        from datetime import datetime, timedelta
        import statistics
        
        # Get scores from the specified time period
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = db.query(Score).join(Application).join(Job).filter(
            Job.company_id == current_user.company_id,
            Score.created_by == 'ai',
            Score.created_at >= cutoff_date
        )
        
        if job_id:
            query = query.filter(Job.id == job_id)
        
        scores = query.all()
        
        if not scores:
            return {
                "success": True,
                "data": {
                    "message": "No scores found for the specified period",
                    "period_days": days_back
                }
            }
        
        # Calculate summary statistics
        category_stats = {}
        overall_scores = []
        
        for category in ['technical', 'communication', 'cultural_fit', 'cognitive', 'behavioral', 'overall']:
            category_scores = [float(s.score) for s in scores if s.category == category]
            
            if category_scores:
                category_stats[category] = {
                    "count": len(category_scores),
                    "mean": round(statistics.mean(category_scores), 2),
                    "median": round(statistics.median(category_scores), 2),
                    "std_dev": round(statistics.stdev(category_scores) if len(category_scores) > 1 else 0, 2),
                    "min": round(min(category_scores), 2),
                    "max": round(max(category_scores), 2)
                }
                
                if category == 'overall':
                    overall_scores = category_scores
        
        # Calculate grade distribution
        grade_distribution = {}
        for score_value in overall_scores:
            grade = scoring_service._score_to_grade(score_value)
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Calculate confidence statistics
        confidence_scores = [float(s.confidence) for s in scores if s.confidence is not None]
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
        
        summary = {
            "period_days": days_back,
            "total_scores": len(scores),
            "unique_applications": len(set(str(s.application_id) for s in scores)),
            "category_statistics": category_stats,
            "grade_distribution": grade_distribution,
            "average_confidence": round(avg_confidence, 2),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/application/{application_id}")
async def delete_application_scores(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all scores for a specific application"""
    
    try:
        # Verify user has access to this application
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.job.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete scores
        from app.models.scoring import Score
        deleted_count = db.query(Score).filter(
            Score.application_id == application_id
        ).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} scores for application {application_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))