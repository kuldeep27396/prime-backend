#!/usr/bin/env python3
"""
Script to create database tables using the migration
"""

import sys
import os
import subprocess

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))

def run_migration():
    """Run the Alembic migration to create tables"""
    try:
        print("🔄 Running database migration...")
        
        # Set environment variable for the database URL
        env = os.environ.copy()
        env['DATABASE_URL'] = 'postgresql://neondb_owner:npg_VT0ZA6FGyaMH@ep-proud-rain-aenatd39-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        
        # Run the migration using Python module execution
        result = subprocess.run([
            sys.executable, '-c',
            '''
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Set up the database URL
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_VT0ZA6FGyaMH@ep-proud-rain-aenatd39-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Import and run the migration
from alembic.config import Config
from alembic import command

# Create Alembic config
alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Run the migration
command.upgrade(alembic_cfg, "head")
print("✅ Database migration completed successfully!")
            '''
        ], cwd=os.path.dirname(__file__), env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database tables created successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    
    return True

def test_connection():
    """Test database connection"""
    try:
        print("🔄 Testing database connection...")
        
        from app.core.config import settings
        from sqlalchemy import create_engine, text
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up PRIME database...")
    
    # Test connection first
    if not test_connection():
        sys.exit(1)
    
    # Run migration
    if not run_migration():
        sys.exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("📋 Created tables:")
    print("  - companies")
    print("  - users") 
    print("  - jobs")
    print("  - candidates")
    print("  - applications")
    print("  - interview_templates")
    print("  - interviews")
    print("  - interview_responses")
    print("  - assessments")
    print("  - assessment_questions")
    print("  - assessment_responses")
    print("  - scores")
    print("  - audit_logs")
    print("  - proctoring_events")