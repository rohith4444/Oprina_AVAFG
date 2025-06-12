#!/usr/bin/env python3
"""
Database setup script for Oprina API.
Creates necessary tables in Supabase.
"""

import os
import sys
import asyncio
from supabase import create_client, Client

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings


async def create_tables():
    """Create necessary database tables."""
    
    # Initialize Supabase client
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # Users table
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email TEXT UNIQUE NOT NULL,
        display_name TEXT,
        avatar_url TEXT,
        preferences JSONB DEFAULT '{}',
        settings JSONB DEFAULT '{}',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT NOW(),
        last_login_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
    """
    
    # Sessions table
    sessions_sql = """
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        session_type TEXT DEFAULT 'chat',
        status TEXT DEFAULT 'active',
        vertex_session_id TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW(),
        last_activity_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
    CREATE INDEX IF NOT EXISTS idx_sessions_vertex_session_id ON sessions(vertex_session_id);
    """
    
    # Messages table
    messages_sql = """
    CREATE TABLE IF NOT EXISTS messages (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL,
        message_type TEXT DEFAULT 'text',
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
    CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
    CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
    """
    
    # Enable UUID extension if not exists
    uuid_sql = "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    
    try:
        print("Creating database tables...")
        
        # Execute SQL commands
        print("- Enabling UUID extension...")
        supabase.rpc('exec_sql', {'sql': uuid_sql}).execute()
        
        print("- Creating users table...")
        supabase.rpc('exec_sql', {'sql': users_sql}).execute()
        
        print("- Creating sessions table...")
        supabase.rpc('exec_sql', {'sql': sessions_sql}).execute()
        
        print("- Creating messages table...")
        supabase.rpc('exec_sql', {'sql': messages_sql}).execute()
        
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("\nNote: If you're using Supabase, you may need to:")
        print("1. Enable the SQL Editor in your Supabase dashboard")
        print("2. Run the SQL commands manually")
        print("3. Ensure your service key has the necessary permissions")
        
        # Print the SQL for manual execution
        print("\n" + "="*50)
        print("SQL to run manually:")
        print("="*50)
        print(uuid_sql)
        print(users_sql)
        print(sessions_sql)
        print(messages_sql)


def main():
    """Main function."""
    print("Oprina API Database Setup")
    print("=" * 25)
    
    # Check environment variables
    if not settings.SUPABASE_URL:
        print("❌ SUPABASE_URL not set in environment")
        return
    
    if not settings.SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_SERVICE_KEY not set in environment")
        return
    
    print(f"Database URL: {settings.SUPABASE_URL}")
    print(f"Service Key: {'*' * (len(settings.SUPABASE_SERVICE_KEY) - 8)}{settings.SUPABASE_SERVICE_KEY[-8:]}")
    print()
    
    # Run setup
    asyncio.run(create_tables())


if __name__ == "__main__":
    main()
