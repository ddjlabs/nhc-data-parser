FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install MariaDB repository and client library
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "b3d5fb3ea9791e93b64a97e8b8a5faacd6e744e9d2c1c7cc3453f0390aa76569 mariadb_repo_setup" | sha256sum -c -
RUN chmod +x mariadb_repo_setup && ./mariadb_repo_setup --mariadb-server-version="mariadb-10.5"
RUN apt update && apt install -y libmariadb3 libmariadb-dev && rm mariadb_repo_setup

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/. /app/

# Create directories
RUN mkdir -p data config

# Clear out any raw-files that may have copied from the source app
RUN rm -rf app/raw-files/*

# Make entrypoint script executable if it exists
RUN if [ -f docker-entrypoint.sh ]; then chmod +x docker-entrypoint.sh; fi

# Set the entrypoint script if it exists
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command to run the application
CMD ["python", "main.py"]
