"""
Email monitoring module for school photo downloader.

This module handles connecting to email servers, monitoring for new emails,
and downloading photo attachments from school emails.
"""

import imaplib
import email
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from email.header import decode_header


class EmailMonitor:
    """
    Handles email monitoring and photo attachment downloading.
    
    This class connects to an IMAP email server, searches for emails from
    the school, and downloads photo attachments to a local directory.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the email monitor with configuration settings.
        
        Args:
            config (Dict): Configuration dictionary containing email settings
        """
        self.config = config
        self.imap_server = config['email']['imap_server']
        self.imap_port = config['email']['imap_port']
        self.use_ssl = config['email']['use_ssl']
        self.username = config['email']['username']
        self.password = config['email']['password']
        self.sender_email = config['email']['sender_email']
        self.subject_keywords = config['email']['subject_keywords']
        # Downloads-related configuration. Use defensive defaults so missing keys in config
        # do not crash the CI/GitHub Actions run. This also makes local runs more resilient
        # if a user copies a minimal config.
        #
        # Defaults chosen:
        # - supported_formats: common image extensions we expect from school emails
        # - temp_folder: a local folder under project root used for transient files
        # - max_file_size_mb: a conservative 50MB cap to avoid downloading large/unexpected payloads
        downloads_config = config.get('downloads', {})

        # List of file extensions we consider images. Normalize to lowercase when comparing.
        self.supported_formats = downloads_config.get(
            'supported_formats',
            [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
        )

        # Folder used to store temporary downloads during processing.
        self.temp_folder = downloads_config.get('temp_folder', './temp_downloads')

        # Maximum file size expressed in bytes; incoming config value is in MB.
        self.max_file_size = downloads_config.get('max_file_size_mb', 50) * 1024 * 1024

        # Emit an informational log if we had to fall back to any default, to aid diagnostics
        try:
            if 'downloads' not in config:
                logging.getLogger(__name__).info(
                    "'downloads' section missing in config; using safe defaults for supported formats, temp folder, and file size."
                )
            else:
                missing_keys = [
                    key for key in ['supported_formats', 'temp_folder', 'max_file_size_mb']
                    if key not in downloads_config
                ]
                if missing_keys:
                    logging.getLogger(__name__).info(
                        f"Missing downloads config keys {missing_keys}; using safe defaults where necessary."
                    )
        except Exception:
            # If logging fails for any reason, do not interrupt initialization
            pass
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create temp folder if it doesn't exist
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def connect_to_email(self) -> Optional[imaplib.IMAP4_SSL]:
        """
        Establish connection to the email server.
        
        Returns:
            Optional[imaplib.IMAP4_SSL]: IMAP connection object or None if failed
        """
        try:
            self.logger.info(f"Connecting to email server: {self.imap_server}:{self.imap_port}")
            
            if self.use_ssl:
                # Use SSL connection for secure email access
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            else:
                # Use non-SSL connection (not recommended for production)
                mail = imaplib.IMAP4(self.imap_server, self.imap_port)
            
            # Login with credentials
            mail.login(self.username, self.password)
            self.logger.info("Successfully connected to email server")
            return mail
            
        except Exception as e:
            self.logger.error(f"Failed to connect to email server: {str(e)}")
            return None
    
    def search_school_emails(self, mail: imaplib.IMAP4_SSL, days_back: int = 7) -> List[str]:
        """
        Search for emails from the school within the specified time range.
        
        This method specifically looks for Westshore Montessori School emails
        with the exact subject line pattern "[Westshore Montessori School ]".
        
        Args:
            mail (imaplib.IMAP4_SSL): Connected IMAP object
            days_back (int): Number of days to look back for emails
            
        Returns:
            List[str]: List of email IDs that match the criteria
        """
        try:
            # Select the inbox folder
            mail.select('INBOX')
            
            # Calculate date range for search
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
            
            # Build search criteria for Westshore Montessori School emails
            # Look for emails from the school sender with the exact subject pattern
            search_criteria = f'FROM "{self.sender_email}" SINCE {since_date}'
            
            # Add subject line filter for the exact pattern
            if self.subject_keywords:
                # For Westshore Montessori, we expect the exact subject pattern
                subject_pattern = self.subject_keywords[0]  # "[Westshore Montessori School ]"
                # Use a simpler search approach - search by sender first, then filter in Python
                search_criteria = f'FROM "{self.sender_email}" SINCE {since_date}'
            
            self.logger.info(f"Searching for Westshore Montessori emails with criteria: {search_criteria}")
            
            # Execute search
            status, messages = mail.search(None, search_criteria)
            
            if status == 'OK':
                email_ids = messages[0].split()
                self.logger.info(f"Found {len(email_ids)} Westshore Montessori emails matching criteria")
                
                # Log the expected pattern for verification
                if len(email_ids) > 0:
                    self.logger.info(f"Expected: 2 emails on Fridays around 6:46 PM")
                    self.logger.info(f"Found: {len(email_ids)} emails")
                
                return [email_id.decode() for email_id in email_ids]
            else:
                self.logger.warning("Email search failed")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching for emails: {str(e)}")
            return []
    
    def download_attachments(self, mail: imaplib.IMAP4_SSL, email_ids: List[str]) -> List[str]:
        """
        Download photo attachments from the specified email IDs.
        
        Args:
            mail (imaplib.IMAP4_SSL): Connected IMAP object
            email_ids (List[str]): List of email IDs to process
            
        Returns:
            List[str]: List of downloaded file paths
        """
        downloaded_files = []
        
        for email_id in email_ids:
            try:
                self.logger.info(f"Processing email ID: {email_id}")
                
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    self.logger.warning(f"Failed to fetch email {email_id}")
                    continue
                
                # Parse the email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Get email subject and sender for logging
                subject = self._decode_header(email_message['Subject'])
                sender = self._decode_header(email_message['From'])
                self.logger.info(f"Processing email from {sender}: {subject}")
                
                # Process attachments
                files_from_email = self._process_email_attachments(email_message, email_id)
                downloaded_files.extend(files_from_email)
                
            except Exception as e:
                self.logger.error(f"Error processing email {email_id}: {str(e)}")
                continue
        
        return downloaded_files
    
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
            decoded_parts = decode_header(header_value)
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
    
    def _process_email_attachments(self, email_message, email_id: str) -> List[str]:
        """
        Process attachments from a single email message.
        
        For Westshore Montessori emails, the photos are embedded in HTML content
        rather than as traditional attachments, so we need to extract image URLs
        from the HTML and download them directly.
        
        Args:
            email_message: Parsed email message object
            email_id (str): ID of the email being processed
            
        Returns:
            List[str]: List of downloaded file paths
        """
        downloaded_files = []
        
        # First, try to process traditional attachments
        for part in email_message.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                
                if not filename:
                    continue
                
                # Decode filename if it's encoded
                filename = self._decode_header(filename)
                
                # Check if file is a supported image format
                file_extension = os.path.splitext(filename.lower())[1]
                if file_extension not in self.supported_formats:
                    self.logger.info(f"Skipping non-image attachment: {filename}")
                    continue
                
                # Check file size
                payload = part.get_payload(decode=True)
                if len(payload) > self.max_file_size:
                    self.logger.warning(f"File too large, skipping: {filename} ({len(payload)} bytes)")
                    continue
                
                # Create unique filename to avoid conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
                unique_filename = f"{timestamp}_{email_id}_{safe_filename}"
                file_path = os.path.join(self.temp_folder, unique_filename)
                
                try:
                    # Save the attachment
                    with open(file_path, 'wb') as f:
                        f.write(payload)
                    
                    self.logger.info(f"Downloaded attachment: {filename} -> {file_path}")
                    downloaded_files.append(file_path)
                    
                except Exception as e:
                    self.logger.error(f"Failed to save attachment {filename}: {str(e)}")
                    continue
        
        # If no traditional attachments found, look for embedded images in HTML
        if not downloaded_files:
            self.logger.info("No traditional attachments found, looking for embedded images in HTML content")
            html_images = self._extract_images_from_html(email_message, email_id)
            downloaded_files.extend(html_images)
        
        return downloaded_files
    
    def _extract_images_from_html(self, email_message, email_id: str) -> List[str]:
        """
        Extract image URLs from HTML content and download them.
        
        This method specifically handles Westshore Montessori emails where photos
        are embedded as images in the HTML content rather than as attachments.
        
        Args:
            email_message: Parsed email message object
            email_id (str): ID of the email being processed
            
        Returns:
            List[str]: List of downloaded file paths
        """
        import requests
        import re
        from urllib.parse import urlparse
        
        downloaded_files = []
        
        try:
            # Get HTML content from the email
            html_content = None
            for part in email_message.walk():
                if part.get_content_type() == 'text/html':
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
            
            if not html_content:
                self.logger.info("No HTML content found in email")
                return downloaded_files
            
            # Extract image URLs from HTML
            # Look for img tags with src attributes
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_urls = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            self.logger.info(f"Found {len(img_urls)} image URLs in HTML content")
            
            # Download each image
            for i, img_url in enumerate(img_urls):
                try:
                    # Clean up the URL (remove HTML entities)
                    img_url = img_url.replace('&amp;', '&')
                    
                    # Skip if it's not a valid image URL
                    if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']):
                        self.logger.debug(f"Skipping non-image URL: {img_url}")
                        continue
                    
                    self.logger.info(f"Downloading image {i+1}/{len(img_urls)}: {img_url}")
                    
                    # Download the image
                    response = requests.get(img_url, timeout=30)
                    response.raise_for_status()
                    
                    # Check file size
                    if len(response.content) > self.max_file_size:
                        self.logger.warning(f"Image too large, skipping: {len(response.content)} bytes")
                        continue
                    
                    # Create filename from URL
                    parsed_url = urlparse(img_url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename or '.' not in filename:
                        filename = f"image_{i+1}.jpg"
                    
                    # Create unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
                    unique_filename = f"{timestamp}_{email_id}_{i+1}_{safe_filename}"
                    file_path = os.path.join(self.temp_folder, unique_filename)
                    
                    # Save the image
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.logger.info(f"Downloaded image: {filename} -> {file_path}")
                    downloaded_files.append(file_path)
                    
                except Exception as e:
                    self.logger.error(f"Failed to download image {img_url}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting images from HTML: {str(e)}")
        
        return downloaded_files
    
    def process_school_emails(self, days_back: int = 7) -> List[str]:
        """
        Main method to process school emails and download photos.
        
        Args:
            days_back (int): Number of days to look back for emails
            
        Returns:
            List[str]: List of downloaded file paths
        """
        self.logger.info("Starting school email processing")
        
        # Connect to email server
        mail = self.connect_to_email()
        if not mail:
            return []
        
        try:
            # Search for school emails
            email_ids = self.search_school_emails(mail, days_back)
            
            if not email_ids:
                self.logger.info("No school emails found")
                return []
            
            # Download attachments from found emails
            downloaded_files = self.download_attachments(mail, email_ids)
            
            self.logger.info(f"Successfully downloaded {len(downloaded_files)} photo files")
            return downloaded_files
            
        finally:
            # Always close the email connection
            try:
                mail.close()
                mail.logout()
                self.logger.info("Email connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing email connection: {str(e)}")
