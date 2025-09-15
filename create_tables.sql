-- Prime Interviews Database Schema
-- Run this SQL script in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_image TEXT,
    role VARCHAR(50) DEFAULT 'candidate',
    experience VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Mentors table
CREATE TABLE IF NOT EXISTS mentors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    current_company VARCHAR(255),
    previous_companies JSONB,
    avatar TEXT,
    bio TEXT,
    specialties JSONB,
    skills JSONB,
    languages JSONB,
    experience INTEGER,
    rating DECIMAL(3,2) DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    hourly_rate DECIMAL(8,2),
    response_time VARCHAR(50),
    timezone VARCHAR(100),
    availability JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for mentors
CREATE INDEX IF NOT EXISTS idx_mentors_user_id ON mentors(user_id);
CREATE INDEX IF NOT EXISTS idx_mentors_name ON mentors(name);
CREATE INDEX IF NOT EXISTS idx_mentors_company ON mentors(current_company);
CREATE INDEX IF NOT EXISTS idx_mentors_experience ON mentors(experience);
CREATE INDEX IF NOT EXISTS idx_mentors_rating ON mentors(rating);
CREATE INDEX IF NOT EXISTS idx_mentors_active ON mentors(is_active);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mentor_id UUID REFERENCES mentors(id) ON DELETE CASCADE,
    session_type VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration INTEGER NOT NULL,
    meeting_type VARCHAR(50),
    meeting_link TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    record_session BOOLEAN DEFAULT false,
    special_requests TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    cancellation_reason TEXT,
    recording_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_mentor_id ON sessions(mentor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_scheduled_at ON sessions(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    recent_searches JSONB,
    favorite_topics JSONB,
    favorite_mentors JSONB,
    timezone VARCHAR(100),
    notification_settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for user preferences
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Skill assessments table
CREATE TABLE IF NOT EXISTS skill_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    skill VARCHAR(255) NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL
);

-- Create indexes for skill assessments
CREATE INDEX IF NOT EXISTS idx_skill_assessments_user_id ON skill_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_skill ON skill_assessments(skill);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    mentor_id UUID REFERENCES mentors(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    comment TEXT,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for reviews
CREATE INDEX IF NOT EXISTS idx_reviews_session_id ON reviews(session_id);
CREATE INDEX IF NOT EXISTS idx_reviews_mentor_id ON reviews(mentor_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_public ON reviews(is_public);

-- Video rooms table
CREATE TABLE IF NOT EXISTS video_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    room_url TEXT NOT NULL,
    participant_token TEXT,
    mentor_token TEXT,
    status VARCHAR(50) DEFAULT 'active',
    recording_url TEXT,
    actual_duration INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for video rooms
CREATE INDEX IF NOT EXISTS idx_video_rooms_room_id ON video_rooms(room_id);
CREATE INDEX IF NOT EXISTS idx_video_rooms_session_id ON video_rooms(session_id);
CREATE INDEX IF NOT EXISTS idx_video_rooms_status ON video_rooms(status);

-- Insert sample data
INSERT INTO users (user_id, email, first_name, last_name, role) VALUES
('mentor_001', 'mentor1@example.com', 'Sarah', 'Johnson', 'mentor'),
('mentor_002', 'mentor2@example.com', 'Mike', 'Chen', 'mentor'),
('user_001', 'user1@example.com', 'John', 'Doe', 'candidate')
ON CONFLICT (user_id) DO NOTHING;

-- Insert sample mentors
INSERT INTO mentors (user_id, name, title, current_company, previous_companies, bio, specialties, skills, languages, experience, rating, review_count, hourly_rate, response_time, timezone, availability, is_active)
SELECT
    u.id,
    'Sarah Johnson',
    'Senior Software Engineer',
    'Google',
    '["Facebook", "Apple"]'::jsonb,
    'Experienced software engineer with 8+ years in tech, specializing in system design and scalable architectures.',
    '["System Design", "Algorithm Interviews", "Technical Leadership"]'::jsonb,
    '["Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes"]'::jsonb,
    '["English", "Spanish"]'::jsonb,
    8,
    4.8,
    142,
    150.00,
    'Within 2 hours',
    'America/New_York',
    '["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17", "Thursday 9-17", "Friday 9-17"]'::jsonb,
    true
FROM users u WHERE u.user_id = 'mentor_001'
ON CONFLICT DO NOTHING;

INSERT INTO mentors (user_id, name, title, current_company, previous_companies, bio, specialties, skills, languages, experience, rating, review_count, hourly_rate, response_time, timezone, availability, is_active)
SELECT
    u.id,
    'Mike Chen',
    'Staff Software Engineer',
    'Meta',
    '["Netflix", "Uber", "Airbnb"]'::jsonb,
    'Full-stack developer with expertise in building scalable web applications and distributed systems.',
    '["Full-Stack Development", "System Architecture", "Performance Optimization"]'::jsonb,
    '["TypeScript", "Node.js", "React", "PostgreSQL", "Redis", "GraphQL"]'::jsonb,
    '["English", "Mandarin"]'::jsonb,
    10,
    4.9,
    98,
    175.00,
    'Within 1 hour',
    'America/Los_Angeles',
    '["Monday 10-18", "Wednesday 10-18", "Friday 10-18", "Saturday 9-15"]'::jsonb,
    true
FROM users u WHERE u.user_id = 'mentor_002'
ON CONFLICT DO NOTHING;

-- Insert sample user preferences
INSERT INTO user_preferences (user_id, recent_searches, favorite_topics, timezone, notification_settings)
SELECT
    u.id,
    '["React", "System Design", "Python"]'::jsonb,
    '["Web Development", "Machine Learning", "Data Structures"]'::jsonb,
    'America/New_York',
    '{"email": true, "sms": false, "push": true}'::jsonb
FROM users u WHERE u.user_id = 'user_001'
ON CONFLICT (user_id) DO NOTHING;

-- Insert sample skill assessments
INSERT INTO skill_assessments (user_id, skill, score, assessed_at)
SELECT
    u.id,
    skill,
    score,
    CURRENT_TIMESTAMP
FROM users u,
(VALUES
    ('Python', 85),
    ('JavaScript', 78),
    ('React', 82),
    ('System Design', 75)
) AS skills(skill, score)
WHERE u.user_id = 'user_001';

COMMENT ON TABLE users IS 'User profiles and authentication data';
COMMENT ON TABLE mentors IS 'Mentor profiles and availability information';
COMMENT ON TABLE sessions IS 'Interview session bookings and details';
COMMENT ON TABLE user_preferences IS 'User settings and preferences';
COMMENT ON TABLE skill_assessments IS 'Skill evaluation records';
COMMENT ON TABLE reviews IS 'Session reviews and ratings';
COMMENT ON TABLE video_rooms IS 'Video call room management';