# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY slskd-mp3-search.py .
COPY docker-entrypoint.sh .
COPY .env.example .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create directories for data persistence
RUN mkdir -p /app/data /app/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SPOTIFY_CACHE_PATH=/app/cache/.spotify_cache

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Default command (will be passed to entrypoint)
CMD []
