"""
Simple test script for AI Scoring and Analytics Engine
Tests core functionality without requiring external APIs
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, create_tables
from app.services.scoring_service import ScoringService, ScoringAnalytics
from app.models.company import Company, User
from app.models.job import Candidate
from app.models.job import Job, Application
from app.models.scoring import Score
from sqlalchemy.orm import Session


async def create_simple_test_data(db: Session):
    """Create simple test data for scoring tests"""
    
    print("Creating simple test data...")
    
    # Clean up existing data
    db.query(Score).delete()
    db.query(Application).delete()
    db.query(Candidate).delete()
    db.query(Job).delete()
    db.query(User).delete()
    db.query(Company).delete()
    db.commit()
    
    # Create test company
    company = Company(
        name="Test Company",
        domain="test.com",
        settings={"scoring_enabled": True}
    )
    db.add(company)
    db.flush()
    
    # Create test user
    user = User(
        company_id=company.id,
        email="test@test.com",
        password_hash="hashed_password",
        role="recruiter",
        profile={"name": "Test User"}
    )
    db.add(user)
    db.flush()
    
    # Create test job
    job = Job(
        company_id=company.id,
        title="Senior Software Engineer",
        description="Looking for an experienced software engineer",
        requirements={
            "skills": ["Python", "JavaScript", "React"],
            "experience": "5+ years",
            "education": "Bachelor's degree"
        },
        status="active",
        created_by=user.id
    )
    db.add(job)
    db.flush()
    
    # Create test candidates and applications
    test_applications = []
    
    for i in range(3):
        candidate = Candidate(
            email=f"candidate{i}@test.com",
            name=f"Test Candidate {i}",
            phone=f"555-000-{i:04d}",
            parsed_data={
                "skills": ["Python", "JavaScript"] if i % 2 == 0 else ["Java", "C++"],
                "experience": [
                    {
                        "title": "Software Engineer",
                        "company": f"Company {i}",
                        "duration": f"{3 + i} years"
                    }
                ]
            }
        )
        db.add(candidate)
        db.flush()
        
        application = Application(
            job_id=job.id,
            candidate_id=candidate.id,
            status="interviewing",
            cover_letter=f"I am very interested in this position. Candidate {i}",
            application_data={"source": "website"}
        )
        db.add(application)
        db.flush()
        
        test_applications.append(application)
    
    db.commit()
    print(f"Created {len(test_applications)} test applications")
    return test_applications


async def create_mock_scores(applications, db: Session):
    """Create mock scores for testing without AI API calls"""
    
    print("Creating mock scores...")
    
    categories = ['technical', 'communication', 'cultural_fit', 'cognitive', 'behavioral']
    
    for i, app in enumerate(applications):
        for j, category in enumerate(categories):
            # Create varied scores for testing
            base_score = 60 + (i * 10) + (j * 2)  # Varied scores
            confidence = 70 + (i * 5) + (j * 3)   # Varied confidence
            
            score = Score(
                application_id=app.id,
                category=category,
                score=min(100, base_score),
                confidence=min(100, confidence),
                reasoning=f"Mock reasoning for {category} - candidate {i}",
                evidence=[f"evidence_1_{category}", f"evidence_2_{category}"],
                created_by='ai'
            )
            db.add(score)
    
    db.commit()
    print("Mock scores created successfully")


async def test_basic_functionality():
    """Test basic scoring functionality without external APIs"""
    
    print("\n=== Testing Basic Functionality ===")
    
    # Initialize database
    await create_tables()
    db = next(get_db())
    
    try:
        # Create test data
        applications = await create_simple_test_data(db)
        await create_mock_scores(applications, db)
        
        scoring_service = ScoringService()
        
        # Test 1: Get existing scores
        app_id = str(applications[0].id)
        print(f"Testing score retrieval for application: {app_id}")
        
        scores = db.query(Score).filter(Score.application_id == app_id).all()
        print(f"Found {len(scores)} scores")
        
        # Format scores using the service
        formatted_scores = await scoring_service._format_score_response(scores, applications[0])
        
        print("Formatted Scores:")
        print(f"Overall Score: {formatted_scores['overall_score']}")
        print(f"Overall Confidence: {formatted_scores['overall_confidence']}")
        
        print("\nCategory Scores:")
        for category, score_data in formatted_scores['category_scores'].items():
            print(f"  {category}: {score_data['score']:.2f} (confidence: {score_data['confidence']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_bias_detection_simple():
    """Test bias detection with mock data"""
    
    print("\n=== Testing Bias Detection (Simple) ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get all test applications
        applications = db.query(Application).all()
        app_ids = [str(app.id) for app in applications]
        
        print(f"Testing bias detection for {len(app_ids)} applications")
        
        # Test statistical bias analysis only (no AI analysis)
        scores = db.query(Score).filter(
            Score.application_id.in_(app_ids),
            Score.created_by == 'ai'
        ).all()
        
        if not scores:
            print("No scores found for bias analysis")
            return False
        
        # Group scores by application and category
        score_data = {}
        for score in scores:
            app_id = str(score.application_id)
            if app_id not in score_data:
                score_data[app_id] = {}
            score_data[app_id][score.category] = float(score.score)
        
        # Perform statistical analysis
        statistical_analysis = await scoring_service._perform_statistical_bias_analysis(
            score_data, None
        )
        
        print("Statistical Bias Analysis Results:")
        for category, stats in statistical_analysis.get('score_distribution', {}).items():
            print(f"  {category}: mean={stats['mean']:.2f}, std_dev={stats['std_dev']:.2f}")
        
        variance_analysis = statistical_analysis.get('variance_analysis', {})
        if variance_analysis:
            print(f"\nVariance Analysis:")
            print(f"  Coefficient of Variation: {variance_analysis.get('coefficient_of_variation', 0):.3f}")
            print(f"  High Variance: {variance_analysis.get('is_high_variance', False)}")
        
        return True
        
    except Exception as e:
        print(f"Bias detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_ranking_simple():
    """Test comparative ranking with mock data"""
    
    print("\n=== Testing Comparative Ranking (Simple) ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get all test applications
        applications = db.query(Application).all()
        app_ids = [str(app.id) for app in applications]
        
        print(f"Generating ranking for {len(app_ids)} applications")
        
        # Create mock overall scores for ranking
        for i, app in enumerate(applications):
            overall_score = 70 + (i * 10)  # Varied overall scores
            
            # Calculate overall score from existing category scores
            category_scores = db.query(Score).filter(
                Score.application_id == app.id,
                Score.created_by == 'ai'
            ).all()
            
            if category_scores:
                # Use the existing weighted calculation
                category_data = {}
                for score in category_scores:
                    category_data[score.category] = {
                        "score": float(score.score),
                        "confidence": float(score.confidence) / 100,
                        "weight": scoring_service.scoring_categories.get(score.category, {}).get("weight", 0.2)
                    }
                
                overall_result = scoring_service._calculate_weighted_overall_score(category_data)
                
                # Create a mock overall score record for ranking test
                mock_overall = Score(
                    application_id=app.id,
                    category='overall_mock',  # Use different name to avoid constraint
                    score=overall_result["score"],
                    confidence=overall_result["confidence"] * 100,
                    reasoning="Mock overall score for testing",
                    evidence=[],
                    created_by='ai'
                )
                db.add(mock_overall)
        
        db.commit()
        
        # Now test ranking with mock overall scores
        mock_scores = db.query(Score).filter(
            Score.application_id.in_(app_ids),
            Score.category == 'overall_mock',
            Score.created_by == 'ai'
        ).all()
        
        if not mock_scores:
            print("No mock overall scores found for ranking")
            return False
        
        # Build ranking data manually for testing
        ranking_data = []
        score_values = []
        
        for score in mock_scores:
            app = db.query(Application).filter(Application.id == score.application_id).first()
            if app:
                ranking_data.append({
                    "application_id": str(app.id),
                    "candidate_name": app.candidate.name,
                    "overall_score": float(score.score),
                    "confidence": float(score.confidence)
                })
                score_values.append(float(score.score))
        
        # Sort by score (descending)
        ranking_data.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Calculate percentiles and ranks
        for i, candidate in enumerate(ranking_data):
            candidate["rank"] = i + 1
            candidate["percentile"] = scoring_service._calculate_percentile(
                candidate["overall_score"], score_values
            )
            candidate["tier"] = scoring_service._get_candidate_tier(candidate["percentile"])
        
        print("Ranking Results:")
        print(f"Total Candidates: {len(ranking_data)}")
        
        print("\nRanked Candidates:")
        for candidate in ranking_data:
            print(f"  {candidate['rank']}. {candidate['candidate_name']}")
            print(f"     Score: {candidate['overall_score']:.2f}")
            print(f"     Percentile: {candidate['percentile']:.1f}")
            print(f"     Tier: {candidate['tier']}")
        
        return True
        
    except Exception as e:
        print(f"Ranking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_analytics_simple():
    """Test analytics functionality with mock data"""
    
    print("\n=== Testing Analytics (Simple) ===")
    
    db = next(get_db())
    
    try:
        # Get test data
        applications = db.query(Application).all()
        scores = db.query(Score).filter(Score.category != 'overall_mock').all()  # Exclude mock scores
        
        print(f"Testing analytics with {len(applications)} applications and {len(scores)} scores")
        
        # Test score trends
        print("\nTesting score trends...")
        trends = ScoringAnalytics.calculate_score_trends(scores, time_period_days=30)
        
        if 'trends' in trends:
            print("Score Trends:")
            for period, trend_data in trends['trends'].items():
                print(f"  Period {period}: mean={trend_data['mean_score']:.2f}, count={trend_data['score_count']}")
        else:
            print("No trend data available")
        
        # Test category correlations
        print("\nTesting category correlations...")
        correlations = ScoringAnalytics.calculate_category_correlations(applications, db)
        
        if 'correlations' in correlations:
            print("Category Correlations:")
            for pair, corr_data in correlations['correlations'].items():
                print(f"  {pair}: r={corr_data['correlation']:.3f}, p={corr_data['p_value']:.3f}")
        else:
            print("No correlation data available")
        
        return True
        
    except Exception as e:
        print(f"Analytics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run simplified scoring service tests"""
    
    print("PRIME AI Scoring and Analytics Engine - Simple Test Suite")
    print("=" * 70)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Bias Detection (Simple)", test_bias_detection_simple),
        ("Comparative Ranking (Simple)", test_ranking_simple),
        ("Analytics (Simple)", test_analytics_simple)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = await test_func()
            results[test_name] = result
            status = "PASSED" if result else "FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"{test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Scoring and Analytics Engine core functionality is working.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())