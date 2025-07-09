#!/bin/bash
set -e

# Function to display usage
show_usage() {
    echo "🎵 SLSKD MP3 Search & Download Tool - Docker Edition"
    echo ""
    echo "Usage:"
    echo "  docker run migsfy-bot [command] [options]"
    echo ""
    echo "Examples:"
    echo "  # Search for a song"
    echo "  docker run migsfy-bot \"Artist - Song\""
    echo ""
    echo "  # Download Spotify playlist"
    echo "  docker run migsfy-bot --playlist \"URL\" --auto"
    echo ""
    echo "  # Show history"
    echo "  docker run migsfy-bot --history"
    echo ""
    echo "  # Interactive mode"
    echo "  docker run -it migsfy-bot bash"
    echo ""
}

# Check if .env file exists
if [ ! -f "/app/.env" ]; then
    echo "⚠️ Warning: .env file not found!"
    echo "💡 Please mount your .env file or use environment variables"
    echo "💡 Example: docker run -v $(pwd)/.env:/app/.env migsfy-bot"
    echo ""
fi

# Create necessary directories
mkdir -p /app/data /app/cache

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    show_usage
    exec python slskd-mp3-search.py
else
    # Execute the Python script with provided arguments
    exec python slskd-mp3-search.py "$@"
fi
