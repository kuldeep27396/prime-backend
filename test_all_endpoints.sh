#!/bin/bash

echo "========================================"
echo "Prime Interviews API - Complete Test Suite"
echo "========================================"

API_BASE="http://localhost:8000"

echo ""
echo "1. HEALTH ENDPOINTS"
echo "=================="

echo "→ Root Endpoint:"
curl -s $API_BASE/ | jq '.'

echo ""
echo "→ Health Check:"
curl -s $API_BASE/health | jq '.'

echo ""
echo "2. EMAIL SERVICE"
echo "==============="

echo "→ Send Test Email:"
curl -s -X POST $API_BASE/api/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "toName": "Test User",
    "subject": "API Test Email",
    "html": "<h1>Test</h1><p>API working!</p>"
  }' | jq '.'

echo ""
echo "3. MENTOR ENDPOINTS (Require Auth)"
echo "================================="

echo "→ List Mentors (will show auth error):"
curl -s "$API_BASE/api/mentors?page=1&limit=2" | jq '.'

echo ""
echo "→ Mentor Details (will show auth error):"
curl -s "$API_BASE/api/mentors/27b81da0-eff0-4ab0-89d6-760a3805b7e6" | jq '.'

echo ""
echo "4. USER ENDPOINTS (Require Auth)"
echo "==============================="

echo "→ Create User (will show auth error):"
curl -s -X POST $API_BASE/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test_user_123",
    "email": "newuser@example.com",
    "firstName": "Test",
    "lastName": "User",
    "role": "candidate"
  }' | jq '.'

echo ""
echo "5. SESSION ENDPOINTS (Require Auth)"
echo "==================================="

echo "→ Create Session (will show auth error):"
curl -s -X POST $API_BASE/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "mentorId": "27b81da0-eff0-4ab0-89d6-760a3805b7e6",
    "sessionType": "Mock Technical Interview",
    "scheduledAt": "2024-01-20T14:00:00Z",
    "duration": 60,
    "meetingType": "video"
  }' | jq '.'

echo ""
echo "6. VIDEO ROOM ENDPOINTS (Require Auth)"
echo "======================================"

echo "→ Create Video Room (will show auth error):"
curl -s -X POST $API_BASE/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-id",
    "duration": 60,
    "participantName": "Test User",
    "mentorName": "Test Mentor"
  }' | jq '.'

echo ""
echo "7. DATABASE VERIFICATION"
echo "======================="

echo "→ Direct database query results:"
echo "Users in database:"
psql 'postgresql://neondb_owner:npg_wY5e9kpoClTs@ep-falling-sea-adt29dsd-pooler.c-2.us-east-1.aws.neon.tech/neondb' \
  -c "SELECT user_id, email, first_name, last_name, role FROM users;" -t

echo ""
echo "Mentors in database:"
psql 'postgresql://neondb_owner:npg_wY5e9kpoClTs@ep-falling-sea-adt29dsd-pooler.c-2.us-east-1.aws.neon.tech/neondb' \
  -c "SELECT name, title, current_company, rating FROM mentors;" -t

echo ""
echo "8. API DOCUMENTATION"
echo "==================="
echo "→ Interactive API docs available at: $API_BASE/docs"
echo "→ Alternative docs at: $API_BASE/redoc"

echo ""
echo "9. AUTHENTICATION NOTES"
echo "======================="
echo "→ All user/mentor/session endpoints require Clerk JWT authentication"
echo "→ To test with authentication, add header: Authorization: Bearer <jwt_token>"
echo "→ Email service works but requires SMTP configuration"
echo "→ Health endpoints work without authentication"

echo ""
echo "10. SAMPLE CURL WITH AUTH (when you have a JWT token)"
echo "===================================================="
echo 'curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/mentors'

echo ""
echo "Test completed! 🚀"