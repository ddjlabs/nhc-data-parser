# NHC Storm Tracker

A Python-based data pipeline and REST API for tracking active hurricanes and tropical storms using data from the National Hurricane Center (NHC) across multiple regions.

## Features

- Multi-region support for tracking storms in Atlantic, Eastern Pacific, and Central Pacific
- Fetches and parses NHC RSS feeds for active storms in all configured regions
- Stores storm data in SQLite database with region association
- Tracks storm history over time in a dedicated history table
- Provides a REST API for accessing storm data with region filtering
- Scheduled pipeline execution using cron expressions
- Includes utilities for database management and debugging
- Supports filtering by region, storm name, ID, status, and season
- Robust XML parsing with namespace handling
- Comprehensive logging with configurable log levels
- Database migration support for schema changes
- Modern timezone handling with UTC standardization

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

### Standard Installation

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

### Docker Installation

Alternatively, you can use Docker to run the application in containers:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd nhc-rest-api
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

This will start two containers:
- API service on port 8000
- Pipeline service running on the configured schedule

See [DOCKER.md](DOCKER.md) for detailed instructions on Docker deployment.

## Usage

### Database Setup and Migration

To initialize or reset the database (including loading region data from config):

```bash
python reset_db.py
```

This will create all database tables and load the region configuration from `config/regions.json`.

To apply database migrations (e.g., adding new fields):

```bash
python migrations.py
```

### Running the Pipeline

```bash
python pipeline.py --log-level INFO
```

This will fetch the latest storm data from all active regions in the NHC and update the database. You can set the log level to one of: DEBUG, INFO, WARNING, ERROR, or CRITICAL.

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

Edit the `.env` file to set your preferred schedule and log level:

```
# Run every hour at minute 0
CRON_SCHEDULE=0 */1 * * *

# Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

#### Region Configuration

Regions are configured in the `config/regions.json` file. Each region has the following properties:
- `region`: Name of the region (e.g., "Atlantic", "Eastern Pacific")
- `RSSfeed`: URL to the region's RSS feed
- `active`: Boolean indicating whether the region is active

### Storm History Tracking

The system automatically tracks the history of storm data changes. For existing storms, a new history record is created only when the `report_date` changes, ensuring that history records represent meaningful updates. For new storms, a history record is always created upon first detection.

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
  - `region_id` - Filter by region ID
- `GET /api/v1/storms/{storm_id}` - Get storm by ID
- `GET /api/v1/storms/name/{storm_name}` - Search storms by name
- `GET /api/v1/regions` - Get all regions
- `GET /api/v1/regions/active` - Get all active regions
- `GET /api/v1/regions/{region_id}` - Get region by ID
- `GET /api/v1/regions/{region_id}/storms` - Get all storms for a specific region

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

#### Regions Table

The `regions` table includes the following fields:
- `id`: Primary key
- `name`: Region name (e.g., Atlantic, Eastern Pacific)
- `rss_feed`: URL to the region's RSS feed
- `active`: Whether this region is active
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

#### Storms Table

The `storms` table includes the following fields:
- `id`: Primary key
- `region_id`: Foreign key to the regions table
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

#### Storm History Table

The `storm_history` table has the same structure as the `storms` table, with an additional `recorded_at` timestamp to track when the history record was created.

## License

This project is open source and available under the [MIT License](LICENSE).

## Project Structure

- `api.py`: FastAPI implementation with endpoints and middleware
- `models.py`: SQLAlchemy ORM models and database configuration
- `nhc_parser.py`: RSS feed parser with robust XML handling
- `pipeline.py`: Main data pipeline for fetching and processing storm data
- `migrations.py`: Database migration script for schema updates
- `reset_db.py`: Utility to reset the database and load region configuration
- `setup.bat`: Windows setup script for environment initialization
- `config/regions.json`: Configuration file for hurricane tracking regions

## Recent Updates

### Multi-Region Support
- Added support for tracking hurricanes across multiple regions (Atlantic, Eastern Pacific, Central Pacific)
- Created a new `regions` table to store region information
- Updated the pipeline to process all active regions dynamically
- Added region-specific API endpoints
- Added foreign key relationships between storms and regions

### API Enhancements
- Added new region-related endpoints
- Updated response models to include region information
- Added ability to filter storms by region

### Database Improvements
- Added region support to database schema
- Enhanced reset_db.py to load regions from config file
- Improved history tracking to only create records on meaningful updates

### Technical Improvements
- Added configurable logging levels via command line and environment variables
- Fixed timezone handling with proper tzinfo dictionaries
- Updated datetime handling to use modern timezone-aware approaches
- Improved error handling and reporting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
