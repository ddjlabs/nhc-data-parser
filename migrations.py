import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from models import Base, engine, SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(column_name: str, table_name: str = 'storms') -> bool:
    """Check if a column exists in a table."""
    with engine.connect() as conn:
        try:
            # SQLite specific query to check column existence
            result = conn.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
            return any(col[1] == column_name for col in result)
        except Exception as e:
            logger.error(f"Error checking if column {column_name} exists: {e}")
            return False

def add_season_column():
    """Add season column to storms table if it doesn't exist."""
    if check_column_exists('season'):
        logger.info("Column 'season' already exists in 'storms' table")
        return
    
    db = SessionLocal()
    try:
        logger.info("Adding 'season' column to 'storms' table")
        
        # Get current year for default value
        from datetime import datetime
        current_year = datetime.utcnow().year
        
        # Add the column with a default value
        db.execute(text(
            f"ALTER TABLE storms ADD COLUMN season INTEGER DEFAULT {current_year}"
        ))
        
        # Create an index on the season column
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_storms_season ON storms(season)"
        ))
        
        db.commit()
        logger.info("Successfully added 'season' column to 'storms' table")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error adding 'season' column: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting database migration")
    add_season_column()
    logger.info("Database migration completed")
