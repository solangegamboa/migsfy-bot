# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/.env.example .env.example

# Make scripts executable
RUN chmod +x scripts/*.sh

# Create directories for data persistence
RUN mkdir -p /app/data /app/cache /app/logs

# Setup cron job for retry failed downloads (daily at 2 AM)
RUN echo "0 2 * * * /app/scripts/retry-failed-downloads.sh >> /app/logs/retry-failed.log 2>&1" > /etc/cron.d/retry-failed
RUN chmod 0644 /etc/cron.d/retry-failed
RUN crontab /etc/cron.d/retry-failed

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SPOTIFY_CACHE_PATH=/app/cache/.spotify_cache
ENV PUID=0
ENV PGID=0

USER root

# Set entrypoint
ENTRYPOINT ["./scripts/docker-entrypoint.sh"]

# Default command (will be passed to entrypoint)
CMD []
