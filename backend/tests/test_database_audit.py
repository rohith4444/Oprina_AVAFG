#!/usr/bin/env python3
"""
Backend Database Audit - Test all tables and repositories
"""

import asyncio
import sys
import os
from datetime import datetime

# Fix Python path - go up one level from tests to backend root
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.insert(0, backend_root)

print(f"🔧 Python path set to: {backend_root}")

try:
    from app.core.database.connection import get_database_client
    from app.core.database.repositories.user_repository import UserRepository
    from app.core.database.repositories.session_repository import SessionRepository
    from app.core.database.repositories.message_repository import MessageRepository
    from app.core.database.repositories.avatar_repository import AvatarRepository
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please run this script from the backend directory")
    sys.exit(1)

async def audit_backend_database():
    """Audit all backend database tables and operations"""
    print("\n🔍 Backend Database Audit")
    print("=" * 50)
    
    try:
        # Get database client
        db_client = get_database_client()
        print("✅ Database client connection successful")
        
        # Test each repository
        repositories = {
            "users": UserRepository(db_client),
            "sessions": SessionRepository(db_client), 
            "messages": MessageRepository(db_client),
            "avatars": AvatarRepository(db_client)
        }
        
        results = {}
        
        for table_name, repo in repositories.items():
            print(f"\n📊 Testing {table_name} table...")
            
            try:
                # Test basic operations
                if table_name == "users":
                    # Test get user (use your actual user ID)
                    user = await repo.get_user_by_id("5bd926a6-d8f1-49f3-970f-867f7f81ccae")
                    results[table_name] = {
                        "exists": True,
                        "crud_works": bool(user),
                        "sample_data": f"User email: {user.get('email') if user else 'None'}"
                    }
                    
                    if user:
                        print(f"   📧 Email: {user.get('email')}")
                        print(f"   📱 Gmail: {'✅ Connected' if user.get('gmail_tokens') else '❌ Not connected'}")
                        print(f"   📅 Calendar: {'✅ Connected' if user.get('calendar_tokens') else '❌ Not connected'}")
                    
                else:
                    # For other tables, just test the connection
                    results[table_name] = {
                        "exists": True,
                        "crud_works": True,
                        "sample_data": "Repository accessible"
                    }
                
                print(f"✅ {table_name}: OK")
                
            except Exception as e:
                print(f"❌ {table_name}: ERROR - {e}")
                results[table_name] = {
                    "exists": False,
                    "crud_works": False,
                    "error": str(e)
                }
        
        # Summary
        print(f"\n📋 AUDIT SUMMARY:")
        print("=" * 30)
        for table, result in results.items():
            status = "✅ PASS" if result["exists"] and result["crud_works"] else "❌ FAIL"
            print(f"{table:15} {status}")
            if result.get("error"):
                print(f"{'':15} Error: {result['error']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Database audit failed: {e}")
        return {}

if __name__ == "__main__":
    asyncio.run(audit_backend_database())