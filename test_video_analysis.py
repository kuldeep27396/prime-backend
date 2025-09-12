"""
Test script for video analysis functionality
"""

import asyncio
import base64
import json
from app.services.video_analysis_service import video_analysis_service


async def test_real_time_proctoring():
    """Test real-time proctoring with a simple test image"""
    print("Testing real-time proctoring...")
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    try:
        result = await video_analysis_service.real_time_proctoring(
            frame_data=test_image_b64,
            session_context={
                "session_id": "test-session",
                "user_id": "test-user",
                "timestamp": 1234567890
            }
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Integrity Score: {result['integrity_score']:.2f}")
            print(f"Engagement Score: {result['engagement_score']:.2f}")
            print(f"Alerts: {len(result['alerts'])}")
            
            if result['alerts']:
                for alert in result['alerts']:
                    print(f"  - {alert['type']}: {alert['message']} ({alert['severity']})")
            
            if result['recommendations']:
                print("Recommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_vision_api_connectivity():
    """Test basic connectivity to vision APIs"""
    print("\nTesting Vision API connectivity...")
    
    try:
        # Test with a more complex prompt
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        result = await video_analysis_service._quick_integrity_check(test_image_b64)
        
        print("API Response:")
        print(json.dumps(result, indent=2))
        
        if "integrity_score" in result:
            print("✅ Vision API is responding correctly")
        else:
            print("⚠️ Vision API response format unexpected")
            
    except Exception as e:
        print(f"❌ Vision API test failed: {str(e)}")


async def test_analysis_prompt_generation():
    """Test analysis prompt generation"""
    print("\nTesting analysis prompt generation...")
    
    service = video_analysis_service
    
    # Test different prompt types
    prompts = [
        ("integrity", "basic"),
        ("engagement", "standard"),
        ("comprehensive", "premium")
    ]
    
    for analysis_type, tier in prompts:
        prompt = service._get_analysis_prompt(analysis_type, tier)
        print(f"\n{analysis_type.upper()} ({tier}):")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Contains JSON format: {'JSON format' in prompt}")
        print(f"Contains scoring: {'score' in prompt.lower()}")


async def test_response_parsing():
    """Test response parsing functionality"""
    print("\nTesting response parsing...")
    
    # Test various response formats
    test_responses = [
        # Valid JSON
        '{"integrity_score": 0.85, "engagement_score": 0.75, "professionalism_score": 0.90, "confidence": 0.8}',
        
        # JSON with extra text
        'Based on the analysis, here are the results: {"integrity_score": 0.7, "engagement_score": 0.6} The candidate appears focused.',
        
        # No JSON, text only
        'The candidate appears professional with good integrity score of 0.8 and engagement of 0.7.',
        
        # Malformed JSON
        '{"integrity_score": 0.85, "engagement_score": 0.75, "missing_bracket"'
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\nTest {i+1}:")
        print(f"Input: {response[:50]}...")
        
        try:
            parsed = video_analysis_service._parse_analysis_response(response)
            print(f"Parsed successfully:")
            print(f"  Integrity: {parsed.get('integrity_score', 'N/A')}")
            print(f"  Engagement: {parsed.get('engagement_score', 'N/A')}")
            print(f"  Confidence: {parsed.get('confidence', 'N/A')}")
        except Exception as e:
            print(f"Parsing failed: {str(e)}")


async def test_score_calculation():
    """Test overall score calculation"""
    print("\nTesting score calculation...")
    
    # Mock analysis results
    mock_results = {
        "integrity_analysis": [
            {"analysis": {"integrity_score": 0.8, "engagement_score": 0.7, "professionalism_score": 0.9}},
            {"analysis": {"integrity_score": 0.9, "engagement_score": 0.8, "professionalism_score": 0.8}},
        ],
        "engagement_analysis": [
            {"analysis": {"integrity_score": 0.8, "engagement_score": 0.7, "professionalism_score": 0.9}},
            {"analysis": {"integrity_score": 0.9, "engagement_score": 0.8, "professionalism_score": 0.8}},
        ],
        "professionalism_analysis": [
            {"analysis": {"integrity_score": 0.8, "engagement_score": 0.7, "professionalism_score": 0.9}},
            {"analysis": {"integrity_score": 0.9, "engagement_score": 0.8, "professionalism_score": 0.8}},
        ]
    }
    
    scores = video_analysis_service._calculate_overall_scores(mock_results)
    
    print("Calculated scores:")
    for key, value in scores.items():
        print(f"  {key}: {value}")
    
    # Verify weighted calculation
    expected_overall = (scores["integrity_score"] * 0.4 + 
                       scores["engagement_score"] * 0.3 + 
                       scores["professionalism_score"] * 0.3)
    
    print(f"\nExpected overall score: {expected_overall:.3f}")
    print(f"Actual overall score: {scores['overall_score']}")
    print(f"Match: {abs(expected_overall - scores['overall_score']) < 0.001}")


async def main():
    """Run all tests"""
    print("Starting Video Analysis Service Tests")
    print("=" * 50)
    
    await test_real_time_proctoring()
    await test_vision_api_connectivity()
    await test_analysis_prompt_generation()
    await test_response_parsing()
    await test_score_calculation()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nNote: Some tests may fail if API keys are not properly configured")
    print("or if network connectivity is limited.")


if __name__ == "__main__":
    asyncio.run(main())