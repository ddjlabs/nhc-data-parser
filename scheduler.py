#!/usr/bin/env python
import os
import sys
import time
import logging
import logging.config
import argparse
from datetime import datetime
from dotenv import load_dotenv
from croniter import croniter
from pipeline import main as run_pipeline

# Load environment variables
load_dotenv()

# Get log level from environment variable or use default
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

def configure_logging(log_level):
    """Configure logging with the specified log level."""
    # Validate log level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        print(f"Invalid log level: {log_level}. Using INFO instead.")
        log_level = 'INFO'
    
    # Configure logging
    logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': log_level,
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'scheduler.log'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': log_level,
            'propagate': True
        }
    }
    })
    return logging.getLogger(__name__)

logger = configure_logging(LOG_LEVEL)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NHC Storm Tracker Pipeline Scheduler")
    parser.add_argument(
        "--log-level", 
        type=str, 
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: from LOG_LEVEL env var or INFO)"
    )
    return parser.parse_args()


def main():
    """Run the NHC pipeline on a schedule defined by CRON_SCHEDULE environment variable."""
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging with specified log level
    logger = configure_logging(args.log_level)
    
    # Get cron schedule from environment variable or use default
    cron_schedule = os.getenv('CRON_SCHEDULE', '0 */1 * * *')  # Default: every hour at minute 0
    
    logger.info(f"Starting NHC Pipeline scheduler with schedule: {cron_schedule} and log level: {args.log_level}")
    logger.info("Press CTRL+C to exit")
    
    # Initialize the cron iterator
    base = datetime.now()
    iter = croniter(cron_schedule, base)
    
    try:
        while True:
            # Get the next run time
            next_run = iter.get_next(datetime)
            logger.info(f"Next pipeline run scheduled for: {next_run}")
            
            # Sleep until the next run time
            now = datetime.now()
            seconds_to_sleep = (next_run - now).total_seconds()
            
            if seconds_to_sleep > 0:
                logger.debug(f"Sleeping for {seconds_to_sleep} seconds until next run")
                time.sleep(seconds_to_sleep)
            
            # Run the pipeline
            logger.info("Starting pipeline run")
            try:
                run_pipeline()
                logger.info("Pipeline run completed successfully")
            except Exception as e:
                logger.error(f"Error during pipeline run: {str(e)}", exc_info=True)
            
            # Update the iterator for the next run
            iter = croniter(cron_schedule, datetime.now())
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
