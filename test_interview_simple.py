"""
Simple test for interview functionality
"""

import asyncio
from app.services.interview_service import InterviewService
from app.schemas.interview import InterviewTemplateCreate


def test_interview_template_validation():
    """Test interview template validation"""
    
    # Create a simple template data
    template_data = InterviewTemplateCreate(
        name="Test Template",
        description="Test description",
        type="technical",
        questions=[
            {
                "id": "q1",
                "type": "technical",
                "category": "coding",
                "content": "Write a function",
                "expected_duration": 300,
                "difficulty": "easy",
                "tags": ["python"],
                "metadata": {}
            }
        ],
        settings={"time_limit": 1800}
    )
    
    # Test that the template data is valid
    assert template_data.name == "Test Template"
    assert template_data.type == "technical"
    assert len(template_data.questions) == 1
    assert template_data.questions[0].id == "q1"
    assert template_data.questions[0].content == "Write a function"
    
    print("✅ Interview template validation test passed!")


def test_question_serialization():
    """Test that questions can be serialized to dict"""
    
    template_data = InterviewTemplateCreate(
        name="Test Template",
        type="technical",
        questions=[
            {
                "id": "q1",
                "type": "technical",
                "category": "coding",
                "content": "Write a function",
                "expected_duration": 300,
                "difficulty": "easy",
                "tags": ["python"],
                "metadata": {}
            }
        ],
        settings={}
    )
    
    # Test serialization
    questions_dict = [q.model_dump() for q in template_data.questions]
    assert len(questions_dict) == 1
    assert questions_dict[0]["id"] == "q1"
    assert questions_dict[0]["content"] == "Write a function"
    
    print("✅ Question serialization test passed!")


if __name__ == "__main__":
    test_interview_template_validation()
    test_question_serialization()
    print("🎉 All tests passed!")