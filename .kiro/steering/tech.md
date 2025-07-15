# Technology Stack

## Core Technologies

- **Python 3.x**: Primary programming language
- **slskd-api**: SoulSeek daemon integration for P2P music downloads
- **spotipy**: Spotify Web API client for playlist and track metadata
- **pylast**: Last.fm API client for music discovery and tagging
- **python-telegram-bot**: Telegram Bot API wrapper
- **python-dotenv**: Environment variable management
- **music-tag**: Audio file metadata manipulation

## Testing Framework

- **pytest**: Primary testing framework
- **pytest-cov**: Code coverage reporting
- Test organization: `tests/unit/` and `tests/integration/`
- Custom pytest markers: `unit`, `integration`, `slow`, `telegram`, `spotify`, `slskd`, `markdown`, `album`

## Build System & Deployment

### Docker

- **Dockerfile**: Multi-stage build with Python base image
- **docker-compose.yml**: Service orchestration with health checks
- **Makefile**: Comprehensive build and deployment commands

### Key Make Commands

```bash
make build          # Build Docker image
make run            # Run container interactively
make telegram-bot   # Start Telegram bot service
make up             # Start with docker-compose
make test           # Run pytest test suite
make clean          # Clean Docker resources
```

### Local Development

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run CLI
python3 src/cli/main.py "search term"

# Run tests
python3 -m pytest tests/

# Start Telegram bot
./scripts/run-telegram-bot.sh
```

## Configuration Management

- **Environment Variables**: `.env` file for API keys and configuration
- **Config Templates**: `config/.env.example` for setup guidance
- **Docker Environment**: PUID/PGID for permission management
- **Logging**: Structured logging to `logs/` directory

## Dependencies Management

- **requirements.txt**: All Python dependencies with version constraints
- **Optional Dependencies**: Graceful degradation when optional packages unavailable
- **System Dependencies**: Handled via Dockerfile (gcc, g++)
