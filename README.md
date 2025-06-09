# NHC Storm Tracker

A Python-based data pipeline and REST API for tracking active hurricanes and tropical storms using data from the National Hurricane Center (NHC).

## Features

- Fetches and parses NHC RSS feeds for active storms
- Stores storm data in SQLite database
- Tracks storm history over time in a dedicated history table
- Provides a REST API for accessing storm data
- Scheduled pipeline execution using cron expressions
- Includes utilities for database management and debugging
- Supports filtering by storm name, ID, status, and season
- Robust XML parsing with namespace handling
- Comprehensive logging for debugging and monitoring
- Database migration support for schema changes

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd nhc-rest-api
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Database Setup and Migration

To initialize or reset the database:

```bash
python reset_db.py
```

To apply database migrations (e.g., adding the season field):

```bash
python migrations.py
```

### Running the Pipeline

```bash
python pipeline.py
```

This will fetch the latest storm data from NHC and update the database.

### Running the Scheduled Pipeline

```bash
python scheduler.py
```

This will run the pipeline on a schedule defined in the `.env` file. The schedule is specified using cron syntax.

### Configuration

Copy the `.env.example` file to `.env` and adjust the settings:

```bash
cp .env.example .env
```

Edit the `.env` file to set your preferred schedule:

```
# Run every hour at minute 0
CRON_SCHEDULE=0 */1 * * *
```

### Storm History Tracking

The system now automatically tracks the history of storm data changes. Each time a storm's data is updated, a new record is added to the `storm_history` table, allowing you to track how storms evolve over time.

To start the FastAPI server:

```bash
uvicorn api:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### API Endpoints

- `GET /` - API root with available endpoints
- `GET /api/v1/storms/active` - Get all active storms
- `GET /api/v1/storms` - Get all storms with optional filters:
  - `season` - Filter by storm season year (defaults to current year if not specified)
  - `status` - Filter by storm status (active/inactive)
  - `storm_type` - Filter by storm type (e.g., HURRICANE, TROPICAL STORM)
  - `min_wind_speed` - Filter by minimum wind speed in MPH
- `GET /api/v1/storms/{storm_id}` - Get storm by ID
- `GET /api/v1/storms/name/{storm_name}` - Search storms by name

### Setting Up a Scheduled Task (Optional)

To keep the storm data up to date, you can set up a scheduled task to run the pipeline periodically. For example, to run it every hour:

#### On Linux/macOS (cron):
```bash
0 * * * * cd /path/to/nhc-rest-api && /path/to/venv/bin/python pipeline.py >> pipeline.log 2>&1
```

#### On Windows (Task Scheduler):
1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger to "Daily" and configure it to repeat every 1 hour
4. Set the action to "Start a program" and point it to your Python script

## Database

The application uses SQLite and stores the database in a file named `nhc_tracker.db` in the `data` directory.

### Database Schema

The main table `storms` includes the following fields:

- `id`: Primary key
- `storm_id`: Unique identifier from NHC (e.g., EP022025)
- `season`: Storm season year (e.g., 2025)
- `storm_name`: Name of the storm (e.g., Barbara)
- `storm_type`: Type of storm (e.g., HURRICANE, TROPICAL STORM)
- `latitude`: Current latitude position
- `longitude`: Current longitude position
- `movement`: Direction and speed of movement
- `wind_speed`: Maximum sustained wind speed in MPH
- `pressure`: Barometric pressure in millibars
- `headline`: Current headline for the storm
- `report`: Full text report
- `report_link`: Link to the detailed report
- `report_date`: Date and time of the report (UTC)
- `wallet`: NHC wallet identifier
- `wallet_url`: URL to the wallet RSS feed
- `status`: Current status (active/inactive)
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

## License

This project is open source and available under the [MIT License](LICENSE).

## Project Structure

- `api.py`: FastAPI implementation with endpoints and middleware
- `models.py`: SQLAlchemy ORM models and database configuration
- `nhc_parser.py`: RSS feed parser with robust XML handling
- `pipeline.py`: Main data pipeline for fetching and processing storm data
- `migrations.py`: Database migration script for schema updates
- `reset_db.py`: Utility to reset the database
- `setup.bat`: Windows setup script for environment initialization

## Recent Updates

- Added `season` field to track the year of each storm
- Improved XML parsing to handle namespace variations
- Fixed storm type extraction to correctly capture storm classifications
- Added database migration support
- Enhanced error handling and logging
- Added robust namespace handling for XML parsing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
