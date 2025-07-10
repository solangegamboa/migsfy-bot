#!/bin/bash

echo "🤖 SLSKD Music Bot - Telegram Edition"
echo "====================================="

# Muda para o diretório raiz do projeto
cd "$(dirname "$0")/.."

# Verifica se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "💡 Copie config/.env.example para .env e configure suas credenciais"
    echo "💡 cp config/.env.example .env"
    exit 1
fi

# Verifica se TELEGRAM_BOT_TOKEN está configurado
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "your_telegram_bot_token_here" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN não está configurado no .env"
    echo "💡 Configure seu token do bot do Telegram"
    echo "💡 Obtenha em: https://t.me/BotFather"
    exit 1
fi

echo "✅ Configuração encontrada"
echo "🚀 Iniciando bot do Telegram..."
echo "💡 Pressione Ctrl+C para parar"
echo ""

# Executa o bot
python3 src/telegram/bot.py
