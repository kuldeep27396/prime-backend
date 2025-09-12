"""
AI Scoring and Analytics Engine
Implements multi-factor scoring, explainable AI, bias detection, and analytics
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from scipy import stats
import asyncio

from app.core.database import get_db
from app.models.scoring import Score
from app.models.job import Application, Job
from app.models.company import User
from app.models.interview import Interview, InterviewResponse
from app.models.assessment import Assessment
from app.services.ai_service import GroqAIService

logger = logging.getLogger(__name__)


class ScoringService:
    """Comprehensive AI scoring and analytics service"""
    
    def __init__(self):
        self.ai_service = GroqAIService()
        
        # Scoring categories and weights
        self.scoring_categories = {
            "technical": {
                "weight": 0.30,
                "description": "Technical competency and problem-solving skills"
            },
            "communication": {
                "weight": 0.25,
                "description": "Communication skills and clarity of expression"
            },
            "cultural_fit": {
                "weight": 0.20,
                "description": "Alignment with company culture and values"
            },
            "cognitive": {
                "weight": 0.15,
                "description": "Cognitive ability and analytical thinking"
            },
            "behavioral": {
                "weight": 0.10,
                "description": "Behavioral traits and soft skills"
            }
        }
        
        # Bias detection thresholds
        self.bias_thresholds = {
            "demographic_parity": 0.8,  # Minimum acceptable parity
            "equalized_odds": 0.8,
            "statistical_significance": 0.05
        }
    
    async def calculate_comprehensive_scores(
        self,
        application_id: str,
        db: Session,
        force_recalculate: bool = False
    ) -> Dict[str, Any]:
        """Calculate comprehensive multi-factor scores for a candidate"""
        
        try:
            # Get application and related data
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Check if scores already exist and are recent
            if not force_recalculate:
                existing_scores = db.query(Score).filter(
                    Score.application_id == application_id,
                    Score.created_by == 'ai'
                ).all()
                
                if existing_scores and len(existing_scores) >= len(self.scoring_categories):
                    # Return existing scores if they're recent (within 24 hours)
                    latest_score = max(existing_scores, key=lambda s: s.created_at)
                    if (datetime.utcnow() - latest_score.created_at).total_seconds() < 86400:
                        return await self._format_score_response(existing_scores, application)
            
            # Gather all assessment data
            assessment_data = await self._gather_assessment_data(application, db)
            
            # Calculate scores for each category
            category_scores = {}
            for category, config in self.scoring_categories.items():
                score_result = await self._calculate_category_score(
                    category, assessment_data, application, db
                )
                category_scores[category] = score_result
            
            # Calculate overall score
            overall_score = self._calculate_weighted_overall_score(category_scores)
            
            # Save scores to database
            saved_scores = await self._save_scores_to_db(
                application_id, category_scores, overall_score, db
            )
            
            # Generate explainable AI summary
            explanation = await self._generate_score_explanation(
                category_scores, overall_score, assessment_data
            )
            
            return {
                "application_id": application_id,
                "overall_score": overall_score["score"],
                "overall_confidence": overall_score["confidence"],
                "category_scores": category_scores,
                "explanation": explanation,
                "scores_metadata": {
                    "calculated_at": datetime.utcnow().isoformat(),
                    "model_version": "v1.0",
                    "data_sources": list(assessment_data.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate scores for application {application_id}: {e}")
            raise Exception(f"Scoring calculation failed: {str(e)}")
    
    async def _gather_assessment_data(
        self,
        application: Application,
        db: Session
    ) -> Dict[str, Any]:
        """Gather all assessment data for scoring"""
        
        data = {
            "application": {
                "id": str(application.id),
                "status": application.status,
                "created_at": application.created_at.isoformat(),
                "cover_letter": application.cover_letter,
                "application_data": application.application_data or {}
            },
            "candidate": {
                "name": application.candidate.name,
                "email": application.candidate.email,
                "parsed_data": application.candidate.parsed_data or {}
            },
            "job": {
                "title": application.job.title,
                "description": application.job.description,
                "requirements": application.job.requirements or {}
            }
        }
        
        # Get interview data
        interviews = db.query(Interview).filter(Interview.application_id == application.id).all()
        data["interviews"] = []
        
        for interview in interviews:
            interview_data = {
                "id": str(interview.id),
                "type": interview.type,
                "status": interview.status,
                "metadata": interview.metadata or {},
                "responses": []
            }
            
            # Get interview responses
            responses = db.query(InterviewResponse).filter(
                InterviewResponse.interview_id == interview.id
            ).all()
            
            for response in responses:
                interview_data["responses"].append({
                    "question_id": response.question_id,
                    "response_type": response.response_type,
                    "content": response.content,
                    "duration": response.duration,
                    "metadata": response.metadata or {}
                })
            
            data["interviews"].append(interview_data)
        
        # Get assessment data
        assessments = db.query(Assessment).filter(Assessment.application_id == application.id).all()
        data["assessments"] = []
        
        for assessment in assessments:
            data["assessments"].append({
                "id": str(assessment.id),
                "type": assessment.type,
                "questions": assessment.questions or [],
                "responses": assessment.responses or [],
                "auto_grade": assessment.auto_grade,
                "manual_grade": assessment.manual_grade,
                "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
            })
        
        return data
    
    async def _calculate_category_score(
        self,
        category: str,
        assessment_data: Dict[str, Any],
        application: Application,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate score for a specific category"""
        
        try:
            # Build category-specific prompt
            scoring_prompt = self._build_category_scoring_prompt(category, assessment_data)
            
            # Use AI to analyze and score
            ai_analysis = await self._get_ai_category_analysis(scoring_prompt, category)
            
            # Validate and normalize score
            score = max(0.0, min(100.0, ai_analysis.get("score", 50.0)))
            confidence = max(0.0, min(1.0, ai_analysis.get("confidence", 0.5)))
            
            return {
                "score": score,
                "confidence": confidence,
                "reasoning": ai_analysis.get("reasoning", "No reasoning provided"),
                "evidence": ai_analysis.get("evidence", []),
                "strengths": ai_analysis.get("strengths", []),
                "weaknesses": ai_analysis.get("weaknesses", []),
                "weight": self.scoring_categories[category]["weight"]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate {category} score: {e}")
            return {
                "score": 50.0,
                "confidence": 0.3,
                "reasoning": f"Unable to calculate {category} score due to technical error",
                "evidence": [],
                "strengths": [],
                "weaknesses": ["Technical evaluation error"],
                "weight": self.scoring_categories[category]["weight"]
            }
    
    def _build_category_scoring_prompt(
        self,
        category: str,
        assessment_data: Dict[str, Any]
    ) -> str:
        """Build AI prompt for category-specific scoring"""
        
        category_descriptions = {
            "technical": """
            Evaluate technical competency based on:
            - Coding assessment performance
            - Technical interview responses
            - Problem-solving approach
            - Code quality and best practices
            - Technical knowledge depth
            """,
            "communication": """
            Evaluate communication skills based on:
            - Clarity of written responses
            - Verbal communication in interviews
            - Ability to explain complex concepts
            - Active listening and engagement
            - Professional language use
            """,
            "cultural_fit": """
            Evaluate cultural fit based on:
            - Alignment with company values
            - Team collaboration indicators
            - Work style preferences
            - Motivation and enthusiasm
            - Long-term career alignment
            """,
            "cognitive": """
            Evaluate cognitive ability based on:
            - Problem-solving approach
            - Analytical thinking
            - Learning ability
            - Pattern recognition
            - Decision-making process
            """,
            "behavioral": """
            Evaluate behavioral traits based on:
            - Leadership potential
            - Adaptability and flexibility
            - Stress management
            - Initiative and proactivity
            - Interpersonal skills
            """
        }
        
        return f"""
        You are an expert recruiter evaluating a candidate's {category} capabilities.
        
        {category_descriptions.get(category, "")}
        
        Assessment Data:
        {json.dumps(assessment_data, indent=2)}
        
        Provide a comprehensive evaluation in JSON format with:
        - score: float between 0-100
        - confidence: float between 0-1 (how confident you are in this score)
        - reasoning: detailed explanation for the score
        - evidence: list of specific examples that support the score
        - strengths: list of key strengths in this category
        - weaknesses: list of areas for improvement
        
        Be objective, fair, and provide specific examples from the data.
        Respond with only valid JSON.
        """
    
    async def _get_ai_category_analysis(
        self,
        prompt: str,
        category: str
    ) -> Dict[str, Any]:
        """Get AI analysis for a specific category"""
        
        messages = [
            {
                "role": "system",
                "content": f"You are an expert in evaluating {category} skills for recruitment. Provide objective, detailed analysis."
            },
            {"role": "user", "content": prompt}
        ]
        
        data = {
            "model": self.ai_service.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3  # Lower temperature for consistent scoring
        }
        
        try:
            response = await self.ai_service._make_request("chat/completions", data)
            analysis_text = response["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get AI analysis for {category}: {e}")
            return {
                "score": 50.0,
                "confidence": 0.3,
                "reasoning": f"Unable to analyze {category} due to technical error",
                "evidence": [],
                "strengths": [],
                "weaknesses": ["Technical evaluation error"]
            }
    
    def _calculate_weighted_overall_score(
        self,
        category_scores: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate weighted overall score from category scores"""
        
        total_weighted_score = 0.0
        total_weight = 0.0
        confidence_scores = []
        
        for category, score_data in category_scores.items():
            weight = score_data["weight"]
            score = score_data["score"]
            confidence = score_data["confidence"]
            
            total_weighted_score += score * weight
            total_weight += weight
            confidence_scores.append(confidence)
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 50.0
        overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
        
        return {
            "score": round(overall_score, 2),
            "confidence": round(overall_confidence, 3),
            "grade": self._score_to_grade(overall_score)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    async def _save_scores_to_db(
        self,
        application_id: str,
        category_scores: Dict[str, Dict[str, Any]],
        overall_score: Dict[str, Any],
        db: Session
    ) -> List[Score]:
        """Save calculated scores to database"""
        
        saved_scores = []
        
        # Delete existing AI-generated scores for this application
        db.query(Score).filter(
            Score.application_id == application_id,
            Score.created_by == 'ai'
        ).delete()
        
        # Save category scores
        for category, score_data in category_scores.items():
            score = Score(
                application_id=application_id,
                category=category,
                score=score_data["score"],
                confidence=score_data["confidence"] * 100,  # Convert to percentage
                reasoning=score_data["reasoning"],
                evidence=score_data.get("evidence", []),
                created_by='ai'
            )
            db.add(score)
            saved_scores.append(score)
        
        # Note: Overall score is calculated on-demand, not stored separately
        # to avoid database constraint violations
        
        db.commit()
        return saved_scores
    
    async def _generate_score_explanation(
        self,
        category_scores: Dict[str, Dict[str, Any]],
        overall_score: Dict[str, Any],
        assessment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate explainable AI summary for scores"""
        
        explanation_prompt = f"""
        Generate a comprehensive explanation for these candidate scores.
        
        Overall Score: {overall_score["score"]}/100 (Grade: {overall_score["grade"]})
        
        Category Breakdown:
        {json.dumps(category_scores, indent=2)}
        
        Provide an explanation in JSON format with:
        - executive_summary: brief 2-3 sentence summary
        - key_strengths: top 3-5 strengths across all categories
        - areas_for_improvement: top 3-5 areas needing development
        - recommendation: "strong_hire" | "hire" | "maybe" | "no_hire"
        - confidence_level: "high" | "medium" | "low"
        - next_steps: suggested next steps in hiring process
        - score_breakdown: explanation of how scores were calculated
        - bias_considerations: any potential bias factors to consider
        
        Be objective and provide actionable insights.
        Respond with only valid JSON.
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert recruiter providing explainable AI insights for hiring decisions."
            },
            {"role": "user", "content": explanation_prompt}
        ]
        
        data = {
            "model": self.ai_service.model,
            "messages": messages,
            "max_tokens": 1200,
            "temperature": 0.4
        }
        
        try:
            response = await self.ai_service._make_request("chat/completions", data)
            explanation_text = response["choices"][0]["message"]["content"].strip()
            
            explanation = json.loads(explanation_text)
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate score explanation: {e}")
            return {
                "executive_summary": "Candidate evaluation completed with mixed results.",
                "key_strengths": ["Manual review recommended"],
                "areas_for_improvement": ["Technical evaluation error"],
                "recommendation": "maybe",
                "confidence_level": "low",
                "next_steps": "Schedule manual review",
                "score_breakdown": "Automated scoring encountered technical issues",
                "bias_considerations": ["Technical evaluation limitations"]
            }
    
    async def _format_score_response(
        self,
        scores: List[Score],
        application: Application
    ) -> Dict[str, Any]:
        """Format existing scores into response format"""
        
        category_scores = {}
        overall_score = None
        
        for score in scores:
            category_scores[score.category] = {
                "score": float(score.score),
                "confidence": float(score.confidence) / 100,
                "reasoning": score.reasoning,
                "evidence": score.evidence or [],
                "weight": self.scoring_categories.get(score.category, {}).get("weight", 0.2)
            }
        
        # Calculate overall score from category scores
        if category_scores:
            overall_score = self._calculate_weighted_overall_score(category_scores)
        else:
            overall_score = {"score": 50.0, "confidence": 0.5, "grade": "F"}
        
        return {
            "application_id": str(application.id),
            "overall_score": overall_score["score"] if overall_score else 50.0,
            "overall_confidence": overall_score["confidence"] if overall_score else 0.5,
            "category_scores": category_scores,
            "scores_metadata": {
                "calculated_at": max(score.created_at for score in scores).isoformat(),
                "model_version": "v1.0",
                "from_cache": True
            }
        }    

    async def detect_bias_in_scores(
        self,
        application_ids: List[str],
        db: Session,
        demographic_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect potential bias in scoring across candidates"""
        
        try:
            # Get all scores for the applications
            scores = db.query(Score).filter(
                Score.application_id.in_(application_ids),
                Score.created_by == 'ai'
            ).all()
            
            if not scores:
                return {"error": "No scores found for bias analysis"}
            
            # Group scores by application and category
            score_data = {}
            for score in scores:
                app_id = str(score.application_id)
                if app_id not in score_data:
                    score_data[app_id] = {}
                score_data[app_id][score.category] = float(score.score)
            
            # Perform statistical bias analysis
            bias_analysis = await self._perform_statistical_bias_analysis(
                score_data, demographic_data
            )
            
            # Perform AI-based bias detection
            ai_bias_analysis = await self._perform_ai_bias_analysis(
                score_data, application_ids, db
            )
            
            # Combine analyses
            combined_analysis = {
                "statistical_analysis": bias_analysis,
                "ai_analysis": ai_bias_analysis,
                "overall_bias_risk": self._calculate_overall_bias_risk(
                    bias_analysis, ai_bias_analysis
                ),
                "recommendations": self._generate_bias_mitigation_recommendations(
                    bias_analysis, ai_bias_analysis
                ),
                "analyzed_at": datetime.utcnow().isoformat(),
                "sample_size": len(application_ids)
            }
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect bias in scores: {e}")
            raise Exception(f"Bias detection failed: {str(e)}")
    
    async def _perform_statistical_bias_analysis(
        self,
        score_data: Dict[str, Dict[str, float]],
        demographic_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform statistical analysis for bias detection"""
        
        analysis = {
            "score_distribution": {},
            "variance_analysis": {},
            "outlier_detection": {},
            "demographic_parity": None
        }
        
        # Analyze score distribution for each category
        for category in self.scoring_categories.keys():
            category_scores = []
            for app_scores in score_data.values():
                if category in app_scores:
                    category_scores.append(app_scores[category])
            
            if category_scores:
                analysis["score_distribution"][category] = {
                    "mean": statistics.mean(category_scores),
                    "median": statistics.median(category_scores),
                    "std_dev": statistics.stdev(category_scores) if len(category_scores) > 1 else 0,
                    "min": min(category_scores),
                    "max": max(category_scores),
                    "count": len(category_scores)
                }
                
                # Detect outliers using IQR method
                q1 = np.percentile(category_scores, 25)
                q3 = np.percentile(category_scores, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [score for score in category_scores 
                           if score < lower_bound or score > upper_bound]
                
                analysis["outlier_detection"][category] = {
                    "outlier_count": len(outliers),
                    "outlier_percentage": len(outliers) / len(category_scores) * 100,
                    "outliers": outliers
                }
        
        # Analyze variance across categories
        overall_scores = []
        for app_scores in score_data.values():
            if 'overall' in app_scores:
                overall_scores.append(app_scores['overall'])
        
        if overall_scores:
            analysis["variance_analysis"] = {
                "coefficient_of_variation": statistics.stdev(overall_scores) / statistics.mean(overall_scores),
                "range": max(overall_scores) - min(overall_scores),
                "is_high_variance": statistics.stdev(overall_scores) > 15  # Threshold for high variance
            }
        
        # Demographic parity analysis (if demographic data provided)
        if demographic_data:
            analysis["demographic_parity"] = await self._analyze_demographic_parity(
                score_data, demographic_data
            )
        
        return analysis
    
    async def _analyze_demographic_parity(
        self,
        score_data: Dict[str, Dict[str, float]],
        demographic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze demographic parity in scoring"""
        
        parity_analysis = {}
        
        # Group scores by demographic attributes
        for attribute, groups in demographic_data.items():
            if attribute in ['gender', 'ethnicity', 'age_group']:
                group_scores = {}
                
                for app_id, group_value in groups.items():
                    if app_id in score_data and 'overall' in score_data[app_id]:
                        if group_value not in group_scores:
                            group_scores[group_value] = []
                        group_scores[group_value].append(score_data[app_id]['overall'])
                
                if len(group_scores) >= 2:
                    # Calculate parity metrics
                    group_means = {group: statistics.mean(scores) 
                                 for group, scores in group_scores.items()}
                    
                    # Statistical significance test (ANOVA)
                    if all(len(scores) > 1 for scores in group_scores.values()):
                        f_stat, p_value = stats.f_oneway(*group_scores.values())
                        is_significant = p_value < self.bias_thresholds["statistical_significance"]
                    else:
                        f_stat, p_value, is_significant = None, None, False
                    
                    parity_analysis[attribute] = {
                        "group_means": group_means,
                        "max_difference": max(group_means.values()) - min(group_means.values()),
                        "f_statistic": f_stat,
                        "p_value": p_value,
                        "is_statistically_significant": is_significant,
                        "parity_ratio": min(group_means.values()) / max(group_means.values()) if max(group_means.values()) > 0 else 0
                    }
        
        return parity_analysis
    
    async def _perform_ai_bias_analysis(
        self,
        score_data: Dict[str, Dict[str, float]],
        application_ids: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """Use AI to detect potential bias patterns"""
        
        # Get application details for context
        applications = db.query(Application).filter(
            Application.id.in_(application_ids)
        ).all()
        
        # Build analysis prompt
        analysis_data = []
        for app in applications:
            app_id = str(app.id)
            if app_id in score_data:
                analysis_data.append({
                    "application_id": app_id,
                    "scores": score_data[app_id],
                    "candidate_name": app.candidate.name,
                    "candidate_data": app.candidate.parsed_data or {},
                    "job_title": app.job.title
                })
        
        bias_prompt = f"""
        Analyze these candidate scores for potential bias patterns.
        
        Scoring Data:
        {json.dumps(analysis_data, indent=2)}
        
        Look for:
        1. Systematic patterns that might indicate bias
        2. Inconsistencies in scoring across similar candidates
        3. Potential cultural or demographic bias indicators
        4. Scoring patterns that don't align with objective qualifications
        
        Provide analysis in JSON format with:
        - bias_indicators: list of potential bias patterns found
        - confidence_level: "high" | "medium" | "low"
        - affected_categories: list of scoring categories showing bias
        - recommendations: list of specific recommendations to address bias
        - fairness_score: float between 0-1 (1 = completely fair)
        
        Be objective and focus on statistical patterns, not individual cases.
        Respond with only valid JSON.
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert in bias detection and fair hiring practices. Analyze objectively."
            },
            {"role": "user", "content": bias_prompt}
        ]
        
        data = {
            "model": self.ai_service.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.2  # Very low temperature for consistent analysis
        }
        
        try:
            response = await self.ai_service._make_request("chat/completions", data)
            analysis_text = response["choices"][0]["message"]["content"].strip()
            
            ai_analysis = json.loads(analysis_text)
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Failed to perform AI bias analysis: {e}")
            return {
                "bias_indicators": ["Unable to analyze due to technical error"],
                "confidence_level": "low",
                "affected_categories": [],
                "recommendations": ["Manual bias review recommended"],
                "fairness_score": 0.5
            }
    
    def _calculate_overall_bias_risk(
        self,
        statistical_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall bias risk assessment"""
        
        risk_factors = []
        risk_score = 0.0
        
        # Statistical risk factors
        variance_analysis = statistical_analysis.get("variance_analysis", {})
        if variance_analysis.get("is_high_variance", False):
            risk_factors.append("High variance in scores")
            risk_score += 0.2
        
        # Outlier risk
        outlier_data = statistical_analysis.get("outlier_detection", {})
        for category, outlier_info in outlier_data.items():
            if outlier_info.get("outlier_percentage", 0) > 10:  # More than 10% outliers
                risk_factors.append(f"High outlier rate in {category}")
                risk_score += 0.1
        
        # Demographic parity risk
        demographic_parity = statistical_analysis.get("demographic_parity", {})
        for attribute, parity_data in demographic_parity.items():
            if parity_data.get("is_statistically_significant", False):
                risk_factors.append(f"Significant demographic disparity in {attribute}")
                risk_score += 0.3
            
            parity_ratio = parity_data.get("parity_ratio", 1.0)
            if parity_ratio < self.bias_thresholds["demographic_parity"]:
                risk_factors.append(f"Low parity ratio for {attribute}")
                risk_score += 0.2
        
        # AI-detected risk factors
        ai_fairness_score = ai_analysis.get("fairness_score", 1.0)
        if ai_fairness_score < 0.7:
            risk_factors.append("AI detected potential bias patterns")
            risk_score += (1.0 - ai_fairness_score) * 0.5
        
        # Normalize risk score
        risk_score = min(1.0, risk_score)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_review": risk_score >= 0.4
        }
    
    def _generate_bias_mitigation_recommendations(
        self,
        statistical_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for bias mitigation"""
        
        recommendations = []
        
        # Statistical recommendations
        variance_analysis = statistical_analysis.get("variance_analysis", {})
        if variance_analysis.get("is_high_variance", False):
            recommendations.append("Review scoring consistency across evaluators")
            recommendations.append("Consider additional training for AI scoring models")
        
        # Demographic parity recommendations
        demographic_parity = statistical_analysis.get("demographic_parity", {})
        for attribute, parity_data in demographic_parity.items():
            if parity_data.get("is_statistically_significant", False):
                recommendations.append(f"Investigate scoring disparities across {attribute} groups")
                recommendations.append(f"Consider blind evaluation processes for {attribute}")
        
        # AI-specific recommendations
        ai_recommendations = ai_analysis.get("recommendations", [])
        recommendations.extend(ai_recommendations)
        
        # General recommendations
        recommendations.extend([
            "Implement regular bias audits",
            "Use diverse evaluation panels",
            "Provide bias awareness training",
            "Consider structured interview processes",
            "Document decision-making rationale"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    async def generate_comparative_ranking(
        self,
        application_ids: List[str],
        db: Session,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comparative ranking with percentiles"""
        
        try:
            # Get scores for all applications
            scores = db.query(Score).filter(
                Score.application_id.in_(application_ids),
                Score.category == 'overall',
                Score.created_by == 'ai'
            ).all()
            
            if not scores:
                return {"error": "No scores found for ranking"}
            
            # Get application details
            applications = db.query(Application).filter(
                Application.id.in_(application_ids)
            ).all()
            
            app_lookup = {str(app.id): app for app in applications}
            
            # Build ranking data
            ranking_data = []
            score_values = []
            
            for score in scores:
                app_id = str(score.application_id)
                if app_id in app_lookup:
                    app = app_lookup[app_id]
                    ranking_data.append({
                        "application_id": app_id,
                        "candidate_name": app.candidate.name,
                        "candidate_email": app.candidate.email,
                        "job_title": app.job.title,
                        "overall_score": float(score.score),
                        "confidence": float(score.confidence),
                        "created_at": score.created_at.isoformat()
                    })
                    score_values.append(float(score.score))
            
            # Sort by score (descending)
            ranking_data.sort(key=lambda x: x["overall_score"], reverse=True)
            
            # Calculate percentiles and ranks
            for i, candidate in enumerate(ranking_data):
                candidate["rank"] = i + 1
                candidate["percentile"] = self._calculate_percentile(
                    candidate["overall_score"], score_values
                )
                candidate["tier"] = self._get_candidate_tier(candidate["percentile"])
            
            # Calculate ranking statistics
            ranking_stats = {
                "total_candidates": len(ranking_data),
                "score_statistics": {
                    "mean": statistics.mean(score_values),
                    "median": statistics.median(score_values),
                    "std_dev": statistics.stdev(score_values) if len(score_values) > 1 else 0,
                    "min": min(score_values),
                    "max": max(score_values)
                },
                "tier_distribution": self._calculate_tier_distribution(ranking_data)
            }
            
            # Generate AI insights
            ranking_insights = await self._generate_ranking_insights(
                ranking_data, ranking_stats
            )
            
            return {
                "rankings": ranking_data,
                "statistics": ranking_stats,
                "insights": ranking_insights,
                "generated_at": datetime.utcnow().isoformat(),
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comparative ranking: {e}")
            raise Exception(f"Ranking generation failed: {str(e)}")
    
    def _calculate_percentile(self, score: float, all_scores: List[float]) -> float:
        """Calculate percentile rank for a score"""
        if not all_scores:
            return 50.0
        
        # Count scores below this score
        below_count = sum(1 for s in all_scores if s < score)
        equal_count = sum(1 for s in all_scores if s == score)
        
        # Calculate percentile using the standard formula
        percentile = (below_count + 0.5 * equal_count) / len(all_scores) * 100
        return round(percentile, 1)
    
    def _get_candidate_tier(self, percentile: float) -> str:
        """Get candidate tier based on percentile"""
        if percentile >= 90:
            return "exceptional"
        elif percentile >= 75:
            return "strong"
        elif percentile >= 50:
            return "average"
        elif percentile >= 25:
            return "below_average"
        else:
            return "weak"
    
    def _calculate_tier_distribution(self, ranking_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of candidates across tiers"""
        tier_counts = {}
        for candidate in ranking_data:
            tier = candidate["tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        return tier_counts
    
    async def _generate_ranking_insights(
        self,
        ranking_data: List[Dict[str, Any]],
        ranking_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insights about the ranking"""
        
        insights_prompt = f"""
        Analyze this candidate ranking and provide insights.
        
        Ranking Data (top 10):
        {json.dumps(ranking_data[:10], indent=2)}
        
        Statistics:
        {json.dumps(ranking_stats, indent=2)}
        
        Provide insights in JSON format with:
        - top_candidates_summary: summary of top 3-5 candidates
        - score_distribution_analysis: analysis of score spread
        - hiring_recommendations: specific hiring recommendations
        - talent_pool_quality: assessment of overall talent pool
        - competitive_analysis: insights about candidate competition
        - next_steps: recommended next steps for hiring team
        
        Be specific and actionable in your recommendations.
        Respond with only valid JSON.
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert talent acquisition analyst providing strategic hiring insights."
            },
            {"role": "user", "content": insights_prompt}
        ]
        
        data = {
            "model": self.ai_service.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.4
        }
        
        try:
            response = await self.ai_service._make_request("chat/completions", data)
            insights_text = response["choices"][0]["message"]["content"].strip()
            
            insights = json.loads(insights_text)
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate ranking insights: {e}")
            return {
                "top_candidates_summary": "Manual review recommended for top candidates",
                "score_distribution_analysis": "Unable to analyze due to technical error",
                "hiring_recommendations": ["Review top candidates manually"],
                "talent_pool_quality": "Requires manual assessment",
                "competitive_analysis": "Technical analysis unavailable",
                "next_steps": ["Schedule manual review of rankings"]
            }   
 
    async def calculate_confidence_intervals(
        self,
        application_id: str,
        db: Session,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Calculate confidence intervals for scores"""
        
        try:
            # Get scores for the application
            scores = db.query(Score).filter(
                Score.application_id == application_id,
                Score.created_by == 'ai'
            ).all()
            
            if not scores:
                return {"error": "No scores found for confidence interval calculation"}
            
            # Get historical data for similar candidates
            historical_data = await self._get_historical_performance_data(
                application_id, db
            )
            
            confidence_intervals = {}
            
            for score in scores:
                if score.category in self.scoring_categories or score.category == 'overall':
                    # Calculate confidence interval based on score confidence and historical variance
                    interval = self._calculate_score_confidence_interval(
                        float(score.score),
                        float(score.confidence) / 100,
                        historical_data.get(score.category, {}),
                        confidence_level
                    )
                    
                    confidence_intervals[score.category] = {
                        "score": float(score.score),
                        "confidence": float(score.confidence),
                        "interval": interval,
                        "reliability": self._assess_score_reliability(
                            float(score.confidence) / 100,
                            historical_data.get(score.category, {})
                        )
                    }
            
            return {
                "application_id": application_id,
                "confidence_level": confidence_level,
                "intervals": confidence_intervals,
                "historical_sample_size": len(historical_data.get("sample_applications", [])),
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence intervals: {e}")
            raise Exception(f"Confidence interval calculation failed: {str(e)}")
    
    def _calculate_score_confidence_interval(
        self,
        score: float,
        confidence: float,
        historical_data: Dict[str, Any],
        confidence_level: float
    ) -> Dict[str, float]:
        """Calculate confidence interval for a specific score"""
        
        # Get z-score for confidence level
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha/2)
        
        # Estimate standard error based on confidence and historical variance
        historical_std = historical_data.get("std_dev", 10.0)  # Default std dev
        
        # Adjust standard error based on AI confidence
        # Lower confidence = higher uncertainty = wider interval
        confidence_adjustment = 1.0 / max(confidence, 0.1)  # Avoid division by zero
        adjusted_std_error = historical_std * confidence_adjustment * 0.1  # Scale factor
        
        # Calculate margin of error
        margin_of_error = z_score * adjusted_std_error
        
        # Calculate interval bounds
        lower_bound = max(0.0, score - margin_of_error)
        upper_bound = min(100.0, score + margin_of_error)
        
        return {
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "margin_of_error": round(margin_of_error, 2),
            "width": round(upper_bound - lower_bound, 2)
        }
    
    def _assess_score_reliability(
        self,
        confidence: float,
        historical_data: Dict[str, Any]
    ) -> str:
        """Assess the reliability of a score"""
        
        sample_size = historical_data.get("sample_size", 0)
        historical_variance = historical_data.get("coefficient_of_variation", 0.5)
        
        # Reliability factors
        confidence_factor = confidence  # 0-1
        sample_size_factor = min(1.0, sample_size / 100)  # Normalize to 0-1
        variance_factor = max(0.0, 1.0 - historical_variance)  # Lower variance = higher reliability
        
        # Combined reliability score
        reliability_score = (confidence_factor * 0.5 + 
                           sample_size_factor * 0.3 + 
                           variance_factor * 0.2)
        
        if reliability_score >= 0.8:
            return "high"
        elif reliability_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    async def _get_historical_performance_data(
        self,
        application_id: str,
        db: Session,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """Get historical performance data for similar candidates"""
        
        try:
            # Get the current application
            application = db.query(Application).filter(
                Application.id == application_id
            ).first()
            
            if not application:
                return {}
            
            # Get similar applications (same job or similar requirements)
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            similar_applications = db.query(Application).filter(
                and_(
                    Application.job_id == application.job_id,
                    Application.created_at >= cutoff_date,
                    Application.id != application_id
                )
            ).all()
            
            if not similar_applications:
                # Fallback to company-wide data
                similar_applications = db.query(Application).join(Job).filter(
                    and_(
                        Job.company_id == application.job.company_id,
                        Application.created_at >= cutoff_date,
                        Application.id != application_id
                    )
                ).limit(100).all()
            
            # Get scores for similar applications
            similar_app_ids = [str(app.id) for app in similar_applications]
            historical_scores = db.query(Score).filter(
                Score.application_id.in_(similar_app_ids),
                Score.created_by == 'ai'
            ).all()
            
            # Group scores by category
            category_data = {}
            for category in list(self.scoring_categories.keys()) + ['overall']:
                category_scores = [
                    float(score.score) for score in historical_scores 
                    if score.category == category
                ]
                
                if category_scores:
                    category_data[category] = {
                        "mean": statistics.mean(category_scores),
                        "std_dev": statistics.stdev(category_scores) if len(category_scores) > 1 else 0,
                        "sample_size": len(category_scores),
                        "coefficient_of_variation": (
                            statistics.stdev(category_scores) / statistics.mean(category_scores)
                            if len(category_scores) > 1 and statistics.mean(category_scores) > 0
                            else 0
                        )
                    }
            
            category_data["sample_applications"] = similar_app_ids
            return category_data
            
        except Exception as e:
            logger.error(f"Failed to get historical performance data: {e}")
            return {}
    
    async def predict_historical_performance(
        self,
        application_id: str,
        db: Session,
        prediction_horizon_days: int = 180
    ) -> Dict[str, Any]:
        """Predict candidate's future performance based on historical patterns"""
        
        try:
            # Get current scores
            current_scores = db.query(Score).filter(
                Score.application_id == application_id,
                Score.created_by == 'ai'
            ).all()
            
            if not current_scores:
                return {"error": "No current scores found for prediction"}
            
            # Get historical hiring outcomes
            historical_outcomes = await self._get_historical_hiring_outcomes(
                application_id, db
            )
            
            # Build prediction model
            predictions = {}
            
            for score in current_scores:
                if score.category in self.scoring_categories or score.category == 'overall':
                    prediction = await self._predict_category_performance(
                        score.category,
                        float(score.score),
                        float(score.confidence),
                        historical_outcomes,
                        prediction_horizon_days
                    )
                    predictions[score.category] = prediction
            
            # Generate overall performance prediction
            overall_prediction = await self._generate_overall_performance_prediction(
                predictions, historical_outcomes
            )
            
            return {
                "application_id": application_id,
                "prediction_horizon_days": prediction_horizon_days,
                "category_predictions": predictions,
                "overall_prediction": overall_prediction,
                "model_metadata": {
                    "historical_sample_size": len(historical_outcomes.get("outcomes", [])),
                    "prediction_confidence": overall_prediction.get("confidence", 0.5),
                    "model_version": "v1.0"
                },
                "predicted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to predict historical performance: {e}")
            raise Exception(f"Performance prediction failed: {str(e)}")
    
    async def _get_historical_hiring_outcomes(
        self,
        application_id: str,
        db: Session,
        lookback_days: int = 365
    ) -> Dict[str, Any]:
        """Get historical hiring outcomes for similar candidates"""
        
        try:
            # Get the current application
            application = db.query(Application).filter(
                Application.id == application_id
            ).first()
            
            if not application:
                return {"outcomes": []}
            
            # Get historical applications with known outcomes
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            historical_apps = db.query(Application).filter(
                and_(
                    Application.job_id == application.job_id,
                    Application.created_at >= cutoff_date,
                    Application.status.in_(['hired', 'rejected']),
                    Application.id != application_id
                )
            ).all()
            
            outcomes = []
            for app in historical_apps:
                # Get scores for this application
                app_scores = db.query(Score).filter(
                    Score.application_id == app.id,
                    Score.created_by == 'ai'
                ).all()
                
                if app_scores:
                    score_dict = {score.category: float(score.score) for score in app_scores}
                    
                    outcomes.append({
                        "application_id": str(app.id),
                        "outcome": app.status,
                        "scores": score_dict,
                        "hired": app.status == 'hired',
                        "days_to_decision": (
                            (app.updated_at - app.created_at).days
                            if app.updated_at else None
                        )
                    })
            
            return {
                "outcomes": outcomes,
                "total_hired": sum(1 for o in outcomes if o["hired"]),
                "total_rejected": sum(1 for o in outcomes if not o["hired"]),
                "hire_rate": (
                    sum(1 for o in outcomes if o["hired"]) / len(outcomes)
                    if outcomes else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical hiring outcomes: {e}")
            return {"outcomes": []}
    
    async def _predict_category_performance(
        self,
        category: str,
        current_score: float,
        confidence: float,
        historical_outcomes: Dict[str, Any],
        prediction_horizon_days: int
    ) -> Dict[str, Any]:
        """Predict performance for a specific category"""
        
        outcomes = historical_outcomes.get("outcomes", [])
        
        if not outcomes:
            return {
                "predicted_success_probability": 0.5,
                "confidence": 0.3,
                "reasoning": "Insufficient historical data for prediction"
            }
        
        # Find similar candidates based on score
        similar_candidates = []
        score_threshold = 10.0  # +/- 10 points
        
        for outcome in outcomes:
            if category in outcome["scores"]:
                historical_score = outcome["scores"][category]
                if abs(historical_score - current_score) <= score_threshold:
                    similar_candidates.append(outcome)
        
        if not similar_candidates:
            # Expand threshold if no similar candidates found
            similar_candidates = outcomes
        
        # Calculate success probability
        hired_count = sum(1 for c in similar_candidates if c["hired"])
        success_probability = hired_count / len(similar_candidates)
        
        # Adjust based on current score relative to historical average
        if outcomes:
            historical_scores = [
                o["scores"].get(category, 50) for o in outcomes 
                if category in o["scores"]
            ]
            if historical_scores:
                historical_mean = statistics.mean(historical_scores)
                score_adjustment = (current_score - historical_mean) / 100 * 0.3
                success_probability = max(0.0, min(1.0, success_probability + score_adjustment))
        
        # Calculate prediction confidence
        prediction_confidence = min(0.9, confidence * len(similar_candidates) / 20)
        
        return {
            "predicted_success_probability": round(success_probability, 3),
            "confidence": round(prediction_confidence, 3),
            "similar_candidates_count": len(similar_candidates),
            "reasoning": f"Based on {len(similar_candidates)} similar candidates with {category} scores near {current_score}"
        }
    
    async def _generate_overall_performance_prediction(
        self,
        category_predictions: Dict[str, Dict[str, Any]],
        historical_outcomes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall performance prediction"""
        
        if not category_predictions:
            return {
                "predicted_success_probability": 0.5,
                "confidence": 0.3,
                "risk_factors": ["No category predictions available"],
                "success_indicators": []
            }
        
        # Weighted average of category predictions
        total_weighted_prob = 0.0
        total_weight = 0.0
        confidence_scores = []
        
        for category, prediction in category_predictions.items():
            if category in self.scoring_categories:
                weight = self.scoring_categories[category]["weight"]
                prob = prediction.get("predicted_success_probability", 0.5)
                conf = prediction.get("confidence", 0.5)
                
                total_weighted_prob += prob * weight
                total_weight += weight
                confidence_scores.append(conf)
        
        overall_probability = total_weighted_prob / total_weight if total_weight > 0 else 0.5
        overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
        
        # Identify risk factors and success indicators
        risk_factors = []
        success_indicators = []
        
        for category, prediction in category_predictions.items():
            prob = prediction.get("predicted_success_probability", 0.5)
            if prob < 0.3:
                risk_factors.append(f"Low success probability in {category}")
            elif prob > 0.7:
                success_indicators.append(f"Strong performance predicted in {category}")
        
        # Overall assessment
        if overall_probability >= 0.7:
            assessment = "strong_candidate"
        elif overall_probability >= 0.5:
            assessment = "moderate_candidate"
        else:
            assessment = "weak_candidate"
        
        return {
            "predicted_success_probability": round(overall_probability, 3),
            "confidence": round(overall_confidence, 3),
            "assessment": assessment,
            "risk_factors": risk_factors,
            "success_indicators": success_indicators,
            "hire_recommendation": overall_probability >= 0.6
        }


# Utility functions for analytics
class ScoringAnalytics:
    """Analytics utilities for scoring system"""
    
    @staticmethod
    def calculate_score_trends(
        scores: List[Score],
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate scoring trends over time"""
        
        if not scores:
            return {"error": "No scores provided"}
        
        # Group scores by time periods
        now = datetime.utcnow()
        period_scores = {}
        
        for score in scores:
            days_ago = (now - score.created_at).days
            period = days_ago // time_period_days
            
            if period not in period_scores:
                period_scores[period] = []
            period_scores[period].append(float(score.score))
        
        # Calculate trends
        trends = {}
        for period, period_score_list in period_scores.items():
            trends[period] = {
                "mean_score": statistics.mean(period_score_list),
                "score_count": len(period_score_list),
                "period_start": (now - timedelta(days=(period + 1) * time_period_days)).isoformat(),
                "period_end": (now - timedelta(days=period * time_period_days)).isoformat()
            }
        
        return {
            "trends": trends,
            "analysis_period_days": time_period_days,
            "total_scores": len(scores)
        }
    
    @staticmethod
    def calculate_category_correlations(
        applications: List[Application],
        db: Session
    ) -> Dict[str, Any]:
        """Calculate correlations between scoring categories"""
        
        if not applications:
            return {"error": "No applications provided"}
        
        # Get all scores for these applications
        app_ids = [str(app.id) for app in applications]
        scores = db.query(Score).filter(
            Score.application_id.in_(app_ids),
            Score.created_by == 'ai'
        ).all()
        
        # Group scores by application and category
        app_scores = {}
        for score in scores:
            app_id = str(score.application_id)
            if app_id not in app_scores:
                app_scores[app_id] = {}
            app_scores[app_id][score.category] = float(score.score)
        
        # Calculate correlations between categories
        categories = ['technical', 'communication', 'cultural_fit', 'cognitive', 'behavioral']
        correlations = {}
        
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                cat1_scores = []
                cat2_scores = []
                
                for app_id, scores_dict in app_scores.items():
                    if cat1 in scores_dict and cat2 in scores_dict:
                        cat1_scores.append(scores_dict[cat1])
                        cat2_scores.append(scores_dict[cat2])
                
                if len(cat1_scores) >= 3:  # Need at least 3 data points
                    correlation, p_value = stats.pearsonr(cat1_scores, cat2_scores)
                    correlations[f"{cat1}_vs_{cat2}"] = {
                        "correlation": round(correlation, 3),
                        "p_value": round(p_value, 3),
                        "sample_size": len(cat1_scores),
                        "is_significant": p_value < 0.05
                    }
        
        return {
            "correlations": correlations,
            "sample_size": len(app_scores),
            "analyzed_at": datetime.utcnow().isoformat()
        }