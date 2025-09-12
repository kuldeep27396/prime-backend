# PRIME Backend

The backend service for PRIME - Predictive Recruitment & Interview Machine. This is a FastAPI-based backend that provides AI-powered recruitment platform APIs.

## 🚀 Features

- **AI-First Approach**: Real-time conversational AI interviewer using Groq's LLM APIs
- **RESTful APIs**: Complete recruitment pipeline APIs
- **Real-time Communication**: WebSocket support for live interviews
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: JWT-based authentication system
- **AI Services**: Groq API, Hugging Face, OpenAI integrations

## 🏗️ Tech Stack

- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Cache**: Redis for caching and task queue
- **AI Services**: Groq API, Hugging Face, OpenAI
- **Authentication**: JWT with passlib
- **Task Queue**: Celery with Redis

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Quick Start

1. **Clone and setup**:
```bash
git clone <repository-url>
cd prime-backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup database**:
```bash
alembic upgrade head
```

6. **Start the server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
docker build -t prime-backend .
docker run -p 8000:8000 --env-file .env prime-backend
```

## 📝 Environment Variables

```env
# Database
DATABASE_URL=postgresql://prime_user:prime_password@localhost:5432/prime_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# AI Services
GROQ_API_KEY=your-groq-api-key
HUGGING_FACE_API_KEY=your-hugging-face-api-key
OPENAI_API_KEY=your-openai-api-key

# File Storage
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token

# Email
RESEND_API_KEY=your-resend-api-key

# Video Services
DAILY_API_KEY=your-daily-api-key
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🚀 Deployment

### Railway

1. Connect repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

### Manual Deployment

```bash
# Build
docker build -t prime-backend .

# Deploy to your preferred platform
```

## 📦 Project Structure

```
prime-backend/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Core configurations
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tasks/           # Background tasks
│   └── main.py          # FastAPI application
├── alembic/             # Database migrations
├── tests/               # Test cases
├── requirements.txt     # Python dependencies
└── Dockerfile          # Container configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.