-- =====================================================================
-- Migration: 05_add_oauth_support.sql
-- Description: Add OAuth support to existing users table (SIMPLIFIED)
-- Date: 2025-01-01
-- =====================================================================

-- Add OAuth-related columns to existing users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS google_user_id TEXT,
ADD COLUMN IF NOT EXISTS gmail_tokens JSONB,
ADD COLUMN IF NOT EXISTS calendar_tokens JSONB,
ADD COLUMN IF NOT EXISTS google_profile JSONB;

-- Create simple indexes for OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_google_user_id ON users(google_user_id);

-- Simple function to check if tokens are expired
CREATE OR REPLACE FUNCTION check_token_expiry(tokens JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if tokens exist and are not expired
    IF tokens IS NULL OR tokens = '{}' THEN
        RETURN FALSE;
    END IF;
    
    -- Check if expires_at exists
    IF NOT (tokens ? 'expires_at') THEN
        RETURN FALSE;
    END IF;
    
    -- Check expiry (tokens contain expires_at timestamp)
    IF (tokens->>'expires_at')::timestamp < NOW() THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Simple function to clean expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_tokens()
RETURNS INTEGER AS $$
DECLARE
    gmail_count INTEGER;
    calendar_count INTEGER;
BEGIN
    -- Clean expired Gmail tokens
    UPDATE users 
    SET gmail_tokens = NULL 
    WHERE gmail_tokens IS NOT NULL 
    AND NOT check_token_expiry(gmail_tokens);
    
    GET DIAGNOSTICS gmail_count = ROW_COUNT;
    
    -- Clean expired Calendar tokens
    UPDATE users 
    SET calendar_tokens = NULL 
    WHERE calendar_tokens IS NOT NULL 
    AND NOT check_token_expiry(calendar_tokens);
    
    GET DIAGNOSTICS calendar_count = ROW_COUNT;
    
    -- Return total count
    RETURN gmail_count + calendar_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON COLUMN users.google_user_id IS 'Google OAuth user ID for login authentication';
COMMENT ON COLUMN users.gmail_tokens IS 'Gmail OAuth tokens (access_token, refresh_token, expires_at)';
COMMENT ON COLUMN users.calendar_tokens IS 'Calendar OAuth tokens (access_token, refresh_token, expires_at)';
COMMENT ON COLUMN users.google_profile IS 'Google profile information from OAuth (name, picture, etc.)';

-- Success message
SELECT 'OAuth support migration completed successfully' AS status;