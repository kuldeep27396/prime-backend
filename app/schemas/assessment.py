"""
Assessment schemas for request/response validation
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class AssessmentType(str, Enum):
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"


class QuestionType(str, Enum):
    CODING = "coding"
    MULTIPLE_CHOICE = "multiple_choice"
    WHITEBOARD = "whiteboard"
    ESSAY = "essay"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    TYPESCRIPT = "typescript"


class TestCase(BaseModel):
    """Test case for coding questions"""
    input: str = Field(..., description="Input for the test case")
    expected_output: str = Field(..., description="Expected output")
    is_hidden: bool = Field(default=False, description="Whether this test case is hidden from candidate")
    timeout: int = Field(default=5, description="Timeout in seconds")


class ExecutionResult(BaseModel):
    """Result of code execution"""
    success: bool = Field(..., description="Whether execution was successful")
    output: Optional[str] = Field(None, description="Program output")
    error: Optional[str] = Field(None, description="Error message if any")
    execution_time: float = Field(..., description="Execution time in seconds")
    memory_usage: Optional[int] = Field(None, description="Memory usage in bytes")
    test_results: List[Dict[str, Any]] = Field(default=[], description="Test case results")


class AssessmentQuestionBase(BaseModel):
    """Base schema for assessment questions"""
    question_type: QuestionType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    time_limit: Optional[int] = Field(None, ge=60, le=7200, description="Time limit in seconds")
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    points: int = Field(default=10, ge=1, le=100)


class CodingQuestionCreate(AssessmentQuestionBase):
    """Schema for creating coding questions"""
    question_type: QuestionType = QuestionType.CODING
    programming_language: ProgrammingLanguage
    starter_code: Optional[str] = Field(None, description="Initial code template")
    test_cases: List[TestCase] = Field(..., min_items=1)
    solution: Optional[str] = Field(None, description="Reference solution")


class MultipleChoiceQuestionCreate(AssessmentQuestionBase):
    """Schema for creating multiple choice questions"""
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: List[str] = Field(..., min_items=2, max_items=6)
    correct_answer: int = Field(..., ge=0, description="Index of correct answer")


class WhiteboardQuestionCreate(AssessmentQuestionBase):
    """Schema for creating whiteboard questions"""
    question_type: QuestionType = QuestionType.WHITEBOARD
    canvas_width: int = Field(default=800, ge=400, le=1920)
    canvas_height: int = Field(default=600, ge=300, le=1080)


class EssayQuestionCreate(AssessmentQuestionBase):
    """Schema for creating essay questions"""
    question_type: QuestionType = QuestionType.ESSAY
    min_words: Optional[int] = Field(None, ge=10)
    max_words: Optional[int] = Field(None, ge=50)


# Union type for assessment question creation
AssessmentQuestionCreate = Union[CodingQuestionCreate, MultipleChoiceQuestionCreate, WhiteboardQuestionCreate, EssayQuestionCreate]


class AssessmentQuestionResponse(BaseModel):
    """Schema for assessment question responses"""
    id: str
    question_type: QuestionType
    title: str
    content: str
    time_limit: Optional[int]
    difficulty: DifficultyLevel
    points: int
    question_metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentResponseCreate(BaseModel):
    """Schema for creating assessment responses"""
    question_id: str
    response_content: Optional[str] = None
    media_url: Optional[str] = None
    time_taken: Optional[int] = Field(None, ge=0, description="Time taken in seconds")


class CodeSubmission(BaseModel):
    """Schema for code submission"""
    question_id: str
    code: str = Field(..., min_length=1)
    programming_language: ProgrammingLanguage
    time_taken: Optional[int] = Field(None, ge=0)


class WhiteboardSubmission(BaseModel):
    """Schema for whiteboard submission"""
    question_id: str
    canvas_data: str = Field(..., description="Canvas data as base64 string")
    time_taken: Optional[int] = Field(None, ge=0)


class AssessmentResponseResponse(BaseModel):
    """Schema for assessment response responses"""
    id: str
    question_id: str
    response_content: Optional[str]
    media_url: Optional[str]
    execution_result: Optional[ExecutionResult]
    time_taken: Optional[int]
    auto_score: Optional[float]
    manual_score: Optional[float]
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    """Schema for creating assessments"""
    application_id: str
    type: AssessmentType
    questions: List[AssessmentQuestionCreate] = []
    time_limit: Optional[int] = Field(None, ge=300, le=14400, description="Total time limit in seconds")


class AssessmentResponse(BaseModel):
    """Schema for assessment responses"""
    id: str
    application_id: str
    type: AssessmentType
    questions: List[AssessmentQuestionResponse] = []
    responses: List[AssessmentResponseResponse] = []
    auto_grade: Optional[Dict[str, Any]]
    manual_grade: Optional[Dict[str, Any]]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentGrade(BaseModel):
    """Schema for assessment grading"""
    total_score: float = Field(..., ge=0, le=100)
    question_scores: Dict[str, float] = {}
    feedback: Optional[str] = None
    graded_by: str  # 'ai' or user_id
    graded_at: datetime


class AssessmentStats(BaseModel):
    """Schema for assessment statistics"""
    total_questions: int
    completed_questions: int
    total_score: Optional[float]
    time_spent: int  # in seconds
    completion_percentage: float
    average_score_per_question: Optional[float]