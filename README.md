# School Photo Downloader

Automatically download photos from your child's school emails and upload them to Google Photos. This script monitors your email for school photos (especially those sent on Fridays) and organizes them in a dedicated Google Photos album.

## Features

- 📧 **Email Monitoring**: Automatically checks for emails from Westshore Montessori School
- 🎯 **Smart Filtering**: Identifies emails with exact subject pattern "[Westshore Montessori School ]"
- 📸 **Photo Download**: Downloads photo attachments from school emails
- ☁️ **Google Photos Integration**: Uploads photos to a dedicated Google Photos album
- 🔄 **Automated Processing**: Can be run manually or scheduled to run automatically
- 📝 **Comprehensive Logging**: Detailed logs for monitoring and troubleshooting
- 🏫 **Westshore Montessori Optimized**: Specifically designed for the school's email pattern (2 emails on Fridays around 6:46 PM)
- 🚀 **GitHub Actions**: Fully automated execution every Friday with cloud-based processing

## Prerequisites

Before setting up the script, you'll need:

1. **Python 3.7+** installed on your system
2. **Gmail account** (or any IMAP-compatible email account)
3. **Google Cloud Project** with Photos Library API enabled
4. **School email address** that sends the photo emails

## Setup Instructions

### 1. Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt
```

### 2. Set Up Google Photos API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Photos Library API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Photos Library API"
   - Click on it and press "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file and save it as `google_photos_credentials.json` in this directory

### 3. Configure Email Settings

1. **For Gmail users**:
   - Enable 2-factor authentication on your Gmail account
   - Generate an App Password:
     - Go to Google Account settings
     - Security > 2-Step Verification > App passwords
     - Generate a password for "Mail"
     - Use this password in the config file (not your regular Gmail password)

2. **For other email providers**:
   - Find your IMAP server settings
   - Update the configuration accordingly

### 4. Create Configuration File

1. Copy the example configuration:
   ```bash
   cp config.yaml config_local.yaml
   ```

2. Edit `config_local.yaml` with your settings:
   ```yaml
   email:
     imap_server: "imap.gmail.com"  # Your email provider's IMAP server
     imap_port: 993
     use_ssl: true
     username: "your_email@gmail.com"  # Your email address
     password: "your_app_password"     # Your app password (not regular password)
     sender_email: "school@westshoremontessori.com"  # Westshore Montessori's email address
     subject_keywords: ["[Westshore Montessori School ]"]  # Exact subject line pattern
     check_frequency_minutes: 60

   google_photos:
     credentials_file: "google_photos_credentials.json"
     token_file: "google_photos_token.json"
     album_name: "School Photos"  # Name of the album in Google Photos

   downloads:
     temp_folder: "./temp_downloads"
     supported_formats: [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
     max_file_size_mb: 50

   logging:
     level: "INFO"
     log_file: "school_photo_downloader.log"
   ```

### 5. Test the Setup

Run the script to test your configuration:

```bash
python school_photo_downloader.py --config config_local.yaml
```

The first time you run it, it will:
1. Open a browser window for Google Photos authentication
2. Ask you to log in and authorize the application
3. Save the authentication token for future use

## Usage

### Manual Execution

```bash
# Run with default settings (looks back 7 days)
python school_photo_downloader.py --config config_local.yaml

# Look back 14 days for school emails
python school_photo_downloader.py --config config_local.yaml --days-back 14
```

### Automated Execution

You can set up the script to run automatically using:

#### Option 1: Cron (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add this line to run every Friday at 6 PM
0 18 * * 5 /usr/bin/python3 /path/to/school_photo_downloader.py --config /path/to/config_local.yaml
```

#### Option 2: Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Weekly" on Fridays
4. Set action to start the Python script

#### Option 3: Systemd Timer (Linux)
Create a systemd service and timer for more robust scheduling.

## Westshore Montessori School Configuration

This script is specifically optimized for **Westshore Montessori School** emails:

### Expected Email Pattern
- **Subject Line**: Exactly `[Westshore Montessori School ]` (with brackets and trailing space)
- **Timing**: Typically sent on Fridays around 6:46 PM
- **Quantity**: Usually 2 separate emails with photos
- **Sender**: School's email address (e.g., `school@westshoremontessori.com`)

### Configuration for Westshore Montessori
Update your `config_local.yaml` with:
```yaml
email:
  sender_email: "school@westshoremontessori.com"  # Replace with actual school email
  subject_keywords: ["[Westshore Montessori School ]"]  # Exact subject pattern
```

The script will:
- ✅ Validate the exact subject line pattern
- ✅ Check for Friday timing (expected pattern)
- ✅ Log whether it finds the expected 2 emails
- ✅ Process all matching emails regardless of timing

## How It Works

1. **Email Monitoring**: The script connects to your email server using IMAP
2. **Email Filtering**: It searches for emails from the school, with special attention to Friday emails
3. **Photo Detection**: Identifies and downloads photo attachments from matching emails
4. **Google Photos Upload**: Uploads the photos to a dedicated album in Google Photos
5. **Cleanup**: Removes temporary downloaded files after successful upload

## Configuration Options

### Email Settings
- `imap_server`: Your email provider's IMAP server
- `imap_port`: IMAP port (usually 993 for SSL)
- `use_ssl`: Whether to use SSL encryption
- `username`: Your email address
- `password`: Your email password or app password
- `sender_email`: The school's email address to monitor
- `subject_keywords`: Keywords to look for in email subjects
- `check_frequency_minutes`: How often to check for new emails (for automated runs)

### Google Photos Settings
- `credentials_file`: Path to your Google Photos API credentials
- `token_file`: Path to store the authentication token
- `album_name`: Name of the album to create in Google Photos

### Download Settings
- `temp_folder`: Temporary folder for downloaded photos
- `supported_formats`: Image file formats to process
- `max_file_size_mb`: Maximum file size to process

### Logging Settings
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `log_file`: Path to the log file

## 🚀 GitHub Actions (Recommended)

For fully automated execution, use GitHub Actions to run the script every Friday:

### Quick Setup

1. **Push your code to GitHub** (make sure to exclude sensitive files)
2. **Add secrets to your repository**:
   - Go to Settings → Secrets and variables → Actions
   - Add the required secrets (see `GITHUB_ACTIONS_SETUP.md` for details)
3. **The workflow will run automatically every Friday at 7:00 PM EST**

### Benefits of GitHub Actions

- ✅ **Fully automated** - no need to run manually
- ✅ **Cloud-based** - runs on GitHub's servers
- ✅ **Reliable** - runs even if your computer is off
- ✅ **Monitored** - see success/failure in GitHub Actions tab
- ✅ **Logs** - detailed logs saved as artifacts
- ✅ **Manual trigger** - can run anytime for testing

### Setup Instructions

See `GITHUB_ACTIONS_SETUP.md` for detailed setup instructions, or run:

```bash
python3 setup_github_secrets.py
```

This will show you exactly what secrets to add to GitHub.

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Make sure you're using an App Password for Gmail (not your regular password)
   - Verify your Google Photos API credentials are correct
   - Check that the Photos Library API is enabled in Google Cloud Console

2. **No Emails Found**:
   - Verify the school's email address is correct
   - Check that the subject keywords match your school's email patterns
   - Try increasing the `days_back` parameter

3. **Upload Failures**:
   - Check your internet connection
   - Verify Google Photos API quotas haven't been exceeded
   - Check the log file for specific error messages

### Log Files

The script creates detailed log files that can help with troubleshooting:
- Check `school_photo_downloader.log` for detailed execution logs
- Look for ERROR and WARNING messages
- The logs include timestamps and detailed error information

## Security Notes

- Never commit your `config_local.yaml` file to version control
- Keep your Google Photos credentials file secure
- Use App Passwords instead of your main email password
- The script only reads emails and doesn't send any emails

## Support

If you encounter issues:

1. Check the log files for error messages
2. Verify your configuration settings
3. Test with a small `days_back` value first
4. Ensure all dependencies are installed correctly

## License

This project is provided as-is for personal use. Please respect your school's policies regarding photo sharing and ensure you have permission to download and store these photos.
