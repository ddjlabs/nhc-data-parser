import logging
from sqlalchemy import text
from models import Base, engine, SessionLocal

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
    
    logger.info("Database reset complete")

if __name__ == "__main__":
    reset_database()
