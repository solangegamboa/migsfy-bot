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
    echo "  # Start Telegram bot"
    echo "  docker run migsfy-bot --telegram-bot"
    echo ""
    echo "  # Interactive mode"
    echo "  docker run -it migsfy-bot bash"
    echo ""
}

# Handle PUID and PGID
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "🔧 Setting up user with PUID=$PUID and PGID=$PGID"

# Create group if it doesn't exist
if ! getent group $PGID > /dev/null 2>&1; then
    groupadd -g $PGID appgroup
else
    GROUPNAME=$(getent group $PGID | cut -d: -f1)
fi

# Create user if it doesn't exist
if ! getent passwd $PUID > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -m -s /bin/bash appuser
else
    USERNAME=$(getent passwd $PUID | cut -d: -f1)
    usermod -g $PGID $USERNAME
fi

# Get the actual username
USERNAME=$(getent passwd $PUID | cut -d: -f1)

# Create necessary directories and set permissions
mkdir -p /app/data /app/cache
chown -R $PUID:$PGID /app/data /app/cache

# Check if .env file exists
if [ ! -f "/app/.env" ]; then
    echo "⚠️ Warning: .env file not found!"
    echo "💡 Please mount your .env file or use environment variables"
    echo "💡 Example: docker run -v $(pwd)/.env:/app/.env migsfy-bot"
    echo ""
fi

# Function to run command as the specified user
run_as_user() {
    if [ "$PUID" = "0" ]; then
        # Running as root
        exec "$@"
    else
        # Running as specified user
        exec su-exec $USERNAME "$@"
    fi
}

# Install su-exec if not present (for Alpine-based images)
if ! command -v su-exec &> /dev/null; then
    # For Debian/Ubuntu based images, use gosu instead
    if ! command -v gosu &> /dev/null; then
        echo "Installing gosu for user switching..."
        apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*
        run_as_user() {
            if [ "$PUID" = "0" ]; then
                exec "$@"
            else
                exec gosu $USERNAME "$@"
            fi
        }
    fi
fi

# Check for Telegram bot command
if [ "$1" = "--telegram-bot" ] || [ "$1" = "--bot" ]; then
    echo "🤖 Starting Telegram Bot..."
    run_as_user python telegram_bot.py
fi

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    show_usage
    run_as_user python slskd-mp3-search.py
else
    # Execute the Python script with provided arguments
    run_as_user python slskd-mp3-search.py "$@"
fi
