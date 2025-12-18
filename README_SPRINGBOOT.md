# Prime Interviews API - Spring Boot Backend

A comprehensive Spring Boot backend service for interview scheduling and management, converted from Python/FastAPI.

## Features

- ✅ Spring Boot 3.2.1 with Java 17
- ✅ PostgreSQL database with Spring Data JPA
- ✅ RESTful API with OpenAPI/Swagger documentation
- ✅ Clerk.js authentication integration
- ✅ CORS middleware configured
- ✅ Comprehensive exception handling
- ✅ Email notifications via Brevo API
- ✅ Entity auditing with created/updated timestamps

## Tech Stack

- **Framework**: Spring Boot 3.2.1
- **Language**: Java 17
- **Database**: PostgreSQL
- **ORM**: Spring Data JPA / Hibernate
- **Security**: Spring Security with JWT (Clerk)
- **Documentation**: SpringDoc OpenAPI 3.0
- **Email**: Brevo (Sendinblue) API
- **Build Tool**: Maven

## Project Structure

```
prime-backend/
├── src/
│   ├── main/
│   │   ├── java/com/primeinterviews/backend/
│   │   │   ├── config/          # Configuration classes
│   │   │   ├── controller/      # REST controllers
│   │   │   ├── dto/             # Data Transfer Objects
│   │   │   ├── entity/          # JPA entities
│   │   │   ├── exception/       # Custom exceptions
│   │   │   ├── repository/      # Spring Data repositories
│   │   │   ├── security/        # Security configuration
│   │   │   ├── service/         # Business logic services
│   │   │   └── PrimeInterviewsApplication.java
│   │   └── resources/
│   │       ├── application.yml  # Main configuration
│   │       └── application-dev.yml  # Development config
│   └── test/
│       └── java/                # Test classes
├── pom.xml                      # Maven dependencies
└── README_SPRINGBOOT.md
```

## Prerequisites

- Java 17 or higher
- Maven 3.6+
- PostgreSQL 12+
- (Optional) Docker for containerized deployment

## Environment Variables

Create a `.env` file or set the following environment variables:

```properties
# Database Configuration
DATABASE_URL=jdbc:postgresql://localhost:5432/primeinterviews
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# Application Configuration
ENVIRONMENT=development
PORT=8080

# Security
SECRET_KEY=your-secret-key-change-in-production

# Clerk Authentication
CLERK_API_KEY=your_clerk_api_key
CLERK_JWT_ISSUER=https://your-clerk-domain.clerk.accounts.dev

# Brevo Email Service
BREVO_API_KEY=your_brevo_api_key
SMTP_FROM_EMAIL=noreply@primeinterviews.com
SMTP_FROM_NAME=Prime Interviews

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# External APIs (optional)
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
```

## Getting Started

### 1. Clone and setup

```bash
cd prime-backend
```

### 2. Configure Database

Create a PostgreSQL database:

```bash
createdb primeinterviews
```

Update `application.yml` or set environment variables for database connection.

### 3. Build the project

```bash
mvn clean install
```

### 4. Run the application

**Development mode (with hot reload)**:
```bash
mvn spring-boot:run
```

**Production mode**:
```bash
java -jar target/prime-backend-2.0.0.jar
```

### 5. Access the application

- **API**: http://localhost:8080
- **Swagger UI**: http://localhost:8080/docs
- **API Docs**: http://localhost:8080/api-docs
- **Health Check**: http://localhost:8080/health

## API Endpoints

### Health & Info
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Users
- `POST /api/users` - Create a new user
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Mentors
- `GET /api/mentors` - List all active mentors
- `GET /api/mentors/{id}` - Get mentor by ID
- `GET /api/mentors/search` - Search mentors by criteria

### Sessions
- `POST /api/sessions` - Book a new session
- `GET /api/sessions/{id}` - Get session details
- `PUT /api/sessions/{id}` - Update session
- `GET /api/users/{userId}/sessions` - Get user's sessions

### Video Rooms
- `POST /api/video/rooms` - Create a video room
- `GET /api/video/rooms/{roomId}` - Get room details
- `POST /api/video/rooms/{roomId}/end` - End a video room

### Analytics
- `GET /api/analytics/dashboard` - Get user analytics dashboard
- `GET /api/analytics/skills` - Get skill progression data

## Database Schema

The application uses 23+ entity tables:

- **Core**: User, Mentor, Session, VideoRoom
- **Preferences**: UserPreference, UserProfile
- **Assessments**: SkillAssessment, Review, SkillProgression
- **Analytics**: UserAnalytics, SessionAnalytics
- **Content**: LearningResource, InterviewQuestion, InterviewTemplate
- **Company**: Company, JobPosting, CompanyMentor
- **Communication**: Notification, EmailTemplate
- **Misc**: RoomParticipant, UserProgress, UserResponse

All tables include audit fields (`created_at`, `updated_at`) and appropriate indexes.

## Authentication

The API uses Clerk for authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_clerk_jwt_token>
```

## Development

### Running Tests

```bash
mvn test
```

### Code Formatting

The project uses standard Java formatting. Configure your IDE accordingly.

### Building for Production

```bash
mvn clean package -DskipTests
```

This creates an executable JAR in `target/prime-backend-2.0.0.jar`

## Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM openjdk:17-jdk-slim
WORKDIR /app
COPY target/prime-backend-2.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Build and run:

```bash
docker build -t prime-backend .
docker run -p 8080:8080 --env-file .env prime-backend
```

## Migration Notes

This application was converted from Python/FastAPI to Java/Spring Boot. Key changes:

1. **Framework**: FastAPI → Spring Boot
2. **ORM**: SQLAlchemy → Spring Data JPA
3. **Validation**: Pydantic → Jakarta Bean Validation
4. **Type System**: Python type hints → Java generics & types
5. **Async**: Python async/await → Spring's reactive support (where needed)
6. **Package Management**: pip/requirements.txt → Maven/pom.xml

## License

MIT License

## Support

For issues and questions, contact support@prime-interviews.com
