#!/usr/bin/env python3
"""
Optimize requirements.txt for Railway deployment
Remove development and testing dependencies
"""

# Essential production dependencies only
PRODUCTION_DEPS = [
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0", 
    "sqlalchemy==2.0.23",
    "alembic==1.12.1",
    "psycopg2-binary==2.9.9",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.6",
    "httpx==0.25.2",
    "python-dotenv==1.0.0",
    "pydantic[email]==2.5.0",
    "pydantic-settings==2.1.0",
    "groq==0.4.1",
]

def create_minimal_requirements():
    """Create minimal requirements file for production"""
    with open("requirements-minimal.txt", "w") as f:
        f.write("# Minimal production requirements for Railway deployment\n")
        for dep in PRODUCTION_DEPS:
            f.write(f"{dep}\n")
    
    print("✅ Created requirements-minimal.txt")
    print(f"📦 Reduced from ~50 packages to {len(PRODUCTION_DEPS)} essential packages")
    print("🚀 This should significantly reduce the Docker image size")

if __name__ == "__main__":
    create_minimal_requirements()