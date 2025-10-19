#!/usr/bin/env python3
"""
Helper script to prepare GitHub secrets for the school photos downloader.
This script will help you format the secrets correctly for GitHub Actions.
"""

import json
import os
import sys
from pathlib import Path

def load_config():
    """Load the local configuration file"""
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        print("Please make sure you're running this from the project directory.")
        return None
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_google_credentials():
    """Load Google Photos credentials"""
    creds_path = "google_photos_credentials.json"
    if not os.path.exists(creds_path):
        print(f"❌ Google Photos credentials not found: {creds_path}")
        return None
    
    with open(creds_path, 'r') as f:
        return json.load(f)

def main():
    print("🔧 GitHub Secrets Setup Helper")
    print("=" * 50)
    print()
    
    # Load configuration
    print("📋 Loading local configuration...")
    config = load_config()
    if not config:
        return False
    
    # Load Google credentials
    print("🔑 Loading Google Photos credentials...")
    google_creds = load_google_credentials()
    if not google_creds:
        return False
    
    print("✅ Configuration loaded successfully!")
    print()
    
    # Display the secrets that need to be added to GitHub
    print("🔐 GitHub Secrets to Add:")
    print("=" * 30)
    print()
    
    # Email credentials
    email_config = config['email']
    print("1. EMAIL_USERNAME")
    print(f"   Value: {email_config['username']}")
    print()
    
    print("2. EMAIL_PASSWORD")
    print(f"   Value: {email_config['password']}")
    print()
    
    print("3. SENDER_EMAIL")
    print(f"   Value: {email_config['sender_email']}")
    print()
    
    # Google Photos credentials
    print("4. GOOGLE_PHOTOS_CREDENTIALS")
    print("   Value: (JSON content below)")
    print("   " + "=" * 50)
    print(json.dumps(google_creds, indent=2))
    print("   " + "=" * 50)
    print()
    
    # Instructions
    print("📝 How to Add These Secrets:")
    print("=" * 30)
    print("1. Go to your GitHub repository")
    print("2. Click 'Settings' tab")
    print("3. Click 'Secrets and variables' → 'Actions'")
    print("4. Click 'New repository secret' for each secret above")
    print("5. Copy the name and value exactly as shown")
    print("6. Click 'Add secret'")
    print()
    
    print("🧪 Testing the Setup:")
    print("=" * 20)
    print("After adding all secrets:")
    print("1. Go to 'Actions' tab in your repository")
    print("2. Find 'School Photos Downloader' workflow")
    print("3. Click 'Run workflow' to test manually")
    print()
    
    print("📚 For detailed instructions, see: GITHUB_ACTIONS_SETUP.md")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
