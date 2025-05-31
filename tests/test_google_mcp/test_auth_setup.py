# tests/test_google_mcp/test_auth_setup.py

import os
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

class TestAuthSetup(unittest.TestCase):
    """Test Google API authentication setup using project settings."""
    
    def test_settings_loaded(self):
        """Test that settings load correctly."""
        self.assertIsNotNone(settings.GOOGLE_CLIENT_SECRET_FILE)
        self.assertIsNotNone(settings.GOOGLE_TOKEN_FILE)
        self.assertTrue(len(settings.GOOGLE_API_SCOPES) > 0)
    
    def test_client_secret_exists(self):
        """Test that client secret file exists at configured path."""
        client_secret_path = settings.google_client_secret_path
        
        self.assertTrue(
            os.path.exists(client_secret_path),
            f"Client secret file not found: {client_secret_path}"
        )
        
        # Verify it's a valid JSON file with correct structure
        import json
        with open(client_secret_path, 'r') as f:
            client_secret = json.load(f)
            
            # Accept both 'web' and 'installed' credential types
            if 'installed' in client_secret:
                cred_section = client_secret['installed']
            elif 'web' in client_secret:
                cred_section = client_secret['web']
            else:
                self.fail("JSON must contain either 'web' or 'installed' credentials")
            
            # Verify required fields exist
            self.assertIn('client_id', cred_section)
            self.assertIn('client_secret', cred_section)
            
            print(f"   ✅ Found {list(client_secret.keys())[0]} credentials")
    
    def test_credentials_validation(self):
        """Test settings credential validation method."""
        is_valid = settings.validate_google_credentials()
        self.assertTrue(is_valid, "Google credentials validation failed")
    
    def test_token_directory_will_be_created(self):
        """Test that token directory path is valid."""
        token_path = settings.google_token_path
        token_dir = os.path.dirname(token_path)
        
        # Directory should exist or be creatable
        if not os.path.exists(token_dir):
            # Test that we can create it
            try:
                os.makedirs(token_dir, exist_ok=True)
                self.assertTrue(os.path.exists(token_dir))
            except Exception as e:
                self.fail(f"Cannot create token directory: {e}")

if __name__ == "__main__":
    unittest.main()