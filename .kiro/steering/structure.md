# Project Structure & Organization

## Directory Layout

```
migsfy-bot/
├── src/                    # Source code (main application logic)
│   ├── cli/               # Command-line interface
│   ├── core/              # Core business logic modules
│   │   └── lastfm/        # Last.fm integration
│   ├── telegram/          # Telegram bot implementation
│   │   └── handlers/      # Bot command handlers
│   └── utils/             # Shared utility functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data and fixtures
├── docs/                  # Documentation
│   ├── CHANGELOG/         # Version history
│   ├── DOCKER/            # Docker-specific docs
│   └── TELEGRAM/          # Telegram bot documentation
├── config/                # Configuration templates
├── scripts/               # Shell scripts and automation
├── logs/                  # Application logs
├── data/                  # Runtime data (download history)
└── cache/                 # Temporary cache files
```

## Code Organization Principles

### Module Structure
- **src/cli/**: Entry points for command-line usage
- **src/core/**: Business logic, API integrations, core algorithms
- **src/telegram/**: Bot-specific code, handlers, message processing
- **src/utils/**: Reusable utilities (file processing, name extraction)

### Import Conventions
- Use relative imports within modules
- Add `sys.path.insert(0, ...)` for cross-module imports
- Graceful handling of optional dependencies with try/except blocks

### File Naming
- Python files: `snake_case.py`
- Test files: `test_*.py` or `*_test.py`
- Scripts: `kebab-case.sh`
- Documentation: `UPPERCASE.md` for main docs, `lowercase.md` for specific guides

## Configuration Files

- **Root level**: `.env`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
- **Config directory**: Templates and examples (`.env.example`)
- **Hidden directories**: `.kiro/`, `.git/`, `.pytest_cache/`

## Data Flow Architecture

1. **CLI Entry** → `src/cli/main.py`
2. **Core Processing** → `src/core/` modules
3. **External APIs** → Spotify, Last.fm, SLSKD integrations
4. **Bot Interface** → `src/telegram/bot.py`
5. **Utilities** → `src/utils/` for common operations

## Testing Structure

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test API integrations and workflows
- **Fixtures**: Shared test data in `tests/fixtures/`
- **Markers**: Use pytest markers for test categorization