#!/usr/bin/env python3
"""
Google Photos API Setup Helper

This script helps you set up the Google Photos API authentication
by guiding you through the OAuth2 flow and testing the connection.
"""

import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Google Photos API scopes
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']


def setup_google_photos_auth():
    """
    Set up Google Photos API authentication.
    
    This function guides the user through the OAuth2 flow and saves
    the credentials for future use.
    """
    print("=" * 60)
    print("Google Photos API Setup")
    print("=" * 60)
    
    # Check if credentials file exists
    credentials_file = "google_photos_credentials.json"
    token_file = "google_photos_token.json"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        print("\nTo fix this:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Photos Library API")
        print("4. Go to APIs & Services > Credentials")
        print("5. Create OAuth client ID (Desktop application)")
        print("6. Download the JSON file and save it as 'google_photos_credentials.json'")
        return False
    
    print(f"✅ Found credentials file: {credentials_file}")
    
    # Start OAuth flow
    try:
        print("\n🔄 Starting OAuth2 authentication flow...")
        print("A browser window will open for you to log in and authorize the application.")
        
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print(f"✅ Authentication successful! Credentials saved to: {token_file}")
        
        # Test the connection
        print("\n🧪 Testing Google Photos API connection...")
        service = build('photoslibrary', 'v1', credentials=creds)
        
        # Try to list albums to test the connection
        albums_response = service.albums().list(pageSize=1).execute()
        albums = albums_response.get('albums', [])
        
        print(f"✅ Successfully connected to Google Photos API!")
        print(f"   Found {len(albums)} albums in your Google Photos")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return False


def test_existing_auth():
    """
    Test existing Google Photos authentication.
    
    Returns:
        bool: True if authentication is valid, False otherwise
    """
    token_file = "google_photos_token.json"
    
    if not os.path.exists(token_file):
        print(f"❌ Token file not found: {token_file}")
        return False
    
    try:
        print("🔄 Testing existing authentication...")
        
        # Load existing credentials
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Refresh token if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                creds.refresh(Request())
                
                # Save refreshed credentials
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                print("✅ Token refreshed successfully")
            else:
                print("❌ Token is invalid and cannot be refreshed")
                return False
        
        # Test the connection
        service = build('photoslibrary', 'v1', credentials=creds)
        albums_response = service.albums().list(pageSize=1).execute()
        albums = albums_response.get('albums', [])
        
        print(f"✅ Authentication is valid!")
        print(f"   Found {len(albums)} albums in your Google Photos")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")
        return False


def main():
    """
    Main function to set up or test Google Photos authentication.
    """
    print("Google Photos API Setup Helper")
    print("This script helps you set up authentication with Google Photos API.\n")
    
    # Check if we already have valid authentication
    if test_existing_auth():
        print("\n🎉 You're all set! Google Photos authentication is working.")
        print("You can now run the main school photo downloader script.")
        return
    
    print("\nSetting up new Google Photos authentication...")
    
    if setup_google_photos_auth():
        print("\n🎉 Setup complete! You can now run the school photo downloader.")
    else:
        print("\n❌ Setup failed. Please check the error messages above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
