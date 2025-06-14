-- Database Performance & Constraints Migration for Oprina API
-- Phase 2 Optimization: Missing Constraints & Performance Indexes
-- 
-- This migration adds:
-- - Missing foreign key constraints
-- - Performance optimization indexes
-- - Data validation constraints
-- - Composite indexes for common queries
--
-- Run with: psql -d your_database -f migrations/004_add_indexes_constraints.sql

-- Add missing foreign key constraints that weren't explicitly defined

-- Ensure service_tokens has proper foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_service_tokens_user_id'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT fk_service_tokens_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add composite indexes for common query patterns

-- Messages table - common queries by session and user
CREATE INDEX IF NOT EXISTS idx_messages_session_role ON messages(session_id, role);
CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session_index ON messages(session_id, message_index);

-- Sessions table - user activity queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_activity ON sessions(user_id, last_activity_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status_activity ON sessions(status, last_activity_at);

-- Service tokens table - OAuth management queries
CREATE INDEX IF NOT EXISTS idx_service_tokens_user_service ON service_tokens(user_id, service_type);
CREATE INDEX IF NOT EXISTS idx_service_tokens_user_provider ON service_tokens(user_id, provider);
CREATE INDEX IF NOT EXISTS idx_service_tokens_service_provider ON service_tokens(service_type, provider);
CREATE INDEX IF NOT EXISTS idx_service_tokens_user_active ON service_tokens(user_id, is_active, is_revoked) 
    WHERE is_active = TRUE AND is_revoked = FALSE;

-- User tokens table - authentication queries
CREATE INDEX IF NOT EXISTS idx_user_tokens_user_type ON user_tokens(user_id, token_type);
CREATE INDEX IF NOT EXISTS idx_user_tokens_type_expires ON user_tokens(token_type, expires_at);
CREATE INDEX IF NOT EXISTS idx_user_tokens_active ON user_tokens(user_id, is_revoked) 
    WHERE is_revoked = FALSE;

-- User activities table - analytics queries
CREATE INDEX IF NOT EXISTS idx_user_activities_user_type ON user_activities(user_id, activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activities_type_created ON user_activities(activity_type, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activities_session_type ON user_activities(session_id, activity_type) 
    WHERE session_id IS NOT NULL;

-- Add data validation constraints

-- Users table validations
DO $$
BEGIN
    -- Email format validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_users_email_format'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT chk_users_email_format 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    END IF;
    
    -- Timezone validation (basic check)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_users_timezone_format'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT chk_users_timezone_format 
        CHECK (timezone ~ '^[A-Za-z_/]+$' OR timezone = 'UTC');
    END IF;
    
    -- Language code validation (ISO 639-1)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_users_language_format'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT chk_users_language_format 
        CHECK (language ~ '^[a-z]{2}(-[A-Z]{2})?$');
    END IF;
END $$;

-- Sessions table validations
DO $$
BEGIN
    -- Session status validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_sessions_status_valid'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT chk_sessions_status_valid 
        CHECK (status IN ('active', 'paused', 'ended', 'archived'));
    END IF;
    
    -- Agent type validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_sessions_agent_type_valid'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT chk_sessions_agent_type_valid 
        CHECK (agent_type ~ '^[a-z][a-z0-9_]*$');
    END IF;
    
    -- Positive values validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_sessions_positive_values'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT chk_sessions_positive_values 
        CHECK (
            message_count >= 0 AND 
            total_tokens_used >= 0 AND 
            estimated_cost >= 0
        );
    END IF;
END $$;

-- Messages table validations
DO $$
BEGIN
    -- Message role validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_messages_role_valid'
    ) THEN
        ALTER TABLE messages 
        ADD CONSTRAINT chk_messages_role_valid 
        CHECK (role IN ('user', 'assistant', 'system', 'function'));
    END IF;
    
    -- Content type validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_messages_content_type_valid'
    ) THEN
        ALTER TABLE messages 
        ADD CONSTRAINT chk_messages_content_type_valid 
        CHECK (content_type IN ('text', 'image', 'audio', 'file'));
    END IF;
    
    -- Message status validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_messages_status_valid'
    ) THEN
        ALTER TABLE messages 
        ADD CONSTRAINT chk_messages_status_valid 
        CHECK (status IN ('pending', 'processing', 'completed', 'error'));
    END IF;
    
    -- Positive token values
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_messages_positive_tokens'
    ) THEN
        ALTER TABLE messages 
        ADD CONSTRAINT chk_messages_positive_tokens 
        CHECK (
            prompt_tokens >= 0 AND 
            completion_tokens >= 0 AND 
            total_tokens >= 0 AND 
            estimated_cost >= 0 AND
            message_index >= 0
        );
    END IF;
END $$;

-- Service tokens table validations
DO $$
BEGIN
    -- Service type format validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_service_tokens_service_type_format'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT chk_service_tokens_service_type_format 
        CHECK (service_type ~ '^[a-z][a-z0-9_]*$');
    END IF;
    
    -- Provider format validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_service_tokens_provider_format'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT chk_service_tokens_provider_format 
        CHECK (provider ~ '^[a-z][a-z0-9_]*$');
    END IF;
    
    -- Token type validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_service_tokens_token_type_valid'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT chk_service_tokens_token_type_valid 
        CHECK (token_type IN ('Bearer', 'Basic', 'ApiKey', 'OAuth'));
    END IF;
    
    -- Provider email format validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_service_tokens_provider_email_format'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT chk_service_tokens_provider_email_format 
        CHECK (
            provider_email IS NULL OR 
            provider_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        );
    END IF;
    
    -- Use count validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_service_tokens_use_count_positive'
    ) THEN
        ALTER TABLE service_tokens 
        ADD CONSTRAINT chk_service_tokens_use_count_positive 
        CHECK (use_count >= 0);
    END IF;
END $$;

-- User tokens table validations
DO $$
BEGIN
    -- Token type validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_user_tokens_type_valid'
    ) THEN
        ALTER TABLE user_tokens 
        ADD CONSTRAINT chk_user_tokens_type_valid 
        CHECK (token_type IN ('refresh', 'reset_password', 'email_verify', 'api_key'));
    END IF;
END $$;

-- Token refresh logs table validations
DO $$
BEGIN
    -- Refresh type validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_token_refresh_logs_type_valid'
    ) THEN
        ALTER TABLE token_refresh_logs 
        ADD CONSTRAINT chk_token_refresh_logs_type_valid 
        CHECK (refresh_type IN ('automatic', 'manual', 'scheduled'));
    END IF;
    
    -- Refresh status validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_token_refresh_logs_status_valid'
    ) THEN
        ALTER TABLE token_refresh_logs 
        ADD CONSTRAINT chk_token_refresh_logs_status_valid 
        CHECK (refresh_status IN ('pending', 'success', 'failed', 'cancelled'));
    END IF;
    
    -- Retry count validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_token_refresh_logs_retry_count_positive'
    ) THEN
        ALTER TABLE token_refresh_logs 
        ADD CONSTRAINT chk_token_refresh_logs_retry_count_positive 
        CHECK (retry_count >= 0);
    END IF;
END $$;

-- Create additional performance views

-- Active user sessions view
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT 
    s.*,
    u.email as user_email,
    u.display_name as user_name,
    u.timezone as user_timezone,
    COUNT(m.id) as actual_message_count,
    MAX(m.created_at) as last_message_at
FROM sessions s
JOIN users u ON s.user_id = u.id
LEFT JOIN messages m ON s.id = m.session_id
WHERE s.status = 'active' AND u.is_active = TRUE
GROUP BY s.id, u.id;

-- User token summary view
CREATE OR REPLACE VIEW user_token_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.display_name,
    COUNT(CASE WHEN st.is_active = TRUE AND st.is_revoked = FALSE THEN 1 END) as active_service_tokens,
    COUNT(CASE WHEN ut.is_revoked = FALSE AND ut.expires_at > NOW() THEN 1 END) as valid_user_tokens,
    MAX(st.last_used_at) as last_service_token_use,
    u.has_google_oauth,
    u.has_microsoft_oauth
FROM users u
LEFT JOIN service_tokens st ON u.id = st.user_id
LEFT JOIN user_tokens ut ON u.id = ut.user_id
WHERE u.is_active = TRUE
GROUP BY u.id;

-- Session activity summary view
CREATE OR REPLACE VIEW session_activity_summary AS
SELECT 
    s.id as session_id,
    s.user_id,
    s.session_name,
    s.status,
    s.message_count,
    s.total_tokens_used,
    s.estimated_cost,
    COUNT(m.id) as actual_message_count,
    SUM(m.total_tokens) as actual_total_tokens,
    SUM(m.estimated_cost) as actual_total_cost,
    MIN(m.created_at) as first_message_at,
    MAX(m.created_at) as last_message_at,
    EXTRACT(EPOCH FROM (MAX(m.created_at) - MIN(m.created_at))) as session_duration_seconds
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
GROUP BY s.id;

-- Function to update session statistics (improved version)
CREATE OR REPLACE FUNCTION update_session_statistics()
RETURNS void AS $$
BEGIN
    -- Update session statistics based on actual message data
    UPDATE sessions 
    SET 
        message_count = subquery.msg_count,
        total_tokens_used = subquery.total_tokens,
        estimated_cost = subquery.total_cost,
        updated_at = NOW()
    FROM (
        SELECT 
            session_id,
            COUNT(*) as msg_count,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COALESCE(SUM(estimated_cost), 0) as total_cost
        FROM messages 
        GROUP BY session_id
    ) as subquery
    WHERE sessions.id = subquery.session_id;
    
    RAISE NOTICE 'Updated session statistics for all sessions';
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Mark expired service tokens as inactive
    UPDATE service_tokens 
    SET 
        is_active = FALSE,
        updated_at = NOW()
    WHERE 
        expires_at IS NOT NULL 
        AND expires_at < NOW() 
        AND is_active = TRUE;
    
    -- Delete expired user tokens
    DELETE FROM user_tokens 
    WHERE expires_at < NOW();
    
    -- Delete old token refresh logs (keep last 30 days)
    DELETE FROM token_refresh_logs 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    RAISE NOTICE 'Cleaned up expired tokens and old refresh logs';
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database optimization migration completed successfully!';
    RAISE NOTICE 'Added performance indexes, data validation constraints, and utility views';
    RAISE NOTICE 'Created cleanup and maintenance functions';
END $$;
