# Database Initialization Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy initialization script
COPY init_db.py .

# Create data directory
RUN mkdir -p /app/data

# Default command
CMD ["python", "init_db.py", "/app/data/nba_data.db"]
