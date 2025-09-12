"""
Application configuration settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_VT0ZA6FGyaMH@ep-proud-rain-aenatd39-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    
    # Railway deployment
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # File Storage - Vercel Blob
    BLOB_READ_WRITE_TOKEN: Optional[str] = os.getenv("BLOB_READ_WRITE_TOKEN")
    
    # AI Services
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    CEREBRAS_API_KEY: Optional[str] = os.getenv("CEREBRAS_API_KEY", "csk-65tnt9v4dkc9c53fwmvweftej6rjr8ck4tcj5mct9pehdjtwimport")
    HUGGING_FACE_API_KEY: Optional[str] = os.getenv("HUGGING_FACE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Email
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    FROM_EMAIL: str = "noreply@prime-recruitment.com"
    
    # Video Services
    DAILY_API_KEY: Optional[str] = os.getenv("DAILY_API_KEY")
    
    # API Base URL
    API_BASE_URL: Optional[str] = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()