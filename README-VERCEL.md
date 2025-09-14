# PRIME API - Vercel Deployment Guide

## Overview
This guide explains how to deploy the PRIME API to Vercel with the necessary modifications for serverless compatibility.

## Files Created for Vercel Deployment

### 1. `vercel.json`
Configuration file that tells Vercel how to build and route your application.

### 2. `api/index.py`
Serverless function entry point that creates a lightweight FastAPI app.

### 3. `requirements.txt` (Modified)
Streamlined dependencies compatible with Vercel's serverless environment.

### 4. `app/core/config_vercel.py`
Lightweight configuration without heavy database dependencies.

## Key Changes Made

### Removed Dependencies
- **Database**: `psycopg2-binary`, `sqlalchemy`, `alembic` (use external database services)
- **Task Queue**: `redis`, `celery` (use Vercel functions instead)
- **Heavy ML**: `opencv-python`, `numpy`, `pillow`, `sentence-transformers`, `chromadb`
- **Data Processing**: `pandas`, `openpyxl`, `scipy`, `scikit-learn`
- **WebSockets**: `websockets` (use Vercel's WebSocket support)

### Kept Dependencies
- Core FastAPI and authentication
- Lightweight AI services (OpenAI, Groq)
- Basic file processing
- HTTP clients and utilities

## Deployment Steps

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project root**:
   ```bash
   vercel
   ```

4. **Set Environment Variables** in Vercel dashboard:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `GROQ_API_KEY`
   - `RESEND_API_KEY`
   - `DATABASE_URL` (if using external database)

## Database Considerations

For production, consider using:
- **Supabase** (PostgreSQL with connection pooling)
- **PlanetScale** (MySQL with serverless driver)
- **Neon** (PostgreSQL serverless)
- **MongoDB Atlas** (NoSQL option)

## API Limitations in Serverless

- **Function Timeout**: 30 seconds max (configurable in vercel.json)
- **Memory**: Limited compared to traditional servers
- **Cold Starts**: First request may be slower
- **Stateless**: No persistent connections or background tasks

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Vercel dev server
vercel dev
```

## Production Considerations

1. **Database**: Use connection pooling services
2. **File Storage**: Use Vercel Blob or external storage (S3, Cloudinary)
3. **Background Tasks**: Use Vercel Cron Jobs or external services
4. **Monitoring**: Set up proper logging and error tracking
5. **Caching**: Use Vercel Edge Cache or external Redis

## Troubleshooting

- **Build Failures**: Check that all dependencies are compatible
- **Import Errors**: Ensure all required modules are in requirements.txt
- **Timeout Issues**: Optimize heavy operations or move to background jobs
- **Memory Issues**: Reduce dependency size or use external services
