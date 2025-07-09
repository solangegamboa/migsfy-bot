# Makefile for SLSKD MP3 Search & Download Tool

# Variables
IMAGE_NAME = migsfy-bot
CONTAINER_NAME = migsfy-bot
VERSION = latest

# Get current user IDs (default to root)
PUID := 0
PGID := 0

# Build the Docker image
build:
	@echo "🔨 Building Docker image..."
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Build with no cache
build-no-cache:
	@echo "🔨 Building Docker image (no cache)..."
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) .

# Run the container interactively
run:
	@echo "🚀 Running container..."
	docker run --rm -it \
		-e PUID=$(PUID) \
		-e PGID=$(PGID) \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION)

# Show current user IDs
show-ids:
	@echo "Current User IDs:"
	@echo "PUID=$(PUID)"
	@echo "PGID=$(PGID)"

# Run Telegram bot
telegram-bot:
	@echo "🤖 Starting Telegram bot..."
	docker run --rm -it \
		-e PUID=$(PUID) \
		-e PGID=$(PGID) \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION) --telegram-bot

# Run Telegram bot locally (without Docker)
telegram-bot-local:
	@echo "🤖 Starting Telegram bot locally..."
	./run-telegram-bot.sh

# Run with docker-compose
up:
	@echo "🚀 Starting with docker-compose..."
	PUID=$(PUID) PGID=$(PGID) docker-compose up -d

# Run with docker-compose (foreground)
up-fg:
	@echo "🚀 Starting with docker-compose (foreground)..."
	PUID=$(PUID) PGID=$(PGID) docker-compose up

# Stop docker-compose services
down:
	@echo "🛑 Stopping docker-compose services..."
	docker-compose down

# View logs
logs:
	@echo "📋 Viewing logs..."
	docker-compose logs -f

# Search for a song
search:
	@echo "🎵 Searching for song..."
	@read -p "Enter search term: " term; \
	docker run --rm -it \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION) "$$term"

# Download Spotify playlist
playlist:
	@echo "🎵 Downloading Spotify playlist..."
	@read -p "Enter playlist URL: " url; \
	docker run --rm -it \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION) --playlist "$$url" --auto

# Show download history
history:
	@echo "📋 Showing download history..."
	docker run --rm -it \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION) --history

# Open interactive shell
shell:
	@echo "🐚 Opening interactive shell..."
	docker run --rm -it \
		-e PUID=$(PUID) \
		-e PGID=$(PGID) \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		--entrypoint bash \
		$(IMAGE_NAME):$(VERSION)

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f

# Remove the image
remove:
	@echo "🗑️ Removing Docker image..."
	docker rmi $(IMAGE_NAME):$(VERSION)

# Show help
help:
	@echo "🎵 SLSKD MP3 Search & Download Tool - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  build              - Build the Docker image"
	@echo "  build-no-cache     - Build the Docker image (no cache)"
	@echo "  run                - Run the container interactively"
	@echo "  show-ids           - Show current PUID and PGID"
	@echo "  telegram-bot       - Start Telegram bot (Docker)"
	@echo "  telegram-bot-local - Start Telegram bot (local)"
	@echo "  up                 - Start with docker-compose (background)"
	@echo "  up-fg              - Start with docker-compose (foreground)"
	@echo "  down               - Stop docker-compose services"
	@echo "  logs               - View container logs"
	@echo "  search             - Search for a song"
	@echo "  playlist           - Download Spotify playlist"
	@echo "  history            - Show download history"
	@echo "  shell              - Open interactive shell"
	@echo "  clean              - Clean up Docker resources"
	@echo "  remove             - Remove Docker image"
	@echo "  help               - Show this help message"
	@echo ""
	@echo "🔐 Permission Management:"
	@echo "  Default: PUID=0 PGID=0 (root user) for maximum compatibility"
	@echo "  All Docker commands run as root by default"
	@echo "  To use your user: PUID=\$(id -u) PGID=\$(id -g) make up"

.PHONY: build build-no-cache run show-ids telegram-bot telegram-bot-local up up-fg down logs search playlist history shell clean remove help
