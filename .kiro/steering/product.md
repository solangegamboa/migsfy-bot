---
inclusion: always
---

# Product Overview

SLSKD MP3 Search & Download Tool (migsfy-bot) is an intelligent music discovery and download system that integrates multiple music services.

## Core Functionality

- **Primary Purpose**: Search and download MP3s via slskd (SoulSeek daemon)
- **Spotify Integration**: Playlist and track metadata extraction
- **Last.fm Integration**: Tag-based discovery and metadata enhancement
- **Telegram Bot**: Chat-based music search interface
- **CLI Interface**: Direct command-line operations

## Development Guidelines

### Code Style & Conventions

- Use `snake_case` for Python files and functions
- Implement graceful error handling with try/except blocks
- Add comprehensive logging for all operations
- Follow modular architecture with clear separation of concerns
- Use relative imports within modules, absolute for cross-module

### Architecture Patterns

- **CLI Layer**: Entry points in `src/cli/`
- **Core Logic**: Business logic in `src/core/`
- **Bot Interface**: Telegram handlers in `src/telegram/`
- **Utilities**: Shared functions in `src/utils/`
- **Configuration**: Environment-based config with `.env` files

### Key Features to Maintain

- Smart fuzzy matching for album/track searches
- Download history tracking with duplicate prevention
- Multi-language support (Portuguese primary, English fallback)
- Automatic metadata extraction and file organization
- Docker containerization for deployment

### Error Handling Standards

- Always handle API failures gracefully
- Log errors with context and stack traces
- Provide user-friendly error messages in Telegram bot
- Implement retry logic for network operations
- Validate inputs before processing

### Testing Requirements

- Unit tests for individual functions
- Integration tests for API interactions
- Use pytest markers: `unit`, `integration`, `telegram`, `spotify`
- Mock external API calls in tests
- Maintain test fixtures in `tests/fixtures/`
