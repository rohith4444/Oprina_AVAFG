-- =====================================================================
-- Migration: 03_create_messages_table.sql
-- Description: Create messages table for storing chat conversation history
-- Date: 2025-06-15
-- =====================================================================

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Message Content
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    
    -- Voice Integration
    message_type VARCHAR(50) DEFAULT 'text' NOT NULL, -- 'voice', 'text'
    voice_metadata JSONB DEFAULT '{}' NOT NULL,
    
    -- Message Ordering
    message_index INTEGER NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    UNIQUE(session_id, message_index),
    CHECK (message_type IN ('voice', 'text')),
    CHECK (message_index > 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_order ON messages(session_id, message_index);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

-- Function to auto-set message_index
CREATE OR REPLACE FUNCTION set_message_index()
RETURNS TRIGGER AS $$
BEGIN
    -- Get next message index for this session
    SELECT COALESCE(MAX(message_index), 0) + 1
    INTO NEW.message_index
    FROM messages
    WHERE session_id = NEW.session_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update session activity when messages are added
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions 
    SET 
        last_activity_at = NOW(), 
        updated_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-set message index (only when not provided)
CREATE TRIGGER trigger_set_message_index
    BEFORE INSERT ON messages
    FOR EACH ROW
    WHEN (NEW.message_index IS NULL)
    EXECUTE FUNCTION set_message_index();

-- Trigger to auto-update session activity
CREATE TRIGGER trigger_update_session_activity
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();

-- Add comments for documentation
COMMENT ON TABLE messages IS 'Chat messages within sessions (user and assistant responses)';
COMMENT ON COLUMN messages.session_id IS 'Reference to session this message belongs to';
COMMENT ON COLUMN messages.user_id IS 'Reference to user (for data ownership)';
COMMENT ON COLUMN messages.role IS 'Message sender: user or assistant';
COMMENT ON COLUMN messages.content IS 'Message text content (transcribed for voice)';
COMMENT ON COLUMN messages.message_type IS 'Source type: voice input or text input';
COMMENT ON COLUMN messages.voice_metadata IS 'Voice processing metadata (duration, confidence, etc.)';
COMMENT ON COLUMN messages.message_index IS 'Order of message within session (auto-generated)';

-- Insert example data for testing (optional - remove in production)
INSERT INTO messages (
    session_id,
    user_id,
    role,
    content,
    message_type,
    voice_metadata,
    message_index
) SELECT 
    s.id,
    s.user_id,
    'user',
    'Hello Oprina, can you help me with my tasks today?',
    'voice',
    '{"duration": 3.2, "confidence": 0.95, "language": "en-US"}'::jsonb,
    1
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE u.email = 'demo@oprina.ai' 
  AND s.title = 'Welcome Chat - Voice Enabled'
ON CONFLICT DO NOTHING;

INSERT INTO messages (
    session_id,
    user_id,
    role,
    content,
    message_type,
    voice_metadata,
    message_index
) SELECT 
    s.id,
    s.user_id,
    'assistant',
    'Hello! I''d be happy to help you with your tasks. I can assist with email management, calendar scheduling, and various productivity tasks. What would you like to work on first?',
    'text',
    '{}'::jsonb,
    2
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE u.email = 'demo@oprina.ai' 
  AND s.title = 'Welcome Chat - Voice Enabled'
ON CONFLICT DO NOTHING;

-- Verify table was created successfully
SELECT 
    'Messages table created successfully' as status,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
    COUNT(CASE WHEN message_type = 'voice' THEN 1 END) as voice_messages
FROM messages;