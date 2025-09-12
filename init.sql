-- Database initialization script for PRIME
-- This script sets up the initial database structure

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    domain VARCHAR,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('admin', 'recruiter', 'interviewer')),
    profile JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    requirements JSONB DEFAULT '{}',
    status VARCHAR DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'closed')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    phone VARCHAR,
    resume_url VARCHAR,
    parsed_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_candidates_email ON candidates(email);

-- Create applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR DEFAULT 'applied' CHECK (status IN ('applied', 'screening', 'interviewing', 'assessed', 'hired', 'rejected')),
    cover_letter TEXT,
    application_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, candidate_id)
);

-- Create interview_templates table
CREATE TABLE IF NOT EXISTS interview_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('one_way', 'live_ai', 'technical')),
    questions JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
    template_id UUID REFERENCES interview_templates(id),
    type VARCHAR NOT NULL CHECK (type IN ('one_way', 'live_ai', 'technical')),
    status VARCHAR DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create interview_responses table
CREATE TABLE IF NOT EXISTS interview_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE NOT NULL,
    question_id VARCHAR NOT NULL,
    response_type VARCHAR NOT NULL CHECK (response_type IN ('video', 'audio', 'text', 'code')),
    content TEXT,
    media_url VARCHAR,
    duration INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create assessments table
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('coding', 'behavioral', 'cognitive')),
    questions JSONB DEFAULT '[]',
    responses JSONB DEFAULT '[]',
    auto_grade JSONB,
    manual_grade JSONB,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create assessment_questions table
CREATE TABLE IF NOT EXISTS assessment_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE NOT NULL,
    question_type VARCHAR NOT NULL CHECK (question_type IN ('coding', 'multiple_choice', 'whiteboard', 'essay')),
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    test_cases JSONB DEFAULT '[]',
    expected_answer TEXT,
    time_limit INTEGER,
    difficulty VARCHAR DEFAULT 'medium',
    points INTEGER DEFAULT 10,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create assessment_responses table
CREATE TABLE IF NOT EXISTS assessment_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE NOT NULL,
    question_id UUID REFERENCES assessment_questions(id) ON DELETE CASCADE NOT NULL,
    response_content TEXT,
    media_url VARCHAR,
    execution_result JSONB,
    time_taken INTEGER,
    auto_score DECIMAL(5,2),
    manual_score DECIMAL(5,2),
    feedback TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create scores table
CREATE TABLE IF NOT EXISTS scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
    category VARCHAR NOT NULL CHECK (category IN ('technical', 'communication', 'cultural_fit', 'cognitive', 'behavioral')),
    score DECIMAL(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    confidence DECIMAL(5,2) CHECK (confidence >= 0 AND confidence <= 100),
    reasoning TEXT,
    evidence JSONB DEFAULT '[]',
    created_by VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id VARCHAR,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create proctoring_events table
CREATE TABLE IF NOT EXISTS proctoring_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE NOT NULL,
    event_type VARCHAR NOT NULL CHECK (event_type IN ('face_detection', 'voice_analysis', 'suspicious_activity', 'browser_focus_lost')),
    severity VARCHAR NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Success message
SELECT 'Database initialization completed successfully!' as status;