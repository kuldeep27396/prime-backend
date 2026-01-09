"""
AI Interview Engine Service
Uses Z.ai API for generating questions, evaluating answers, and creating reports
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# Z.ai API configuration
ZAI_API_URL = os.getenv("ZAI_API_URL", "https://api.z.ai/v1")
ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")


class AIInterviewEngine:
    """AI-powered interview engine using Z.ai API"""
    
    def __init__(self):
        self.api_url = ZAI_API_URL
        self.api_key = ZAI_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if AI engine is properly configured"""
        return bool(self.api_key)
    
    async def _call_zai_api(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Make a call to Z.ai API"""
        if not self.is_configured():
            raise ValueError("Z.ai API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "zephyr-7b-beta",  # Or whichever model Z.ai provides
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Z.ai API error: {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def generate_screening_questions(
        self,
        job_title: str,
        job_description: str,
        skills_required: List[str],
        question_count: int = 5,
        difficulty: str = "medium",
        custom_questions: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate AI interview questions for a job screening"""
        
        # If custom questions are provided, use them as base
        if custom_questions:
            questions = []
            for i, q in enumerate(custom_questions[:question_count]):
                questions.append({
                    "id": f"q_{i+1}",
                    "question": q.get("question", ""),
                    "category": q.get("category", "custom"),
                    "difficulty": difficulty,
                    "time_limit_seconds": 180,
                    "expected_points": []
                })
            return questions
        
        prompt = f"""You are an AI interview assistant. Generate {question_count} interview questions for a {job_title} position.

Job Description: {job_description}
Required Skills: {', '.join(skills_required)}
Difficulty Level: {difficulty}

Generate a mix of:
- Technical questions related to the skills
- Behavioral questions about past experiences
- Problem-solving scenarios

For each question, provide:
1. The question text
2. Category (technical/behavioral/situational)
3. Key points the candidate should cover

Format as JSON array:
[{{"question": "...", "category": "...", "expected_points": ["point1", "point2"]}}]
"""
        
        try:
            response = await self._call_zai_api([
                {"role": "system", "content": "You are an expert technical recruiter generating interview questions."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON from response
            questions_data = json.loads(response)
            
            questions = []
            for i, q in enumerate(questions_data[:question_count]):
                questions.append({
                    "id": f"q_{i+1}",
                    "question": q["question"],
                    "category": q.get("category", "technical"),
                    "difficulty": difficulty,
                    "time_limit_seconds": 180,
                    "expected_points": q.get("expected_points", [])
                })
            
            return questions
            
        except Exception as e:
            print(f"Failed to generate questions via AI: {e}")
            # Fallback to default questions
            return self._get_default_questions(job_title, skills_required, question_count)
    
    async def generate_mock_questions(
        self,
        category: str,
        topic: Optional[str] = None,
        difficulty: str = "medium",
        question_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate questions for mock interview practice"""
        
        category_prompts = {
            "dsa": "Data Structures and Algorithms coding problems",
            "system_design": "System Design and Architecture",
            "behavioral": "Behavioral and situational interview",
            "frontend": "Frontend development with JavaScript/React",
            "backend": "Backend development and API design",
            "devops": "DevOps, CI/CD, and Cloud infrastructure",
            "data_science": "Data Science and Machine Learning"
        }
        
        category_desc = category_prompts.get(category, category)
        topic_context = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Generate {question_count} {difficulty}-level interview questions for {category_desc}{topic_context}.

For each question, provide:
1. The question text
2. Key concepts to cover in the answer
3. Time limit suggestion in seconds

Format as JSON array:
[{{"question": "...", "expected_points": ["point1", "point2"], "time_limit": 180}}]
"""
        
        try:
            response = await self._call_zai_api([
                {"role": "system", "content": f"You are an expert interviewer for {category_desc} positions."},
                {"role": "user", "content": prompt}
            ])
            
            questions_data = json.loads(response)
            
            questions = []
            for i, q in enumerate(questions_data[:question_count]):
                questions.append({
                    "id": f"q_{i+1}",
                    "question": q["question"],
                    "category": category,
                    "difficulty": difficulty,
                    "time_limit_seconds": q.get("time_limit", 180),
                    "expected_points": q.get("expected_points", [])
                })
            
            return questions
            
        except Exception as e:
            print(f"Failed to generate mock questions via AI: {e}")
            return self._get_default_mock_questions(category, question_count)
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        expected_points: List[str],
        category: str = "technical"
    ) -> Dict[str, Any]:
        """Evaluate a candidate's answer to a question"""
        
        prompt = f"""Evaluate this interview answer:

Question: {question}

Expected Key Points: {', '.join(expected_points) if expected_points else 'N/A'}

Candidate's Answer: {answer}

Evaluate the answer on:
1. Score (0-100)
2. Key strengths
3. Areas for improvement
4. Which expected points were covered

Format as JSON:
{{"score": 75, "feedback": "...", "strengths": ["..."], "improvements": ["..."], "points_covered": ["..."], "points_missing": ["..."]}}
"""
        
        try:
            response = await self._call_zai_api([
                {"role": "system", "content": "You are an expert interviewer evaluating candidate responses."},
                {"role": "user", "content": prompt}
            ])
            
            return json.loads(response)
            
        except Exception as e:
            print(f"Failed to evaluate answer via AI: {e}")
            # Fallback evaluation
            return {
                "score": 60,
                "feedback": "Answer evaluated with basic criteria.",
                "strengths": ["Attempted the question"],
                "improvements": ["Could provide more detail"],
                "points_covered": [],
                "points_missing": expected_points
            }
    
    async def generate_interview_report(
        self,
        job_title: str,
        candidate_name: str,
        questions_and_answers: List[Dict[str, Any]],
        question_evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive interview report"""
        
        # Calculate overall scores
        total_score = sum(e.get("score", 0) for e in question_evaluations)
        overall_score = total_score // len(question_evaluations) if question_evaluations else 0
        
        # Aggregate strengths and weaknesses
        all_strengths = []
        all_improvements = []
        for e in question_evaluations:
            all_strengths.extend(e.get("strengths", []))
            all_improvements.extend(e.get("improvements", []))
        
        # Get unique values
        strengths = list(set(all_strengths))[:5]
        improvements = list(set(all_improvements))[:5]
        
        summary_prompt = f"""Based on this interview evaluation for a {job_title} position, write a professional summary:

Candidate: {candidate_name}
Overall Score: {overall_score}/100

Question-by-Question Performance:
{json.dumps(question_evaluations, indent=2)}

Provide:
1. Brief summary paragraph
2. Recommendation (strongly_recommend, recommend, neutral, not_recommend)
3. Recommendation reason

Format as JSON:
{{"summary": "...", "recommendation": "...", "recommendation_reason": "..."}}
"""
        
        try:
            response = await self._call_zai_api([
                {"role": "system", "content": "You are a hiring manager writing interview feedback reports."},
                {"role": "user", "content": summary_prompt}
            ])
            
            summary_data = json.loads(response)
            
            return {
                "overall_score": overall_score,
                "technical_score": self._calc_category_score(question_evaluations, "technical"),
                "communication_score": min(overall_score + 10, 100),  # Approximation
                "problem_solving_score": self._calc_category_score(question_evaluations, "situational"),
                "summary": summary_data.get("summary", f"Candidate scored {overall_score}/100 overall."),
                "strengths": strengths,
                "areas_to_improve": improvements,
                "recommendation": summary_data.get("recommendation", self._get_recommendation(overall_score)),
                "recommendation_reason": summary_data.get("recommendation_reason", f"Based on overall score of {overall_score}"),
                "question_evaluations": question_evaluations
            }
            
        except Exception as e:
            print(f"Failed to generate report via AI: {e}")
            return {
                "overall_score": overall_score,
                "technical_score": overall_score,
                "communication_score": overall_score,
                "problem_solving_score": overall_score,
                "summary": f"Candidate {candidate_name} completed the interview with an overall score of {overall_score}/100.",
                "strengths": strengths,
                "areas_to_improve": improvements,
                "recommendation": self._get_recommendation(overall_score),
                "recommendation_reason": f"Based on overall score of {overall_score}",
                "question_evaluations": question_evaluations
            }
    
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured data (ATS-style)"""
        
        prompt = f"""Parse this resume and extract structured information:

{resume_text}

Extract:
1. Name
2. Email
3. Phone
4. Years of experience (estimate)
5. Current title
6. Current company
7. Skills (list)
8. Programming languages (if applicable)
9. Education (list with degree, school, year)
10. Work history (list with title, company, duration)

Format as JSON:
{{"name": "...", "email": "...", "phone": "...", "years_of_experience": 5, "current_title": "...", "current_company": "...", "skills": [...], "programming_languages": [...], "education": [...], "work_history": [...]}}
"""
        
        try:
            response = await self._call_zai_api([
                {"role": "system", "content": "You are an ATS system parsing resumes."},
                {"role": "user", "content": prompt}
            ], max_tokens=1500)
            
            return json.loads(response)
            
        except Exception as e:
            print(f"Failed to parse resume via AI: {e}")
            return {}
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _get_recommendation(self, score: int) -> str:
        """Get recommendation based on score"""
        if score >= 85:
            return "strongly_recommend"
        elif score >= 70:
            return "recommend"
        elif score >= 50:
            return "neutral"
        else:
            return "not_recommend"
    
    def _calc_category_score(self, evaluations: List[Dict], category: str) -> int:
        """Calculate score for a specific category"""
        category_evals = [e for e in evaluations if e.get("category") == category]
        if not category_evals:
            return sum(e.get("score", 0) for e in evaluations) // len(evaluations) if evaluations else 0
        return sum(e.get("score", 0) for e in category_evals) // len(category_evals)
    
    def _get_default_questions(self, job_title: str, skills: List[str], count: int) -> List[Dict[str, Any]]:
        """Get default fallback questions"""
        default = [
            {
                "id": "q_1",
                "question": "Tell me about yourself and your relevant experience.",
                "category": "behavioral",
                "difficulty": "easy",
                "time_limit_seconds": 180,
                "expected_points": ["Background", "Relevant experience", "Why interested in this role"]
            },
            {
                "id": "q_2",
                "question": f"What experience do you have with {skills[0] if skills else 'key technologies'}?",
                "category": "technical",
                "difficulty": "medium",
                "time_limit_seconds": 180,
                "expected_points": ["Direct experience", "Projects completed", "Results achieved"]
            },
            {
                "id": "q_3",
                "question": "Describe a challenging project you worked on and how you overcame obstacles.",
                "category": "situational",
                "difficulty": "medium",
                "time_limit_seconds": 240,
                "expected_points": ["Problem description", "Actions taken", "Results", "Lessons learned"]
            },
            {
                "id": "q_4",
                "question": f"How would you approach solving a complex problem in {job_title}?",
                "category": "technical",
                "difficulty": "hard",
                "time_limit_seconds": 300,
                "expected_points": ["Problem analysis", "Solution approach", "Trade-offs considered"]
            },
            {
                "id": "q_5",
                "question": "Where do you see yourself in 5 years and why does this role interest you?",
                "category": "behavioral",
                "difficulty": "easy",
                "time_limit_seconds": 180,
                "expected_points": ["Career goals", "Role alignment", "Motivation"]
            }
        ]
        return default[:count]
    
    def _get_default_mock_questions(self, category: str, count: int) -> List[Dict[str, Any]]:
        """Get default mock interview questions by category"""
        defaults = {
            "dsa": [
                {"question": "Explain the difference between arrays and linked lists. When would you use each?", "expected_points": ["Memory allocation", "Access time", "Insert/delete operations"]},
                {"question": "What is the time complexity of binary search? Explain how it works.", "expected_points": ["O(log n)", "Divide and conquer", "Sorted array requirement"]},
                {"question": "How would you detect a cycle in a linked list?", "expected_points": ["Two pointer technique", "Fast and slow pointers", "O(1) space solution"]}
            ],
            "system_design": [
                {"question": "Design a URL shortening service like bit.ly.", "expected_points": ["ID generation", "Database design", "Caching", "Scaling"]},
                {"question": "How would you design a real-time chat application?", "expected_points": ["WebSockets", "Message queues", "Database choice", "Scaling"]}
            ],
            "behavioral": [
                {"question": "Tell me about a time you disagreed with a teammate. How did you handle it?", "expected_points": ["Situation", "Your approach", "Resolution", "Outcome"]},
                {"question": "Describe a project you're most proud of.", "expected_points": ["Challenge", "Your role", "Impact", "Learnings"]}
            ]
        }
        
        category_qs = defaults.get(category, defaults["behavioral"])
        questions = []
        for i, q in enumerate(category_qs[:count]):
            questions.append({
                "id": f"q_{i+1}",
                "question": q["question"],
                "category": category,
                "difficulty": "medium",
                "time_limit_seconds": 180,
                "expected_points": q.get("expected_points", [])
            })
        
        return questions


# Singleton instance
ai_engine = AIInterviewEngine()
