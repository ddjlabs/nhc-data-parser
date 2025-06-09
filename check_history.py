#!/usr/bin/env python
import logging
from sqlalchemy import select, func
from models import SessionLocal, Storm, StormHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_storm_history():
    """Check the storm_history table and display statistics."""
    with SessionLocal() as db:
        # Count storms in the main table
        storm_count = db.query(func.count(Storm.id)).scalar()
        logger.info(f"Total storms in database: {storm_count}")
        
        # Count history records
        history_count = db.query(func.count(StormHistory.id)).scalar()
        logger.info(f"Total storm history records: {history_count}")
        
        # Get unique storm IDs in history
        unique_storms = db.query(func.count(func.distinct(StormHistory.storm_id))).scalar()
        logger.info(f"Number of unique storms with history: {unique_storms}")
        
        # Show sample history records
        logger.info("Sample history records:")
        history_records = db.query(StormHistory).order_by(StormHistory.recorded_at.desc()).limit(5).all()
        
        for record in history_records:
            logger.info(f"Storm: {record.storm_name} (ID: {record.storm_id})")
            logger.info(f"  Type: {record.storm_type}")
            logger.info(f"  Position: {record.latitude}, {record.longitude}")
            logger.info(f"  Wind Speed: {record.wind_speed} MPH")
            logger.info(f"  Pressure: {record.pressure} mb")
            logger.info(f"  Recorded At: {record.recorded_at}")
            logger.info("---")

if __name__ == "__main__":
    check_storm_history()
