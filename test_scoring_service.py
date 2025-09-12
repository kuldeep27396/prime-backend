"""
Test script for AI Scoring and Analytics Engine
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, create_tables
from app.services.scoring_service import ScoringService, ScoringAnalytics
from app.models.company import Company, User
from app.models.job import Job, Application
from app.models.scoring import Score
from app.models.interview import Interview, InterviewResponse
from app.models.assessment import Assessment
from sqlalchemy.orm import Session


async def create_test_data(db: Session):
    """Create test data for scoring tests"""
    
    print("Creating test data...")
    
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
    
    for i in range(5):
        from app.models.company import Candidate
        
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
                ],
                "education": [
                    {
                        "degree": "Bachelor's",
                        "field": "Computer Science",
                        "school": f"University {i}"
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
        
        # Create interview data
        interview = Interview(
            application_id=application.id,
            type="live_ai",
            status="completed",
            metadata={
                "duration_minutes": 30 + i * 5,
                "questions_asked": 8 + i,
                "ai_model": "llama3-70b-8192"
            }
        )
        db.add(interview)
        db.flush()
        
        # Add interview responses
        responses = [
            {
                "question_id": "q1",
                "content": f"I have {3 + i} years of experience in software development...",
                "response_type": "text"
            },
            {
                "question_id": "q2", 
                "content": f"My technical skills include Python, JavaScript, and {'React' if i % 2 == 0 else 'Angular'}...",
                "response_type": "text"
            },
            {
                "question_id": "q3",
                "content": f"I work well in teams and have led {i + 1} projects...",
                "response_type": "text"
            }
        ]
        
        for resp_data in responses:
            response = InterviewResponse(
                interview_id=interview.id,
                question_id=resp_data["question_id"],
                response_type=resp_data["response_type"],
                content=resp_data["content"],
                duration=60 + i * 10,
                metadata={"confidence": 0.7 + i * 0.05}
            )
            db.add(response)
        
        # Create assessment data
        assessment = Assessment(
            application_id=application.id,
            type="coding",
            questions=[
                {
                    "id": "coding1",
                    "type": "coding",
                    "content": "Implement a binary search algorithm",
                    "difficulty": "medium"
                }
            ],
            responses=[
                {
                    "question_id": "coding1",
                    "code": f"def binary_search(arr, target):\n    # Implementation by candidate {i}\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
                    "execution_time": 150 + i * 20,
                    "test_results": {"passed": 8 + i, "total": 10}
                }
            ],
            auto_grade={
                "score": 75 + i * 5,
                "feedback": f"Good implementation with {8 + i}/10 test cases passing"
            },
            completed_at=datetime.utcnow()
        )
        db.add(assessment)
        
        test_applications.append(application)
    
    db.commit()
    print(f"Created {len(test_applications)} test applications")
    return test_applications


async def test_score_calculation():
    """Test comprehensive score calculation"""
    
    print("\n=== Testing Score Calculation ===")
    
    # Initialize database
    await create_tables()
    db = next(get_db())
    
    try:
        # Create test data
        applications = await create_test_data(db)
        scoring_service = ScoringService()
        
        # Test score calculation for first application
        app_id = str(applications[0].id)
        print(f"Calculating scores for application: {app_id}")
        
        scores = await scoring_service.calculate_comprehensive_scores(
            app_id, db, force_recalculate=True
        )
        
        print("Score calculation results:")
        print(f"Overall Score: {scores['overall_score']}")
        print(f"Overall Confidence: {scores['overall_confidence']}")
        
        print("\nCategory Scores:")
        for category, score_data in scores['category_scores'].items():
            print(f"  {category}: {score_data['score']:.2f} (confidence: {score_data['confidence']:.3f})")
        
        print("\nExplanation:")
        explanation = scores.get('explanation', {})
        print(f"  Executive Summary: {explanation.get('executive_summary', 'N/A')}")
        print(f"  Recommendation: {explanation.get('recommendation', 'N/A')}")
        print(f"  Key Strengths: {explanation.get('key_strengths', [])}")
        
        # Test caching (should return cached results)
        print("\nTesting score caching...")
        cached_scores = await scoring_service.calculate_comprehensive_scores(
            app_id, db, force_recalculate=False
        )
        
        print(f"Cached result - Overall Score: {cached_scores['overall_score']}")
        print(f"From cache: {cached_scores.get('scores_metadata', {}).get('from_cache', False)}")
        
        return True
        
    except Exception as e:
        print(f"Score calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_bias_detection():
    """Test bias detection functionality"""
    
    print("\n=== Testing Bias Detection ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get all test applications
        applications = db.query(Application).all()
        app_ids = [str(app.id) for app in applications]
        
        print(f"Testing bias detection for {len(app_ids)} applications")
        
        # Calculate scores for all applications first
        for app_id in app_ids:
            try:
                await scoring_service.calculate_comprehensive_scores(app_id, db)
                print(f"  Calculated scores for {app_id}")
            except Exception as e:
                print(f"  Failed to calculate scores for {app_id}: {e}")
        
        # Test bias detection
        print("\nRunning bias detection analysis...")
        
        # Create mock demographic data
        demographic_data = {
            "gender": {app_ids[0]: "male", app_ids[1]: "female", app_ids[2]: "male", 
                      app_ids[3]: "female", app_ids[4]: "male"},
            "ethnicity": {app_ids[0]: "white", app_ids[1]: "asian", app_ids[2]: "hispanic", 
                         app_ids[3]: "black", app_ids[4]: "white"}
        }
        
        bias_analysis = await scoring_service.detect_bias_in_scores(
            app_ids, db, demographic_data
        )
        
        print("Bias Detection Results:")
        print(f"Overall Bias Risk: {bias_analysis['overall_bias_risk']['risk_level']}")
        print(f"Risk Score: {bias_analysis['overall_bias_risk']['risk_score']}")
        print(f"Risk Factors: {bias_analysis['overall_bias_risk']['risk_factors']}")
        
        print("\nStatistical Analysis:")
        stat_analysis = bias_analysis['statistical_analysis']
        for category, stats in stat_analysis.get('score_distribution', {}).items():
            print(f"  {category}: mean={stats['mean']:.2f}, std_dev={stats['std_dev']:.2f}")
        
        print("\nAI Analysis:")
        ai_analysis = bias_analysis['ai_analysis']
        print(f"  Fairness Score: {ai_analysis.get('fairness_score', 'N/A')}")
        print(f"  Confidence Level: {ai_analysis.get('confidence_level', 'N/A')}")
        print(f"  Bias Indicators: {ai_analysis.get('bias_indicators', [])}")
        
        print("\nRecommendations:")
        for rec in bias_analysis.get('recommendations', [])[:5]:  # Show first 5
            print(f"  - {rec}")
        
        return True
        
    except Exception as e:
        print(f"Bias detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_comparative_ranking():
    """Test comparative ranking functionality"""
    
    print("\n=== Testing Comparative Ranking ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get all test applications
        applications = db.query(Application).all()
        app_ids = [str(app.id) for app in applications]
        
        print(f"Generating ranking for {len(app_ids)} applications")
        
        ranking = await scoring_service.generate_comparative_ranking(
            app_ids, db
        )
        
        print("Ranking Results:")
        print(f"Total Candidates: {ranking['statistics']['total_candidates']}")
        
        print("\nScore Statistics:")
        stats = ranking['statistics']['score_statistics']
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Median: {stats['median']:.2f}")
        print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
        
        print("\nTier Distribution:")
        tier_dist = ranking['statistics']['tier_distribution']
        for tier, count in tier_dist.items():
            print(f"  {tier}: {count} candidates")
        
        print("\nTop 3 Candidates:")
        for i, candidate in enumerate(ranking['rankings'][:3]):
            print(f"  {i+1}. {candidate['candidate_name']}")
            print(f"     Score: {candidate['overall_score']:.2f}")
            print(f"     Percentile: {candidate['percentile']:.1f}")
            print(f"     Tier: {candidate['tier']}")
        
        print("\nRanking Insights:")
        insights = ranking.get('insights', {})
        print(f"  Talent Pool Quality: {insights.get('talent_pool_quality', 'N/A')}")
        print(f"  Hiring Recommendations: {insights.get('hiring_recommendations', [])}")
        
        return True
        
    except Exception as e:
        print(f"Comparative ranking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_confidence_intervals():
    """Test confidence interval calculation"""
    
    print("\n=== Testing Confidence Intervals ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get first test application
        application = db.query(Application).first()
        app_id = str(application.id)
        
        print(f"Calculating confidence intervals for application: {app_id}")
        
        intervals = await scoring_service.calculate_confidence_intervals(
            app_id, db, confidence_level=0.95
        )
        
        print("Confidence Interval Results:")
        print(f"Confidence Level: {intervals['confidence_level']}")
        print(f"Historical Sample Size: {intervals['historical_sample_size']}")
        
        print("\nCategory Intervals:")
        for category, interval_data in intervals['intervals'].items():
            interval = interval_data['interval']
            print(f"  {category}:")
            print(f"    Score: {interval_data['score']:.2f}")
            print(f"    Interval: [{interval['lower_bound']:.2f}, {interval['upper_bound']:.2f}]")
            print(f"    Width: {interval['width']:.2f}")
            print(f"    Reliability: {interval_data['reliability']}")
        
        return True
        
    except Exception as e:
        print(f"Confidence intervals test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_performance_prediction():
    """Test historical performance prediction"""
    
    print("\n=== Testing Performance Prediction ===")
    
    db = next(get_db())
    
    try:
        scoring_service = ScoringService()
        
        # Get first test application
        application = db.query(Application).first()
        app_id = str(application.id)
        
        print(f"Predicting performance for application: {app_id}")
        
        # Create some historical outcome data first
        print("Creating historical outcome data...")
        applications = db.query(Application).all()
        for i, app in enumerate(applications[1:]):  # Skip first one
            app.status = "hired" if i % 2 == 0 else "rejected"
        db.commit()
        
        prediction = await scoring_service.predict_historical_performance(
            app_id, db, prediction_horizon_days=180
        )
        
        print("Performance Prediction Results:")
        overall_pred = prediction['overall_prediction']
        print(f"Success Probability: {overall_pred['predicted_success_probability']:.3f}")
        print(f"Assessment: {overall_pred['assessment']}")
        print(f"Hire Recommendation: {overall_pred['hire_recommendation']}")
        print(f"Confidence: {overall_pred['confidence']:.3f}")
        
        print("\nCategory Predictions:")
        for category, pred in prediction['category_predictions'].items():
            print(f"  {category}:")
            print(f"    Success Probability: {pred['predicted_success_probability']:.3f}")
            print(f"    Confidence: {pred['confidence']:.3f}")
            print(f"    Similar Candidates: {pred['similar_candidates_count']}")
        
        print("\nRisk Factors:")
        for risk in overall_pred.get('risk_factors', []):
            print(f"  - {risk}")
        
        print("\nSuccess Indicators:")
        for indicator in overall_pred.get('success_indicators', []):
            print(f"  - {indicator}")
        
        return True
        
    except Exception as e:
        print(f"Performance prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_analytics():
    """Test analytics functionality"""
    
    print("\n=== Testing Analytics ===")
    
    db = next(get_db())
    
    try:
        # Get test data
        applications = db.query(Application).all()
        scores = db.query(Score).all()
        
        print(f"Testing analytics with {len(applications)} applications and {len(scores)} scores")
        
        # Test score trends
        print("\nTesting score trends...")
        trends = ScoringAnalytics.calculate_score_trends(scores, time_period_days=30)
        
        print("Score Trends:")
        for period, trend_data in trends.get('trends', {}).items():
            print(f"  Period {period}: mean={trend_data['mean_score']:.2f}, count={trend_data['score_count']}")
        
        # Test category correlations
        print("\nTesting category correlations...")
        correlations = ScoringAnalytics.calculate_category_correlations(applications, db)
        
        print("Category Correlations:")
        for pair, corr_data in correlations.get('correlations', {}).items():
            print(f"  {pair}: r={corr_data['correlation']:.3f}, p={corr_data['p_value']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"Analytics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all scoring service tests"""
    
    print("PRIME AI Scoring and Analytics Engine - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Score Calculation", test_score_calculation),
        ("Bias Detection", test_bias_detection),
        ("Comparative Ranking", test_comparative_ranking),
        ("Confidence Intervals", test_confidence_intervals),
        ("Performance Prediction", test_performance_prediction),
        ("Analytics", test_analytics)
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
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Scoring and Analytics Engine is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())