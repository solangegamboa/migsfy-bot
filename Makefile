# Makefile para gerenciar o projeto migsfy-bot

.PHONY: help build run stop logs clean test telegram-bot

# Variáveis
CONTAINER_NAME = migsfy-bot
IMAGE_NAME = migsfy-bot

help: ## Mostra esta ajuda
	@echo "🎵 SLSKD MP3 Search & Download Tool - Docker Commands"
	@echo ""
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Constrói a imagem Docker
	@echo "🔨 Construindo imagem Docker..."
	docker build -t $(IMAGE_NAME) .

run: ## Executa o container em modo daemon
	@echo "🚀 Iniciando container..."
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME) --daemon

stop: ## Para o container
	@echo "🛑 Parando container..."
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

logs: ## Mostra logs do container
	@echo "📝 Logs do container:"
	docker logs -f $(CONTAINER_NAME)

logs-telegram: ## Mostra logs específicos do bot do Telegram
	@echo "🤖 Logs do bot do Telegram:"
	docker exec $(CONTAINER_NAME) tail -f /app/logs/telegram-bot.log

clean: ## Remove container e imagem
	@echo "🧹 Limpando..."
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME) || true

test: ## Testa se o bot funciona
	@echo "🧪 Testando bot do Telegram..."
	docker exec $(CONTAINER_NAME) python3 -c "from src.telegram.bot import TelegramMusicBot; print('✅ Bot OK')"

telegram-bot: ## Executa apenas o bot do Telegram
	@echo "🤖 Executando bot do Telegram..."
	docker run -it --rm \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME) --telegram-bot

shell: ## Abre shell no container
	@echo "🐚 Abrindo shell no container..."
	docker exec -it $(CONTAINER_NAME) bash

restart: stop run ## Para e reinicia o container

rebuild: clean build run ## Reconstrói e reinicia tudo

status: ## Mostra status do container
	@echo "📊 Status do container:"
	@docker ps -a --filter name=$(CONTAINER_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Comandos de desenvolvimento
dev-build: ## Constrói imagem para desenvolvimento
	@echo "🔨 Construindo imagem de desenvolvimento..."
	docker build -t $(IMAGE_NAME):dev .

dev-run: ## Executa em modo desenvolvimento com volumes
	@echo "🚀 Iniciando em modo desenvolvimento..."
	docker run -it --rm \
		--name $(CONTAINER_NAME)-dev \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME):dev bash
