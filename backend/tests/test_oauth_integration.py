#!/usr/bin/env python3
"""
Test script for OAuth integration with Supabase authentication.
Tests the complete flow: Frontend → Backend → OAuth endpoints.
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

def test_oauth_status(token: str):
    """Test OAuth status endpoint with Supabase token"""
    print("🔧 Test 1: Testing OAuth status endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/oauth/status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OAuth status endpoint successful")
            print(f"   Gmail connected: {data.get('gmail', {}).get('connected', False)}")
            print(f"   Calendar connected: {data.get('calendar', {}).get('connected', False)}")
            return True
        else:
            print(f"❌ OAuth status failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OAuth status test failed: {str(e)}")
        return False

def test_oauth_connect_url(token: str, service: str):
    """Test OAuth connect URL generation"""
    print(f"🔧 Test 2: Testing {service} connect URL generation...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/oauth/connect/{service}", headers=headers, allow_redirects=False)
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')
            print(f"✅ {service} connect URL generated successfully")
            print(f"   Redirect URL starts with: {redirect_url[:60]}...")
            
            # Check if it's a valid Google OAuth URL
            if "accounts.google.com/o/oauth2" in redirect_url:
                print(f"   ✅ Valid Google OAuth URL")
                return True
            else:
                print(f"   ❌ Invalid OAuth URL")
                return False
        else:
            print(f"❌ {service} connect failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {service} connect test failed: {str(e)}")
        return False

def test_oauth_endpoints(token: str):
    """Test all OAuth endpoints"""
    print("🚀 Testing OAuth Integration with Supabase Authentication")
    print("=" * 70)
    
    # Test status endpoint
    status_ok = test_oauth_status(token)
    print()
    
    # Test Gmail connect
    gmail_ok = test_oauth_connect_url(token, "gmail")
    print()
    
    # Test Calendar connect
    calendar_ok = test_oauth_connect_url(token, "calendar")
    print()
    
    print("=" * 70)
    
    if status_ok and gmail_ok and calendar_ok:
        print("🎉 ALL OAUTH TESTS PASSED!")
        print("✅ Supabase authentication working with OAuth endpoints")
        print("✅ Gmail connection URL generation working")
        print("✅ Calendar connection URL generation working")
        print("\n🚀 Ready for frontend testing!")
        return True
    else:
        print("❌ Some OAuth tests failed")
        print("Please check your backend configuration and Supabase auth setup")
        return False

def get_token_from_user():
    """Get Supabase token from user input"""
    print("\n📋 To get your Supabase token:")
    print("1. Open your browser and login to the frontend")
    print("2. Open Browser DevTools (F12)")
    print("3. Go to Application/Storage tab")
    print("4. Find 'sb-<project-id>-auth-token' in localStorage")
    print("5. Copy the 'access_token' value")
    
    token = input("\n🔑 Paste your Supabase access token here: ").strip()
    
    if not token:
        print("❌ No token provided")
        return None
    
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]  # Remove quotes if present
    
    return token

def main():
    """Main test function"""
    print("🔧 OAuth Integration Test with Supabase Authentication")
    print("This script tests that your backend OAuth endpoints work with Supabase tokens")
    
    # Get token from user
    token = get_token_from_user()
    if not token:
        return False
    
    # Run tests
    return test_oauth_endpoints(token)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)