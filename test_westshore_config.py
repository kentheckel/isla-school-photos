#!/usr/bin/env python3
"""
Test script for Westshore Montessori School email configuration.

This script helps you test and verify that your email configuration
is working correctly with the Westshore Montessori School email pattern.
"""

import os
import sys
import yaml
from datetime import datetime, timedelta
from school_photo_downloader import SchoolPhotoDownloader


def test_configuration():
    """Test the email configuration for Westshore Montessori School."""
    print("=" * 60)
    print("Westshore Montessori School Configuration Test")
    print("=" * 60)
    
    # Check if config file exists
    config_file = "config_local.yaml"
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        print("Please create config_local.yaml first")
        return False
    
    # Load configuration
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        print(f"✅ Configuration file loaded: {config_file}")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False
    
    # Check email configuration
    print("\n📧 Email Configuration Check:")
    email_config = config.get('email', {})
    
    sender_email = email_config.get('sender_email', '')
    subject_keywords = email_config.get('subject_keywords', [])
    
    print(f"  Sender Email: {sender_email}")
    print(f"  Subject Keywords: {subject_keywords}")
    
    # Validate Westshore Montessori pattern
    expected_subject = "[Westshore Montessori School ]"
    if expected_subject in subject_keywords:
        print(f"  ✅ Subject pattern matches Westshore Montessori: {expected_subject}")
    else:
        print(f"  ⚠️  Subject pattern doesn't match expected: {expected_subject}")
        print(f"     Current: {subject_keywords}")
    
    if sender_email and sender_email != "school@example.com":
        print(f"  ✅ Sender email configured: {sender_email}")
    else:
        print(f"  ⚠️  Sender email needs to be updated from example")
    
    # Test email connection
    print("\n🔌 Testing Email Connection:")
    try:
        downloader = SchoolPhotoDownloader(config_file)
        print("  ✅ SchoolPhotoDownloader initialized successfully")
        
        # Test email connection
        mail = downloader.email_monitor.connect_to_email()
        if mail:
            print("  ✅ Email connection successful")
            
            # Test search for recent emails
            print("\n🔍 Testing Email Search:")
            email_ids = downloader.email_monitor.search_school_emails(mail, days_back=7)
            print(f"  Found {len(email_ids)} emails in the last 7 days")
            
            if email_ids:
                print("  ✅ Emails found - configuration appears to be working")
                
                # Test enhanced filtering
                print("\n🎯 Testing Enhanced Filtering:")
                filtered_ids = downloader._enhanced_email_filtering(mail, email_ids)
                print(f"  {len(filtered_ids)} emails passed the Westshore Montessori filter")
                
                if len(filtered_ids) == 2:
                    print("  ✅ Perfect! Found exactly 2 emails as expected")
                elif len(filtered_ids) > 0:
                    print(f"  ⚠️  Found {len(filtered_ids)} emails (expected 2)")
                else:
                    print("  ⚠️  No emails passed the filter")
            else:
                print("  ℹ️  No emails found in the last 7 days")
                print("     This might be normal if no school emails were sent recently")
            
            # Close connection
            try:
                mail.close()
                mail.logout()
                print("  ✅ Email connection closed")
            except:
                pass
                
        else:
            print("  ❌ Email connection failed")
            print("     Check your email credentials and IMAP settings")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing email configuration: {e}")
        return False
    
    # Test Google Photos configuration
    print("\n📸 Testing Google Photos Configuration:")
    google_config = config.get('google_photos', {})
    credentials_file = google_config.get('credentials_file', 'google_photos_credentials.json')
    token_file = google_config.get('token_file', 'google_photos_token.json')
    
    if os.path.exists(credentials_file):
        print(f"  ✅ Google Photos credentials file found: {credentials_file}")
    else:
        print(f"  ⚠️  Google Photos credentials file not found: {credentials_file}")
        print("     Run 'python setup_google_photos.py' to set up Google Photos")
    
    if os.path.exists(token_file):
        print(f"  ✅ Google Photos token file found: {token_file}")
    else:
        print(f"  ℹ️  Google Photos token file not found: {token_file}")
        print("     This will be created on first run")
    
    print("\n" + "=" * 60)
    print("Configuration Test Summary")
    print("=" * 60)
    print("✅ Email configuration appears to be working")
    print("✅ Ready to process Westshore Montessori School emails")
    print("\nNext steps:")
    print("1. Run: python school_photo_downloader.py --config config_local.yaml")
    print("2. Check the logs for detailed processing information")
    print("=" * 60)
    
    return True


def main():
    """Main function."""
    try:
        success = test_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
