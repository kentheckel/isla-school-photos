#!/usr/bin/env python3
"""
School Photo Downloader Scheduler

This script runs the school photo downloader on a schedule.
It's designed to be run as a background service or daemon.

Usage:
    python run_scheduler.py [--config CONFIG_FILE] [--interval MINUTES]
"""

import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime
from school_photo_downloader import SchoolPhotoDownloader


class PhotoDownloaderScheduler:
    """
    Scheduler class for running the school photo downloader periodically.
    
    This class handles scheduling, logging, and error recovery for
    automated photo downloading.
    """
    
    def __init__(self, config_path: str = "config.yaml", interval_minutes: int = 60):
        """
        Initialize the scheduler.
        
        Args:
            config_path (str): Path to the configuration file
            interval_minutes (int): How often to run the downloader (in minutes)
        """
        self.config_path = config_path
        self.interval_minutes = interval_minutes
        self.downloader = None
        self.logger = self._setup_logging()
        
        # Statistics
        self.run_count = 0
        self.success_count = 0
        self.last_run = None
        self.last_success = None
    
    def _setup_logging(self):
        """
        Set up logging for the scheduler.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/scheduler.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _run_downloader(self):
        """
        Run the school photo downloader and handle results.
        
        This method is called by the scheduler and handles logging,
        error recovery, and statistics tracking.
        """
        self.run_count += 1
        self.last_run = datetime.now()
        
        self.logger.info("=" * 60)
        self.logger.info(f"Starting scheduled photo download (Run #{self.run_count})")
        self.logger.info(f"Time: {self.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
        
        try:
            # Initialize downloader if not already done
            if not self.downloader:
                self.downloader = SchoolPhotoDownloader(self.config_path)
            
            # Run the photo downloader
            success = self.downloader.process_school_photos(days_back=7)
            
            if success:
                self.success_count += 1
                self.last_success = datetime.now()
                self.logger.info("✅ Photo download completed successfully")
            else:
                self.logger.warning("⚠️ Photo download completed with warnings or errors")
            
            # Log statistics
            success_rate = (self.success_count / self.run_count) * 100
            self.logger.info(f"Statistics: {self.success_count}/{self.run_count} successful runs ({success_rate:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error in scheduled photo download: {str(e)}")
            self.logger.exception("Full error details:")
        
        self.logger.info("=" * 60)
        self.logger.info("Scheduled run completed")
        self.logger.info("=" * 60)
    
    def start_scheduler(self):
        """
        Start the scheduler and run indefinitely.
        
        This method sets up the schedule and runs the scheduler
        until interrupted by the user or system.
        """
        self.logger.info("Starting School Photo Downloader Scheduler")
        self.logger.info(f"Configuration: {self.config_path}")
        self.logger.info(f"Check interval: {self.interval_minutes} minutes")
        
        # Schedule the job
        schedule.every(self.interval_minutes).minutes.do(self._run_downloader)
        
        # Run immediately on startup (optional)
        self.logger.info("Running initial check...")
        self._run_downloader()
        
        # Main scheduler loop
        self.logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}")
            raise
    
    def run_once(self):
        """
        Run the downloader once and exit.
        
        This is useful for testing or manual execution.
        """
        self.logger.info("Running photo downloader once...")
        self._run_downloader()
        self.logger.info("Single run completed")


def main():
    """
    Main entry point for the scheduler.
    """
    parser = argparse.ArgumentParser(
        description="Schedule the school photo downloader to run periodically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_scheduler.py
    python run_scheduler.py --config config_local.yaml --interval 30
    python run_scheduler.py --once  # Run once and exit
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in minutes (default: 60)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        print("Please create a configuration file based on config.yaml")
        sys.exit(1)
    
    # Create and run the scheduler
    scheduler = PhotoDownloaderScheduler(args.config, args.interval)
    
    try:
        if args.once:
            scheduler.run_once()
        else:
            scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
