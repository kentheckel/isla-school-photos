#!/usr/bin/env python3
"""
Test script that uploads photos and then scans the library to verify they actually made it.
This will help us debug why photos aren't appearing in Google Photos.
"""

import os
import sys
import yaml
import json
from datetime import datetime, timedelta
from google_photos_uploader import GooglePhotosUploader
from email_monitor import EmailMonitor

def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_upload_and_verify():
    """Test uploading photos and verifying they appear in the library"""
    
    print("=" * 80)
    print("🔍 GOOGLE PHOTOS UPLOAD & VERIFICATION TEST")
    print("=" * 80)
    
    # Load configuration
    config = load_config()
    
    # Step 1: Get some test photos
    print("\n📸 Step 1: Getting test photos...")
    email_monitor = EmailMonitor(config)
    
    try:
        mail = email_monitor.connect_to_email()
        if not mail:
            print("❌ Failed to connect to email")
            return False
        
        # Search for recent school emails
        email_ids = email_monitor.search_school_emails(mail, days_back=7)
        
        if not email_ids:
            print("ℹ️  No school emails found, using existing photos...")
            # Look for existing photos in temp_downloads
            temp_dir = "temp_downloads"
            if os.path.exists(temp_dir):
                existing_photos = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                if existing_photos:
                    print(f"✅ Found {len(existing_photos)} existing photos to test with")
                    test_photos = existing_photos[:3]  # Test with first 3 photos
                else:
                    print("❌ No photos available for testing")
                    return False
            else:
                print("❌ No photos available for testing")
                return False
        else:
            print(f"✅ Found {len(email_ids)} school emails")
            # Download photos from emails
            photos = email_monitor.download_attachments(mail, email_ids)
            if not photos:
                print("❌ No photos downloaded from emails")
                return False
            test_photos = photos[:3]  # Test with first 3 photos
        
        print(f"📸 Testing with {len(test_photos)} photos:")
        for i, photo in enumerate(test_photos, 1):
            filename = os.path.basename(photo)
            size = os.path.getsize(photo)
            print(f"  {i}. {filename} ({size:,} bytes)")
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ Error getting test photos: {str(e)}")
        return False
    
    # Step 2: Initialize Google Photos uploader
    print("\n🔐 Step 2: Authenticating with Google Photos...")
    uploader = GooglePhotosUploader(config)
    
    if not uploader.authenticate():
        print("❌ Failed to authenticate with Google Photos")
        return False
    
    print("✅ Successfully authenticated with Google Photos")
    
    # Step 3: Get library state BEFORE upload
    print("\n📚 Step 3: Checking library state BEFORE upload...")
    try:
        # Get recent photos from library
        request = uploader.service.mediaItems().list(pageSize=10)
        response_before = request.execute()
        photos_before = response_before.get('mediaItems', [])
        
        print(f"📊 Library state before upload:")
        print(f"  - Recent photos count: {len(photos_before)}")
        if photos_before:
            print(f"  - Most recent photo: {photos_before[0].get('filename', 'Unknown')}")
            print(f"  - Most recent photo ID: {photos_before[0].get('id', 'Unknown')}")
        else:
            print("  - No photos found in library")
            
    except Exception as e:
        print(f"⚠️  Could not check library state before upload: {str(e)}")
        photos_before = []
    
    # Step 4: Upload test photos
    print(f"\n⬆️  Step 4: Uploading {len(test_photos)} test photos...")
    
    uploaded_tokens = []
    for i, photo_path in enumerate(test_photos, 1):
        print(f"\n📤 Uploading photo {i}/{len(test_photos)}: {os.path.basename(photo_path)}")
        
        try:
            # Upload the photo
            token = uploader.upload_photo(photo_path)
            if token:
                uploaded_tokens.append(token)
                print(f"✅ Upload successful, token: {token[:50]}...")
            else:
                print(f"❌ Upload failed for {os.path.basename(photo_path)}")
                
        except Exception as e:
            print(f"❌ Upload error for {os.path.basename(photo_path)}: {str(e)}")
    
    print(f"\n📊 Upload Summary:")
    print(f"  - Photos attempted: {len(test_photos)}")
    print(f"  - Upload tokens received: {len(uploaded_tokens)}")
    
    if not uploaded_tokens:
        print("❌ No photos were successfully uploaded")
        return False
    
    # Step 5: Wait a moment for photos to process
    print(f"\n⏳ Step 5: Waiting for photos to process in Google Photos...")
    import time
    time.sleep(5)  # Wait 5 seconds for processing
    
    # Step 6: Check library state AFTER upload
    print(f"\n🔍 Step 6: Checking library state AFTER upload...")
    try:
        # Get recent photos from library
        request = uploader.service.mediaItems().list(pageSize=20)
        response_after = request.execute()
        photos_after = response_after.get('mediaItems', [])
        
        print(f"📊 Library state after upload:")
        print(f"  - Recent photos count: {len(photos_after)}")
        
        # Compare before and after
        new_photos = len(photos_after) - len(photos_before)
        print(f"  - New photos detected: {new_photos}")
        
        if photos_after:
            print(f"\n📸 Most recent photos in library:")
            for i, photo in enumerate(photos_after[:5], 1):
                filename = photo.get('filename', 'Unknown')
                photo_id = photo.get('id', 'Unknown')
                creation_time = photo.get('mediaMetadata', {}).get('creationTime', 'Unknown')
                print(f"  {i}. {filename}")
                print(f"     ID: {photo_id}")
                print(f"     Created: {creation_time}")
                print()
        else:
            print("  - No photos found in library")
            
    except Exception as e:
        print(f"❌ Could not check library state after upload: {str(e)}")
        return False
    
    # Step 7: Try to find our specific uploaded photos
    print(f"\n🔍 Step 7: Searching for our uploaded photos...")
    try:
        # Search for photos uploaded in the last few minutes
        now = datetime.now()
        recent_time = now - timedelta(minutes=10)
        
        found_our_photos = []
        for photo in photos_after:
            creation_time_str = photo.get('mediaMetadata', {}).get('creationTime', '')
            if creation_time_str:
                try:
                    # Parse the creation time
                    creation_time = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))
                    if creation_time > recent_time:
                        found_our_photos.append(photo)
                except:
                    pass
        
        print(f"📊 Photos uploaded in last 10 minutes: {len(found_our_photos)}")
        
        if found_our_photos:
            print(f"✅ Found our uploaded photos!")
            for i, photo in enumerate(found_our_photos, 1):
                filename = photo.get('filename', 'Unknown')
                photo_id = photo.get('id', 'Unknown')
                print(f"  {i}. {filename} (ID: {photo_id})")
        else:
            print(f"❌ Could not find our uploaded photos in the library")
            print(f"   This suggests the uploads may not have been processed correctly")
            
    except Exception as e:
        print(f"❌ Error searching for our photos: {str(e)}")
    
    # Step 8: Test album functionality
    print(f"\n📁 Step 8: Testing album functionality...")
    try:
        # Try to list albums
        albums_request = uploader.service.albums().list(pageSize=10)
        albums_response = albums_request.execute()
        albums = albums_response.get('albums', [])
        
        print(f"📊 Albums in library: {len(albums)}")
        for i, album in enumerate(albums[:5], 1):
            title = album.get('title', 'Unknown')
            album_id = album.get('id', 'Unknown')
            print(f"  {i}. {title} (ID: {album_id})")
            
    except Exception as e:
        print(f"⚠️  Could not list albums: {str(e)}")
    
    print(f"\n" + "=" * 80)
    print(f"🏁 TEST COMPLETE")
    print(f"=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_upload_and_verify()
    sys.exit(0 if success else 1)
