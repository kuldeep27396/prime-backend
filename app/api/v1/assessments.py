"""
Assessments API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.company import User
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentResponse
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse as AssessmentResponseSchema,
    CodeSubmission, WhiteboardSubmission, ExecutionResult,
    AssessmentGrade, AssessmentStats
)
from app.services.assessment_service import assessment_service

router = APIRouter()


@router.post("/", response_model=AssessmentResponseSchema)
async def create_assessment(
    assessment_data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new technical assessment"""
    try:
        assessment = await assessment_service.create_assessment(db, assessment_data)
        return assessment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.get("/{assessment_id}", response_model=AssessmentResponseSchema)
async def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assessment by ID"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    return assessment


@router.post("/{assessment_id}/submit-code")
async def submit_code(
    assessment_id: str,
    submission: CodeSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit code for a coding question"""
    try:
        response = await assessment_service.submit_code(db, submission)
        return {
            "message": "Code submitted successfully",
            "response_id": str(response.id),
            "auto_score": response.auto_score,
            "execution_result": response.execution_result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution failed: {str(e)}"
        )


@router.post("/{assessment_id}/submit-whiteboard")
async def submit_whiteboard(
    assessment_id: str,
    submission: WhiteboardSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit whiteboard drawing"""
    try:
        response = await assessment_service.submit_whiteboard(db, submission)
        return {
            "message": "Whiteboard submitted successfully",
            "response_id": str(response.id)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Whiteboard submission failed: {str(e)}"
        )


@router.post("/{assessment_id}/grade", response_model=AssessmentGrade)
async def grade_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-grade an assessment"""
    try:
        grade = await assessment_service.grade_assessment(db, assessment_id)
        return grade
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grading failed: {str(e)}"
        )


@router.get("/{assessment_id}/stats", response_model=AssessmentStats)
async def get_assessment_stats(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assessment statistics"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    responses = db.query(AssessmentResponse).filter(
        AssessmentResponse.assessment_id == assessment_id
    ).all()
    
    total_questions = len(questions)
    completed_questions = len(responses)
    
    # Calculate total score and time spent
    total_score = None
    time_spent = sum(r.time_taken or 0 for r in responses)
    
    if assessment.auto_grade:
        total_score = assessment.auto_grade.get('total_score')
    
    completion_percentage = (completed_questions / total_questions * 100) if total_questions > 0 else 0
    average_score = total_score if total_score is not None else None
    
    return AssessmentStats(
        total_questions=total_questions,
        completed_questions=completed_questions,
        total_score=total_score,
        time_spent=time_spent,
        completion_percentage=completion_percentage,
        average_score_per_question=average_score
    )


@router.get("/{assessment_id}/questions")
async def get_assessment_questions(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all questions for an assessment"""
    questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    return [
        {
            "id": str(q.id),
            "question_type": q.question_type,
            "title": q.title,
            "content": q.content,
            "time_limit": q.time_limit,
            "difficulty": q.difficulty,
            "points": q.points,
            "metadata": q.question_metadata
        }
        for q in questions
    ]


@router.post("/execute-code")
async def execute_code_preview(
    submission: CodeSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute code without saving (for preview/testing)"""
    try:
        # Get question to get test cases
        question = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.id == submission.question_id
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Get test cases from question metadata
        test_cases = question.question_metadata.get("test_cases", [])
        if not test_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No test cases found for this question"
            )
        
        # Execute code
        from app.schemas.assessment import TestCase
        test_case_objects = [TestCase(**tc) for tc in test_cases]
        
        execution_result = await assessment_service.code_executor.execute_code(
            code=submission.code,
            language=submission.programming_language,
            test_cases=test_case_objects
        )
        
        return execution_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution failed: {str(e)}"
        )