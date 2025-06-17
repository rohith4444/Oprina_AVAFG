-- =====================================================================
-- Migration: 006_create_avatar_quotas_table.sql
-- Description: Create user avatar quotas table for 20-minute lifetime limit tracking
-- Date: 2025-06-16
-- =====================================================================

-- Create user_avatar_quotas table
CREATE TABLE IF NOT EXISTS user_avatar_quotas (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User Relationship (Foreign Key)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Quota Tracking (20-minute lifetime limit)
    total_seconds_used INTEGER DEFAULT 0 NOT NULL,
    quota_exhausted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    UNIQUE(user_id), -- One quota record per user
    CHECK (total_seconds_used >= 0),
    CHECK (total_seconds_used <= 1200) -- 20 minutes max
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_avatar_quotas_user_id ON user_avatar_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_avatar_quotas_exhausted ON user_avatar_quotas(quota_exhausted);
CREATE INDEX IF NOT EXISTS idx_avatar_quotas_usage ON user_avatar_quotas(total_seconds_used);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_avatar_quotas_updated_at 
    BEFORE UPDATE ON user_avatar_quotas 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to get or create quota for a user
CREATE OR REPLACE FUNCTION get_or_create_user_quota(p_user_id UUID)
RETURNS user_avatar_quotas AS $$
DECLARE
    quota_record user_avatar_quotas;
BEGIN
    -- Try to get existing quota
    SELECT * INTO quota_record 
    FROM user_avatar_quotas 
    WHERE user_id = p_user_id;
    
    -- If no quota exists, create one
    IF NOT FOUND THEN
        INSERT INTO user_avatar_quotas (user_id, total_seconds_used, quota_exhausted)
        VALUES (p_user_id, 0, FALSE)
        RETURNING * INTO quota_record;
    END IF;
    
    RETURN quota_record;
END;
$$ LANGUAGE plpgsql;

-- Function to update quota usage
CREATE OR REPLACE FUNCTION update_quota_usage(p_user_id UUID, p_session_duration INTEGER)
RETURNS user_avatar_quotas AS $$
DECLARE
    quota_record user_avatar_quotas;
    new_total INTEGER;
BEGIN
    -- Get current quota
    SELECT * INTO quota_record 
    FROM user_avatar_quotas 
    WHERE user_id = p_user_id;
    
    -- Calculate new total
    new_total := quota_record.total_seconds_used + p_session_duration;
    
    -- Update quota
    UPDATE user_avatar_quotas 
    SET 
        total_seconds_used = new_total,
        quota_exhausted = (new_total >= 1200), -- 20 minutes
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING * INTO quota_record;
    
    RETURN quota_record;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE user_avatar_quotas IS 'Avatar streaming quotas - 20 minute lifetime limit per user';
COMMENT ON COLUMN user_avatar_quotas.user_id IS 'Reference to user (one quota per user)';
COMMENT ON COLUMN user_avatar_quotas.total_seconds_used IS 'Total seconds of avatar streaming used (lifetime)';
COMMENT ON COLUMN user_avatar_quotas.quota_exhausted IS 'Whether user has exhausted 20-minute limit';

-- Insert quota for demo user if exists
INSERT INTO user_avatar_quotas (user_id, total_seconds_used, quota_exhausted)
SELECT id, 0, FALSE
FROM users 
WHERE email = 'demo@oprina.ai'
ON CONFLICT (user_id) DO NOTHING;

-- Verify table was created successfully
SELECT 
    'Avatar quotas table created successfully' as status,
    COUNT(*) as total_quotas
FROM user_avatar_quotas;