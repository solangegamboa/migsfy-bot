# Makefile for SLSKD MP3 Search & Download Tool

# Variables
IMAGE_NAME = migsfy-bot
CONTAINER_NAME = migsfy-bot
VERSION = latest

# Build the Docker image
build:
	@echo "🔨 Building Docker image..."
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Run the container interactively
run:
	@echo "🚀 Running container..."
	docker run --rm -it \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/cache:/app/cache \
		$(IMAGE_NAME):$(VERSION)

# Run with docker-compose
up:
	@echo "🚀 Starting with docker-compose..."
	docker-compose up -d

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
	@echo "  build     - Build the Docker image"
	@echo "  run       - Run the container interactively"
	@echo "  up        - Start with docker-compose"
	@echo "  down      - Stop docker-compose services"
	@echo "  logs      - View container logs"
	@echo "  search    - Search for a song"
	@echo "  playlist  - Download Spotify playlist"
	@echo "  history   - Show download history"
	@echo "  shell     - Open interactive shell"
	@echo "  clean     - Clean up Docker resources"
	@echo "  remove    - Remove Docker image"
	@echo "  help      - Show this help message"

.PHONY: build run up down logs search playlist history shell clean remove help
