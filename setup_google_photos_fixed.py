#!/usr/bin/env python3
"""
Fixed Google Photos API Setup
This script helps set up Google Photos API with proper permissions.
"""

import os
import json
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Google Photos API scopes - these are the correct ones
SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.appendonly'
]

def setup_google_photos():
    """Set up Google Photos API with proper authentication."""
    
    print("🔧 Google Photos API Setup (Fixed Version)")
    print("=" * 50)
    print()
    
    # Check if credentials file exists
    credentials_file = "google_photos_credentials.json"
    token_file = "google_photos_token.json"
    
    if not os.path.exists(credentials_file):
        print("❌ Error: google_photos_credentials.json not found")
        print()
        print("📋 Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the 'Photos Library API'")
        print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'")
        print("5. Choose 'Desktop application'")
        print("6. Download the JSON file and save it as 'google_photos_credentials.json'")
        print("7. Run this script again")
        return False
    
    print("✅ Found credentials file")
    print()
    
    # Load credentials
    try:
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        # Extract client info
        client_info = creds_data.get('installed', creds_data.get('web', {}))
        client_id = client_info.get('client_id')
        client_secret = client_info.get('client_secret')
        
        print(f"📋 Project: {creds_data.get('project_id', 'Unknown')}")
        print(f"📋 Client ID: {client_id[:20]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False
    
    # Set up OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file, 
        SCOPES,
        redirect_uri='http://localhost:8080'
    )
    
    creds = None
    
    # Check if we have existing valid credentials
    if os.path.exists(token_file):
        print("🔄 Loading existing credentials...")
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.valid:
                print("✅ Using existing valid credentials")
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print("❌ Invalid credentials, need to re-authenticate")
                creds = None
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            creds = None
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        print("🔐 Starting OAuth authentication...")
        print("📱 This will open your browser for authentication")
        print()
        
        try:
            creds = flow.run_local_server(port=8080)
            print("✅ Authentication successful!")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    # Save credentials
    try:
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 Credentials saved to {token_file}")
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False
    
    # Test the API connection
    print()
    print("🧪 Testing Google Photos API connection...")
    
    try:
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        
        # Try to list some media items to test the connection
        request = service.mediaItems().list(pageSize=1)
        response = request.execute()
        
        print("✅ Google Photos API connection successful!")
        print(f"📊 Found {len(response.get('mediaItems', []))} media items in your library")
        
        # Test album listing
        try:
            albums_request = service.albums().list(pageSize=1)
            albums_response = albums_request.execute()
            print("✅ Album access working!")
        except Exception as e:
            print(f"⚠️  Album access issue: {e}")
            print("   (This is normal - we'll upload to main library)")
        
        print()
        print("🎉 Google Photos API setup complete!")
        print("✅ You can now use the automatic photo uploader")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print()
        print("🔧 Troubleshooting steps:")
        print("1. Make sure 'Photos Library API' is enabled in Google Cloud Console")
        print("2. Check that your OAuth consent screen is properly configured")
        print("3. Try deleting google_photos_token.json and running this again")
        return False

if __name__ == "__main__":
    success = setup_google_photos()
    if success:
        print("\n🚀 Ready to use automatic photo upload!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
