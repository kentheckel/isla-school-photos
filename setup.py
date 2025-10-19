#!/usr/bin/env python3
"""
Quick Setup Script for School Photo Downloader

This script helps you quickly set up the school photo downloader
by creating the necessary configuration files and directories.
"""

import os
import sys
import shutil
from pathlib import Path


def create_directories():
    """Create necessary directories for the application."""
    directories = [
        "temp_downloads",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def create_local_config():
    """Create a local configuration file from the template."""
    config_template = "config.yaml"
    config_local = "config_local.yaml"
    
    if os.path.exists(config_local):
        print(f"⚠️  Local config already exists: {config_local}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping config creation")
            return
    
    if os.path.exists(config_template):
        shutil.copy(config_template, config_local)
        print(f"✅ Created local config: {config_local}")
        print("   Please edit this file with your email and Google Photos settings")
    else:
        print(f"❌ Template config not found: {config_template}")


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "google-auth",
        "google-auth-oauthlib", 
        "google-auth-httplib2",
        "google-api-python-client",
        "Pillow",
        "python-dateutil",
        "python-dotenv",
        "pyyaml",
        "schedule"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nTo install missing packages, run:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True


def main():
    """Main setup function."""
    print("=" * 60)
    print("School Photo Downloader - Quick Setup")
    print("=" * 60)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Create local config
    print("\n⚙️  Setting up configuration...")
    create_local_config()
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    if deps_ok:
        print("✅ Basic setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit config_local.yaml with your email and Google Photos settings")
        print("2. Set up Google Photos API credentials (see README.md)")
        print("3. Test the setup: python setup_google_photos.py")
        print("4. Run the downloader: python school_photo_downloader.py --config config_local.yaml")
    else:
        print("⚠️  Setup completed with warnings")
        print("Please install missing dependencies before proceeding")
    
    print("\nFor detailed instructions, see README.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
