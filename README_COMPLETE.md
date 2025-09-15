# Prime Interviews - Backend API

## Overview
This is a comprehensive FastAPI backend for the Prime Interviews platform - a complete interview scheduling and management system with Clerk authentication, mentor discovery, session booking, video call integration, and analytics.

## Features

### 🔐 Authentication & Authorization
- **Clerk.js Integration**: Secure JWT-based authentication
- **Role-Based Access**: Support for candidates, mentors, and admins
- **Protected Endpoints**: All user operations require authentication

### 👥 User Management
- **Profile Management**: Create and update user profiles
- **Session History**: Track interview history and progress
- **Skill Assessments**: Store and retrieve skill evaluation data
- **User Analytics**: Comprehensive dashboard analytics

### 🎯 Mentor Discovery
- **Advanced Search**: Filter mentors by skills, companies, experience, price, and rating
- **Pagination**: Efficient paginated results
- **Detailed Profiles**: Complete mentor information with reviews
- **Availability Tracking**: Real-time availability status

### 📅 Session Management
- **Booking System**: Schedule interview sessions with mentors
- **Status Tracking**: Manage session lifecycle (pending → confirmed → completed)
- **Feedback System**: Rating and feedback collection
- **Cancellation Support**: Handle session cancellations with reasons

### 📹 Video Integration
- **Room Creation**: Generate video call rooms for sessions
- **Token Management**: Secure participant and mentor tokens
- **Status Monitoring**: Track room status and participants

### 📧 Email Notifications
- **SMTP Integration**: Automated email notifications
- **Booking Confirmations**: Email confirmations for session bookings
- **Customizable Templates**: HTML email templates

### 📊 Analytics & Reporting
- **Dashboard Data**: User statistics and progress tracking
- **Session Analytics**: Comprehensive session metrics
- **Activity Logging**: Recent activity tracking

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Virtual environment (recommended)

### Quick Setup

1. **Clone and Setup Environment**:
```bash
git clone <repository-url>
cd prime-backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**:
```bash
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)
```

3. **Database Setup**:
```bash
# Run the setup script to create tables and seed sample data
python setup.py
```

4. **Start Development Server**:
```bash
python -m app.main
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

Create a `.env` file with the following configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/prime_interviews

# Authentication (Clerk)
CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_key
CLERK_SECRET_KEY=sk_test_your_clerk_secret

# Email Service (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Prime Interviews
SMTP_SECURE=true

# Video Service (HMS - Optional)
HMS_APP_ID=your_hms_app_id
HMS_APP_SECRET=your_hms_app_secret

# API Configuration
PORT=8000
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Security
JWT_SECRET=your_jwt_secret_key
```

## API Endpoints

### 🏥 Health & Status
- `GET /` - Root endpoint with API information
- `GET /health` - Health check with service status

### 👤 User Management
- `POST /api/users` - Create or update user profile
- `GET /api/users/{user_id}` - Get user profile and history
- `GET /api/users/{user_id}/analytics` - Get user dashboard analytics

### 🎯 Mentor Management
- `GET /api/mentors` - Get paginated mentors with filtering
- `GET /api/mentors/{mentor_id}` - Get detailed mentor profile

### 📅 Session Management
- `POST /api/sessions` - Create new interview session
- `GET /api/sessions` - Get user's sessions (with filtering)
- `PATCH /api/sessions/{session_id}` - Update session status/feedback

### 📹 Video Integration
- `POST /api/rooms` - Create video call room
- `GET /api/rooms/{room_id}/status` - Get room status and participants

### 📧 Email Service
- `POST /api/send-email` - Send transactional emails

## Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User profiles and authentication data
- **mentors**: Mentor profiles and availability
- **sessions**: Interview session bookings
- **user_preferences**: User settings and preferences
- **skill_assessments**: Skill evaluation records
- **reviews**: Session reviews and ratings
- **video_rooms**: Video call room management

## Authentication

The API uses Clerk.js for authentication. Include your Clerk JWT token in the Authorization header:

```
Authorization: Bearer <your_clerk_jwt_token>
```

### JWT Payload Structure
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "image_url": "https://...",
  "iat": 1640995200,
  "exp": 1641081600
}
```

## Error Handling

The API uses standardized error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "validation_error_field",
      "value": "invalid_value"
    }
  }
}
```

Common error codes:
- `UNAUTHORIZED`: Missing or invalid authentication
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., time slot already booked)
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server internal error

## Development

### Project Structure
```
prime-backend/
├── api/
│   └── index.py              # Legacy endpoint (compatibility)
├── app/
│   ├── main.py              # Main FastAPI application
│   ├── auth/
│   │   └── clerk_auth.py    # Clerk authentication
│   ├── database/
│   │   ├── __init__.py      # Database exports
│   │   ├── database.py      # Database connection
│   │   ├── models.py        # SQLAlchemy models
│   │   └── migrations.py    # Database migrations
│   ├── routers/
│   │   ├── users.py         # User management endpoints
│   │   ├── mentors.py       # Mentor discovery endpoints
│   │   └── sessions.py      # Session booking endpoints
│   ├── schemas/
│   │   ├── common.py        # Common response schemas
│   │   ├── user.py          # User-related schemas
│   │   ├── mentor.py        # Mentor-related schemas
│   │   └── session.py       # Session-related schemas
│   └── email_service.py     # Email service implementation
├── setup.py                 # Database setup and seeding script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md              # This file
```

### Running in Development
```bash
# With auto-reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Operations
```bash
# Create tables and seed sample data
python setup.py

# Run migrations (when using Alembic)
alembic upgrade head
```

### Testing
```bash
# Run tests (implement with pytest)
pytest tests/

# Test specific endpoint
curl -X GET http://localhost:8000/health
```

## Deployment

### Vercel Deployment
The project is configured for Vercel deployment:

```bash
vercel deploy
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "app.main"]
```

### Environment Setup for Production
- Use environment-specific `.env` files
- Set up proper database connections
- Configure email service credentials
- Set up monitoring and logging

## Rate Limiting

API endpoints have rate limits:
- **General API**: 100 requests per minute per user
- **Email API**: 10 requests per minute per user
- **Search API**: 30 requests per minute per user

## Monitoring & Logging

The API includes:
- Health check endpoints for monitoring
- Structured error responses
- Request/response logging
- Database connection health checks

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test thoroughly
4. Commit with descriptive messages
5. Push to your fork and create a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Write comprehensive docstrings
- Add tests for new features

## Security

- All endpoints use HTTPS in production
- JWT tokens for authentication
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for allowed origins only

## License

MIT License - see LICENSE file for details

## Support

For questions or issues:
- Create an issue in this repository
- Email: support@prime-interviews.com
- Documentation: Visit /docs endpoint when running