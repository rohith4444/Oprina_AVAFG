-- Avatar Usage System Migration for Oprina API
-- Phase 1.5 Avatar Integration: Usage Tracking & Quotas
-- 
-- This migration creates tables for:
-- - Avatar usage tracking (HeyGen sessions)
-- - User quotas (20-minute limit per user)
-- - Monthly usage summaries for billing
--
-- Run with: psql -d your_database -f migrations/002_add_avatar_usage.sql

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Avatar usage records table for tracking HeyGen avatar sessions
CREATE TABLE IF NOT EXISTS avatar_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Avatar session details
    avatar_session_id VARCHAR(255) NOT NULL, -- HeyGen session ID
    avatar_name VARCHAR(255) NOT NULL, -- Name of avatar used
    
    -- Session timing
    session_started_at TIMESTAMPTZ NOT NULL,
    session_ended_at TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    
    -- Usage metrics
    words_spoken INTEGER DEFAULT 0,
    messages_count INTEGER DEFAULT 0,
    
    -- Cost tracking
    estimated_cost DECIMAL(10,4) DEFAULT 0.0000,
    billing_period VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'error', 'timeout')),
    CONSTRAINT valid_billing_period CHECK (billing_period ~ '^\d{4}-\d{2}$'),
    CONSTRAINT positive_duration CHECK (duration_seconds >= 0),
    CONSTRAINT positive_words CHECK (words_spoken >= 0),
    CONSTRAINT positive_messages CHECK (messages_count >= 0),
    CONSTRAINT positive_cost CHECK (estimated_cost >= 0)
);

-- Usage quotas table for tracking user limits (20 minutes total per user)
CREATE TABLE IF NOT EXISTS usage_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Quota limits (20 minutes total per user account)
    total_limit_minutes INTEGER NOT NULL DEFAULT 20,
    used_minutes INTEGER NOT NULL DEFAULT 0,
    used_seconds INTEGER NOT NULL DEFAULT 0,
    
    -- Session tracking
    session_count INTEGER NOT NULL DEFAULT 0,
    
    -- Quota status
    quota_exhausted BOOLEAN NOT NULL DEFAULT FALSE,
    exhausted_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_quota UNIQUE (user_id),
    CONSTRAINT positive_limits CHECK (total_limit_minutes > 0),
    CONSTRAINT positive_used CHECK (used_minutes >= 0 AND used_seconds >= 0),
    CONSTRAINT positive_sessions CHECK (session_count >= 0)
);

-- Usage summaries table for monthly billing reports
CREATE TABLE IF NOT EXISTS usage_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Billing period
    billing_period VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Usage totals for the month
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_duration_seconds INTEGER NOT NULL DEFAULT 0,
    total_words_spoken INTEGER NOT NULL DEFAULT 0,
    total_messages INTEGER NOT NULL DEFAULT 0,
    
    -- Cost totals
    total_estimated_cost DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_billing_period UNIQUE (user_id, billing_period),
    CONSTRAINT valid_summary_billing_period CHECK (billing_period ~ '^\d{4}-\d{2}$'),
    CONSTRAINT positive_summary_totals CHECK (
        total_sessions >= 0 AND 
        total_duration_seconds >= 0 AND 
        total_words_spoken >= 0 AND 
        total_messages >= 0 AND 
        total_estimated_cost >= 0
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_avatar_usage_user_id ON avatar_usage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_session_id ON avatar_usage_records(session_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_avatar_session_id ON avatar_usage_records(avatar_session_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_billing_period ON avatar_usage_records(billing_period);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_status ON avatar_usage_records(status);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_created_at ON avatar_usage_records(created_at);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_user_billing ON avatar_usage_records(user_id, billing_period);

CREATE INDEX IF NOT EXISTS idx_usage_quotas_user_id ON usage_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_quotas_exhausted ON usage_quotas(quota_exhausted);
CREATE INDEX IF NOT EXISTS idx_usage_quotas_created_at ON usage_quotas(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_summaries_user_id ON usage_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_summaries_billing_period ON usage_summaries(billing_period);
CREATE INDEX IF NOT EXISTS idx_usage_summaries_user_billing ON usage_summaries(user_id, billing_period);
CREATE INDEX IF NOT EXISTS idx_usage_summaries_created_at ON usage_summaries(created_at);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_avatar_usage_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_avatar_usage_updated_at
    BEFORE UPDATE ON avatar_usage_records
    FOR EACH ROW
    EXECUTE FUNCTION update_avatar_usage_updated_at();

CREATE TRIGGER trigger_update_usage_quotas_updated_at
    BEFORE UPDATE ON usage_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_avatar_usage_updated_at();

CREATE TRIGGER trigger_update_usage_summaries_updated_at
    BEFORE UPDATE ON usage_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_avatar_usage_updated_at();

-- Function to automatically update quota usage when avatar session ends
CREATE OR REPLACE FUNCTION update_quota_on_avatar_session_end()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update quota when session is completed and duration is set
    IF NEW.status = 'completed' AND NEW.duration_seconds IS NOT NULL AND 
       (OLD.status != 'completed' OR OLD.duration_seconds IS NULL) THEN
        
        -- Update or create quota record
        INSERT INTO usage_quotas (user_id, used_seconds, used_minutes, session_count)
        VALUES (
            NEW.user_id,
            NEW.duration_seconds,
            NEW.duration_seconds / 60,
            1
        )
        ON CONFLICT (user_id) DO UPDATE SET
            used_seconds = usage_quotas.used_seconds + NEW.duration_seconds,
            used_minutes = (usage_quotas.used_seconds + NEW.duration_seconds) / 60,
            session_count = usage_quotas.session_count + 1,
            quota_exhausted = ((usage_quotas.used_seconds + NEW.duration_seconds) / 60) >= usage_quotas.total_limit_minutes,
            exhausted_at = CASE 
                WHEN ((usage_quotas.used_seconds + NEW.duration_seconds) / 60) >= usage_quotas.total_limit_minutes 
                     AND NOT usage_quotas.quota_exhausted 
                THEN NOW() 
                ELSE usage_quotas.exhausted_at 
            END,
            updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update quota when avatar session ends
CREATE TRIGGER update_quota_on_session_end
    AFTER UPDATE ON avatar_usage_records
    FOR EACH ROW
    EXECUTE FUNCTION update_quota_on_avatar_session_end();

-- Function to automatically update monthly summaries
CREATE OR REPLACE FUNCTION update_usage_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update summary when session is completed
    IF NEW.status = 'completed' AND NEW.duration_seconds IS NOT NULL THEN
        
        -- Update or create monthly summary
        INSERT INTO usage_summaries (
            user_id, 
            billing_period, 
            total_sessions, 
            total_duration_seconds, 
            total_words_spoken, 
            total_messages, 
            total_estimated_cost
        )
        VALUES (
            NEW.user_id,
            NEW.billing_period,
            1,
            NEW.duration_seconds,
            NEW.words_spoken,
            NEW.messages_count,
            NEW.estimated_cost
        )
        ON CONFLICT (user_id, billing_period) DO UPDATE SET
            total_sessions = usage_summaries.total_sessions + 1,
            total_duration_seconds = usage_summaries.total_duration_seconds + NEW.duration_seconds,
            total_words_spoken = usage_summaries.total_words_spoken + NEW.words_spoken,
            total_messages = usage_summaries.total_messages + NEW.messages_count,
            total_estimated_cost = usage_summaries.total_estimated_cost + NEW.estimated_cost,
            updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update monthly summaries
CREATE TRIGGER update_monthly_summary
    AFTER UPDATE ON avatar_usage_records
    FOR EACH ROW
    EXECUTE FUNCTION update_usage_summary();

-- Function to clean up old usage records (keep last 12 months)
CREATE OR REPLACE FUNCTION cleanup_old_usage_records()
RETURNS void AS $$
BEGIN
    -- Delete usage records older than 12 months
    DELETE FROM avatar_usage_records 
    WHERE created_at < NOW() - INTERVAL '12 months';
    
    -- Delete usage summaries older than 24 months
    DELETE FROM usage_summaries 
    WHERE created_at < NOW() - INTERVAL '24 months';
    
    RAISE NOTICE 'Cleaned up old usage records and summaries';
END;
$$ LANGUAGE plpgsql;

-- Create view for active avatar sessions
CREATE OR REPLACE VIEW active_avatar_sessions AS
SELECT 
    aur.*,
    u.email as user_email,
    u.display_name as user_name,
    s.session_name,
    s.title as session_title
FROM avatar_usage_records aur
JOIN users u ON aur.user_id = u.id
JOIN sessions s ON aur.session_id = s.id
WHERE aur.status = 'active';

-- Create view for user quota status
CREATE OR REPLACE VIEW user_quota_status AS
SELECT 
    uq.*,
    u.email as user_email,
    u.display_name as user_name,
    (uq.total_limit_minutes * 60 - uq.used_seconds) as seconds_remaining,
    (uq.total_limit_minutes - uq.used_minutes) as minutes_remaining,
    ROUND((uq.used_minutes::decimal / uq.total_limit_minutes::decimal) * 100, 2) as usage_percentage
FROM usage_quotas uq
JOIN users u ON uq.user_id = u.id;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Avatar usage system migration completed successfully!';
    RAISE NOTICE 'Created tables: avatar_usage_records, usage_quotas, usage_summaries';
    RAISE NOTICE 'Created indexes, triggers, and views for avatar usage tracking';
END $$;
