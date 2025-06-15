-- =====================================================================
-- Migration: 02_create_sessions_table.sql
-- Description: Create sessions table for chat session management
-- Date: 2025-06-15
-- =====================================================================

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User Relationship
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Vertex AI Integration
    vertex_session_id TEXT, -- Links to Google Cloud Vertex AI session
    
    -- Session Management
    status VARCHAR(50) DEFAULT 'active' NOT NULL, -- active, ended, deleted
    title VARCHAR(500) DEFAULT 'New Chat', -- For UI display in sidebar
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CHECK (status IN ('active', 'ended', 'deleted'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_vertex_id ON sessions(vertex_session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);

-- Create trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION update_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_sessions_updated_at();

-- Add comments for documentation
COMMENT ON TABLE sessions IS 'Chat sessions between users and AI agent';
COMMENT ON COLUMN sessions.user_id IS 'Reference to user who owns this session';
COMMENT ON COLUMN sessions.vertex_session_id IS 'Google Cloud Vertex AI session identifier';
COMMENT ON COLUMN sessions.status IS 'Session lifecycle status (active, ended, deleted)';
COMMENT ON COLUMN sessions.title IS 'Display title for session in UI sidebar';
COMMENT ON COLUMN sessions.last_activity_at IS 'Timestamp of last message in session';

-- Insert example data for testing (optional - remove in production)
INSERT INTO sessions (
    user_id,
    title,
    status
) SELECT 
    id,
    'Welcome Chat - Voice Enabled',
    'active'
FROM users 
WHERE email = 'demo@oprina.ai'
ON CONFLICT DO NOTHING;

-- Verify table was created successfully
SELECT 
    'Sessions table created successfully' as status,
    COUNT(*) as total_sessions
FROM sessions;