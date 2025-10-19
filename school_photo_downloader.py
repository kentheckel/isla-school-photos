#!/usr/bin/env python3
"""
School Photo Downloader - Main Script

This script automatically monitors email for school photos and uploads them to Google Photos.
It's designed to run periodically to check for new emails from your child's school.

Usage:
    python school_photo_downloader.py [--config CONFIG_FILE] [--days-back DAYS]

Features:
    - Monitors email for school photos (especially Friday emails)
    - Downloads photo attachments automatically
    - Uploads photos to Google Photos in a dedicated album
    - Comprehensive logging and error handling
    - Configurable email filtering and settings
"""

import os
import sys
import logging
import argparse
import yaml
from datetime import datetime, timedelta
from typing import Dict, List
import shutil

# Import our custom modules
from email_monitor import EmailMonitor
from google_photos_uploader import GooglePhotosUploader


class SchoolPhotoDownloader:
    """
    Main orchestrator class for the school photo downloader.
    
    This class coordinates email monitoring, photo downloading, and Google Photos uploading.
    It handles configuration loading, logging setup, and the overall workflow.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the school photo downloader.
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Initialize components
        self.email_monitor = EmailMonitor(self.config)
        self.google_uploader = GooglePhotosUploader(self.config)
        
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict: Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Validate required configuration sections
            required_sections = ['email', 'google_photos', 'downloads', 'logging']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Missing required configuration section: {section}")
            
            return config
            
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {self.config_path}")
            print("Please create a configuration file based on config.yaml")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """
        Set up logging configuration based on config file settings.
        """
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'].upper())
        log_file = log_config['log_file']
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        """
        Clean up temporary downloaded files after processing.
        
        Args:
            file_paths (List[str]): List of file paths to clean up
        """
        try:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temporary files: {str(e)}")
    
    def _decode_header(self, header_value: str) -> str:
        """
        Decode email header values that may be encoded.
        
        Args:
            header_value (str): Raw header value
            
        Returns:
            str: Decoded header value
        """
        if not header_value:
            return ""
        
        try:
            import email.header
            decoded_parts = email.header.decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string
        except Exception:
            return str(header_value)
    
    def _is_friday_email(self, email_date: str) -> bool:
        """
        Check if an email was sent on a Friday.
        
        Args:
            email_date (str): Email date string
            
        Returns:
            bool: True if email was sent on Friday
        """
        try:
            # Parse email date (format: "Fri, 15 Dec 2023 14:30:00 +0000")
            from email.utils import parsedate_to_datetime
            parsed_date = parsedate_to_datetime(email_date)
            return parsed_date.weekday() == 4  # Friday is weekday 4
        except Exception:
            return False
    
    def _enhanced_email_filtering(self, mail, email_ids: List[str]) -> List[str]:
        """
        Apply enhanced filtering to identify Westshore Montessori School emails.
        
        This method specifically looks for emails with the exact subject pattern
        "[Westshore Montessori School ]" and validates the expected pattern of
        2 emails typically sent on Fridays around 6:46 PM.
        
        Args:
            mail: IMAP connection object
            email_ids (List[str]): List of email IDs to filter
            
        Returns:
            List[str]: Filtered list of email IDs
        """
        filtered_ids = []
        friday_emails = []
        other_emails = []
        
        for email_id in email_ids:
            try:
                # Fetch email headers
                status, msg_data = mail.fetch(email_id, '(RFC822.HEADER)')
                
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                import email
                email_message = email.message_from_bytes(email_body)
                
                # Get email details
                subject = email_message.get('Subject', '')
                sender = email_message.get('From', '')
                date = email_message.get('Date', '')
                
                # Decode headers
                subject = self._decode_header(subject)
                sender = self._decode_header(sender)
                
                # Check if it's from the school
                if self.config['email']['sender_email'].lower() not in sender.lower():
                    self.logger.debug(f"Email {email_id} filtered out: not from school sender")
                    continue
                
                # Check for exact subject pattern match
                expected_subject = "[Westshore Montessori School ]"
                if expected_subject not in subject:
                    self.logger.debug(f"Email {email_id} filtered out: subject doesn't match pattern")
                    continue
                
                # Check if it's a Friday email (expected pattern)
                is_friday = self._is_friday_email(date)
                
                # Log email details for debugging
                self.logger.info(f"Westshore Montessori Email {email_id}:")
                self.logger.info(f"  From: {sender}")
                self.logger.info(f"  Subject: {subject}")
                self.logger.info(f"  Date: {date}")
                self.logger.info(f"  Is Friday: {is_friday}")
                
                # Categorize emails
                if is_friday:
                    friday_emails.append(email_id)
                    self.logger.info(f"  ✅ Friday email - expected pattern")
                else:
                    other_emails.append(email_id)
                    self.logger.info(f"  ⚠️  Non-Friday email - unexpected timing")
                
                # Include all emails that match the subject pattern
                filtered_ids.append(email_id)
                
            except Exception as e:
                self.logger.warning(f"Error filtering email {email_id}: {str(e)}")
                continue
        
        # Log summary of findings
        self.logger.info(f"Email filtering summary:")
        self.logger.info(f"  Total emails found: {len(email_ids)}")
        self.logger.info(f"  Friday emails: {len(friday_emails)}")
        self.logger.info(f"  Other day emails: {len(other_emails)}")
        self.logger.info(f"  Emails passing filter: {len(filtered_ids)}")
        
        # Validate expected pattern
        if len(friday_emails) == 2:
            self.logger.info("✅ Perfect! Found exactly 2 Friday emails as expected")
        elif len(friday_emails) > 0:
            self.logger.warning(f"⚠️  Found {len(friday_emails)} Friday emails (expected 2)")
        else:
            self.logger.warning("⚠️  No Friday emails found - this might be unexpected")
        
        return filtered_ids
    
    def process_school_photos(self, days_back: int = 7) -> bool:
        """
        Main method to process school photos from email and upload to Google Photos.
        
        Args:
            days_back (int): Number of days to look back for emails
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting school photo processing")
        self.logger.info(f"Looking back {days_back} days for school emails")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Connect to email and find school emails
            self.logger.info("Step 1: Connecting to email and searching for school emails")
            mail = self.email_monitor.connect_to_email()
            if not mail:
                self.logger.error("Failed to connect to email server")
                return False
            
            try:
                # Search for emails from school
                email_ids = self.email_monitor.search_school_emails(mail, days_back)
                
                if not email_ids:
                    self.logger.info("No school emails found")
                    return True
                
                # Apply enhanced filtering
                self.logger.info(f"Found {len(email_ids)} potential school emails, applying enhanced filtering...")
                filtered_email_ids = self._enhanced_email_filtering(mail, email_ids)
                
                if not filtered_email_ids:
                    self.logger.info("No emails passed the enhanced filtering criteria")
                    return True
                
                self.logger.info(f"Found {len(filtered_email_ids)} emails that match school photo criteria")
                
                # Step 2: Download photo attachments
                self.logger.info("Step 2: Downloading photo attachments")
                downloaded_files = self.email_monitor.download_attachments(mail, filtered_email_ids)
                
                if not downloaded_files:
                    self.logger.info("No photo attachments found in school emails")
                    return True
                
                self.logger.info(f"Downloaded {len(downloaded_files)} photo files")
                
            finally:
                # Always close email connection
                try:
                    mail.close()
                    mail.logout()
                except Exception as e:
                    self.logger.warning(f"Error closing email connection: {str(e)}")
            
            # Step 3: Authenticate with Google Photos
            self.logger.info("Step 3: Authenticating with Google Photos")
            if not self.google_uploader.authenticate():
                self.logger.error("Failed to authenticate with Google Photos")
                return False
            
            # Step 4: Upload photos to Google Photos
            self.logger.info("Step 4: Uploading photos to Google Photos")
            upload_success = self.google_uploader.upload_photos(downloaded_files)
            
            if upload_success:
                self.logger.info("Successfully processed school photos!")
            else:
                self.logger.error("Failed to upload photos to Google Photos")
                return False
            
            # Step 5: Cleanup temporary files
            self.logger.info("Step 5: Cleaning up temporary files")
            self._cleanup_temp_files(downloaded_files)
            
            self.logger.info("=" * 60)
            self.logger.info("School photo processing completed successfully!")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in main processing: {str(e)}")
            return False


def main():
    """
    Main entry point for the school photo downloader script.
    """
    parser = argparse.ArgumentParser(
        description="Automatically download school photos from email and upload to Google Photos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python school_photo_downloader.py
    python school_photo_downloader.py --config my_config.yaml
    python school_photo_downloader.py --days-back 14
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Number of days to look back for school emails (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        print("Please create a configuration file based on config.yaml")
        sys.exit(1)
    
    # Create and run the downloader
    downloader = SchoolPhotoDownloader(args.config)
    
    try:
        success = downloader.process_school_photos(args.days_back)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
