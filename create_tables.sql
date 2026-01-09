-- Prime Interviews Database Schema v3.0
-- B2B Candidate Screening + AI Mock Interviews
-- Run this SQL script in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- ENUM TYPES
-- ==========================================

DO $$ BEGIN
    CREATE TYPE plan_type AS ENUM ('free', 'starter', 'growth', 'enterprise', 'pay_per_use');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE candidate_status AS ENUM ('applied', 'invited', 'interview_scheduled', 'interview_completed', 'shortlisted', 'rejected', 'hired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE interview_status AS ENUM ('pending', 'in_progress', 'completed', 'expired', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE interview_type AS ENUM ('screening', 'mock');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ==========================================
-- COMPANIES TABLE (B2B Clients)
-- ==========================================

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    logo_url TEXT,
    website TEXT,
    industry VARCHAR(255),
    company_size VARCHAR(50),
    description TEXT,
    headquarters VARCHAR(255),
    
    -- Billing & Plan
    plan_type VARCHAR(50) DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 2,
    credits_used INTEGER DEFAULT 0,
    billing_email VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    
    is_active BOOLEAN DEFAULT true,
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);
CREATE INDEX IF NOT EXISTS idx_companies_plan ON companies(plan_type);
CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(is_active);

-- ==========================================
-- USERS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_image TEXT,
    role VARCHAR(50) DEFAULT 'user',
    experience VARCHAR(100),
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);

-- ==========================================
-- USER PREFERENCES TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    recent_searches JSONB,
    favorite_topics JSONB,
    preferred_difficulty VARCHAR(50) DEFAULT 'medium',
    timezone VARCHAR(100),
    notification_settings JSONB,
    mock_history_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- ==========================================
-- JOBS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Job Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    requirements JSONB,
    skills_required JSONB,
    experience_min INTEGER DEFAULT 0,
    experience_max INTEGER DEFAULT 20,
    location VARCHAR(255),
    job_type VARCHAR(50),
    department VARCHAR(255),
    salary_min DECIMAL(10, 2),
    salary_max DECIMAL(10, 2),
    
    -- AI Interview Configuration
    ai_questions JSONB,
    question_count INTEGER DEFAULT 5,
    interview_duration INTEGER DEFAULT 15,
    difficulty_level VARCHAR(50) DEFAULT 'medium',
    passing_score INTEGER DEFAULT 60,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    is_public BOOLEAN DEFAULT true,
    application_deadline TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);

-- ==========================================
-- CANDIDATES TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Candidate Info
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    linkedin_url TEXT,
    
    -- Resume
    resume_url TEXT,
    resume_text TEXT,
    resume_parsed JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'applied',
    
    -- AI Evaluation
    ai_score INTEGER CHECK (ai_score >= 0 AND ai_score <= 100),
    ai_summary TEXT,
    ai_strengths JSONB,
    ai_weaknesses JSONB,
    ai_recommendation VARCHAR(50),
    shortlisted BOOLEAN DEFAULT false,
    shortlist_reason TEXT,
    
    -- Interview
    interview_token VARCHAR(255) UNIQUE,
    interview_link TEXT,
    interview_sent_at TIMESTAMP WITH TIME ZONE,
    interview_expires_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_job ON candidates(job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_shortlisted ON candidates(shortlisted);
CREATE INDEX IF NOT EXISTS idx_candidates_token ON candidates(interview_token);

-- ==========================================
-- AI INTERVIEW SESSIONS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS ai_interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Owner
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    
    -- Type
    interview_type VARCHAR(50) NOT NULL,
    mock_category VARCHAR(50),
    topic VARCHAR(255),
    difficulty VARCHAR(50) DEFAULT 'medium',
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    actual_duration_seconds INTEGER,
    
    -- Q&A
    questions JSONB,
    answers JSONB,
    
    -- AI Evaluation
    ai_evaluation JSONB,
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score INTEGER,
    communication_score INTEGER,
    problem_solving_score INTEGER,
    ai_feedback TEXT,
    
    -- Recording (TODO)
    recording_url TEXT,
    recording_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    browser_info JSONB,
    ip_address VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_sessions_candidate ON ai_interview_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_user ON ai_interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_type ON ai_interview_sessions(interview_type);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_status ON ai_interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_category ON ai_interview_sessions(mock_category);

-- ==========================================
-- INTERVIEW QUESTIONS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    question TEXT NOT NULL,
    question_type VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    difficulty VARCHAR(50),
    
    expected_answer TEXT,
    evaluation_criteria JSONB,
    keywords JSONB,
    follow_up_questions JSONB,
    
    skills_tested JSONB,
    companies_asked_at JSONB,
    time_limit_seconds INTEGER DEFAULT 180,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_type ON interview_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_questions_category ON interview_questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON interview_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_active ON interview_questions(is_active);

-- ==========================================
-- MOCK INTERVIEW CATEGORIES TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS mock_interview_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(50),
    
    topics JSONB,
    difficulty_levels JSONB DEFAULT '["easy", "medium", "hard"]',
    
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_premium BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mock_categories_name ON mock_interview_categories(name);
CREATE INDEX IF NOT EXISTS idx_mock_categories_active ON mock_interview_categories(is_active);

-- ==========================================
-- USER MOCK PROGRESS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS user_mock_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    category VARCHAR(100) NOT NULL,
    topic VARCHAR(255),
    
    total_attempts INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    average_score DECIMAL(5, 2) DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    last_score INTEGER,
    
    total_time_spent_seconds INTEGER DEFAULT 0,
    
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mock_progress_user ON user_mock_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_progress_category ON user_mock_progress(category);

-- ==========================================
-- SKILL ASSESSMENTS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS skill_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill VARCHAR(255) NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 100) NOT NULL,
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    interview_session_id UUID REFERENCES ai_interview_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_assessments_user ON skill_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_skill ON skill_assessments(skill);

-- ==========================================
-- NOTIFICATIONS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    is_read BOOLEAN DEFAULT false,
    is_email_sent BOOLEAN DEFAULT false,
    
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_company ON notifications(company_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);

-- ==========================================
-- EMAIL LOGS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    to_email VARCHAR(255) NOT NULL,
    to_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    email_type VARCHAR(100),
    
    candidate_id UUID REFERENCES candidates(id) ON DELETE SET NULL,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    
    status VARCHAR(50) DEFAULT 'sent',
    provider_message_id VARCHAR(255),
    
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_email_logs_to ON email_logs(to_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

-- ==========================================
-- COMPANY ANALYTICS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS company_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID UNIQUE NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    total_jobs_posted INTEGER DEFAULT 0,
    total_candidates INTEGER DEFAULT 0,
    total_interviews_conducted INTEGER DEFAULT 0,
    total_shortlisted INTEGER DEFAULT 0,
    total_hired INTEGER DEFAULT 0,
    
    average_candidate_score DECIMAL(5, 2) DEFAULT 0,
    average_time_to_shortlist_hours DECIMAL(10, 2) DEFAULT 0,
    
    monthly_stats JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_analytics_company ON company_analytics(company_id);

-- ==========================================
-- USER ANALYTICS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS user_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    total_mock_sessions INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    average_score DECIMAL(5, 2) DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    
    category_stats JSONB,
    skills_improved JSONB,
    weak_areas JSONB,
    
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_analytics_user ON user_analytics(user_id);

-- ==========================================
-- SEED DATA: Mock Interview Categories
-- ==========================================

INSERT INTO mock_interview_categories (name, display_name, description, icon, color, topics, order_index) VALUES
('dsa', 'Data Structures & Algorithms', 'Practice coding problems on arrays, trees, graphs, dynamic programming, and more.', 'code', 'blue', 
 '[{"name": "Arrays & Strings", "question_count": 50}, {"name": "Linked Lists", "question_count": 30}, {"name": "Trees & Graphs", "question_count": 45}, {"name": "Dynamic Programming", "question_count": 40}, {"name": "Sorting & Searching", "question_count": 25}]', 
 1),
('system_design', 'System Design', 'Learn to design scalable systems like URL shorteners, chat apps, and social networks.', 'server', 'purple',
 '[{"name": "URL Shortener", "question_count": 10}, {"name": "Chat System", "question_count": 10}, {"name": "Social Media Feed", "question_count": 8}, {"name": "E-commerce", "question_count": 12}, {"name": "Video Streaming", "question_count": 8}]',
 2),
('behavioral', 'Behavioral Interview', 'Prepare for questions about leadership, teamwork, and problem-solving experiences.', 'users', 'green',
 '[{"name": "Leadership", "question_count": 20}, {"name": "Teamwork", "question_count": 25}, {"name": "Conflict Resolution", "question_count": 15}, {"name": "Problem Solving", "question_count": 20}, {"name": "Career Goals", "question_count": 10}]',
 3),
('frontend', 'Frontend Development', 'Test your knowledge of HTML, CSS, JavaScript, React, and modern frontend practices.', 'layout', 'orange',
 '[{"name": "JavaScript Core", "question_count": 40}, {"name": "React", "question_count": 35}, {"name": "CSS & Layouts", "question_count": 25}, {"name": "Performance", "question_count": 15}, {"name": "TypeScript", "question_count": 20}]',
 4),
('backend', 'Backend Development', 'Practice API design, database queries, authentication, and server architecture.', 'database', 'red',
 '[{"name": "API Design", "question_count": 30}, {"name": "Databases", "question_count": 35}, {"name": "Authentication", "question_count": 20}, {"name": "Caching", "question_count": 15}, {"name": "Microservices", "question_count": 20}]',
 5),
('devops', 'DevOps & Cloud', 'Questions on CI/CD, Docker, Kubernetes, AWS, and infrastructure as code.', 'cloud', 'cyan',
 '[{"name": "Docker & Containers", "question_count": 25}, {"name": "Kubernetes", "question_count": 20}, {"name": "CI/CD", "question_count": 20}, {"name": "AWS", "question_count": 30}, {"name": "Terraform", "question_count": 15}]',
 6),
('data_science', 'Data Science', 'Practice ML concepts, statistics, and data analysis questions.', 'bar-chart', 'pink',
 '[{"name": "Machine Learning", "question_count": 35}, {"name": "Statistics", "question_count": 25}, {"name": "Python for Data", "question_count": 30}, {"name": "SQL for Analytics", "question_count": 20}, {"name": "Deep Learning", "question_count": 20}]',
 7)
ON CONFLICT (name) DO NOTHING;

-- ==========================================
-- SAMPLE DATA: Interview Questions
-- ==========================================

INSERT INTO interview_questions (question, question_type, category, difficulty, expected_answer, skills_tested, time_limit_seconds) VALUES
('Tell me about yourself and your experience.', 'behavioral', 'behavioral', 'easy', 
 'Candidate should provide a concise 2-3 minute summary of their professional background, key achievements, and why they are interested in this role.',
 '["communication", "self-awareness"]', 180),
 
('What is the difference between let, const, and var in JavaScript?', 'technical', 'frontend', 'easy',
 'var is function-scoped and hoisted, let is block-scoped and not hoisted, const is block-scoped, not hoisted, and cannot be reassigned.',
 '["javascript", "scope"]', 120),

('Design a URL shortening service like bit.ly.', 'technical', 'system_design', 'medium',
 'Should discuss: unique ID generation (base62 encoding), database schema, read/write ratio optimization, caching, scaling considerations.',
 '["system design", "scalability", "databases"]', 600),

('What is the time complexity of binary search?', 'technical', 'dsa', 'easy',
 'O(log n) - each comparison eliminates half of the remaining elements.',
 '["algorithms", "time complexity"]', 60),

('Describe a situation where you had to deal with a difficult team member.', 'behavioral', 'behavioral', 'medium',
 'Candidate should use STAR method: describe Situation, Task, Action taken, and Result. Should show empathy and problem-solving.',
 '["teamwork", "conflict resolution", "communication"]', 180),

('Explain the concept of closures in JavaScript.', 'technical', 'frontend', 'medium',
 'A closure is a function that has access to variables in its outer (enclosing) lexical scope, even after the outer function has returned.',
 '["javascript", "closures", "scope"]', 180),

('What is the difference between SQL and NoSQL databases?', 'technical', 'backend', 'easy',
 'SQL: relational, structured schema, ACID compliance. NoSQL: non-relational, flexible schema, horizontal scaling, eventual consistency.',
 '["databases", "sql", "nosql"]', 180),

('How would you optimize a slow API endpoint?', 'technical', 'backend', 'medium',
 'Profiling to find bottlenecks, database query optimization, caching, pagination, async processing, CDN for static content.',
 '["performance", "optimization", "api design"]', 300)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE companies IS 'B2B client companies using the screening platform';
COMMENT ON TABLE users IS 'Platform users - both mock practice users and company admins';
COMMENT ON TABLE jobs IS 'Job postings created by companies for candidate screening';
COMMENT ON TABLE candidates IS 'Candidates who apply to jobs and go through AI screening';
COMMENT ON TABLE ai_interview_sessions IS 'AI interview sessions for both B2B screening and mock practice';
COMMENT ON TABLE mock_interview_categories IS 'Categories for mock interview practice (DSA, System Design, etc.)';