-- Initial Schema Migration for Oprina API
-- Phase 1 Core Tables: Users, Sessions, Messages
-- 
-- This migration creates the foundational tables needed for:
-- - User management and authentication
-- - Session tracking and management  
-- - Chat message history
--
-- Run with: psql -d your_database -f migrations/001_initial_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL for OAuth-only users
    display_name VARCHAR(255),
    avatar_url TEXT,
    
    -- User preferences
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP,
    
    -- OAuth integration flags
    has_google_oauth BOOLEAN DEFAULT FALSE,
    has_microsoft_oauth BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    last_login_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session identification
    session_token VARCHAR(255) UNIQUE NOT NULL,
    session_name VARCHAR(255), -- User-friendly session name
    
    -- Session metadata
    title VARCHAR(500), -- Auto-generated or user-defined title
    description TEXT,
    context_data JSONB DEFAULT '{}', -- Session-specific context
    
    -- Agent configuration
    agent_type VARCHAR(100) DEFAULT 'default',
    agent_config JSONB DEFAULT '{}',
    
    -- Session statistics
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10,4) DEFAULT 0.0000,
    
    -- Session lifecycle
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT NOW(),
    
    -- Session status
    status VARCHAR(50) DEFAULT 'active', -- active, paused, ended, archived
    is_archived BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(50) NOT NULL, -- user, assistant, system, function
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, image, audio, file
    
    -- Message metadata
    message_index INTEGER NOT NULL, -- Order within session
    parent_message_id UUID REFERENCES messages(id), -- For threaded conversations
    
    -- Agent processing
    agent_response_data JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    
    -- Token usage
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10,4) DEFAULT 0.0000,
    
    -- Voice/Avatar integration
    has_voice_response BOOLEAN DEFAULT FALSE,
    voice_response_url TEXT,
    has_avatar_response BOOLEAN DEFAULT FALSE,
    avatar_session_id VARCHAR(255),
    
    -- Message status
    status VARCHAR(50) DEFAULT 'completed', -- pending, processing, completed, error
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure message order within session
    UNIQUE(session_id, message_index)
);

-- User authentication tokens table
CREATE TABLE user_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token details
    token_type VARCHAR(50) NOT NULL, -- refresh, reset_password, email_verify
    token_hash VARCHAR(255) NOT NULL,
    token_data JSONB DEFAULT '{}',
    
    -- Token lifecycle
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User activity log table
CREATE TABLE user_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity details
    activity_type VARCHAR(100) NOT NULL, -- login, logout, session_start, message_sent, etc.
    activity_data JSONB DEFAULT '{}',
    
    -- Context
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_activity ON sessions(last_activity_at);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_index ON messages(message_index);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);

CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);
CREATE INDEX idx_user_tokens_type ON user_tokens(token_type);
CREATE INDEX idx_user_tokens_expires ON user_tokens(expires_at);
CREATE INDEX idx_user_tokens_hash ON user_tokens(token_hash);

CREATE INDEX idx_user_activities_user_id ON user_activities(user_id);
CREATE INDEX idx_user_activities_type ON user_activities(activity_type);
CREATE INDEX idx_user_activities_session ON user_activities(session_id);
CREATE INDEX idx_user_activities_created_at ON user_activities(created_at);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at 
    BEFORE UPDATE ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_tokens_updated_at 
    BEFORE UPDATE ON user_tokens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update session statistics
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update message count and token usage for the session
    UPDATE sessions 
    SET 
        message_count = (
            SELECT COUNT(*) FROM messages 
            WHERE session_id = NEW.session_id
        ),
        total_tokens_used = (
            SELECT COALESCE(SUM(total_tokens), 0) FROM messages 
            WHERE session_id = NEW.session_id
        ),
        estimated_cost = (
            SELECT COALESCE(SUM(estimated_cost), 0) FROM messages 
            WHERE session_id = NEW.session_id
        ),
        last_activity_at = NOW()
    WHERE id = NEW.session_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update session stats when messages change
CREATE TRIGGER update_session_stats_on_message_insert
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION update_session_stats();

CREATE TRIGGER update_session_stats_on_message_update
    AFTER UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_session_stats();

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Log login activity
    IF TG_OP = 'UPDATE' AND OLD.last_login_at IS DISTINCT FROM NEW.last_login_at THEN
        INSERT INTO user_activities (user_id, activity_type, activity_data)
        VALUES (NEW.id, 'login', jsonb_build_object('login_time', NEW.last_login_at));
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-log user activities
CREATE TRIGGER log_user_login_activity
    AFTER UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- Initial admin user (development only)
-- Password: 'admin123' (hashed with bcrypt)
INSERT INTO users (
    email, 
    password_hash, 
    display_name, 
    is_active, 
    is_verified, 
    email_verified_at
) VALUES (
    'admin@oprina.dev',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewF5A0PWkz8eWru.',
    'Admin User',
    TRUE,
    TRUE,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Migration completion log
DO $$
BEGIN
    RAISE NOTICE 'Initial schema migration completed successfully!';
    RAISE NOTICE 'Created tables: users, sessions, messages, user_tokens, user_activities';
    RAISE NOTICE 'Created indexes and triggers for performance and data integrity';
    RAISE NOTICE 'Default admin user: admin@oprina.dev (password: admin123)';
END $$;
