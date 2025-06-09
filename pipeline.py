import logging
import logging.config
from datetime import datetime
from sqlalchemy.orm import Session
from models import Storm, SessionLocal, init_db
from nhc_parser import fetch_rss_feed, get_storm_data

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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'DEBUG',
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

def update_storm_data(db: Session, storm_data: dict) -> Storm:
    """Update or create storm record in database."""
    logger.debug(f"Updating storm data: {storm_data.get('storm_id')}")
    
    # Ensure season is set to current year for new storms
    if 'season' not in storm_data:
        storm_data['season'] = datetime.utcnow().year
        logger.debug(f"Set season to current year: {storm_data['season']}")
    
    # Check if storm already exists
    storm = db.query(Storm).filter(Storm.storm_id == storm_data["storm_id"]).first()
    
    if storm:
        # Update existing storm
        updates = []
        for key, value in storm_data.items():
            if getattr(storm, key) != value:
                updates.append(f"{key}: {getattr(storm, key)} -> {value}")
                setattr(storm, key, value)
        storm.status = "active"
        
        if updates:
            logger.debug(f"Updating storm {storm.storm_name} ({storm.storm_id}) with changes: {', '.join(updates)}")
            logger.info(f"Updated storm: {storm.storm_name} ({storm.storm_id})")
        else:
            logger.debug(f"No changes detected for storm {storm.storm_name} ({storm.storm_id})")
    else:
        # Create new storm
        storm = Storm(**storm_data)
        storm.status = "active"
        db.add(storm)
        logger.debug(f"Creating new storm: {storm.storm_name} ({storm.storm_id})")
        logger.info(f"Added new storm: {storm.storm_name} ({storm.storm_id})")
    
    try:
        db.commit()
        db.refresh(storm)
        logger.debug(f"Successfully committed changes for storm {storm.storm_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing storm {storm.storm_id}: {str(e)}", exc_info=True)
        raise
        
    return storm

def process_wallet_feed(db: Session, wallet_url: str):
    """Process individual wallet feed for additional storm data."""
    if not wallet_url:
        logger.debug("No wallet URL provided, skipping wallet feed processing")
        return
        
    logger.info(f"Processing wallet feed: {wallet_url}")
    logger.debug(f"Fetching wallet feed from URL: {wallet_url}")
    
    try:
        soup = fetch_rss_feed(wallet_url)
        if not soup:
            logger.warning(f"No data returned from wallet feed: {wallet_url}")
            return
            
        items = soup.find_all('item')
        logger.debug(f"Found {len(items)} items in wallet feed: {wallet_url}")
        
        for i, item in enumerate(items, 1):
            logger.debug(f"Processing item {i}/{len(items)} from wallet feed")
            storm_data = get_storm_data(item)
            if storm_data:
                logger.debug(f"Updating storm data from wallet feed item {i}")
                update_storm_data(db, storm_data)
            else:
                logger.debug(f"No storm data found in wallet feed item {i}")
                
    except Exception as e:
        logger.error(f"Error processing wallet feed {wallet_url}: {str(e)}", exc_info=True)
        raise

def main():
    """Main pipeline function to process NHC feed and update database."""
    logger.info("Initializing NHC data pipeline...")
    
    # Initialize database
    logger.debug("Initializing database...")
    init_db()
    
    db = SessionLocal()
    logger.debug("Database session created")
    
    try:
        logger.info("Starting NHC data pipeline...")
        
        # Mark all existing storms as inactive initially
        logger.debug("Marking all existing storms as inactive...")
        updated_count = db.query(Storm).update({"status": "inactive"})
        logger.debug(f"Marked {updated_count} existing storms as inactive")
        db.commit()
        
        # Fetch main NHC RSS feed
        main_feed_url = "https://www.nhc.noaa.gov/index-ep.xml"
        logger.info(f"Fetching main feed: {main_feed_url}")
        logger.debug("Initiating RSS feed fetch...")
        
        soup = fetch_rss_feed(main_feed_url)
        if not soup:
            logger.error("Failed to fetch main RSS feed - no data returned")
            return
            
        items = soup.find_all('item')
        logger.info(f"Found {len(items)} items in main feed")
        logger.debug(f"Processing {len(items)} items from main feed...")
        
        # Process each item in the feed
        for i, item in enumerate(items, 1):
            logger.debug(f"Processing item {i}/{len(items)} from main feed")
            try:
                storm_data = get_storm_data(item)
                if storm_data:
                    logger.debug(f"Updating storm data for item {i}")
                    storm = update_storm_data(db, storm_data)
                    
                    # Process wallet feed if available
                    if storm and storm.wallet_url:
                        logger.debug(f"Processing wallet feed for storm {storm.storm_id}")
                        process_wallet_feed(db, storm.wallet_url)
                    else:
                        logger.debug(f"No wallet URL for storm {storm.storm_id}")
                else:
                    logger.debug(f"No storm data found in item {i}")
                    
            except Exception as e:
                logger.error(f"Error processing item {i}: {str(e)}", exc_info=True)
                continue  # Continue with next item on error
        
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
