import logging
import json
import os
from sqlalchemy import text
from datetime import datetime
from models import Base, engine, SessionLocal, Region, load_regions_from_json, update_existing_storms_region

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def reset_database():
    """Drop all tables and recreate them to reset the database."""
    logger.info("Resetting database...")
    
    # Drop all tables
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(engine)
    logger.info("All tables dropped successfully")
    
    # Recreate tables
    logger.info("Recreating tables...")
    Base.metadata.create_all(engine)
    logger.info("Tables recreated successfully")
    
    # Load regions from config file
    logger.info("Loading regions from config file...")
    db = SessionLocal()
    try:
        # Load regions from config/regions.json
        config_dir = os.environ.get("CONFIG_DIR", "config")
        config_path = os.path.join(config_dir, "regions.json")
        if os.path.exists(config_path):
            # Call load_regions_from_json with just the db session
            load_regions_from_json(db)
            
            # Query and log the loaded regions
            regions = db.query(Region).all()
            logger.info(f"Loaded {len(regions)} regions from config file")
            for region in regions:
                logger.info(f"  - {region.name} ({'active' if region.active else 'inactive'})")
        else:
            logger.warning(f"Config file not found: {config_path}")
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading regions: {str(e)}")
        raise
    finally:
        db.close()
    
    logger.info("Database reset complete")

if __name__ == "__main__":
    reset_database()
    logger.info("Database has been reset and initialized with region data")
