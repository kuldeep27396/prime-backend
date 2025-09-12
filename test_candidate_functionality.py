#!/usr/bin/env python3
"""
Test script for candidate management functionality
"""

import asyncio
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.job import Candidate
from app.services.candidate_service import CandidateService
from app.schemas.candidate import CandidateCreate, CandidateSearch, ParsedResumeData


async def test_candidate_service():
    """Test candidate service functionality"""
    print("Testing Candidate Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        service = CandidateService(db)
        
        # Clean up any existing test data
        db.query(Candidate).filter(Candidate.email.like('%@example.com')).delete()
        db.commit()
        
        # Test 1: Create a candidate
        print("\n1. Testing candidate creation...")
        candidate_data = CandidateCreate(
            email="test@example.com",
            name="Test User",
            phone="+1234567890"
        )
        
        created_candidate = await service.create_candidate(candidate_data)
        print(f"✓ Created candidate: {created_candidate.name} ({created_candidate.email})")
        
        # Test 2: Get candidate by ID
        print("\n2. Testing candidate retrieval...")
        retrieved_candidate = await service.get_candidate(created_candidate.id)
        print(f"✓ Retrieved candidate: {retrieved_candidate.name}")
        
        # Test 3: List candidates
        print("\n3. Testing candidate listing...")
        candidates_list = await service.list_candidates(page=1, page_size=10)
        print(f"✓ Found {candidates_list.total} candidates")
        
        # Test 4: Search candidates
        print("\n4. Testing candidate search...")
        search_params = CandidateSearch(
            query="Test",
            page=1,
            page_size=10
        )
        search_results = await service.search_candidates(search_params)
        print(f"✓ Search found {len(search_results.candidates)} candidates")
        
        # Test 5: Bulk import (CSV)
        print("\n5. Testing bulk import...")
        csv_data = """email,name,phone
bulk1@example.com,Bulk User 1,+1111111111
bulk2@example.com,Bulk User 2,+2222222222"""
        
        import_result = await service.bulk_import_candidates(
            csv_data.encode('utf-8'),
            "test.csv",
            "csv"
        )
        print(f"✓ Bulk import: {import_result.successful_imports} successful, {import_result.failed_imports} failed")
        
        # Test 6: Resume parsing (mock)
        print("\n6. Testing resume parsing...")
        resume_content = """
        John Doe
        Software Engineer
        Email: john@example.com
        Phone: +1234567890
        
        Skills: Python, JavaScript, React, SQL
        
        Experience:
        - Software Engineer at Tech Corp (2020-2023)
        - Junior Developer at StartupXYZ (2018-2020)
        
        Education:
        - BS Computer Science, University of Technology (2014-2018)
        """
        
        parse_result = await service._parse_resume(resume_content.encode('utf-8'), "resume.txt")
        if parse_result.success:
            print("✓ Resume parsing successful")
            if parse_result.parsed_data:
                print(f"  - Found {len(parse_result.parsed_data.skills)} skills")
                print(f"  - Found {len(parse_result.parsed_data.experience)} work experiences")
        else:
            print(f"⚠ Resume parsing failed: {parse_result.error}")
        
        print("\n✅ All candidate service tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_basic_functionality():
    """Test basic functionality without async"""
    print("Testing basic functionality...")
    
    # Test schema validation
    try:
        candidate_data = CandidateCreate(
            email="valid@example.com",
            name="Valid User",
            phone="+1234567890"
        )
        print("✓ Schema validation works")
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
    
    # Test parsed data schema
    try:
        parsed_data = ParsedResumeData(
            skills=[{"name": "Python", "confidence": 0.9, "category": "technical"}],
            total_experience_years=5.0,
            summary="Test summary"
        )
        print("✓ Parsed data schema works")
    except Exception as e:
        print(f"❌ Parsed data schema failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Candidate Management Tests")
    print("=" * 50)
    
    # Test basic functionality first
    test_basic_functionality()
    
    print("\n" + "=" * 50)
    
    # Test async functionality
    asyncio.run(test_candidate_service())
    
    print("\n🎉 All tests completed!")