#!/usr/bin/env python3
"""
Debug script to check Supabase configuration with special character handling
"""

import os
import sys
sys.path.append('.')

try:
    from app.config import get_settings
    settings = get_settings()
    
    print("🔧 Checking Supabase Configuration...")
    print("=" * 50)
    
    # Check each required variable
    variables = {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": settings.SUPABASE_SERVICE_KEY, 
        "SUPABASE_ANON_KEY": settings.SUPABASE_ANON_KEY,
        "SUPABASE_JWT_SECRET": settings.SUPABASE_JWT_SECRET
    }
    
    all_good = True
    
    for var_name, var_value in variables.items():
        if var_value and var_value.strip():
            print(f"✅ {var_name}: Set (length: {len(var_value)})")
            
            # Special check for JWT secret with special characters
            if var_name == "SUPABASE_JWT_SECRET":
                special_chars = ["/", "+", "="]
                found_chars = [char for char in special_chars if char in var_value]
                if found_chars:
                    print(f"   📝 Contains special characters: {found_chars}")
                    print(f"   📝 First 10 chars: {var_value[:10]}...")
                    print(f"   📝 Last 10 chars: ...{var_value[-10:]}")
        else:
            print(f"❌ {var_name}: Missing or empty")
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("✅ All Supabase configuration variables are set!")
        
        # Test JWT secret specifically
        print("\n🔧 Testing JWT Secret handling...")
        try:
            import jwt
            
            # Create a test token with the JWT secret
            test_payload = {"test": "data", "exp": 9999999999}
            
            # Clean the JWT secret - remove quotes if they exist
            jwt_secret = settings.SUPABASE_JWT_SECRET.strip().strip('"').strip("'")
            print(f"   📝 Cleaned JWT secret length: {len(jwt_secret)}")
            
            # Test encoding
            test_token = jwt.encode(test_payload, jwt_secret, algorithm="HS256")
            print("   ✅ JWT encoding successful")
            
            # Test decoding
            decoded = jwt.decode(test_token, jwt_secret, algorithms=["HS256"])
            print("   ✅ JWT decoding successful")
            
        except Exception as e:
            print(f"   ❌ JWT secret test failed: {e}")
        
        # Test Supabase client creation
        print("\n🔧 Testing Supabase client creation...")
        try:
            from app.utils.supabase_auth import get_supabase_client
            client = get_supabase_client()
            if client:
                print("   ✅ Supabase client created successfully!")
            else:
                print("   ❌ Supabase client creation failed")
        except Exception as e:
            print(f"   ❌ Error creating Supabase client: {e}")
    else:
        print("❌ Please set missing configuration variables in your .env file")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
except Exception as e:
    print(f"❌ Error: {e}")