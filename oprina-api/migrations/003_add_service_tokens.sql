-- Service Tokens Migration for Oprina API
-- Phase 2 OAuth Integration: Service Tokens
-- 
-- This migration creates tables for:
-- - Service token storage (OAuth tokens, API keys)
-- - Token refresh logging
-- - Secure token management
--
-- Run with: psql -d your_database -f migrations/003_add_service_tokens.sql

-- Service tokens table for OAuth and API key storage
CREATE TABLE IF NOT EXISTS service_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Service identification
    service_type VARCHAR(100) NOT NULL, -- gmail, calendar, microsoft, etc.
    service_name VARCHAR(200), -- Human-readable service name
    
    -- Token data (encrypted)
    access_token_encrypted TEXT NOT NULL, -- Encrypted access token
    refresh_token_encrypted TEXT, -- Encrypted refresh token (if available)
    id_token_encrypted TEXT, -- Encrypted ID token (if available)
    
    -- Token metadata
    token_type VARCHAR(50) DEFAULT 'Bearer' NOT NULL, -- Bearer, Basic, ApiKey, etc.
    scope TEXT, -- Granted scopes (space-separated)
    expires_at TIMESTAMPTZ, -- When access token expires
    
    -- OAuth provider details
    provider VARCHAR(50) NOT NULL, -- google, microsoft, github, etc.
    provider_user_id VARCHAR(200), -- Provider's user ID
    provider_email VARCHAR(255), -- Email from provider
    
    -- Token status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,
    
    -- Usage tracking
    last_used_at TIMESTAMPTZ,
    use_count INTEGER NOT NULL DEFAULT 0,
    
    -- Additional metadata
    token_metadata JSONB, -- Additional token info
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_service_provider UNIQUE (user_id, service_type, provider),
    CONSTRAINT valid_service_type CHECK (service_type ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT valid_provider CHECK (provider ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT valid_provider_email CHECK (provider_email IS NULL OR provider_email ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- Token refresh logs table for tracking refresh operations
CREATE TABLE IF NOT EXISTS token_refresh_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_token_id UUID NOT NULL REFERENCES service_tokens(id) ON DELETE CASCADE,
    
    -- Refresh details
    refresh_type VARCHAR(50) NOT NULL DEFAULT 'automatic',
    refresh_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Timing information
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Token expiry information
    previous_expires_at TIMESTAMPTZ,
    new_expires_at TIMESTAMPTZ,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Additional metadata
    refresh_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_refresh_type CHECK (refresh_type IN ('automatic', 'manual', 'scheduled')),
    CONSTRAINT valid_refresh_status CHECK (refresh_status IN ('pending', 'success', 'failed', 'cancelled'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_tokens_user_id ON service_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_service_tokens_service_type ON service_tokens(service_type);
CREATE INDEX IF NOT EXISTS idx_service_tokens_provider ON service_tokens(provider);
CREATE INDEX IF NOT EXISTS idx_service_tokens_active ON service_tokens(is_active, is_revoked) WHERE is_active = TRUE AND is_revoked = FALSE;
CREATE INDEX IF NOT EXISTS idx_service_tokens_expires_at ON service_tokens(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_service_tokens_created_at ON service_tokens(created_at);
CREATE INDEX IF NOT EXISTS idx_service_tokens_user_active ON service_tokens(user_id, is_active, is_revoked) WHERE is_active = TRUE AND is_revoked = FALSE;

CREATE INDEX IF NOT EXISTS idx_token_refresh_logs_service_token_id ON token_refresh_logs(service_token_id);
CREATE INDEX IF NOT EXISTS idx_token_refresh_logs_status ON token_refresh_logs(refresh_status);
CREATE INDEX IF NOT EXISTS idx_token_refresh_logs_created_at ON token_refresh_logs(created_at);

-- Update trigger for service_tokens updated_at
CREATE OR REPLACE FUNCTION update_service_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_service_tokens_updated_at
    BEFORE UPDATE ON service_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_service_tokens_updated_at();

-- Function to automatically revoke old tokens when new ones are added
CREATE OR REPLACE FUNCTION revoke_old_service_tokens()
RETURNS TRIGGER AS $$
BEGIN
    -- When a new active token is inserted, revoke old tokens of the same type
    IF NEW.is_active = TRUE AND NEW.is_revoked = FALSE THEN
        UPDATE service_tokens 
        SET 
            is_active = FALSE,
            is_revoked = TRUE,
            updated_at = NOW()
        WHERE 
            user_id = NEW.user_id 
            AND service_type = NEW.service_type 
            AND provider = NEW.provider
            AND id != NEW.id
            AND is_active = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-revoke old tokens
CREATE TRIGGER revoke_old_tokens_on_insert
    AFTER INSERT ON service_tokens
    FOR EACH ROW EXECUTE FUNCTION revoke_old_service_tokens();

-- Function to update user OAuth flags when tokens are added/removed
CREATE OR REPLACE FUNCTION update_user_oauth_flags()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user OAuth flags based on active tokens
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Check for Google OAuth
        UPDATE users 
        SET has_google_oauth = EXISTS(
            SELECT 1 FROM service_tokens 
            WHERE user_id = NEW.user_id 
            AND provider = 'google' 
            AND is_active = TRUE 
            AND is_revoked = FALSE
        )
        WHERE id = NEW.user_id;
        
        -- Check for Microsoft OAuth
        UPDATE users 
        SET has_microsoft_oauth = EXISTS(
            SELECT 1 FROM service_tokens 
            WHERE user_id = NEW.user_id 
            AND provider = 'microsoft' 
            AND is_active = TRUE 
            AND is_revoked = FALSE
        )
        WHERE id = NEW.user_id;
        
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Update flags after deletion
        UPDATE users 
        SET 
            has_google_oauth = EXISTS(
                SELECT 1 FROM service_tokens 
                WHERE user_id = OLD.user_id 
                AND provider = 'google' 
                AND is_active = TRUE 
                AND is_revoked = FALSE
            ),
            has_microsoft_oauth = EXISTS(
                SELECT 1 FROM service_tokens 
                WHERE user_id = OLD.user_id 
                AND provider = 'microsoft' 
                AND is_active = TRUE 
                AND is_revoked = FALSE
            )
        WHERE id = OLD.user_id;
        
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Triggers to auto-update user OAuth flags
CREATE TRIGGER update_user_oauth_on_token_change
    AFTER INSERT OR UPDATE ON service_tokens
    FOR EACH ROW EXECUTE FUNCTION update_user_oauth_flags();

CREATE TRIGGER update_user_oauth_on_token_delete
    AFTER DELETE ON service_tokens
    FOR EACH ROW EXECUTE FUNCTION update_user_oauth_flags();

-- Function to clean up expired tokens (can be called by cron job)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    cleanup_count INTEGER;
BEGIN
    -- Mark expired tokens as inactive
    UPDATE service_tokens 
    SET 
        is_active = FALSE,
        updated_at = NOW()
    WHERE 
        expires_at IS NOT NULL 
        AND expires_at < NOW() 
        AND is_active = TRUE;
    
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    
    -- Log the cleanup operation
    INSERT INTO token_refresh_logs (
        service_token_id,
        refresh_type,
        refresh_status,
        refresh_started_at,
        refresh_completed_at,
        error_message,
        refresh_metadata
    )
    SELECT 
        id,
        'cleanup',
        'success',
        NOW(),
        NOW(),
        'Token expired and marked inactive',
        jsonb_build_object('cleanup_batch', NOW())
    FROM service_tokens 
    WHERE 
        expires_at IS NOT NULL 
        AND expires_at < NOW() 
        AND is_active = FALSE
        AND updated_at > NOW() - INTERVAL '1 minute'; -- Only recently updated ones
    
    RETURN cleanup_count;
END;
$$ language 'plpgsql';

-- View for active tokens summary
CREATE VIEW active_service_tokens AS
SELECT 
    st.id,
    st.user_id,
    u.email as user_email,
    st.service_type,
    st.service_name,
    st.provider,
    st.provider_email,
    st.token_type,
    st.scope,
    st.expires_at,
    CASE 
        WHEN st.expires_at IS NULL THEN 'never'
        WHEN st.expires_at < NOW() THEN 'expired'
        WHEN st.expires_at < NOW() + INTERVAL '1 hour' THEN 'expiring_soon'
        ELSE 'valid'
    END as expiry_status,
    st.last_used_at,
    st.created_at,
    st.updated_at
FROM service_tokens st
JOIN users u ON st.user_id = u.id
WHERE st.is_active = TRUE AND st.is_revoked = FALSE;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON service_tokens TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON token_refresh_logs TO postgres;
GRANT SELECT ON active_service_tokens TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Migration completion log
DO $$
BEGIN
    RAISE NOTICE 'Service tokens migration completed successfully!';
    RAISE NOTICE 'Created tables: service_tokens, token_refresh_logs';
    RAISE NOTICE 'Created indexes, triggers, and views for token management';
    RAISE NOTICE 'OAuth integration ready for Gmail, Calendar, and Microsoft services';
END $$; 