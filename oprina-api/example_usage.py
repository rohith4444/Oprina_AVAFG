#!/usr/bin/env python3
"""
Real-world example showing how migration files connect to repositories.

This example demonstrates the complete flow from database setup to application usage.
"""

import asyncio
from supabase import create_client

# Import our components
from app.config import settings
from app.core.database.startup_validator import run_startup_validation
from app.core.database.repositories.user_repository import UserRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.avatar_usage_repository import UsageRepository


async def main():
    """Complete example showing migration -> repository -> application flow."""
    print("🚀 Oprina API Database Integration Example")
    print("=" * 50)
    
    # Step 1: Initialize database connection
    print("\n1️⃣ Initializing database connection...")
    try:
        db_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("✅ Database client created")
    except Exception as e:
        print(f"❌ Failed to create database client: {e}")
        return
    
    # Step 2: Run startup validation
    print("\n2️⃣ Running startup validation...")
    validation_results = await run_startup_validation(db_client)
    
    if not validation_results["startup_successful"]:
        print("❌ Startup validation failed!")
        print("Issues detected:")
        for warning in validation_results["warnings"]:
            print(f"  ⚠️ {warning}")
        
        print("\n🔧 To fix these issues:")
        print("1. Run database migrations in order:")
        print("   psql -d your_db -f migrations/001_initial_schema.sql")
        print("   psql -d your_db -f migrations/002_add_avatar_usage.sql")
        print("   psql -d your_db -f migrations/003_add_service_tokens.sql")
        print("   psql -d your_db -f migrations/004_add_indexes_constraints.sql")
        print("   psql -d your_db -f migrations/005_add_schema_migrations.sql")
        return
    
    print("✅ Database validation passed!")
    
    # Step 3: Initialize repositories
    print("\n3️⃣ Initializing repositories...")
    try:
        user_repo = UserRepository(db_client)
        session_repo = SessionRepository(db_client)
        message_repo = MessageRepository(db_client)
        usage_repo = UsageRepository(db_client)
        
        print(f"✅ UserRepository -> table: {user_repo.table_name}")
        print(f"✅ SessionRepository -> table: {session_repo.table_name}")
        print(f"✅ MessageRepository -> table: {message_repo.table_name}")
        print("✅ All repositories initialized")
    except Exception as e:
        print(f"❌ Failed to initialize repositories: {e}")
        return
    
    # Step 4: Demonstrate real usage
    print("\n4️⃣ Demonstrating real application usage...")
    
    try:
        # Create a user (uses migration-created 'users' table)
        print("\n👤 Creating user...")
        user_data = {
            "email": "demo@oprina.ai",
            "display_name": "Demo User",
            "preferences": {"theme": "dark", "language": "en"},
            "timezone": "UTC"
        }
        
        user = await user_repo.create_user(user_data)
        print(f"✅ User created: {user['email']} (ID: {user['id'][:8]}...)")
        
        # Create a chat session (uses migration-created 'sessions' table)
        print("\n💬 Creating chat session...")
        session_data = {
            "user_id": user["id"],
            "session_name": "Gmail Help Session",
            "agent_type": "gmail_agent",
            "context_data": {"initial_request": "Help me organize my emails"}
        }
        
        session = await session_repo.create_session(session_data)
        print(f"✅ Session created: {session['session_name']} (ID: {session['id'][:8]}...)")
        
        # Create a message (uses migration-created 'messages' table)
        print("\n📝 Creating message...")
        message_data = {
            "session_id": session["id"],
            "role": "user",
            "content": "Can you help me organize my Gmail inbox?",
            "message_index": 1
        }
        
        message = await message_repo.create_message(message_data)
        print(f"✅ Message created: '{message['content'][:30]}...' (ID: {message['id'][:8]}...)")
        
        # Check avatar usage quota (uses migration-created avatar tables)
        print("\n🎭 Checking avatar usage quota...")
        quota_status = await usage_repo.check_quota_limits(user["id"])
        print(f"✅ Quota check: {quota_status['used_minutes']}/{quota_status['total_limit_minutes']} minutes used")
        print(f"   Can create session: {quota_status['can_create_session']}")
        print(f"   Usage percentage: {quota_status['usage_percentage']}%")
        
        print("\n🔗 Migration -> Repository Connection Verified:")
        print("   ✅ Migration 001 created 'users' table -> UserRepository works")
        print("   ✅ Migration 001 created 'sessions' table -> SessionRepository works")
        print("   ✅ Migration 001 created 'messages' table -> MessageRepository works")
        print("   ✅ Migration 002 created avatar tables -> UsageRepository works")
        
    except Exception as e:
        print(f"❌ Application usage failed: {e}")
        print("\nThis usually means:")
        print("1. Database migrations haven't been run")
        print("2. Table names in repositories don't match migration schema")
        print("3. Required columns are missing from tables")
        return
    
    print("\n🎉 SUCCESS: Complete integration working!")
    print("=" * 50)
    print("Your migration files have successfully created the database schema")
    print("that your repository classes expect to work with.")


if __name__ == "__main__":
    asyncio.run(main()) 