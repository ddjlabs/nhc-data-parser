# Docker Deployment Guide for NHC Storm Tracker

This guide explains how to deploy the NHC Storm Tracker using Docker containers. The application has been split into two separate services:

1. **API Service**: Provides the REST API endpoints for accessing storm data
2. **Pipeline Service**: Handles data collection from NHC feeds on a scheduled basis

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic understanding of Docker concepts

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd nhc-rest-api
   ```

2. Make sure the `config/regions.json` file exists and contains the correct region configurations:
   ```json
   [
       {"region": "Atlantic", "RSSfeed": "https://www.nhc.noaa.gov/index-at.xml", "active": true},
       {"region": "Central Pacific", "RSSfeed": "https://www.nhc.noaa.gov/index-cp.xml", "active": true},
       {"region": "Eastern Pacific", "RSSfeed": "https://www.nhc.noaa.gov/index-ep.xml", "active": true}
   ]
   ```

3. Create a `.env` file with your configuration:
   ```
   # Run every hour at minute 0
   CRON_SCHEDULE=0 */1 * * *
   
   # Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   LOG_LEVEL=INFO
   ```

4. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

5. Access the API at http://localhost:8000

## Container Details

### API Container

- Runs the FastAPI application
- Exposes port 8000 for API access
- Mounts the `data` and `config` directories as volumes
- Automatically initializes the database if it doesn't exist

### Pipeline Container

- Runs the scheduler that executes the data pipeline on a schedule
- Uses the same database as the API container
- Mounts the `data` and `config` directories as volumes
- Automatically initializes the database if it doesn't exist

## Configuration

### Environment Variables

Both containers support the following environment variables:

- `DATABASE_URL`: SQLite database URL (default: `sqlite:///data/nhc_tracker.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `CRON_SCHEDULE`: Cron expression for the pipeline schedule (default: `0 */1 * * *`)
- `DATA_DIR`: Directory for data files (default: `data`)
- `CONFIG_DIR`: Directory for configuration files (default: `config`)

### Volumes

The Docker Compose configuration mounts two volumes:

- `./data:/app/data`: Persists the SQLite database
- `./config:/app/config`: Provides access to configuration files

## Maintenance

### Viewing Logs

```bash
# View logs from the API container
docker-compose logs api

# View logs from the pipeline container
docker-compose logs pipeline

# Follow logs in real-time
docker-compose logs -f
```

### Restarting Services

```bash
# Restart the API service
docker-compose restart api

# Restart the pipeline service
docker-compose restart pipeline

# Restart all services
docker-compose restart
```

### Updating the Application

1. Pull the latest code:
   ```bash
   git pull
   ```

2. Rebuild and restart the containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## Troubleshooting

### Database Issues

If you need to reset the database:

1. Stop the containers:
   ```bash
   docker-compose down
   ```

2. Delete the database file:
   ```bash
   rm data/nhc_tracker.db
   ```

3. Restart the containers:
   ```bash
   docker-compose up -d
   ```

The database will be automatically reinitialized with the regions from your configuration.

### Container Won't Start

Check the logs for errors:

```bash
docker-compose logs
```

Common issues include:
- Missing configuration files
- Permission problems with mounted volumes
- Port conflicts (if port 8000 is already in use)

## Advanced Usage

### Running a One-Time Pipeline Update

To manually trigger the pipeline without waiting for the schedule:

```bash
docker-compose exec pipeline python pipeline.py
```

### Accessing the Database Directly

```bash
docker-compose exec api sqlite3 /app/data/nhc_tracker.db
```

### Custom Configuration

You can modify the Docker Compose file to add custom environment variables or change the port mapping as needed.
