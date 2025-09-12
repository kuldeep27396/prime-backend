"""
AI service for LLM integration with Groq API and Cerebras fallback
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import httpx
import asyncio
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class CerebrasAIService:
    """Service for interacting with Cerebras API as fallback"""
    
    def __init__(self):
        self.api_key = settings.CEREBRAS_API_KEY
        self.base_url = "https://api.cerebras.ai/v1"
        self.model = "llama-3.3-70b"  # Primary Cerebras model
        self.trial_model = "llama3.1-8b"  # Faster model for trials
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Cerebras API"""
        if not self.api_key:
            raise ValueError("CEREBRAS_API_KEY not configured")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Cerebras API request failed: {e}")
                raise Exception(f"Cerebras AI service unavailable: {str(e)}")


class GroqAIService:
    """Service for interacting with Groq API with Cerebras fallback"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama3-70b-8192"  # Primary model for production
        self.trial_model = "llama3-8b-8192"  # Faster model for trials
        
        # Initialize Cerebras fallback
        self.cerebras_service = CerebrasAIService()
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Groq API with Cerebras fallback"""
        
        # Try Groq first
        if self.api_key:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/{endpoint}",
                        headers=headers,
                        json=data,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    logger.info("Successfully used Groq API")
                    return response.json()
                except httpx.HTTPError as e:
                    logger.warning(f"Groq API request failed, trying Cerebras fallback: {e}")
        
        # Fallback to Cerebras
        try:
            logger.info("Using Cerebras API as fallback")
            
            # Map Groq model names to Cerebras equivalents
            cerebras_data = data.copy()
            if data.get("model") == "llama3-70b-8192":
                cerebras_data["model"] = "llama-3.3-70b"
            elif data.get("model") == "llama3-8b-8192":
                cerebras_data["model"] = "llama3.1-8b"
            
            return await self.cerebras_service._make_request(endpoint, cerebras_data)
            
        except Exception as cerebras_error:
            logger.error(f"Both Groq and Cerebras APIs failed: {cerebras_error}")
            raise Exception(f"All AI services unavailable. Groq: API error, Cerebras: {str(cerebras_error)}")
    
    async def generate_chatbot_response(
        self,
        conversation_history: List[Dict[str, str]],
        question_config: Dict[str, Any],
        candidate_context: Dict[str, Any],
        is_trial: bool = False
    ) -> str:
        """Generate chatbot response for pre-screening"""
        
        model = self.trial_model if is_trial else self.model
        
        # Build system prompt for chatbot personality
        system_prompt = self._build_chatbot_system_prompt(question_config, candidate_context)
        
        # Prepare messages for the API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            role = "assistant" if msg["sender"] == "bot" else "user"
            messages.append({"role": role, "content": msg["content"]})
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Failed to generate chatbot response: {e}")
            return "I apologize, but I'm having trouble processing your response right now. Could you please try again?"
    
    async def evaluate_candidate_response(
        self,
        question: str,
        candidate_response: str,
        evaluation_criteria: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate candidate response using AI"""
        
        system_prompt = self._build_evaluation_system_prompt(evaluation_criteria, job_context)
        
        user_prompt = f"""
        Question: {question}
        Candidate Response: {candidate_response}
        
        Please evaluate this response and provide a structured assessment.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.3,  # Lower temperature for more consistent evaluation
            "top_p": 0.8
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            evaluation_text = response["choices"][0]["message"]["content"].strip()
            
            # Parse the structured evaluation
            return self._parse_evaluation_response(evaluation_text)
        except Exception as e:
            logger.error(f"Failed to evaluate candidate response: {e}")
            return {
                "score": 50.0,
                "reasoning": "Unable to evaluate response due to technical issues",
                "keywords_found": [],
                "sentiment": "neutral",
                "confidence": 0.5
            }
    
    async def generate_follow_up_question(
        self,
        original_question: str,
        candidate_response: str,
        follow_up_rules: Dict[str, Any]
    ) -> Optional[str]:
        """Generate dynamic follow-up question based on candidate response"""
        
        system_prompt = """You are an expert interviewer conducting a pre-screening conversation. 
        Based on the candidate's response, generate a relevant follow-up question that will help 
        gather more specific information or clarify their answer. Keep questions conversational 
        and professional. If no follow-up is needed, respond with "NO_FOLLOWUP"."""
        
        user_prompt = f"""
        Original Question: {original_question}
        Candidate Response: {candidate_response}
        Follow-up Rules: {json.dumps(follow_up_rules)}
        
        Generate an appropriate follow-up question or respond with "NO_FOLLOWUP" if none is needed.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.6
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            follow_up = response["choices"][0]["message"]["content"].strip()
            
            return None if follow_up == "NO_FOLLOWUP" else follow_up
        except Exception as e:
            logger.error(f"Failed to generate follow-up question: {e}")
            return None
    
    async def generate_pre_screening_summary(
        self,
        session_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive pre-screening summary and recommendation"""
        
        system_prompt = """You are an expert recruiter analyzing a candidate's pre-screening responses. 
        Provide a comprehensive summary with strengths, concerns, and a clear recommendation."""
        
        user_prompt = f"""
        Job Requirements: {json.dumps(job_requirements)}
        Session Data: {json.dumps(session_data)}
        
        Please provide:
        1. Key strengths demonstrated by the candidate
        2. Areas of concern or gaps
        3. Overall recommendation (proceed/reject/needs_review)
        4. Brief reasoning for the recommendation
        
        Format your response as JSON with keys: strengths, concerns, recommendation, reasoning
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.4
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            summary_text = response["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            return json.loads(summary_text)
        except Exception as e:
            logger.error(f"Failed to generate pre-screening summary: {e}")
            return {
                "strengths": ["Unable to analyze due to technical issues"],
                "concerns": ["Technical evaluation error"],
                "recommendation": "needs_review",
                "reasoning": "Manual review required due to system error"
            }
    
    def _build_chatbot_system_prompt(
        self,
        question_config: Dict[str, Any],
        candidate_context: Dict[str, Any]
    ) -> str:
        """Build system prompt for chatbot personality"""
        
        personality = question_config.get("personality", "professional")
        
        base_prompt = f"""You are a {personality} AI recruiter conducting a pre-screening conversation 
        with a job candidate. Your role is to ask questions, listen to responses, and maintain a 
        natural conversation flow.
        
        Guidelines:
        - Be conversational and engaging
        - Ask one question at a time
        - Acknowledge candidate responses before moving to the next question
        - Keep responses concise and professional
        - Show genuine interest in their answers
        - If a response is unclear, politely ask for clarification
        
        Candidate Context: {json.dumps(candidate_context)}
        
        Current Question Context: {json.dumps(question_config)}
        """
        
        return base_prompt
    
    def _build_evaluation_system_prompt(
        self,
        evaluation_criteria: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> str:
        """Build system prompt for response evaluation"""
        
        return f"""You are an expert recruiter evaluating candidate responses during pre-screening.
        
        Evaluation Criteria: {json.dumps(evaluation_criteria)}
        Job Context: {json.dumps(job_context)}
        
        For each response, provide:
        1. A score from 0-100 based on relevance, completeness, and quality
        2. Clear reasoning for the score
        3. Key keywords or phrases that influenced the evaluation
        4. Sentiment analysis (positive/neutral/negative)
        5. Confidence level in your evaluation (0-1)
        
        Format your response as JSON with keys: score, reasoning, keywords_found, sentiment, confidence
        """
    
    def _parse_evaluation_response(self, evaluation_text: str) -> Dict[str, Any]:
        """Parse AI evaluation response into structured format"""
        try:
            # Try to parse as JSON first
            return json.loads(evaluation_text)
        except json.JSONDecodeError:
            # Fallback parsing if not valid JSON
            logger.warning("Failed to parse evaluation as JSON, using fallback parsing")
            
            # Extract score using regex or simple parsing
            score = 50.0  # Default score
            reasoning = evaluation_text
            
            # Simple keyword extraction
            keywords_found = []
            
            return {
                "score": score,
                "reasoning": reasoning,
                "keywords_found": keywords_found,
                "sentiment": "neutral",
                "confidence": 0.7
            }


    async def start_live_ai_interview(
        self,
        job_context: Dict[str, Any],
        candidate_context: Dict[str, Any],
        interview_config: Dict[str, Any],
        is_trial: bool = False
    ) -> Dict[str, Any]:
        """Start a live AI interview session"""
        
        model = self.trial_model if is_trial else self.model
        
        # Generate initial interview plan
        system_prompt = self._build_live_interview_system_prompt(
            job_context, candidate_context, interview_config
        )
        
        # Generate opening question
        opening_prompt = f"""
        Based on the job requirements and candidate background, generate an engaging 
        opening question to start the interview. Keep it conversational and welcoming.
        
        Job: {job_context.get('title', 'Position')}
        Candidate: {candidate_context.get('name', 'Candidate')}
        
        Respond with just the opening question, no additional text.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": opening_prompt}
        ]
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            opening_question = response["choices"][0]["message"]["content"].strip()
            
            # Initialize session state
            session_state = {
                "session_id": f"live_ai_{datetime.utcnow().timestamp()}",
                "model": model,
                "conversation_history": [],
                "current_question": opening_question,
                "question_count": 1,
                "topics_covered": [],
                "candidate_state": {
                    "engagement_level": "neutral",
                    "confidence_level": 0.5,
                    "technical_depth": "beginner",
                    "communication_style": "unknown"
                },
                "interview_phase": "opening",  # opening, technical, behavioral, closing
                "adaptive_difficulty": "medium",
                "system_prompt": system_prompt,
                "started_at": datetime.utcnow().isoformat()
            }
            
            return {
                "session_state": session_state,
                "opening_question": opening_question,
                "status": "started"
            }
            
        except Exception as e:
            logger.error(f"Failed to start live AI interview: {e}")
            raise Exception(f"Failed to start interview: {str(e)}")
    
    async def process_candidate_response_live(
        self,
        session_state: Dict[str, Any],
        candidate_response: str,
        response_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process candidate response and generate next question in live interview"""
        
        if not candidate_response.strip():
            return {
                "ai_response": "I didn't catch that. Could you please repeat your answer?",
                "session_state": session_state,
                "analysis": {"confidence": 0.0, "sentiment": "neutral"}
            }
        
        # Analyze the response
        analysis = await self._analyze_response_sentiment_confidence(
            candidate_response, session_state.get("current_question", "")
        )
        
        # Update candidate state based on analysis
        session_state = self._update_candidate_state(session_state, analysis, candidate_response)
        
        # Add to conversation history
        session_state["conversation_history"].append({
            "role": "candidate",
            "content": candidate_response,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis
        })
        
        # Generate AI response and next question
        ai_response = await self._generate_live_ai_response(session_state, candidate_response)
        
        # Update session state
        session_state["conversation_history"].append({
            "role": "ai",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        session_state["current_question"] = ai_response
        session_state["question_count"] += 1
        
        # Determine if interview should continue or wrap up
        should_continue = self._should_continue_interview(session_state)
        
        return {
            "ai_response": ai_response,
            "session_state": session_state,
            "analysis": analysis,
            "should_continue": should_continue,
            "interview_phase": session_state.get("interview_phase", "ongoing")
        }
    
    async def _analyze_response_sentiment_confidence(
        self,
        response: str,
        question: str
    ) -> Dict[str, Any]:
        """Analyze candidate response for sentiment and confidence"""
        
        analysis_prompt = f"""
        Analyze this candidate's interview response for sentiment and confidence level.
        
        Question: {question}
        Response: {response}
        
        Provide analysis in JSON format with:
        - sentiment: "positive", "neutral", or "negative"
        - confidence: float between 0.0 and 1.0
        - engagement: "high", "medium", or "low"
        - clarity: "clear", "somewhat_clear", or "unclear"
        - technical_depth: "advanced", "intermediate", "basic", or "none"
        - key_points: list of main points mentioned
        - concerns: list of any red flags or concerns
        
        Respond with only valid JSON.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert interview analyst. Provide objective, structured analysis."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            analysis_text = response["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze response: {e}")
            # Return default analysis
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "engagement": "medium",
                "clarity": "somewhat_clear",
                "technical_depth": "basic",
                "key_points": [],
                "concerns": []
            }
    
    def _update_candidate_state(
        self,
        session_state: Dict[str, Any],
        analysis: Dict[str, Any],
        response: str
    ) -> Dict[str, Any]:
        """Update candidate state based on response analysis"""
        
        candidate_state = session_state.get("candidate_state", {})
        
        # Update engagement level
        engagement = analysis.get("engagement", "medium")
        if engagement == "high":
            candidate_state["engagement_level"] = "high"
        elif engagement == "low" and candidate_state.get("engagement_level") != "high":
            candidate_state["engagement_level"] = "low"
        
        # Update confidence level (running average)
        new_confidence = analysis.get("confidence", 0.5)
        current_confidence = candidate_state.get("confidence_level", 0.5)
        candidate_state["confidence_level"] = (current_confidence + new_confidence) / 2
        
        # Update technical depth
        tech_depth = analysis.get("technical_depth", "basic")
        if tech_depth in ["advanced", "intermediate"] and candidate_state.get("technical_depth") != "advanced":
            candidate_state["technical_depth"] = tech_depth
        
        # Update communication style
        clarity = analysis.get("clarity", "somewhat_clear")
        if clarity == "clear":
            candidate_state["communication_style"] = "clear"
        elif clarity == "unclear":
            candidate_state["communication_style"] = "unclear"
        
        session_state["candidate_state"] = candidate_state
        return session_state
    
    async def _generate_live_ai_response(
        self,
        session_state: Dict[str, Any],
        candidate_response: str
    ) -> str:
        """Generate AI interviewer response and next question"""
        
        # Build context from conversation history
        conversation_context = ""
        for msg in session_state["conversation_history"][-6:]:  # Last 6 messages
            role = "Interviewer" if msg["role"] == "ai" else "Candidate"
            conversation_context += f"{role}: {msg['content']}\n"
        
        # Determine next question type based on interview phase and candidate state
        next_question_guidance = self._get_next_question_guidance(session_state)
        
        response_prompt = f"""
        You are conducting a live AI interview. Based on the candidate's response, 
        provide a brief acknowledgment and then ask the next appropriate question.
        
        Current Interview Phase: {session_state.get('interview_phase', 'ongoing')}
        Question Count: {session_state.get('question_count', 1)}
        Candidate State: {json.dumps(session_state.get('candidate_state', {}))}
        
        Recent Conversation:
        {conversation_context}
        
        Candidate's Latest Response: {candidate_response}
        
        Next Question Guidance: {next_question_guidance}
        
        Respond with:
        1. Brief acknowledgment of their answer (1-2 sentences)
        2. The next interview question
        
        Keep the tone conversational and professional. Adapt difficulty based on their responses.
        """
        
        messages = [
            {"role": "system", "content": session_state.get("system_prompt", "")},
            {"role": "user", "content": response_prompt}
        ]
        
        data = {
            "model": session_state.get("model", self.model),
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            return response["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return "Thank you for that response. Let me ask you another question to learn more about your background."
    
    def _get_next_question_guidance(self, session_state: Dict[str, Any]) -> str:
        """Get guidance for the next question based on interview state"""
        
        question_count = session_state.get("question_count", 1)
        phase = session_state.get("interview_phase", "opening")
        candidate_state = session_state.get("candidate_state", {})
        
        if question_count <= 2:
            return "Ask about their background and experience relevant to the role"
        elif question_count <= 4:
            if candidate_state.get("technical_depth") in ["advanced", "intermediate"]:
                return "Ask a technical question to assess their skills"
            else:
                return "Ask about their motivation and interest in the role"
        elif question_count <= 6:
            return "Ask a behavioral question about teamwork or problem-solving"
        elif question_count <= 8:
            return "Ask about their career goals and how this role fits"
        else:
            return "Begin wrapping up - ask if they have questions for you"
    
    def _should_continue_interview(self, session_state: Dict[str, Any]) -> bool:
        """Determine if interview should continue based on various factors"""
        
        question_count = session_state.get("question_count", 1)
        candidate_state = session_state.get("candidate_state", {})
        
        # Basic question count limit
        if question_count >= 10:
            return False
        
        # If candidate is highly engaged and confident, can continue longer
        if (candidate_state.get("engagement_level") == "high" and 
            candidate_state.get("confidence_level", 0) > 0.7 and 
            question_count < 12):
            return True
        
        # If candidate seems disengaged, wrap up sooner
        if (candidate_state.get("engagement_level") == "low" and 
            question_count >= 6):
            return False
        
        return question_count < 8
    
    def _build_live_interview_system_prompt(
        self,
        job_context: Dict[str, Any],
        candidate_context: Dict[str, Any],
        interview_config: Dict[str, Any]
    ) -> str:
        """Build system prompt for live AI interviewer"""
        
        return f"""You are an expert AI interviewer conducting a live video interview. 
        Your role is to assess the candidate's fit for the position through natural conversation.
        
        Job Context:
        - Title: {job_context.get('title', 'Position')}
        - Company: {job_context.get('company', 'Company')}
        - Key Requirements: {json.dumps(job_context.get('requirements', {}))}
        
        Candidate Context:
        - Name: {candidate_context.get('name', 'Candidate')}
        - Background: {json.dumps(candidate_context.get('background', {}))}
        
        Interview Guidelines:
        - Be conversational and engaging
        - Ask follow-up questions based on responses
        - Adapt difficulty based on candidate's demonstrated skill level
        - Cover technical skills, behavioral traits, and cultural fit
        - Keep questions relevant to the job requirements
        - Maintain a professional but friendly tone
        - Acknowledge good answers and provide encouragement
        - If answers are unclear, politely ask for clarification
        
        Interview Structure:
        1. Opening: Welcome and background questions
        2. Technical: Role-specific technical questions
        3. Behavioral: Situational and behavioral questions
        4. Closing: Candidate questions and next steps
        
        Remember: This is a real-time conversation. Keep responses concise and natural.
        """

    async def generate_interview_summary(
        self,
        session_state: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive interview summary and recommendation"""
        
        conversation_history = session_state.get("conversation_history", [])
        candidate_state = session_state.get("candidate_state", {})
        
        # Build conversation transcript
        transcript = ""
        for msg in conversation_history:
            role = "Interviewer" if msg["role"] == "ai" else "Candidate"
            transcript += f"{role}: {msg['content']}\n\n"
        
        summary_prompt = f"""
        Analyze this live AI interview and provide a comprehensive summary.
        
        Job Requirements: {json.dumps(job_context.get('requirements', {}))}
        
        Interview Transcript:
        {transcript}
        
        Candidate State Analysis:
        {json.dumps(candidate_state)}
        
        Provide a detailed analysis in JSON format with:
        - overall_score: float between 0-100
        - technical_assessment: {{score: float, strengths: [str], weaknesses: [str]}}
        - communication_skills: {{score: float, clarity: str, engagement: str}}
        - cultural_fit: {{score: float, reasoning: str}}
        - behavioral_traits: {{teamwork: str, problem_solving: str, adaptability: str}}
        - key_strengths: [str] (top 3-5 strengths)
        - areas_of_concern: [str] (potential issues)
        - recommendation: "strong_hire" | "hire" | "maybe" | "no_hire"
        - reasoning: str (detailed explanation for recommendation)
        - next_steps: str (suggested next steps in hiring process)
        
        Respond with only valid JSON.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert interview analyst providing objective assessment."},
            {"role": "user", "content": summary_prompt}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            summary_text = response["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            summary = json.loads(summary_text)
            
            # Add metadata
            summary["interview_metadata"] = {
                "duration_minutes": len(conversation_history) * 2,  # Rough estimate
                "question_count": session_state.get("question_count", 0),
                "interview_phase": session_state.get("interview_phase", "completed"),
                "model_used": session_state.get("model", self.model),
                "completed_at": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate interview summary: {e}")
            return {
                "overall_score": 50.0,
                "technical_assessment": {"score": 50.0, "strengths": [], "weaknesses": ["Unable to assess due to technical error"]},
                "communication_skills": {"score": 50.0, "clarity": "unknown", "engagement": "unknown"},
                "cultural_fit": {"score": 50.0, "reasoning": "Unable to assess"},
                "behavioral_traits": {"teamwork": "unknown", "problem_solving": "unknown", "adaptability": "unknown"},
                "key_strengths": ["Manual review required"],
                "areas_of_concern": ["Technical evaluation error"],
                "recommendation": "maybe",
                "reasoning": "Interview analysis failed due to technical issues. Manual review recommended.",
                "next_steps": "Schedule manual review of interview recording",
                "interview_metadata": {
                    "duration_minutes": 0,
                    "question_count": 0,
                    "interview_phase": "error",
                    "model_used": self.model,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }


# Global instance
ai_service = GroqAIService()