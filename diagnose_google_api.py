#!/usr/bin/env python3
"""
Google Photos API Diagnostic Tool
This helps diagnose what's wrong with the Google Photos API setup.
"""

import json
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Test scopes
SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.appendonly'
]

def diagnose_api():
    """Diagnose Google Photos API issues."""
    
    print("🔍 Google Photos API Diagnostic Tool")
    print("=" * 40)
    print()
    
    # Check credentials file
    try:
        with open('google_photos_credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        client_info = creds_data.get('installed', creds_data.get('web', {}))
        client_id = client_info.get('client_id')
        project_id = creds_data.get('project_id', 'Unknown')
        
        print(f"✅ Credentials file found")
        print(f"📋 Project ID: {project_id}")
        print(f"📋 Client ID: {client_id[:20]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False
    
    # Test authentication
    print("🔐 Testing authentication...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'google_photos_credentials.json', 
            SCOPES,
            redirect_uri='http://localhost:8080'
        )
        
        # Check if we have existing token
        try:
            creds = Credentials.from_authorized_user_file('google_photos_token.json', SCOPES)
            if creds and creds.valid:
                print("✅ Using existing valid credentials")
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing credentials...")
                creds.refresh(Request())
            else:
                print("❌ Invalid credentials")
                creds = None
        except:
            print("❌ No valid token found")
            creds = None
        
        if not creds or not creds.valid:
            print("🔐 Starting fresh authentication...")
            creds = flow.run_local_server(port=8080)
        
        print("✅ Authentication successful")
        print()
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Test API access
    print("🧪 Testing API access...")
    
    # Test 1: Basic API call
    try:
        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=1',
            headers=headers
        )
        
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Photos Library API is working!")
            print(f"📸 Found {len(data.get('mediaItems', []))} photos")
        elif response.status_code == 403:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"❌ API Error: {error_msg}")
            
            if "insufficient authentication scopes" in error_msg:
                print()
                print("🔧 This means:")
                print("1. Photos Library API is not enabled in Google Cloud Console")
                print("2. Or the OAuth consent screen is not configured properly")
                print()
                print("📋 To fix this:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Select your project")
                print("3. Go to 'APIs & Services' → 'Library'")
                print("4. Search for 'Photos Library API' and ENABLE it")
                print("5. Go to 'APIs & Services' → 'OAuth consent screen'")
                print("6. Make sure it's configured and add your email as a test user")
                
        else:
            print(f"❌ Unexpected error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Check if we can at least upload
    print()
    print("🧪 Testing upload capability...")
    
    try:
        # Try to get upload URL (this should work even if we can't list photos)
        upload_response = requests.post(
            'https://photoslibrary.googleapis.com/v1/uploads',
            headers={
                'Authorization': f'Bearer {creds.token}',
                'Content-Type': 'application/octet-stream',
                'X-Goog-Upload-Protocol': 'raw',
                'X-Goog-Upload-File-Name': 'test.jpg'
            },
            data=b'test'
        )
        
        if upload_response.status_code == 200:
            print("✅ Upload capability working!")
        else:
            print(f"❌ Upload test failed: {upload_response.status_code}")
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")
    
    return True

if __name__ == "__main__":
    diagnose_api()
