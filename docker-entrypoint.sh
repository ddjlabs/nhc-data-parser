#!/bin/bash
set -e

# Initialize the database if it doesn't exist
if [ ! -f /app/data/nhc_tracker.db ]; then
    echo "Database not found. Initializing database..."
    python reset_db.py
    echo "Database initialized successfully."
fi

# Execute the command passed to the script
exec "$@"
