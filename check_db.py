from sqlalchemy import create_engine, inspect, text
from models import Base, Storm, SessionLocal, DB_FILENAME, SQLALCHEMY_DATABASE_URL

def check_database():
    # Use the same database engine configuration as in models.py
    print(f"Using database: {DB_FILENAME}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Get table information
        inspector = inspect(engine)
        columns = inspector.get_columns('storms')
        
        print("\n=== Database Schema ===")
        print("Columns in 'storms' table:")
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
            
        # Check if any data exists
        result = db.execute(text("SELECT COUNT(*) as count FROM storms"))
        count = result.scalar()
        print(f"\nTotal storms in database: {count}")
        
        if count > 0:
            # Get sample data
            print("\nSample storm data:")
            result = db.execute(text("SELECT storm_id, storm_name, storm_type, season FROM storms LIMIT 5"))
            for row in result:
                print(f"ID: {row.storm_id}, Name: {row.storm_name}, Type: {row.storm_type}, Season: {row.season}")
                
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
