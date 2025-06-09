import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SessionType
from datetime import datetime
import pytz
import os

# Configure logging
logger = logging.getLogger(__name__)

# Database setup
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)  # Ensure data directory exists
DB_FILENAME = os.path.join(DATA_DIR, "nhc_tracker.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILENAME}"

def get_engine():
    """Create and configure the SQLAlchemy engine with logging."""
    logger.info(f"Initializing database engine for SQLite database: {DB_FILENAME}")
    return create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL query logging
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add event listeners for connection and transaction events
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    logger.debug(f"New database connection established: {dbapi_connection}")

@event.listens_for(engine, 'close')
def receive_close(dbapi_connection, connection_record):
    logger.debug("Database connection closed")

@event.listens_for(engine, 'before_cursor_execute')
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    if len(statement) > 1000:
        statement = statement[:1000] + '...'
    logger.debug(f"Executing SQL: {statement}")
    if params:
        logger.debug(f"Parameters: {params}")

@event.listens_for(engine, 'after_cursor_execute')
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    if context and hasattr(context, 'rowcount'):
        logger.debug(f"Rows affected: {context.rowcount}")

@event.listens_for(engine, 'handle_error')
def receive_handle_error(exception_context):
    logger.error("Database error occurred", exc_info=exception_context.original_exception)

def get_db() -> SessionType:
    """Get a database session with proper error handling."""
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error, rolling back changes", exc_info=True)
        db.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        db.close()

class Storm(Base):
    __tablename__ = "storms"
    
    id = Column(Integer, primary_key=True, index=True)
    storm_id = Column(String, unique=True, index=True, comment="Unique storm identifier from NHC")
    season = Column(Integer, index=True, comment="Storm season (year)", default=lambda: datetime.utcnow().year)
    storm_name = Column(String, comment="Name of the storm")
    storm_type = Column(String, comment="Type of storm (e.g., Hurricane, Tropical Storm)")
    latitude = Column(Float, comment="Current latitude of storm center")
    longitude = Column(Float, comment="Current longitude of storm center")
    movement = Column(String, comment="Movement direction and speed")
    wind_speed = Column(Integer, comment="Maximum sustained wind speed in MPH")
    pressure = Column(Integer, comment="Minimum central pressure in mb")
    headline = Column(String, comment="Headline/most important information")
    report = Column(String, comment="Full report/description from RSS")
    report_link = Column(String, comment="URL to the full report")
    report_date = Column(DateTime, comment="Date/time when the report was published")
    wallet = Column(String, comment="NHC wallet identifier")
    wallet_url = Column(String, comment="URL to the wallet-specific RSS feed")
    status = Column(String, default="active", comment="Current status (active/inactive)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                       comment="Record last update timestamp")
    
    def __repr__(self) -> str:
        return f"<Storm(id={self.id}, name='{self.storm_name}', type='{self.storm_type}', season={self.season})>"
    
    @classmethod
    def get_current_season(cls) -> int:
        """Get the current storm season (year)."""
        return datetime.utcnow().year
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Create tables
def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database tables", exc_info=True)
        raise

if __name__ == "__main__":
    init_db()
