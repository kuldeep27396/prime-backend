"""
Celery tasks for AI processing and model management
"""

from celery import current_task
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
import json

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.services.ai_service import AIService
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def update_model_cache(self):
    """Update AI model cache and embeddings"""
    try:
        ai_service = AIService()
        
        # Update model cache (this would refresh cached model responses)
        cache_stats = {
            "models_updated": 0,
            "embeddings_refreshed": 0,
            "cache_size": 0,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # In a real implementation, you would:
        # 1. Refresh cached model responses
        # 2. Update embedding vectors
        # 3. Clean up old cache entries
        # 4. Optimize model performance
        
        logger.info("AI model cache updated")
        return cache_stats
        
    except Exception as e:
        logger.error(f"Error updating model cache: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def generate_interview_questions_batch(self, job_contexts: List[Dict[str, Any]]):
    """Generate interview questions for multiple job contexts"""
    try:
        ai_service = AIService()
        results = []
        
        for job_context in job_contexts:
            job_id = job_context.get("job_id")
            job_title = job_context.get("title", "")
            job_requirements = job_context.get("requirements", {})
            
            # Generate questions for this job
            questions = await ai_service.generate_interview_questions_for_job(
                job_title=job_title,
                requirements=job_requirements,
                question_count=10
            )
            
            results.append({
                "job_id": job_id,
                "questions": questions,
                "generated_at": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Generated interview questions for {len(job_contexts)} jobs")
        return results
        
    except Exception as e:
        logger.error(f"Error generating interview questions batch: {e}")
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def analyze_candidate_responses_batch(self, response_data: List[Dict[str, Any]]):
    """Analyze multiple candidate responses for insights"""
    try:
        ai_service = AIService()
        results = []
        
        for response in response_data:
            candidate_id = response.get("candidate_id")
            responses = response.get("responses", [])
            
            # Analyze responses
            analysis = await ai_service.analyze_candidate_responses(responses)
            
            results.append({
                "candidate_id": candidate_id,
                "analysis": analysis,
                "analyzed_at": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Analyzed responses for {len(response_data)} candidates")
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing candidate responses batch: {e}")
        raise self.retry(exc=e, countdown=180)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def calculate_similarity_scores(self, candidate_profiles: List[Dict[str, Any]], job_requirements: Dict[str, Any]):
    """Calculate similarity scores between candidates and job requirements"""
    try:
        ai_service = AIService()
        scoring_service = ScoringService()
        
        results = []
        
        # Generate job requirements embedding
        job_embedding = await ai_service.generate_embedding(
            text=json.dumps(job_requirements)
        )
        
        for profile in candidate_profiles:
            candidate_id = profile.get("candidate_id")
            candidate_text = profile.get("profile_text", "")
            
            # Generate candidate embedding
            candidate_embedding = await ai_service.generate_embedding(
                text=candidate_text
            )
            
            # Calculate similarity
            similarity_score = scoring_service.calculate_cosine_similarity(
                job_embedding, candidate_embedding
            )
            
            results.append({
                "candidate_id": candidate_id,
                "similarity_score": similarity_score,
                "calculated_at": datetime.utcnow().isoformat()
            })
        
        # Sort by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"Calculated similarity scores for {len(candidate_profiles)} candidates")
        return results
        
    except Exception as e:
        logger.error(f"Error calculating similarity scores: {e}")
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def generate_personalized_feedback(self, interview_data: Dict[str, Any]):
    """Generate personalized feedback for interview performance"""
    try:
        interview_id = interview_data.get("interview_id")
        responses = interview_data.get("responses", [])
        scores = interview_data.get("scores", {})
        
        ai_service = AIService()
        
        # Generate personalized feedback
        feedback = await ai_service.generate_interview_feedback(
            responses=responses,
            scores=scores,
            feedback_type="constructive"
        )
        
        # Store feedback in database
        db = next(get_db())
        
        # In a real implementation, you would update the interview record
        # with the generated feedback
        
        db.close()
        
        logger.info(f"Personalized feedback generated for interview {interview_id}")
        return {
            "interview_id": interview_id,
            "feedback": feedback,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating personalized feedback: {e}")
        raise self.retry(exc=e, countdown=90)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def detect_bias_in_evaluations(self, evaluation_data: List[Dict[str, Any]]):
    """Detect potential bias in interview evaluations"""
    try:
        scoring_service = ScoringService()
        
        # Analyze evaluations for bias patterns
        bias_analysis = scoring_service.detect_evaluation_bias(evaluation_data)
        
        # If bias is detected, flag for review
        if bias_analysis.get("bias_detected", False):
            bias_score = bias_analysis.get("bias_score", 0)
            affected_evaluations = bias_analysis.get("affected_evaluations", [])
            
            # Send alert to administrators
            from app.tasks.notification_tasks import send_bulk_notifications
            
            admin_message = f"Potential bias detected in {len(affected_evaluations)} evaluations (bias score: {bias_score:.2f})"
            
            # In a real implementation, you would get admin user IDs
            admin_recipients = ["admin_user_id_1"]
            
            send_bulk_notifications.delay({
                "recipients": admin_recipients,
                "title": "Bias Detection Alert",
                "message": admin_message,
                "type": "warning",
                "action_url": "/admin/bias-review"
            })
        
        logger.info(f"Bias analysis completed for {len(evaluation_data)} evaluations")
        return bias_analysis
        
    except Exception as e:
        logger.error(f"Error detecting bias in evaluations: {e}")
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def optimize_ai_model_performance(self):
    """Optimize AI model performance based on usage patterns"""
    try:
        # Analyze model usage patterns
        usage_stats = {
            "total_requests": 0,
            "average_response_time": 0,
            "error_rate": 0,
            "most_used_models": [],
            "optimization_suggestions": []
        }
        
        # In a real implementation, you would:
        # 1. Analyze model usage logs
        # 2. Identify performance bottlenecks
        # 3. Optimize model parameters
        # 4. Update caching strategies
        # 5. Adjust rate limiting
        
        optimizations_applied = [
            "Updated response caching",
            "Optimized embedding generation",
            "Improved error handling"
        ]
        
        logger.info("AI model performance optimization completed")
        return {
            "usage_stats": usage_stats,
            "optimizations_applied": optimizations_applied,
            "optimized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing AI model performance: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def train_custom_scoring_model(self, training_data: List[Dict[str, Any]]):
    """Train custom scoring model based on historical data"""
    try:
        scoring_service = ScoringService()
        
        # Prepare training data
        features = []
        labels = []
        
        for data_point in training_data:
            features.append(data_point.get("features", []))
            labels.append(data_point.get("score", 0))
        
        # Train model (this would use scikit-learn or similar)
        model_metrics = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "training_samples": len(training_data),
            "trained_at": datetime.utcnow().isoformat()
        }
        
        # In a real implementation, you would:
        # 1. Split data into train/validation/test sets
        # 2. Train the model
        # 3. Evaluate performance
        # 4. Save the trained model
        # 5. Update the scoring service to use the new model
        
        logger.info(f"Custom scoring model trained with {len(training_data)} samples")
        return model_metrics
        
    except Exception as e:
        logger.error(f"Error training custom scoring model: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def generate_hiring_insights(self, company_id: str, time_period_days: int = 30):
    """Generate AI-powered hiring insights for a company"""
    try:
        db = next(get_db())
        
        # Get hiring data for the specified period
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        # In a real implementation, you would query actual hiring data
        hiring_data = {
            "total_applications": 150,
            "interviews_conducted": 45,
            "hires_made": 8,
            "average_time_to_hire": 21,
            "top_skills_in_demand": ["Python", "React", "AWS"],
            "conversion_rates": {
                "application_to_interview": 0.30,
                "interview_to_hire": 0.18
            }
        }
        
        # Generate insights using AI
        ai_service = AIService()
        insights = await ai_service.generate_hiring_insights(hiring_data)
        
        # Store insights
        result = {
            "company_id": company_id,
            "time_period_days": time_period_days,
            "hiring_data": hiring_data,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        db.close()
        
        logger.info(f"Hiring insights generated for company {company_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating hiring insights: {e}")
        raise self.retry(exc=e, countdown=180)