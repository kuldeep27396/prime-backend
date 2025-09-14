# PRIME API - FastAPI Backend

A minimal FastAPI backend optimized for Vercel deployment, ready for future API development.

## Features

- ✅ FastAPI with automatic OpenAPI documentation
- ✅ CORS middleware configured
- ✅ Vercel serverless deployment ready
- ✅ Health check endpoints
- ✅ Development and production configurations

## Project Structure

```
prime-backend/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app/
│   ├── __init__.py
│   └── main.py           # Local development FastAPI app
├── requirements.txt      # Minimal dependencies for Vercel
├── vercel.json          # Vercel deployment configuration
├── .env.example         # Environment variables template
└── README.md
```

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server**:
   ```bash
   python -m app.main
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Deployment to Vercel

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Set environment variables** in Vercel dashboard if needed:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `GROQ_API_KEY`

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /api/v1/status` - API status endpoint
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Adding New APIs

This is a minimal setup ready for expansion. To add new APIs:

1. Create new router files in `app/api/v1/`
2. Import and include routers in both `app/main.py` and `api/index.py`
3. Add any new dependencies to `requirements.txt`
4. Update environment variables in `.env.example`

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **python-dotenv**: Environment variable management

Minimal dependencies ensure fast builds and deployments on Vercel.
