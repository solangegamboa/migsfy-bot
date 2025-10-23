#!/bin/bash

# Script para executar o bot do Telegram
# Pode ser usado tanto no Docker quanto localmente

set -e

# Detecta se está rodando no Docker
if [ -d "/app" ] && [ -f "/app/.env" ]; then
    echo "🐳 Executando no Docker"
    cd /app
    ENV_FILE="/app/.env"
    LOG_FILE="/app/logs/telegram-bot.log"
    PYTHON_PATH="/app/src"
else
    echo "💻 Executando localmente"
    cd "$(dirname "$0")/.."
    ENV_FILE=".env"
    LOG_FILE="logs/telegram-bot.log"
    PYTHON_PATH="src"
fi

# Verifica se o arquivo .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Arquivo .env não encontrado em: $ENV_FILE"
    echo "💡 Copie o arquivo .env.example e configure suas credenciais"
    exit 1
fi

# Verifica se o token do Telegram está configurado
if ! grep -q "TELEGRAM_BOT_TOKEN" "$ENV_FILE" || grep -q "^TELEGRAM_BOT_TOKEN=$" "$ENV_FILE"; then
    echo "❌ TELEGRAM_BOT_TOKEN não configurado no .env"
    echo "💡 Configure o token do seu bot do Telegram no arquivo .env"
    exit 1
fi

# Cria diretório de logs se não existir
mkdir -p "$(dirname "$LOG_FILE")"

# Exporta PYTHONPATH para encontrar os módulos
export PYTHONPATH="$PYTHON_PATH:$PYTHONPATH"

echo "🤖 Iniciando bot do Telegram..."
echo "📁 Diretório: $(pwd)"
echo "📝 Log: $LOG_FILE"
echo "🐍 Python Path: $PYTHONPATH"

# Executa o bot
if [ "$1" = "--daemon" ]; then
    echo "🔄 Executando em modo daemon..."
    nohup python3 -m src.telegram.bot > "$LOG_FILE" 2>&1 &
    BOT_PID=$!
    echo "✅ Bot iniciado em background (PID: $BOT_PID)"
    echo "📝 Logs: tail -f $LOG_FILE"
else
    echo "▶️ Executando em modo interativo..."
    python3 -m src.telegram.bot
fi
