# GitHub Actions Setup for School Photos Downloader

This guide will help you set up automatic execution of the school photo downloader using GitHub Actions.

## 🚀 What This Does

The GitHub Action will automatically:
- Run every Friday at 7:00 PM EST (when school emails typically arrive)
- Download photos from Westshore Montessori School emails
- Upload them directly to your Google Photos library
- Send you notifications about success/failure

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Email Credentials**: Gmail app password for IMAP access
3. **Google Photos API**: OAuth credentials file

## 🔧 Setup Instructions

### Step 1: Add Secrets to GitHub Repository

Go to your GitHub repository → Settings → Secrets and variables → Actions, then add these secrets:

#### Required Secrets:

1. **`EMAIL_USERNAME`**
   - Value: Your Gmail address (e.g., `kent.heckel@gmail.com`)

2. **`EMAIL_PASSWORD`**
   - Value: Your Gmail app password (e.g., `ejxz hlsk voxk voum`)

3. **`SENDER_EMAIL`**
   - Value: `notifications@transparentclassroom.com`

4. **`GOOGLE_PHOTOS_CREDENTIALS`**
   - Value: The entire contents of your `google_photos_credentials.json` file
   - Copy and paste the entire JSON content (including the curly braces)

### Step 2: Upload Google Photos Credentials

1. Open your `google_photos_credentials.json` file
2. Copy the entire contents
3. Go to GitHub repository → Settings → Secrets and variables → Actions
4. Click "New repository secret"
5. Name: `GOOGLE_PHOTOS_CREDENTIALS`
6. Value: Paste the entire JSON content
7. Click "Add secret"

### Step 3: Test the Workflow

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Find "School Photos Downloader" workflow
4. Click "Run workflow" button
5. Click "Run workflow" to test it manually

## ⏰ Schedule

The workflow is configured to run:
- **When**: Every Friday at 7:00 PM EST
- **What**: Downloads and uploads school photos automatically
- **Manual**: You can also trigger it manually anytime

## 📊 Monitoring

### Check Results:
1. Go to Actions tab in your GitHub repository
2. Look for the latest "School Photos Downloader" run
3. Click on it to see detailed logs
4. Green checkmark = success, red X = failure

### Logs:
- All logs are saved as artifacts
- Download them to troubleshoot if needed
- Logs include email search, photo download, and upload details

## 🔍 Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Check that all secrets are correctly set
   - Verify Gmail app password is correct
   - Ensure Google Photos API is enabled

2. **No Photos Found**
   - Check if school emails arrived on expected day
   - Verify sender email matches exactly
   - Check logs for email search details

3. **Upload Failed**
   - Verify Google Photos credentials are valid
   - Check if Photos Library API is enabled
   - Ensure OAuth consent screen is configured

### Manual Testing:

You can test the workflow manually:
1. Go to Actions → School Photos Downloader
2. Click "Run workflow"
3. Optionally change the "days_back" parameter
4. Click "Run workflow"

## 📱 Notifications

The workflow will:
- ✅ Show success message in GitHub Actions logs
- ❌ Show error details if something fails
- 📋 Save detailed logs as downloadable artifacts

## 🔒 Security Notes

- All sensitive data (passwords, API keys) are stored as GitHub Secrets
- Credentials are only used during workflow execution
- All sensitive files are cleaned up after each run
- Logs don't contain sensitive information

## 🎯 Success Indicators

When working correctly, you should see:
1. **GitHub Actions**: Green checkmark for successful runs
2. **Google Photos**: New photos appear in your library every Friday
3. **Logs**: "Successfully uploaded X photos to Google Photos main library"

## 📞 Support

If you encounter issues:
1. Check the GitHub Actions logs first
2. Download the logs artifact for detailed information
3. Verify all secrets are correctly configured
4. Test the script locally first to ensure it works

---

**🎉 Once set up, you'll never have to manually download school photos again!**
