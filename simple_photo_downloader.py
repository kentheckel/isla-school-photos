#!/usr/bin/env python3
"""
Simple School Photo Downloader
Downloads photos from school emails and saves them locally with proper organization.
"""

import os
import sys
import yaml
from datetime import datetime
from email_monitor import EmailMonitor

def main():
    """Main function to download school photos."""
    print("=" * 60)
    print("Simple School Photo Downloader")
    print("=" * 60)
    
    # Load configuration
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: config.yaml not found")
        return False
    
    # Create organized output directory
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"school_photos_{today}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Saving photos to: {output_dir}/")
    print()
    
    # Initialize email monitor
    email_monitor = EmailMonitor(config)
    
    try:
        # Connect to email
        print("📧 Connecting to email...")
        mail = email_monitor.connect_to_email()
        if not mail:
            print("❌ Failed to connect to email")
            return False
        
        # Search for school emails
        print("🔍 Searching for school emails...")
        email_ids = email_monitor.search_school_emails(mail, days_back=7)
        
        if not email_ids:
            print("ℹ️  No school emails found")
            return True
        
        print(f"✅ Found {len(email_ids)} school emails")
        print()
        
        # Process all emails at once
        print("📸 Downloading photos from all emails...")
        photos = email_monitor.download_attachments(mail, email_ids)
        
        if photos:
            print(f"✅ Downloaded {len(photos)} photos total")
            
            # Move photos to organized directory
            for i, photo_path in enumerate(photos, 1):
                filename = os.path.basename(photo_path)
                # Create a cleaner filename
                clean_filename = f"photo_{i:02d}_{filename}"
                new_path = os.path.join(output_dir, clean_filename)
                
                # Move the file
                os.rename(photo_path, new_path)
                print(f"💾 Saved: {clean_filename}")
            
            total_photos = len(photos)
        else:
            print("ℹ️  No photos found in any emails")
            total_photos = 0
        
        # Summary
        print("=" * 60)
        print("✅ Download Complete!")
        print(f"📸 Total photos downloaded: {total_photos}")
        print(f"📁 Photos saved to: {output_dir}/")
        print()
        print("📋 Next steps:")
        print("1. Open the photos folder on your computer")
        print("2. Select all photos")
        print("3. Right-click and choose 'Upload to Google Photos'")
        print("4. Or drag and drop them into Google Photos in your browser")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    finally:
        if 'mail' in locals():
            mail.logout()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
