"""
Assessment service for technical evaluations
"""

import asyncio
import json
import time
import base64
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.assessment import Assessment, AssessmentQuestion, AssessmentResponse
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse as AssessmentResponseSchema,
    CodeSubmission, ExecutionResult, TestCase, ProgrammingLanguage,
    AssessmentGrade, WhiteboardSubmission
)
from app.core.database import get_db


class CodeExecutionService:
    """Service for executing code using Judge0 API"""
    
    def __init__(self):
        # Judge0 API configuration
        self.judge0_host = "judge0-extra-ce.p.rapidapi.com"
        self.judge0_key = "1246ea2ee8mshd398907cf74dfeep135401jsn3c98d3a7accb"
        self.base_url = f"https://{self.judge0_host}"
        
        # Language ID mapping for Judge0 (updated with correct IDs)
        self.language_ids = {
            ProgrammingLanguage.PYTHON: 31,      # Python for ML (3.12.5)
            ProgrammingLanguage.JAVA: 4,         # Java (OpenJDK 14.0.1)
            ProgrammingLanguage.CPP: 2,          # C++ (Clang 10.0.1)
            ProgrammingLanguage.CSHARP: 30,      # C# (.NET Core SDK 8.0.302)
            # Note: JavaScript, TypeScript, Go, and Rust are not available in this Judge0 instance
            # We'll handle these with error messages
        }
    
    async def execute_code(
        self, 
        code: str, 
        language: ProgrammingLanguage, 
        test_cases: List[TestCase],
        timeout: int = 10
    ) -> ExecutionResult:
        """Execute code with test cases using Judge0 API"""
        
        return await self._execute_with_judge0(code, language, test_cases, timeout)
    
    async def _execute_with_judge0(
        self, 
        code: str, 
        language: ProgrammingLanguage, 
        test_cases: List[TestCase],
        timeout: int
    ) -> ExecutionResult:
        """Execute code using Judge0 API"""
        
        try:
            language_id = self.language_ids.get(language)
            if not language_id:
                return ExecutionResult(
                    success=False,
                    error=f"Language {language} not supported",
                    execution_time=0,
                    test_results=[]
                )
            
            headers = {
                'x-rapidapi-key': self.judge0_key,
                'x-rapidapi-host': self.judge0_host,
                'Content-Type': 'application/json'
            }
            
            test_results = []
            total_time = 0
            
            async with httpx.AsyncClient() as client:
                for i, test_case in enumerate(test_cases):
                    start_time = time.time()
                    
                    try:
                        # Prepare submission data (Judge0 expects raw strings, not base64)
                        submission_data = {
                            "source_code": code,
                            "language_id": language_id,
                            "stdin": test_case.input,
                            "expected_output": test_case.expected_output,
                            "cpu_time_limit": min(timeout, test_case.timeout),
                            "memory_limit": 128000,  # 128MB
                            "wall_time_limit": min(timeout, test_case.timeout) + 5
                        }
                        
                        # Submit code for execution
                        submit_response = await client.post(
                            f"{self.base_url}/submissions",
                            headers=headers,
                            json=submission_data,
                            timeout=30
                        )
                        
                        if submit_response.status_code != 201:
                            raise Exception(f"Submission failed: {submit_response.text}")
                        
                        submission = submit_response.json()
                        token = submission["token"]
                        
                        # Poll for result
                        max_polls = 20
                        poll_count = 0
                        
                        while poll_count < max_polls:
                            await asyncio.sleep(0.5)  # Wait 500ms between polls
                            
                            result_response = await client.get(
                                f"{self.base_url}/submissions/{token}",
                                headers=headers,
                                timeout=10
                            )
                            
                            if result_response.status_code != 200:
                                raise Exception(f"Failed to get result: {result_response.text}")
                            
                            result = result_response.json()
                            
                            # Check if execution is complete
                            if result["status"]["id"] not in [1, 2]:  # Not "In Queue" or "Processing"
                                break
                            
                            poll_count += 1
                        
                        execution_time = time.time() - start_time
                        total_time += execution_time
                        
                        # Process result
                        status_id = result["status"]["id"]
                        
                        # Handle output (Judge0 returns raw strings, not base64)
                        stdout = result.get("stdout", "") or ""
                        stderr = result.get("stderr", "") or ""
                        
                        actual_output = stdout.strip()
                        expected_output = test_case.expected_output.strip()
                        
                        # Determine if test passed
                        passed = False
                        error_msg = None
                        
                        if status_id == 3:  # Accepted
                            passed = actual_output == expected_output
                        elif status_id == 4:  # Wrong Answer
                            passed = False
                        elif status_id == 5:  # Time Limit Exceeded
                            error_msg = "Time Limit Exceeded"
                        elif status_id == 6:  # Compilation Error
                            error_msg = f"Compilation Error: {stderr}"
                        elif status_id == 7:  # Runtime Error (SIGSEGV)
                            error_msg = f"Runtime Error: {stderr}"
                        elif status_id == 8:  # Runtime Error (SIGXFSZ)
                            error_msg = "Runtime Error: Output Limit Exceeded"
                        elif status_id == 9:  # Runtime Error (SIGFPE)
                            error_msg = "Runtime Error: Floating Point Exception"
                        elif status_id == 10:  # Runtime Error (SIGABRT)
                            error_msg = "Runtime Error: Aborted"
                        elif status_id == 11:  # Runtime Error (NZEC)
                            error_msg = f"Runtime Error: Non-zero Exit Code - {stderr}"
                        elif status_id == 12:  # Runtime Error (Other)
                            error_msg = f"Runtime Error: {stderr}"
                        elif status_id == 13:  # Internal Error
                            error_msg = "Internal Error"
                        elif status_id == 14:  # Exec Format Error
                            error_msg = "Exec Format Error"
                        else:
                            error_msg = f"Unknown status: {result['status']['description']}"
                        
                        test_result = {
                            'test_case_index': i,
                            'input': test_case.input,
                            'expected_output': expected_output,
                            'actual_output': actual_output,
                            'passed': passed,
                            'execution_time': float(result.get('time', 0)) or execution_time,
                            'memory_usage': result.get('memory'),
                            'is_hidden': test_case.is_hidden,
                            'status': result['status']['description']
                        }
                        
                        if error_msg:
                            test_result['error'] = error_msg
                        if stderr:
                            test_result['stderr'] = stderr
                        
                        test_results.append(test_result)
                        
                    except Exception as e:
                        test_results.append({
                            'test_case_index': i,
                            'input': test_case.input,
                            'expected_output': test_case.expected_output,
                            'actual_output': '',
                            'passed': False,
                            'execution_time': time.time() - start_time,
                            'error': str(e),
                            'is_hidden': test_case.is_hidden
                        })
            
            # Calculate overall success
            passed_tests = sum(1 for result in test_results if result['passed'])
            success = passed_tests == len(test_cases)
            
            return ExecutionResult(
                success=success,
                output=f"Passed {passed_tests}/{len(test_cases)} test cases",
                execution_time=total_time,
                test_results=test_results
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Judge0 execution failed: {str(e)}",
                execution_time=0,
                test_results=[]
            )
    



class AssessmentService:
    """Service for managing technical assessments"""
    
    def __init__(self):
        self.code_executor = CodeExecutionService()
    
    async def create_assessment(self, db: Session, assessment_data: AssessmentCreate) -> Assessment:
        """Create a new assessment"""
        
        assessment = Assessment(
            application_id=assessment_data.application_id,
            type=assessment_data.type.value,
            questions=[],
            responses=[]
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Create questions
        for question_data in assessment_data.questions:
            question = AssessmentQuestion(
                assessment_id=assessment.id,
                question_type=question_data.question_type.value,
                title=question_data.title,
                content=question_data.content,
                time_limit=question_data.time_limit,
                difficulty=question_data.difficulty.value,
                points=question_data.points,
                question_metadata=self._serialize_question_metadata(question_data)
            )
            
            db.add(question)
        
        db.commit()
        return assessment
    
    async def submit_code(self, db: Session, submission: CodeSubmission) -> AssessmentResponse:
        """Submit and execute code for a coding question"""
        
        # Get question and test cases
        question = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.id == submission.question_id
        ).first()
        
        if not question:
            raise ValueError("Question not found")
        
        if question.question_type != "coding":
            raise ValueError("Question is not a coding question")
        
        # Get test cases from question metadata
        test_cases = [
            TestCase(**tc) for tc in question.question_metadata.get("test_cases", [])
        ]
        
        # Execute code
        execution_result = await self.code_executor.execute_code(
            code=submission.code,
            language=submission.programming_language,
            test_cases=test_cases
        )
        
        # Calculate score based on test results
        if execution_result.test_results:
            passed_tests = sum(1 for result in execution_result.test_results if result['passed'])
            total_tests = len(execution_result.test_results)
            auto_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        else:
            auto_score = 0
        
        # Save response
        response = AssessmentResponse(
            assessment_id=question.assessment_id,
            question_id=question.id,
            response_content=submission.code,
            execution_result=execution_result.dict(),
            time_taken=submission.time_taken,
            auto_score=auto_score
        )
        
        db.add(response)
        db.commit()
        db.refresh(response)
        
        return response
    
    async def submit_whiteboard(self, db: Session, submission: WhiteboardSubmission) -> AssessmentResponse:
        """Submit whiteboard drawing"""
        
        question = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.id == submission.question_id
        ).first()
        
        if not question:
            raise ValueError("Question not found")
        
        if question.question_type != "whiteboard":
            raise ValueError("Question is not a whiteboard question")
        
        # Save canvas data (in real implementation, save to blob storage)
        response = AssessmentResponse(
            assessment_id=question.assessment_id,
            question_id=question.id,
            response_content=submission.canvas_data,
            time_taken=submission.time_taken
        )
        
        db.add(response)
        db.commit()
        db.refresh(response)
        
        return response
    
    async def grade_assessment(self, db: Session, assessment_id: str) -> AssessmentGrade:
        """Auto-grade an assessment"""
        
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise ValueError("Assessment not found")
        
        responses = db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment_id
        ).all()
        
        total_score = 0
        total_points = 0
        question_scores = {}
        
        for response in responses:
            question = db.query(AssessmentQuestion).filter(
                AssessmentQuestion.id == response.question_id
            ).first()
            
            if question and response.auto_score is not None:
                weighted_score = (float(response.auto_score) / 100) * question.points
                total_score += weighted_score
                total_points += question.points
                question_scores[str(response.question_id)] = float(response.auto_score)
        
        final_score = (total_score / total_points * 100) if total_points > 0 else 0
        
        grade = AssessmentGrade(
            total_score=final_score,
            question_scores=question_scores,
            graded_by="ai",
            graded_at=datetime.now()
        )
        
        # Update assessment with grade
        assessment.auto_grade = grade.dict()
        db.commit()
        
        return grade
    
    def _serialize_question_metadata(self, question_data) -> Dict[str, Any]:
        """Serialize question-specific metadata"""
        metadata = {}
        
        if hasattr(question_data, 'programming_language'):
            metadata['programming_language'] = question_data.programming_language.value
        if hasattr(question_data, 'starter_code'):
            metadata['starter_code'] = question_data.starter_code
        if hasattr(question_data, 'test_cases'):
            metadata['test_cases'] = [tc.dict() for tc in question_data.test_cases]
        if hasattr(question_data, 'solution'):
            metadata['solution'] = question_data.solution
        if hasattr(question_data, 'options'):
            metadata['options'] = question_data.options
        if hasattr(question_data, 'correct_answer'):
            metadata['correct_answer'] = question_data.correct_answer
        if hasattr(question_data, 'canvas_width'):
            metadata['canvas_width'] = question_data.canvas_width
        if hasattr(question_data, 'canvas_height'):
            metadata['canvas_height'] = question_data.canvas_height
        if hasattr(question_data, 'min_words'):
            metadata['min_words'] = question_data.min_words
        if hasattr(question_data, 'max_words'):
            metadata['max_words'] = question_data.max_words
        
        return metadata


# Global service instance
assessment_service = AssessmentService()