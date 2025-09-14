# Prime Interviews - Backend API Documentation

## Overview

This document outlines all the API endpoints required for the Prime Interviews frontend application, including data models, input/output specifications, authentication requirements, and database schema.

## Base Information

- **Application**: Prime Interviews - Interview Scheduling Platform
- **Frontend**: React.js with Vite
- **Email Service**: Resend API with React Email templates
- **Authentication**: Clerk.js
- **Current Backend**: Node.js/Express (test implementation running on port 8000)

## Current API Endpoints

### 1. Email Service API

#### POST /api/send-email

**Description**: Send interview invitation emails using Resend API with React Email templates

**Authentication**: None required (internal service)

**Request Body**:
```json
{
  "to": "string",           // Recipient email address
  "toName": "string",       // Recipient name
  "subject": "string",      // Email subject line
  "html": "string"          // Rendered HTML email content
}
```

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Email sent successfully via Resend",
  "messageId": "string"     // Resend message ID for tracking
}
```

**Response Error (500)**:
```json
{
  "success": false,
  "message": "Failed to send email: [error details]"
}
```

**Example Usage**:
```javascript
const response = await fetch('/api/send-email', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    to: 'candidate@example.com',
    toName: 'John Doe',
    subject: 'Interview Invitation: Senior Developer Position',
    html: renderToString(<InterviewInvitationEmail {...props} />)
  })
});
```

---

## Required API Endpoints for Complete Application

### 2. User Management APIs

#### POST /api/users
**Description**: Create or update user profile after Clerk authentication

**Authentication**: Required (Clerk JWT token)

**Headers**:
```
Authorization: Bearer <clerk_jwt_token>
```

**Request Body**:
```json
{
  "userId": "string",        // Clerk user ID
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "profileImage": "string",  // URL to profile image
  "role": "string",          // "candidate", "mentor", "admin"
  "experience": "string",    // Experience level
  "skills": ["string"],      // Array of skills
  "preferences": {
    "recentSearches": ["string"],
    "favoriteTopics": ["string"],
    "timezone": "string"
  }
}
```

**Response**:
```json
{
  "success": true,
  "user": {
    "id": "string",
    "userId": "string",      // Clerk user ID
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "role": "string",
    "createdAt": "ISO8601",
    "updatedAt": "ISO8601"
  }
}
```

#### GET /api/users/:userId
**Description**: Get user profile and session history

**Authentication**: Required

**Response**:
```json
{
  "profile": {
    "userId": "string",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "role": "string",
    "experience": "string",
    "profileImage": "string"
  },
  "sessionHistory": [
    {
      "id": "string",
      "mentorId": "string",
      "date": "ISO8601",
      "duration": "number",
      "type": "string",
      "rating": "number",
      "feedback": "string"
    }
  ],
  "skillAssessments": [
    {
      "skill": "string",
      "score": "number",
      "assessedAt": "ISO8601"
    }
  ],
  "favorites": ["string"],    // Array of mentor IDs
  "preferences": {
    "recentSearches": ["string"],
    "favoriteTopics": ["string"],
    "timezone": "string"
  }
}
```

### 3. Mentor Management APIs

#### GET /api/mentors
**Description**: Get paginated list of mentors with filtering

**Query Parameters**:
```
?page=1
&limit=20
&skills=React,JavaScript
&companies=Google,Meta
&rating_min=4.5
&price_min=50
&price_max=200
&experience_min=5
&languages=English,Spanish
&search=system+design
```

**Response**:
```json
{
  "mentors": [
    {
      "id": "string",
      "name": "string",
      "title": "string",
      "currentCompany": "string",
      "previousCompanies": ["string"],
      "avatar": "string",
      "bio": "string",
      "specialties": ["string"],
      "skills": ["string"],
      "languages": ["string"],
      "experience": "number",
      "rating": "number",
      "reviewCount": "number",
      "hourlyRate": "number",
      "responseTime": "string",
      "timezone": "string",
      "availability": ["string"]    // Available time slots
    }
  ],
  "pagination": {
    "page": "number",
    "limit": "number",
    "total": "number",
    "totalPages": "number"
  },
  "filters": {
    "availableSkills": ["string"],
    "availableCompanies": ["string"],
    "availableLanguages": ["string"],
    "priceRange": { "min": "number", "max": "number" },
    "experienceRange": { "min": "number", "max": "number" }
  }
}
```

#### GET /api/mentors/:mentorId
**Description**: Get detailed mentor profile

**Response**:
```json
{
  "id": "string",
  "name": "string",
  "title": "string",
  "currentCompany": "string",
  "previousCompanies": ["string"],
  "avatar": "string",
  "bio": "string",
  "specialties": ["string"],
  "skills": ["string"],
  "languages": ["string"],
  "experience": "number",
  "rating": "number",
  "reviewCount": "number",
  "hourlyRate": "number",
  "responseTime": "string",
  "timezone": "string",
  "availability": ["string"],
  "reviews": [
    {
      "id": "string",
      "userId": "string",
      "userName": "string",
      "rating": "number",
      "comment": "string",
      "date": "ISO8601",
      "sessionType": "string"
    }
  ],
  "upcomingSlots": ["string"],
  "isAvailable": "boolean"
}
```

### 4. Booking/Session APIs

#### POST /api/sessions
**Description**: Create new interview session booking

**Authentication**: Required

**Request Body**:
```json
{
  "mentorId": "string",
  "sessionType": "string",       // "Mock Technical Interview", "System Design", etc.
  "scheduledAt": "ISO8601",      // Session date/time
  "duration": "number",          // Duration in minutes
  "meetingType": "string",       // "video", "audio", "in-person"
  "recordSession": "boolean",
  "specialRequests": "string",
  "meetingLink": "string",       // Generated room URL for video calls
  "participantEmail": "string",  // Participant's email for notifications
  "participantName": "string"
}
```

**Response**:
```json
{
  "success": true,
  "session": {
    "id": "string",
    "userId": "string",
    "mentorId": "string",
    "sessionType": "string",
    "scheduledAt": "ISO8601",
    "duration": "number",
    "meetingType": "string",
    "meetingLink": "string",
    "status": "string",           // "pending", "confirmed", "completed", "cancelled"
    "recordSession": "boolean",
    "specialRequests": "string",
    "createdAt": "ISO8601"
  },
  "emailSent": "boolean"
}
```

#### GET /api/sessions
**Description**: Get user's session history and upcoming sessions

**Authentication**: Required

**Query Parameters**:
```
?status=upcoming
&limit=10
&page=1
```

**Response**:
```json
{
  "sessions": [
    {
      "id": "string",
      "mentorId": "string",
      "mentorName": "string",
      "mentorAvatar": "string",
      "mentorCompany": "string",
      "sessionType": "string",
      "scheduledAt": "ISO8601",
      "duration": "number",
      "meetingType": "string",
      "meetingLink": "string",
      "status": "string",
      "rating": "number",          // If completed
      "feedback": "string",        // If completed
      "recordingUrl": "string"     // If recorded and available
    }
  ],
  "stats": {
    "totalSessions": "number",
    "completedSessions": "number",
    "upcomingSessions": "number",
    "averageRating": "number",
    "totalHours": "number"
  }
}
```

#### PATCH /api/sessions/:sessionId
**Description**: Update session status, add feedback, or cancel

**Authentication**: Required

**Request Body**:
```json
{
  "status": "string",           // "cancelled", "completed"
  "rating": "number",           // 1-5 rating
  "feedback": "string",         // Session feedback
  "cancellationReason": "string"
}
```

### 5. Dashboard Analytics APIs

#### GET /api/users/:userId/analytics
**Description**: Get user dashboard analytics and progress data

**Authentication**: Required

**Response**:
```json
{
  "stats": {
    "totalInterviews": "number",
    "completedCount": "number",
    "upcomingCount": "number",
    "averageScore": "number",
    "totalHoursSpent": "number"
  },
  "progressData": [
    {
      "month": "string",
      "score": "number",
      "interviews": "number"
    }
  ],
  "skillAssessments": [
    {
      "skill": "string",
      "score": "number",
      "assessedAt": "ISO8601"
    }
  ],
  "upcomingInterviews": [
    {
      "id": "string",
      "mentorName": "string",
      "company": "string",
      "title": "string",
      "scheduledAt": "ISO8601",
      "type": "string",
      "difficulty": "string"
    }
  ],
  "recentActivity": [
    {
      "type": "string",          // "session_completed", "skill_assessed", etc.
      "description": "string",
      "date": "ISO8601",
      "metadata": "object"
    }
  ]
}
```

### 6. Video Call Integration APIs

#### POST /api/rooms
**Description**: Create video call room for interview sessions

**Authentication**: Required

**Request Body**:
```json
{
  "sessionId": "string",
  "duration": "number",         // Duration in minutes
  "participantName": "string",
  "mentorName": "string",
  "recordSession": "boolean"
}
```

**Response**:
```json
{
  "roomId": "string",
  "roomUrl": "string",
  "participantToken": "string",  // HMS token for participant
  "mentorToken": "string",       // HMS token for mentor (if applicable)
  "expiresAt": "ISO8601"
}
```

#### GET /api/rooms/:roomId/status
**Description**: Get room status and participants

**Response**:
```json
{
  "roomId": "string",
  "status": "string",           // "active", "ended", "not_started"
  "participants": [
    {
      "name": "string",
      "role": "string",         // "participant", "mentor"
      "joinedAt": "ISO8601",
      "isActive": "boolean"
    }
  ],
  "recordingUrl": "string",     // If recording is available
  "duration": "number"          // Actual session duration
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) UNIQUE NOT NULL,  -- Clerk user ID
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  profile_image TEXT,
  role VARCHAR(50) DEFAULT 'candidate',   -- candidate, mentor, admin
  experience VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Mentors Table
```sql
CREATE TABLE mentors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  title VARCHAR(255),
  current_company VARCHAR(255),
  previous_companies JSONB,              -- Array of companies
  avatar TEXT,
  bio TEXT,
  specialties JSONB,                     -- Array of specialties
  skills JSONB,                          -- Array of skills
  languages JSONB,                       -- Array of languages
  experience INTEGER,
  rating DECIMAL(3,2) DEFAULT 0,
  review_count INTEGER DEFAULT 0,
  hourly_rate DECIMAL(8,2),
  response_time VARCHAR(50),
  timezone VARCHAR(100),
  availability JSONB,                    -- Array of available slots
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  mentor_id UUID REFERENCES mentors(id),
  session_type VARCHAR(255),
  scheduled_at TIMESTAMP NOT NULL,
  duration INTEGER NOT NULL,            -- Duration in minutes
  meeting_type VARCHAR(50),             -- video, audio, in-person
  meeting_link TEXT,
  status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed, completed, cancelled
  record_session BOOLEAN DEFAULT false,
  special_requests TEXT,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  feedback TEXT,
  cancellation_reason TEXT,
  recording_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### User Preferences Table
```sql
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  recent_searches JSONB,                -- Array of recent search terms
  favorite_topics JSONB,                -- Array of favorite topics
  favorite_mentors JSONB,               -- Array of mentor IDs
  timezone VARCHAR(100),
  notification_settings JSONB,          -- Email, SMS preferences
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Skill Assessments Table
```sql
CREATE TABLE skill_assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  skill VARCHAR(255) NOT NULL,
  score INTEGER CHECK (score >= 0 AND score <= 100),
  assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id UUID REFERENCES sessions(id)  -- Optional: linked to session
);
```

### Reviews Table
```sql
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id),
  mentor_id UUID REFERENCES mentors(id),
  user_id UUID REFERENCES users(id),
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  is_public BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Video Rooms Table
```sql
CREATE TABLE video_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id VARCHAR(255) UNIQUE NOT NULL,
  session_id UUID REFERENCES sessions(id),
  room_url TEXT NOT NULL,
  participant_token TEXT,
  mentor_token TEXT,
  status VARCHAR(50) DEFAULT 'active',  -- active, ended
  recording_url TEXT,
  actual_duration INTEGER,              -- Actual duration in minutes
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP
);
```

---

## Authentication & Authorization

### Authentication Flow
1. Frontend uses Clerk.js for user authentication
2. Clerk provides JWT tokens for authenticated requests
3. Backend verifies JWT tokens using Clerk's public keys
4. User information extracted from JWT payload

### Headers for Authenticated Requests
```
Authorization: Bearer <clerk_jwt_token>
Content-Type: application/json
```

### JWT Payload Structure
```json
{
  "sub": "user_id",           // Clerk user ID
  "email": "string",
  "email_verified": "boolean",
  "first_name": "string",
  "last_name": "string",
  "image_url": "string",
  "iss": "https://clerk_instance.clerk.accounts.dev",
  "iat": "number",
  "exp": "number"
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "string",           // ERROR_CODE
    "message": "string",        // Human-readable message
    "details": "object"         // Additional error details
  }
}
```

### Common Error Codes
- `UNAUTHORIZED`: Missing or invalid authentication token
- `FORBIDDEN`: User lacks required permissions
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Requested resource not found
- `CONFLICT`: Resource conflict (e.g., time slot already booked)
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server internal error

---

## Email Integration

### Current Implementation
- **Service**: Resend API
- **Templates**: React Email components
- **Endpoint**: `/api/send-email`

### Email Types
1. **Interview Invitations**: Sent when booking is confirmed
2. **Reminders**: 24 hours before session
3. **Cancellations**: When sessions are cancelled
4. **Feedback Requests**: After completed sessions
5. **Welcome Emails**: For new user registration

### Email Template Data Structure
```javascript
// Interview Invitation Email Props
{
  to_name: "string",
  meeting_title: "string",
  meeting_date: "string",      // Formatted date
  meeting_time: "string",      // Formatted time
  meeting_duration: "string",  // "60 minutes"
  meeting_description: "string",
  meeting_link: "string",      // Video call URL
  mentor_name: "string",
  mentor_company: "string"
}
```

---

## Environment Variables

### Required Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379

# Authentication
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Email Service
RESEND_API_KEY=re_...

# Video Service (HMS)
HMS_APP_ID=...
HMS_APP_SECRET=...

# API Configuration
PORT=8000
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Security
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

---

## Rate Limiting

### API Rate Limits
- **General API**: 100 requests per minute per user
- **Email API**: 10 requests per minute per user
- **Search API**: 30 requests per minute per user
- **File Upload**: 5 requests per minute per user

### Implementation
```javascript
// Express rate limiting middleware
const rateLimit = require('express-rate-limit');

const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,            // Limit each IP to 100 requests per windowMs
  message: 'Too many API requests, please try again later.'
});
```

---

## API Response Examples

### Successful Booking Flow
```javascript
// 1. Create session
POST /api/sessions
Response: { success: true, session: {...}, emailSent: true }

// 2. Create video room
POST /api/rooms
Response: { roomId: "...", roomUrl: "...", participantToken: "..." }

// 3. Send confirmation email
POST /api/send-email
Response: { success: true, messageId: "..." }
```

### Error Scenarios
```javascript
// Time slot conflict
POST /api/sessions
Response: {
  success: false,
  error: {
    code: "CONFLICT",
    message: "Selected time slot is no longer available",
    details: { conflictingSessionId: "..." }
  }
}

// Validation error
POST /api/sessions
Response: {
  success: false,
  error: {
    code: "VALIDATION_ERROR",
    message: "Invalid session duration",
    details: { field: "duration", value: -30 }
  }
}
```

---

## Notes for Backend Implementation

1. **Database**: PostgreSQL recommended with proper indexing on frequently queried fields
2. **Caching**: Redis for session data, mentor availability, and user preferences
3. **File Storage**: AWS S3 or similar for profile images and session recordings
4. **Real-time**: WebSocket connections for live session status updates
5. **Monitoring**: Implement logging and monitoring for email delivery, session creation, and API performance
6. **Backup**: Regular database backups and session recording backup strategy
7. **Testing**: Comprehensive API tests including authentication, validation, and integration tests

This documentation provides the complete specification for implementing the backend APIs needed to support the Prime Interviews frontend application.