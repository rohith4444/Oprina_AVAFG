-- =====================================================================
-- Migration: 001_create_users_table.sql
-- Description: Create users table with all required fields for Oprina API
-- Date: 2025-06-14
-- =====================================================================

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication Fields
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL for OAuth-only users
    
    -- Profile Fields (Your UI Requirements)
    full_name VARCHAR(255),           -- Main name field from UI
    preferred_name VARCHAR(255),      -- Optional nickname from UI  
    display_name VARCHAR(255),        -- Keep for compatibility
    avatar_url TEXT,
    
    -- Preferences (Your UI Requirements)
    work_type VARCHAR(100),           -- Dropdown: "What best describes your work?"
    ai_preferences TEXT,              -- Text area: "What personal preferences should Oprina consider?"
    
    -- System Preferences (Generic)
    preferences JSONB DEFAULT '{}',   -- For additional settings
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- OAuth Integration Flags
    has_google_oauth BOOLEAN DEFAULT FALSE NOT NULL,
    has_microsoft_oauth BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Activity Tracking
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at);
CREATE INDEX IF NOT EXISTS idx_users_work_type ON users(work_type);

-- Create trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts for Oprina API with profile and preferences';
COMMENT ON COLUMN users.email IS 'User email address (unique, required)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password (NULL for OAuth-only users)';
COMMENT ON COLUMN users.full_name IS 'Users full name (main name field for UI)';
COMMENT ON COLUMN users.preferred_name IS 'Users preferred name/nickname (optional)';
COMMENT ON COLUMN users.work_type IS 'What best describes your work (from UI dropdown)';
COMMENT ON COLUMN users.ai_preferences IS 'Personal preferences for AI responses (from UI text area)';
COMMENT ON COLUMN users.preferences IS 'Additional user preferences as JSON';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active (for soft delete)';
COMMENT ON COLUMN users.has_google_oauth IS 'Whether user has connected Google OAuth';
COMMENT ON COLUMN users.has_microsoft_oauth IS 'Whether user has connected Microsoft OAuth';

-- Insert example data for testing (optional - remove in production)
INSERT INTO users (
    email, 
    full_name, 
    preferred_name, 
    work_type, 
    ai_preferences,
    is_active,
    is_verified
) VALUES (
    'demo@oprina.ai',
    'Demo User',
    'Demo',
    'Software Developer', 
    'Please provide detailed explanations and focus on code examples',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Verify table was created successfully
SELECT 
    'Users table created successfully' as status,
    COUNT(*) as total_users
FROM users;