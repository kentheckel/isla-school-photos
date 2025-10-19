"""
Google Photos uploader module for school photo downloader.

This module handles authentication with Google Photos API and uploading
photos to a specified album in Google Photos.
"""

import os
import json
import logging
from typing import List, Optional, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time


class GooglePhotosUploader:
    """
    Handles Google Photos API authentication and photo uploading.
    
    This class manages OAuth2 authentication with Google Photos API,
    creates or finds the specified album, and uploads photos to it.
    """
    
    # Google Photos API scopes required for uploading photos and managing albums
    SCOPES = [
        'https://www.googleapis.com/auth/photoslibrary',
        'https://www.googleapis.com/auth/photoslibrary.appendonly'
    ]
    
    def __init__(self, config: Dict):
        """
        Initialize the Google Photos uploader with configuration settings.
        
        Args:
            config (Dict): Configuration dictionary containing Google Photos settings
        """
        self.config = config
        self.credentials_file = config['google_photos']['credentials_file']
        self.token_file = config['google_photos']['token_file']
        self.album_name = config['google_photos']['album_name']
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize service (will be set after authentication)
        self.service = None
        self.album_id = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Photos API using OAuth2.
        
        This method handles the OAuth2 flow, including refreshing tokens
        and storing credentials for future use.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_file):
                self.logger.info("Loading existing Google Photos credentials")
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired Google Photos credentials")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting Google Photos OAuth flow")
                    
                    if not os.path.exists(self.credentials_file):
                        self.logger.error(f"Credentials file not found: {self.credentials_file}")
                        self.logger.error("Please download your OAuth2 credentials from Google Cloud Console")
                        return False
                    
                    # Start OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info("Google Photos credentials saved")
            
            # Build the Google Photos service
            self.service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
            self.logger.info("Successfully authenticated with Google Photos API")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Photos authentication failed: {str(e)}")
            return False
    
    def find_or_create_album(self) -> Optional[str]:
        """
        Find existing album or create a new one with the specified name.
        
        Returns:
            Optional[str]: Album ID if successful, None otherwise
        """
        try:
            if not self.service:
                self.logger.error("Google Photos service not initialized")
                return None
            
            self.logger.info(f"Looking for album: {self.album_name}")
            
            # Search for existing albums
            albums_response = self.service.albums().list(pageSize=50).execute()
            albums = albums_response.get('albums', [])
            
            # Look for existing album with the same name
            for album in albums:
                if album.get('title') == self.album_name:
                    self.album_id = album['id']
                    self.logger.info(f"Found existing album: {self.album_name} (ID: {self.album_id})")
                    return self.album_id
            
            # Create new album if not found
            self.logger.info(f"Creating new album: {self.album_name}")
            album_body = {
                'album': {
                    'title': self.album_name
                }
            }
            
            created_album = self.service.albums().create(body=album_body).execute()
            self.album_id = created_album['id']
            self.logger.info(f"Created new album: {self.album_name} (ID: {self.album_id})")
            
            return self.album_id
            
        except Exception as e:
            self.logger.error(f"Error finding/creating album: {str(e)}")
            return None
    
    def upload_photo(self, file_path: str, description: str = "") -> Optional[str]:
        """
        Upload a single photo to Google Photos.
        
        This method performs the complete two-step process:
        1. Upload the media file to get an upload token
        2. Create a media item in the user's library using the token
        
        Args:
            file_path (str): Path to the photo file to upload
            description (str): Optional description for the photo
            
        Returns:
            Optional[str]: Media item ID if successful, None otherwise
        """
        try:
            if not self.service:
                self.logger.error("Google Photos service not initialized")
                return None
            
            if not os.path.exists(file_path):
                self.logger.error(f"Photo file not found: {file_path}")
                return None
            
            # Get file info for logging
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            self.logger.info(f"Uploading photo: {file_name} ({file_size} bytes)")
            
            # Step 1: Upload the photo using the correct Google Photos API method
            with open(file_path, 'rb') as photo_file:
                # First, upload the bytes to get an upload token
                upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
                headers = {
                    'Authorization': f'Bearer {self.service._http.credentials.token}',
                    'Content-Type': 'application/octet-stream',
                    'X-Goog-Upload-Protocol': 'raw',
                    'X-Goog-Upload-File-Name': file_name
                }
                
                import requests
                upload_response = requests.post(upload_url, data=photo_file.read(), headers=headers)
                upload_response.raise_for_status()
                upload_token = upload_response.text
                
                if not upload_token:
                    self.logger.error(f"Failed to get upload token for {file_name}")
                    return None
                
                self.logger.info(f"Got upload token for {file_name}: {upload_token[:50]}...")
            
            # Step 2: Create the media item in the user's library
            try:
                # Prepare the media item creation request
                media_item_request = {
                    'newMediaItems': [{
                        'description': description,
                        'simpleMediaItem': {
                            'uploadToken': upload_token
                        }
                    }]
                }
                
                # Create the media item
                create_request = self.service.mediaItems().batchCreate(body=media_item_request)
                create_response = create_request.execute()
                
                # Check if the creation was successful
                if 'newMediaItemResults' in create_response and create_response['newMediaItemResults']:
                    result = create_response['newMediaItemResults'][0]
                    if 'mediaItem' in result:
                        media_item_id = result['mediaItem']['id']
                        self.logger.info(f"Successfully created media item for {file_name}, ID: {media_item_id}")
                        return media_item_id
                    else:
                        self.logger.error(f"Failed to create media item for {file_name}: {result.get('status', 'Unknown error')}")
                        return None
                else:
                    self.logger.error(f"Failed to create media item for {file_name}: No results in response")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Error creating media item for {file_name}: {str(e)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading photo {file_path}: {str(e)}")
            return None
    
    def add_photos_to_album(self, upload_tokens: List[str]) -> bool:
        """
        Add uploaded photos to the specified album.
        
        Args:
            upload_tokens (List[str]): List of upload tokens from successful uploads
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.album_id:
                self.logger.error("Google Photos service or album not initialized")
                return False
            
            if not upload_tokens:
                self.logger.warning("No upload tokens provided")
                return True
            
            self.logger.info(f"Adding {len(upload_tokens)} photos to album")
            
            # Prepare batch request
            new_media_items = []
            for token in upload_tokens:
                new_media_items.append({
                    'simpleMediaItem': {
                        'uploadToken': token
                    }
                })
            
            # Create batch create request
            batch_create_request = {
                'albumId': self.album_id,
                'newMediaItems': new_media_items
            }
            
            # Execute batch create
            batch_response = self.service.mediaItems().batchCreate(body=batch_create_request).execute()
            
            # Check results
            new_media_item_results = batch_response.get('newMediaItemResults', [])
            successful_uploads = len([result for result in new_media_item_results 
                                    if result.get('status', {}).get('code') == 'SUCCESS'])
            
            self.logger.info(f"Successfully added {successful_uploads}/{len(upload_tokens)} photos to album")
            
            # Log any failures
            for i, result in enumerate(new_media_item_results):
                status = result.get('status', {})
                if status.get('code') != 'SUCCESS':
                    self.logger.warning(f"Failed to add photo {i+1} to album: {status.get('message', 'Unknown error')}")
            
            return successful_uploads > 0
            
        except Exception as e:
            self.logger.error(f"Error adding photos to album: {str(e)}")
            return False
    
    def upload_photos(self, photo_paths: List[str]) -> bool:
        """
        Upload multiple photos to Google Photos and add them to the album.
        
        Args:
            photo_paths (List[str]): List of file paths to upload
            
        Returns:
            bool: True if at least one photo was successfully uploaded, False otherwise
        """
        try:
            if not photo_paths:
                self.logger.info("No photos to upload")
                return True
            
            # Ensure we're authenticated
            if not self.service:
                self.logger.info("Authenticating with Google Photos...")
                if not self.authenticate():
                    self.logger.error("Failed to authenticate with Google Photos")
                    return False
            
            self.logger.info(f"Starting upload of {len(photo_paths)} photos to Google Photos")
            
            # Try to find or create album, but don't fail if we can't
            if not self.album_id:
                self.logger.info("Attempting to find or create album...")
                if not self.find_or_create_album():
                    self.logger.warning("Could not find or create album, will upload to main library")
                    self.album_id = None
            
            # Upload each photo and collect upload tokens
            upload_tokens = []
            successful_uploads = 0
            
            for photo_path in photo_paths:
                try:
                    # Generate description from filename
                    filename = os.path.basename(photo_path)
                    description = f"School photo: {filename}"
                    
                    # Upload the photo
                    upload_token = self.upload_photo(photo_path, description)
                    
                    if upload_token:
                        upload_tokens.append(upload_token)
                        successful_uploads += 1
                    else:
                        self.logger.warning(f"Failed to upload: {photo_path}")
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error processing photo {photo_path}: {str(e)}")
                    continue
            
            if not upload_tokens:
                self.logger.error("No photos were successfully uploaded")
                return False
            
            # Add uploaded photos to the album (if we have one)
            if self.album_id and upload_tokens:
                album_success = self.add_photos_to_album(upload_tokens)
                if album_success:
                    self.logger.info(f"Successfully uploaded {successful_uploads} photos to Google Photos album: {self.album_name}")
                else:
                    self.logger.warning("Photos were uploaded but failed to add to album")
            else:
                self.logger.info(f"Successfully uploaded {successful_uploads} photos to Google Photos main library")
            
            return successful_uploads > 0
            
        except Exception as e:
            self.logger.error(f"Error in upload_photos: {str(e)}")
            return False
