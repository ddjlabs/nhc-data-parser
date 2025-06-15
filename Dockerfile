FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files for the pipeline
COPY pipeline.py .
COPY models.py .
COPY nhc_parser.py .
COPY scheduler.py .
COPY reset_db.py .
COPY docker-entrypoint.sh .

# Create directories
RUN mkdir -p data config

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Command to run the scheduler (which will run the pipeline on schedule)
CMD ["python", "scheduler.py"]
