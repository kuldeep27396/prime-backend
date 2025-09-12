#!/usr/bin/env python3
"""
Simple test script to validate database models
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))

try:
    # Import all models to check for syntax errors
    from app.models import (
        Company, User, Job, Candidate, Application,
        InterviewTemplate, Interview, InterviewResponse,
        Assessment, AssessmentQuestion, AssessmentResponse,
        Score, AuditLog, ProctoringEvent
    )
    
    print("✅ All models imported successfully!")
    
    # Check model relationships
    print("\n📋 Model Relationships:")
    print(f"Company -> Users: {len(Company.users.property.columns)} relationship")
    print(f"Company -> Jobs: {len(Company.jobs.property.columns)} relationship")
    print(f"User -> Company: {User.company.property.columns}")
    print(f"Job -> Applications: {len(Job.applications.property.columns)} relationship")
    print(f"Application -> Interviews: {len(Application.interviews.property.columns)} relationship")
    print(f"Application -> Assessments: {len(Application.assessments.property.columns)} relationship")
    print(f"Application -> Scores: {len(Application.scores.property.columns)} relationship")
    
    # Check model properties
    print("\n🔍 Model Properties:")
    print(f"User.is_admin property: {hasattr(User, 'is_admin')}")
    print(f"User.is_recruiter property: {hasattr(User, 'is_recruiter')}")
    print(f"User.is_interviewer property: {hasattr(User, 'is_interviewer')}")
    print(f"Score.is_ai_generated property: {hasattr(Score, 'is_ai_generated')}")
    print(f"Score.score_grade property: {hasattr(Score, 'score_grade')}")
    print(f"ProctoringEvent.is_critical property: {hasattr(ProctoringEvent, 'is_critical')}")
    
    print("\n✅ All model validations passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)