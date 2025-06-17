#!/usr/bin/env python3
"""
Test script for Supabase authentication integration.
Run this script to validate Phase 1 implementation.

Usage:
    python test_supabase_auth.py
    
Requirements:
    1. Backend server running on localhost:8000
    2. Frontend running with user logged in
    3. Supabase token copied from browser
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

def test_connection():
    """Test 1: Basic Supabase connection"""
    print("🔧 Test 1: Testing Supabase connection...")
    
    try:
        response = requests.get(f"{API_BASE}/test/supabase/connection")
        data = response.json()
        
        if data.get("connected"):
            print("✅ Supabase connection successful")
            return True
        else:
            print(f"❌ Supabase connection failed: {data.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def test_manual_token(token: str):
    """Test 2: Manual token validation"""
    print("🔧 Test 2: Testing manual token validation...")
    
    try:
        response = requests.post(
            f"{API_BASE}/test/supabase/manual-token-test",
            json={"token": token}
        )
        data = response.json()
        
        if data.get("token_valid"):
            print("✅ Manual token validation successful")
            print(f"   User: {data['user_data']['email']}")
            print(f"   ID: {data['user_data']['id']}")
            return True
        else:
            print(f"❌ Manual token validation failed: {data.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Manual token test failed: {str(e)}")
        return False

def test_authenticated_endpoint(token: str):
    """Test 3: Authenticated endpoint with dependency injection"""
    print("🔧 Test 3: Testing authenticated endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/test/supabase/validate-token",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Authenticated endpoint successful")
            print(f"   User: {data['user']['email']}")
            print(f"   Backend sync: {data['user']['backend_sync']}")
            return True
        else:
            print(f"❌ Authenticated endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Authenticated endpoint test failed: {str(e)}")
        return False

def test_user_sync(token: str):
    """Test 4: User synchronization between Supabase and backend"""
    print("🔧 Test 4: Testing user synchronization...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/test/supabase/user-info",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            backend_user = data.get("backend_user", {})
            
            if backend_user.get("exists_in_backend"):
                print("✅ User synchronization successful")
                print(f"   Supabase ID: {data['supabase_user']['id']}")
                print(f"   Backend ID: {backend_user['id']}")
                print(f"   Sync Status: {data['sync_status']}")
                return True
            else:
                print("❌ User not synchronized to backend")
                return False
        else:
            print(f"❌ User sync test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ User sync test failed: {str(e)}")
        return False

def test_optional_auth():
    """Test 5: Optional authentication (no token)"""
    print("🔧 Test 5: Testing optional authentication...")
    
    try:
        response = requests.get(f"{API_BASE}/test/supabase/optional-auth")
        data = response.json()
        
        if data.get("status") == "anonymous":
            print("✅ Optional auth (no token) working")
            return True
        else:
            print(f"❌ Optional auth test failed: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Optional auth test failed: {str(e)}")
        return False

def get_token_from_user():
    """Get Supabase token from user input"""
    print("\n📋 To get your Supabase token:")
    print("1. Open your browser and login to the frontend")
    print("2. Open Browser DevTools (F12)")
    print("3. Go to Application/Storage tab")
    print("4. Find 'sb-<project-id>-auth-token' in localStorage")
    print("5. Copy the 'access_token' value")
    print("\nAlternatively:")
    print("1. In DevTools Console, run: localStorage.getItem('sb-<project-id>-auth-token')")
    print("2. Copy the access_token from the JSON response")
    
    token = input("\n🔑 Paste your Supabase access token here: ").strip()
    
    if not token:
        print("❌ No token provided")
        return None
    
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]  # Remove quotes if present
    
    return token

def main():
    """Run all tests"""
    print("🚀 Starting Supabase Authentication Tests for Phase 1")
    print("=" * 60)
    
    # Test 1: Connection
    if not test_connection():
        print("\n❌ Basic connection failed. Check your Supabase configuration.")
        return False
    
    print()
    
    # Get token from user
    token = get_token_from_user()
    if not token:
        return False
    
    print("\n" + "=" * 60)
    
    # Test 2: Manual token validation
    if not test_manual_token(token):
        print("\n❌ Token validation failed. Check your token and JWT secret.")
        return False
    
    print()
    
    # Test 3: Authenticated endpoint
    if not test_authenticated_endpoint(token):
        print("\n❌ Authenticated endpoint failed. Check dependency injection.")
        return False
    
    print()
    
    # Test 4: User sync
    if not test_user_sync(token):
        print("\n❌ User sync failed. Check user repository and database.")
        return False
    
    print()
    
    # Test 5: Optional auth
    if not test_optional_auth():
        print("\n❌ Optional auth failed. Check optional dependency.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! Phase 1 implementation is working correctly.")
    print("\n✅ Supabase token validation: Working")
    print("✅ User synchronization: Working") 
    print("✅ Backend integration: Working")
    print("✅ Dependency injection: Working")
    print("\n🚀 Ready to proceed to Phase 2!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)