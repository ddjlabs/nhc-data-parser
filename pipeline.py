import logging
import logging.config
import os
import time
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import Storm, StormHistory, SessionLocal, init_db, Region
from nhc_parser import fetch_rss_feed, get_storm_data

# Load environment variables from .env file
load_dotenv()

# Get cron schedule from environment variable or use default
CRON_SCHEDULE = os.getenv('CRON_SCHEDULE', '0 */1 * * *')  # Default: every hour at minute 0

# Get log level from environment variable or use default
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

def configure_logging(log_level):
    """Configure logging with the specified log level."""
    # Validate log level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        print(f"Invalid log level: {log_level}. Using INFO instead.")
        log_level = 'INFO'
        
    # Configure logging with detailed format
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
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console'],
                'level': log_level,
                'propagate': True
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',  # Reduce SQLAlchemy engine log level
                'handlers': ['console'],
                'propagate': False
            },
        }
    })

logger = logging.getLogger(__name__)

def update_storm_data(db: Session, storm_data: dict, region_id: int) -> Storm:
    """Update or create storm data in the database.
    
    Args:
        db: Database session
        storm_data: Dictionary containing storm data
        region_id: ID of the region this storm belongs to
        
    Returns:
        Storm: Updated or created Storm object
    """
    storm_id = storm_data.get('storm_id')
    if not storm_id:
        logger.warning("Storm data missing storm_id, cannot update")
        return None
        
    # Check if storm exists
    storm = db.query(Storm).filter(Storm.storm_id == storm_id).first()
    create_history = False
    
    # Ensure season is set (use current year if not provided)
    if 'season' not in storm_data or not storm_data['season']:
        current_year = datetime.now(timezone.utc).year
        storm_data['season'] = current_year
        logger.debug(f"Set season to current year: {current_year}")
    
    # Set status to active since we found it in the feed
    storm_data['status'] = "active"
    
    try:
        if storm:
            logger.debug(f"Updating existing storm: {storm_id}")
            
            # Check if report_date has changed
            if 'report_date' in storm_data and storm.report_date != storm_data['report_date']:
                logger.debug(f"Report date changed for storm {storm_id}, creating history record")
                create_history = True
            
            # Update storm fields
            for key, value in storm_data.items():
                if hasattr(storm, key):
                    setattr(storm, key, value)
            
            storm.region_id = region_id  # Ensure region is set
        else:
            logger.debug(f"Creating new storm: {storm_id}")
            storm_data['region_id'] = region_id  # Add region_id to storm data
            storm = Storm(**storm_data)
            db.add(storm)
            create_history = True  # Always create history for new storms
        
        # Create history record if needed
        if create_history:
            logger.debug(f"Creating history record for storm {storm_id}")
            history_data = storm_data.copy()
            history_data['region_id'] = region_id  # Add region_id to history data
            
            # Create history record with all the same data
            history_record = StormHistory(**history_data)
            db.add(history_record)
            logger.debug(f"Created history record with status={history_data['status']}, season={history_data['season']}")
        
        db.commit()
        return storm
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating storm data for {storm_id}: {str(e)}", exc_info=True)
        raise

def process_wallet_feed(db: Session, wallet_url: str, region_id: int) -> None:
    """Process a wallet-specific RSS feed to update storm data.
    
    Args:
        db: Database session
        wallet_url: URL to the wallet-specific RSS feed
        region_id: ID of the region this wallet belongs to
    """
    logger.info(f"Processing wallet feed: {wallet_url}")
    
    try:
        soup = fetch_rss_feed(wallet_url)
        if not soup:
            logger.warning(f"No data returned from wallet feed: {wallet_url}")
            return
            
        items = soup.find_all('item')
        logger.debug(f"Found {len(items)} items in wallet feed")
        
        for i, item in enumerate(items, 1):
            logger.debug(f"Processing item {i}/{len(items)} from wallet feed")
            storm_data = get_storm_data(item)
            if storm_data:
                logger.debug(f"Updating storm data from wallet feed item {i}")
                update_storm_data(db, storm_data, region_id)
            else:
                logger.debug(f"No storm data found in wallet feed item {i}")
                
    except Exception as e:
        logger.error(f"Error processing wallet feed {wallet_url}: {str(e)}", exc_info=True)
        raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NHC Storm Tracker Data Pipeline")
    parser.add_argument(
        "--log-level", 
        type=str, 
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: from LOG_LEVEL env var or INFO)"
    )
    return parser.parse_args()


def process_region(db: Session, region: Region) -> None:
    """Process a specific hurricane region.
    
    Args:
        db: Database session
        region: Region object to process
    """
    logger.info(f"Processing region: {region.name} with feed: {region.rss_feed}")
    
    try:
        # Fetch region's RSS feed
        soup = fetch_rss_feed(region.rss_feed)
        if not soup:
            logger.error(f"Failed to fetch RSS feed for region {region.name} - no data returned")
            return
            
        items = soup.find_all('item')
        logger.info(f"Found {len(items)} items in {region.name} feed")
        logger.debug(f"Processing {len(items)} items from {region.name} feed...")
        
        # Process each item in the feed
        for i, item in enumerate(items, 1):
            logger.debug(f"Processing item {i}/{len(items)} from {region.name} feed")
            try:
                storm_data = get_storm_data(item)
                if storm_data:
                    logger.debug(f"Updating storm data for item {i}")
                    storm = update_storm_data(db, storm_data, region.id)
                    
                    # Process wallet feed if available
                    if storm and storm.wallet_url:
                        logger.debug(f"Processing wallet feed for storm {storm.storm_id}")
                        process_wallet_feed(db, storm.wallet_url, region.id)
                    else:
                        logger.debug(f"No wallet URL for storm {storm.storm_id}")
                else:
                    logger.debug(f"No storm data found in item {i}")
                    
            except Exception as e:
                logger.error(f"Error processing item {i} in region {region.name}: {str(e)}", exc_info=True)
                continue  # Continue with next item on error
    
    except Exception as e:
        logger.error(f"Error processing region {region.name}: {str(e)}", exc_info=True)
        raise


def main():
    """Main pipeline function to process NHC feed and update database."""
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging with specified log level
    configure_logging(args.log_level)
    
    logger.info(f"Initializing NHC data pipeline with log level: {args.log_level}")
    
    db = SessionLocal()
    logger.debug("Database session created")
    
    try:
        logger.info("Starting NHC data pipeline...")
        
        # Mark all existing storms as inactive initially
        logger.debug("Marking all existing storms as inactive...")
        updated_count = db.query(Storm).update({"status": "inactive"})
        logger.debug(f"Marked {updated_count} existing storms as inactive")
        db.commit()
        
        # Get all active regions
        active_regions = db.query(Region).filter(Region.active == True).all()
        
        if not active_regions:
            logger.warning("No active regions found in the database")
            return
        
        # Log active regions at INFO level
        region_names = [region.name for region in active_regions]
        logger.info(f"Processing {len(active_regions)} active regions: {', '.join(region_names)}")
        
        # Process each active region
        for region in active_regions:
            process_region(db, region)
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.critical(f"Critical error in pipeline: {str(e)}", exc_info=True)
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()
            logger.debug("Database session closed")

if __name__ == "__main__":
    main()
