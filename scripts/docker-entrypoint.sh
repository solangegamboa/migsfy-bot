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

# Handle PUID and PGID (default to root)
PUID=${PUID:-0}
PGID=${PGID:-0}

echo "🔧 Running with PUID=$PUID and PGID=$PGID"

# Create necessary directories and set permissions
mkdir -p /app/data /app/cache /app/logs
chmod 755 /app/data /app/cache /app/logs

# Setup cron for Last.fm auto downloads if configured
if [ -f "/app/.env" ] && grep -q "LASTFM_AUTO_TAGS" /app/.env; then
    echo "⏰ Configurando cron para downloads automáticos do Last.fm..."
    
    # Install crontab
    if [ -f "/app/scripts/crontab-lastfm" ]; then
        crontab /app/scripts/crontab-lastfm
        echo "✅ Crontab instalado"
    fi
    
    # Start cron service
    service cron start
    echo "🚀 Serviço cron iniciado"
    
    # Show next scheduled run
    NEXT_RUN=$(crontab -l | grep lastfm-auto-download | head -1 | awk '{print $1, $2, $3, $4, $5}')
    echo "📅 Próxima execução: $NEXT_RUN (a cada 48 horas)"
else
    echo "ℹ️ Cron não configurado (LASTFM_AUTO_TAGS não encontrado no .env)"
fi

# Check if .env file exists
if [ ! -f "/app/.env" ]; then
    echo "⚠️ Warning: .env file not found!"
    echo "💡 Please mount your .env file or use environment variables"
    echo "💡 Example: docker run -v $(pwd)/.env:/app/.env migsfy-bot"
    echo ""
fi

# Function to run command (simplified for root usage)
run_command() {
    if [ "$PUID" = "0" ] && [ "$PGID" = "0" ]; then
        # Running as root (default)
        exec "$@"
    else
        # If custom PUID/PGID specified, try to use them
        if command -v gosu &> /dev/null; then
            # Create user if needed
            if ! getent passwd $PUID > /dev/null 2>&1; then
                if ! getent group $PGID > /dev/null 2>&1; then
                    groupadd -g $PGID appgroup
                fi
                useradd -u $PUID -g $PGID -m -s /bin/bash appuser
            fi
            USERNAME=$(getent passwd $PUID | cut -d: -f1)
            chown -R $PUID:$PGID /app/data /app/cache /app/logs
            exec gosu $USERNAME "$@"
        else
            echo "⚠️ Custom PUID/PGID specified but gosu not available, running as root"
            exec "$@"
        fi
    fi
}

# Check for Telegram bot command
if [ "$1" = "--telegram-bot" ] || [ "$1" = "--bot" ]; then
    echo "🤖 Starting Telegram Bot..."
    run_command python src/telegram/bot.py
fi

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    show_usage
    run_command python src/cli/main.py
else
    # Execute the Python script with provided arguments
    run_command python src/cli/main.py "$@"
fi
