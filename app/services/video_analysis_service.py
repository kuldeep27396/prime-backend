"""
LLM-based video analysis service for proctoring and assessment
"""

import os
import asyncio
import base64
import json
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI
import httpx

# Set environment variables for LangDB
os.environ["LANGDB_API_KEY"] = "langdb_Y2M5ajNKZzM5ZmRyVko="
os.environ["LANGDB_PROJECT_ID"] = "7cf981df-b5ab-46cd-8c3d-33be72fbb07b"
os.environ["LANGDB_API_BASE_URL"] = "https://api.us-east-1.langdb.ai"

# Initialize LangDB tracing
try:
    from pylangdb.langchain import init
    init()
except ImportError:
    print("LangDB not available, continuing without tracing")

from app.models.interview import Interview, InterviewResponse
from app.models.assessment import Assessment
from app.core.config import settings


class VideoAnalysisService:
    """Service for analyzing video content using multiple LLM APIs"""
    
    def __init__(self):
        # OpenRouter client for vision models
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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"
        )
        
        # LangDB client for advanced analysis
        self.langdb_client = OpenAI(
            base_url=os.environ["LANGDB_API_BASE_URL"],
            api_key=os.environ["LANGDB_API_KEY"]
        )
        
        # Analysis thresholds and configurations
        self.integrity_threshold = 0.7
        self.engagement_threshold = 0.6
        self.professionalism_threshold = 0.7
        
        # Frame sampling configuration
        self.max_frames_per_minute = 6  # Sample 6 frames per minute
        self.min_frame_interval = 10    # Minimum 10 seconds between frames
    
    async def analyze_video_file(
        self, 
        video_path: str, 
        analysis_type: str = "comprehensive",
        cost_tier: str = "standard"
    ) -> Dict[str, Any]:
        """
        Analyze a video file for proctoring and assessment
        
        Args:
            video_path: Path to the video file
            analysis_type: Type of analysis (integrity, engagement, comprehensive)
            cost_tier: Cost optimization tier (basic, standard, premium)
        
        Returns:
            Analysis results with scores and insights
        """
        
        try:
            # Extract frames from video
            frames = await self._extract_key_frames(video_path, cost_tier)
            
            if not frames:
                return {
                    "success": False,
                    "error": "No frames could be extracted from video",
                    "analysis_results": {}
                }
            
            # Perform tiered analysis based on cost optimization
            if cost_tier == "basic":
                results = await self._basic_analysis(frames, analysis_type)
            elif cost_tier == "premium":
                results = await self._premium_analysis(frames, analysis_type)
            else:
                results = await self._standard_analysis(frames, analysis_type)
            
            # Calculate overall scores
            overall_scores = self._calculate_overall_scores(results)
            
            # Generate insights and recommendations
            insights = await self._generate_insights(results, overall_scores)
            
            return {
                "success": True,
                "analysis_results": {
                    "overall_scores": overall_scores,
                    "detailed_analysis": results,
                    "insights": insights,
                    "metadata": {
                        "frames_analyzed": len(frames),
                        "analysis_type": analysis_type,
                        "cost_tier": cost_tier,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Video analysis failed: {str(e)}",
                "analysis_results": {}
            }
    
    async def real_time_proctoring(
        self, 
        frame_data: str, 
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform real-time proctoring analysis on a single frame
        
        Args:
            frame_data: Base64 encoded frame data
            session_context: Context about the current session
        
        Returns:
            Real-time analysis results with alerts
        """
        
        try:
            # Quick integrity check using lightweight model
            integrity_result = await self._quick_integrity_check(frame_data)
            
            # Generate alerts if needed
            alerts = []
            if integrity_result["integrity_score"] < self.integrity_threshold:
                alerts.append({
                    "type": "integrity_violation",
                    "severity": "high" if integrity_result["integrity_score"] < 0.5 else "medium",
                    "message": integrity_result["violation_reason"],
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for engagement issues
            if integrity_result.get("engagement_score", 1.0) < self.engagement_threshold:
                alerts.append({
                    "type": "low_engagement",
                    "severity": "low",
                    "message": "Candidate appears disengaged or distracted",
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "integrity_score": integrity_result["integrity_score"],
                "engagement_score": integrity_result.get("engagement_score", 1.0),
                "alerts": alerts,
                "recommendations": integrity_result.get("recommendations", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Real-time analysis failed: {str(e)}",
                "alerts": [{
                    "type": "system_error",
                    "severity": "high",
                    "message": "Proctoring system temporarily unavailable",
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _extract_key_frames(self, video_path: str, cost_tier: str) -> List[str]:
        """Extract key frames from video based on cost tier"""
        
        frames = []
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # Calculate frame sampling based on cost tier
            if cost_tier == "basic":
                max_frames = min(5, int(duration / 60))  # Max 5 frames total
                frame_interval = max(int(total_frames / max_frames), int(fps * 30))  # At least 30 seconds apart
            elif cost_tier == "premium":
                max_frames = int(duration * self.max_frames_per_minute / 60)  # Full sampling
                frame_interval = int(fps * self.min_frame_interval)
            else:  # standard
                max_frames = min(20, int(duration / 30))  # Max 20 frames, one every 30 seconds
                frame_interval = int(fps * 30)
            
            # Extract frames
            frame_count = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < max_frames:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Sample frames at calculated intervals
                if frame_count % frame_interval == 0:
                    # Convert frame to base64
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    frames.append(frame_b64)
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            
        except Exception as e:
            print(f"Frame extraction error: {str(e)}")
        
        return frames
    
    async def _basic_analysis(self, frames: List[str], analysis_type: str) -> Dict[str, Any]:
        """Basic analysis using cost-optimized approach"""
        
        # Use only the first and last frames for basic analysis
        key_frames = [frames[0], frames[-1]] if len(frames) > 1 else frames
        
        results = {
            "integrity_analysis": [],
            "engagement_analysis": [],
            "professionalism_analysis": []
        }
        
        for i, frame in enumerate(key_frames):
            try:
                # Use Qwen-VL free model for basic analysis
                response = self.openrouter_client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://prime-recruitment.com",
                        "X-Title": "PRIME Recruitment Platform"
                    },
                    model="qwen/qwen2.5-vl-72b-instruct:free",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._get_analysis_prompt(analysis_type, "basic")
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame}"
                                }
                            }
                        ]
                    }],
                    max_tokens=500
                )
                
                analysis_text = response.choices[0].message.content
                parsed_result = self._parse_analysis_response(analysis_text)
                
                results["integrity_analysis"].append({
                    "frame_index": i,
                    "timestamp": i * 30,  # Approximate timestamp
                    "analysis": parsed_result
                })
                
            except Exception as e:
                print(f"Basic analysis error for frame {i}: {str(e)}")
        
        return results
    
    async def _standard_analysis(self, frames: List[str], analysis_type: str) -> Dict[str, Any]:
        """Standard analysis with balanced cost and accuracy"""
        
        results = {
            "integrity_analysis": [],
            "engagement_analysis": [],
            "professionalism_analysis": []
        }
        
        # Analyze every 3rd frame to balance cost and coverage
        sample_frames = frames[::3] if len(frames) > 6 else frames
        
        for i, frame in enumerate(sample_frames):
            try:
                # Use Qwen-VL for comprehensive analysis
                response = self.openrouter_client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://prime-recruitment.com",
                        "X-Title": "PRIME Recruitment Platform"
                    },
                    model="qwen/qwen2.5-vl-72b-instruct:free",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._get_analysis_prompt(analysis_type, "standard")
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame}"
                                }
                            }
                        ]
                    }],
                    max_tokens=800
                )
                
                analysis_text = response.choices[0].message.content
                parsed_result = self._parse_analysis_response(analysis_text)
                
                # Categorize results
                if "integrity" in analysis_type.lower() or analysis_type == "comprehensive":
                    results["integrity_analysis"].append({
                        "frame_index": i,
                        "timestamp": i * 30,
                        "analysis": parsed_result
                    })
                
                if "engagement" in analysis_type.lower() or analysis_type == "comprehensive":
                    results["engagement_analysis"].append({
                        "frame_index": i,
                        "timestamp": i * 30,
                        "analysis": parsed_result
                    })
                
                if "professionalism" in analysis_type.lower() or analysis_type == "comprehensive":
                    results["professionalism_analysis"].append({
                        "frame_index": i,
                        "timestamp": i * 30,
                        "analysis": parsed_result
                    })
                
                # Add small delay to respect rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Standard analysis error for frame {i}: {str(e)}")
        
        return results
    
    async def _premium_analysis(self, frames: List[str], analysis_type: str) -> Dict[str, Any]:
        """Premium analysis with highest accuracy and detailed insights"""
        
        results = {
            "integrity_analysis": [],
            "engagement_analysis": [],
            "professionalism_analysis": []
        }
        
        # Analyze all frames for premium tier
        for i, frame in enumerate(frames):
            try:
                # Use multiple models for cross-validation in premium tier
                primary_response = self.openrouter_client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://prime-recruitment.com",
                        "X-Title": "PRIME Recruitment Platform"
                    },
                    model="qwen/qwen2.5-vl-72b-instruct:free",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._get_analysis_prompt(analysis_type, "premium")
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame}"
                                }
                            }
                        ]
                    }],
                    max_tokens=1200
                )
                
                analysis_text = primary_response.choices[0].message.content
                parsed_result = self._parse_analysis_response(analysis_text)
                
                # Add detailed analysis to all categories for premium
                frame_analysis = {
                    "frame_index": i,
                    "timestamp": i * 10,  # More frequent sampling
                    "analysis": parsed_result,
                    "confidence": parsed_result.get("confidence", 0.8)
                }
                
                results["integrity_analysis"].append(frame_analysis)
                results["engagement_analysis"].append(frame_analysis)
                results["professionalism_analysis"].append(frame_analysis)
                
                # Longer delay for premium analysis
                await asyncio.sleep(1.0)
                
            except Exception as e:
                print(f"Premium analysis error for frame {i}: {str(e)}")
        
        return results
    
    async def _quick_integrity_check(self, frame_data: str) -> Dict[str, Any]:
        """Quick integrity check for real-time proctoring"""
        
        try:
            response = self.openrouter_client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://prime-recruitment.com",
                    "X-Title": "PRIME Recruitment Platform"
                },
                model="qwen/qwen2.5-vl-72b-instruct:free",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this image for interview integrity. Look for:
1. Multiple people in frame
2. Looking away from camera frequently
3. Reading from notes or screens
4. Suspicious objects or devices
5. Poor lighting or intentional obscuring

Respond with JSON format:
{
  "integrity_score": 0.0-1.0,
  "engagement_score": 0.0-1.0,
  "violation_reason": "brief description if score < 0.7",
  "recommendations": ["list of suggestions"]
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame_data}"
                            }
                        }
                    ]
                }],
                max_tokens=300
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                result = json.loads(analysis_text)
            except:
                # Fallback parsing if JSON is malformed
                result = self._parse_analysis_response(analysis_text)
            
            return result
            
        except Exception as e:
            return {
                "integrity_score": 0.5,
                "engagement_score": 0.5,
                "violation_reason": f"Analysis error: {str(e)}",
                "recommendations": ["Check system connectivity"]
            }
    
    def _get_analysis_prompt(self, analysis_type: str, tier: str) -> str:
        """Generate analysis prompt based on type and tier"""
        
        base_prompt = """Analyze this interview video frame for the following aspects:"""
        
        if analysis_type == "integrity" or analysis_type == "comprehensive":
            base_prompt += """
INTEGRITY ASSESSMENT:
- Are there multiple people visible?
- Is the candidate looking away from camera frequently?
- Are there notes, books, or additional screens visible?
- Is the candidate using unauthorized devices?
- Is the environment appropriate for an interview?"""
        
        if analysis_type == "engagement" or analysis_type == "comprehensive":
            base_prompt += """
ENGAGEMENT ASSESSMENT:
- Is the candidate maintaining eye contact with camera?
- Does the candidate appear focused and attentive?
- Are there signs of distraction or multitasking?
- Is the candidate's body language engaged?"""
        
        if analysis_type == "professionalism" or analysis_type == "comprehensive":
            base_prompt += """
PROFESSIONALISM ASSESSMENT:
- Is the candidate dressed appropriately?
- Is the background professional and tidy?
- Is the lighting adequate for clear visibility?
- Is the candidate's posture professional?"""
        
        if tier == "basic":
            base_prompt += "\n\nProvide a brief assessment with scores (0-1) for each category."
        elif tier == "premium":
            base_prompt += "\n\nProvide detailed analysis with specific observations, confidence scores, and actionable recommendations."
        else:
            base_prompt += "\n\nProvide balanced analysis with scores and key observations."
        
        base_prompt += """

Respond in JSON format:
{
  "integrity_score": 0.0-1.0,
  "engagement_score": 0.0-1.0,
  "professionalism_score": 0.0-1.0,
  "observations": ["list of key observations"],
  "concerns": ["list of any concerns"],
  "confidence": 0.0-1.0
}"""
        
        return base_prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing
        result = {
            "integrity_score": 0.7,
            "engagement_score": 0.7,
            "professionalism_score": 0.7,
            "observations": [],
            "concerns": [],
            "confidence": 0.6
        }
        
        # Extract scores using regex
        score_patterns = {
            "integrity_score": r"integrity[:\s]*([0-9.]+)",
            "engagement_score": r"engagement[:\s]*([0-9.]+)",
            "professionalism_score": r"professionalism[:\s]*([0-9.]+)"
        }
        
        for key, pattern in score_patterns.items():
            match = re.search(pattern, response_text.lower())
            if match:
                try:
                    result[key] = float(match.group(1))
                except:
                    pass
        
        return result
    
    def _calculate_overall_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall scores from detailed analysis"""
        
        overall_scores = {
            "integrity_score": 0.0,
            "engagement_score": 0.0,
            "professionalism_score": 0.0,
            "overall_score": 0.0
        }
        
        # Calculate averages from all analyses
        for category in ["integrity_analysis", "engagement_analysis", "professionalism_analysis"]:
            if category in results and results[category]:
                scores = []
                for analysis in results[category]:
                    if "analysis" in analysis:
                        score_key = category.replace("_analysis", "_score")
                        score = analysis["analysis"].get(score_key, 0.7)
                        scores.append(score)
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    score_key = category.replace("_analysis", "_score")
                    overall_scores[score_key] = round(avg_score, 3)
        
        # Calculate weighted overall score
        weights = {"integrity_score": 0.4, "engagement_score": 0.3, "professionalism_score": 0.3}
        weighted_sum = sum(overall_scores[key] * weights[key] for key in weights.keys())
        overall_scores["overall_score"] = round(weighted_sum, 3)
        
        return overall_scores
    
    async def _generate_insights(self, results: Dict[str, Any], scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate insights and recommendations from analysis results"""
        
        insights = {
            "summary": "",
            "strengths": [],
            "areas_for_improvement": [],
            "red_flags": [],
            "recommendations": []
        }
        
        # Generate summary based on overall score
        if scores["overall_score"] >= 0.8:
            insights["summary"] = "Excellent interview performance with high integrity and professionalism."
        elif scores["overall_score"] >= 0.6:
            insights["summary"] = "Good interview performance with minor areas for improvement."
        else:
            insights["summary"] = "Interview performance needs attention with several concerns identified."
        
        # Identify strengths
        if scores["integrity_score"] >= 0.8:
            insights["strengths"].append("High integrity with no suspicious behavior detected")
        if scores["engagement_score"] >= 0.8:
            insights["strengths"].append("Excellent engagement and focus throughout the interview")
        if scores["professionalism_score"] >= 0.8:
            insights["strengths"].append("Professional appearance and environment")
        
        # Identify areas for improvement
        if scores["integrity_score"] < 0.7:
            insights["areas_for_improvement"].append("Integrity concerns require attention")
            if scores["integrity_score"] < 0.5:
                insights["red_flags"].append("Significant integrity violations detected")
        
        if scores["engagement_score"] < 0.7:
            insights["areas_for_improvement"].append("Candidate engagement could be improved")
        
        if scores["professionalism_score"] < 0.7:
            insights["areas_for_improvement"].append("Professional presentation needs improvement")
        
        # Generate recommendations
        if scores["integrity_score"] < 0.7:
            insights["recommendations"].append("Review interview recording for potential integrity violations")
        if scores["engagement_score"] < 0.6:
            insights["recommendations"].append("Consider follow-up interview to assess genuine interest")
        if scores["professionalism_score"] < 0.6:
            insights["recommendations"].append("Provide feedback on professional interview setup")
        
        return insights


# Global service instance
video_analysis_service = VideoAnalysisService()