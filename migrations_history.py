import logging
import sqlite3
import os
from datetime import datetime
from models import DATA_DIR, DB_FILENAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def add_storm_history_table():
    """Add storm_history table to the database."""
    logger.info("Starting migration to add storm_history table")
    
    try:
        # Connect to the database
        logger.info(f"Connecting to database: {DB_FILENAME}")
        conn = sqlite3.connect(DB_FILENAME)
        cursor = conn.cursor()
        
        # Check if storm_history table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='storm_history'")
        if cursor.fetchone():
            logger.info("storm_history table already exists, skipping creation")
            conn.close()
            return
        
        # Create the storm_history table
        logger.info("Creating storm_history table")
        cursor.execute('''
        CREATE TABLE storm_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storm_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            storm_name TEXT,
            storm_type TEXT,
            latitude REAL,
            longitude REAL,
            movement TEXT,
            wind_speed INTEGER,
            pressure INTEGER,
            headline TEXT,
            report TEXT,
            report_link TEXT,
            report_date TIMESTAMP,
            wallet TEXT,
            wallet_url TEXT,
            status TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes
        logger.info("Creating indexes on storm_history table")
        cursor.execute('CREATE INDEX idx_storm_history_storm_id ON storm_history (storm_id)')
        cursor.execute('CREATE INDEX idx_storm_history_season ON storm_history (season)')
        cursor.execute('CREATE INDEX idx_storm_history_recorded_at ON storm_history (recorded_at)')
        
        # Commit the changes
        conn.commit()
        logger.info("Successfully created storm_history table and indexes")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    add_storm_history_table()
