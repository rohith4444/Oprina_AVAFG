-- =====================================================================
-- Migration: 007_create_avatar_sessions_table.sql
-- Description: Create avatar sessions table to track HeyGen streaming sessions
-- Date: 2025-06-16
-- =====================================================================

-- Create avatar_sessions table
CREATE TABLE IF NOT EXISTS avatar_sessions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User Relationship (Foreign Key)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- HeyGen Integration
    heygen_session_id TEXT NOT NULL UNIQUE,
    
    -- Session Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Session Status
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    
    -- Optional Metadata
    avatar_name VARCHAR(255) DEFAULT 'Ann_Therapist_public',
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CHECK (status IN ('active', 'completed', 'error', 'timeout')),
    CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    CHECK (duration_seconds IS NULL OR duration_seconds <= 900) -- 15 minutes max
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_avatar_sessions_user_id ON avatar_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_avatar_sessions_heygen_id ON avatar_sessions(heygen_session_id);
CREATE INDEX IF NOT EXISTS idx_avatar_sessions_status ON avatar_sessions(status);
CREATE INDEX IF NOT EXISTS idx_avatar_sessions_started_at ON avatar_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_avatar_sessions_active ON avatar_sessions(user_id, status) WHERE status = 'active';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_avatar_sessions_updated_at 
    BEFORE UPDATE ON avatar_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to end a session and calculate duration
CREATE OR REPLACE FUNCTION end_avatar_session(p_heygen_session_id TEXT, p_error_message TEXT DEFAULT NULL)
RETURNS avatar_sessions AS $$
DECLARE
    session_record avatar_sessions;
    calculated_duration INTEGER;
    final_status VARCHAR(50);
BEGIN
    -- Get the session
    SELECT * INTO session_record 
    FROM avatar_sessions 
    WHERE heygen_session_id = p_heygen_session_id 
    AND status = 'active';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active session not found for heygen_session_id: %', p_heygen_session_id;
    END IF;
    
    -- Calculate duration in seconds
    calculated_duration := EXTRACT(EPOCH FROM (NOW() - session_record.started_at))::INTEGER;
    
    -- Determine final status
    IF p_error_message IS NOT NULL THEN
        final_status := 'error';
    ELSIF calculated_duration >= 900 THEN
        final_status := 'timeout';
    ELSE
        final_status := 'completed';
    END IF;
    
    -- Update the session
    UPDATE avatar_sessions 
    SET 
        ended_at = NOW(),
        duration_seconds = calculated_duration,
        status = final_status,
        error_message = p_error_message,
        updated_at = NOW()
    WHERE heygen_session_id = p_heygen_session_id
    RETURNING * INTO session_record;
    
    -- Update user quota
    PERFORM update_quota_usage(session_record.user_id, calculated_duration);
    
    RETURN session_record;
END;
$$ LANGUAGE plpgsql;

-- Function to get active sessions for a user
CREATE OR REPLACE FUNCTION get_user_active_sessions(p_user_id UUID)
RETURNS SETOF avatar_sessions AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM avatar_sessions
    WHERE user_id = p_user_id 
    AND status = 'active'
    ORDER BY started_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old inactive sessions (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_orphaned_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleanup_count INTEGER;
BEGIN
    -- End sessions that have been active for more than 25 minutes (5 min grace period)
    UPDATE avatar_sessions 
    SET 
        ended_at = NOW(),
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER,
        status = 'timeout',
        error_message = 'Session cleanup - exceeded maximum duration',
        updated_at = NOW()
    WHERE status = 'active' 
    AND started_at < NOW() - INTERVAL '25 minutes';
    
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    
    -- Update quotas for cleaned up sessions
    UPDATE user_avatar_quotas 
    SET 
        total_seconds_used = (
            SELECT COALESCE(SUM(duration_seconds), 0)
            FROM avatar_sessions 
            WHERE avatar_sessions.user_id = user_avatar_quotas.user_id
            AND status IN ('completed', 'timeout', 'error')
            AND duration_seconds IS NOT NULL
        ),
        quota_exhausted = (
            SELECT COALESCE(SUM(duration_seconds), 0) >= 900
            FROM avatar_sessions 
            WHERE avatar_sessions.user_id = user_avatar_quotas.user_id
            AND status IN ('completed', 'timeout', 'error')
            AND duration_seconds IS NOT NULL
        ),
        updated_at = NOW()
    WHERE user_id IN (
        SELECT DISTINCT user_id 
        FROM avatar_sessions 
        WHERE status = 'timeout' 
        AND updated_at >= NOW() - INTERVAL '1 minute'
    );
    
    RETURN cleanup_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE avatar_sessions IS 'HeyGen avatar streaming sessions with duration tracking';
COMMENT ON COLUMN avatar_sessions.user_id IS 'Reference to user who created the session';
COMMENT ON COLUMN avatar_sessions.heygen_session_id IS 'HeyGen SDK session ID (unique)';
COMMENT ON COLUMN avatar_sessions.started_at IS 'When session was created';
COMMENT ON COLUMN avatar_sessions.ended_at IS 'When session was ended (NULL for active)';
COMMENT ON COLUMN avatar_sessions.duration_seconds IS 'Total session duration in seconds';
COMMENT ON COLUMN avatar_sessions.status IS 'Session status (active, completed, error, timeout)';
COMMENT ON COLUMN avatar_sessions.avatar_name IS 'HeyGen avatar name used';

-- Verify table was created successfully
SELECT 
    'Avatar sessions table created successfully' as status,
    COUNT(*) as total_sessions
FROM avatar_sessions;