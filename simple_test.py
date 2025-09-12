#!/usr/bin/env python3
"""
Simple test app for Railway deployment verification
"""

from fastapi import FastAPI
import os

app = FastAPI(title="PRIME Test", version="1.0.0")

@app.get("/")
def read_root():
    return {
        "message": "PRIME Railway Test Successful!",
        "status": "working",
        "python_version": os.sys.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "prime-backend-test"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)