#!/bin/bash

# Script melhorado para executar o bot do Telegram
# Com tratamento de erros e restart automático

BOT_SCRIPT="telegram_bot.py"
LOG_FILE="telegram_bot.log"
MAX_RESTARTS=5
RESTART_DELAY=10

echo "🤖 Iniciando MigsFy Telegram Bot (versão melhorada)"
echo "📁 Diretório: $(pwd)"
echo "📝 Log: $LOG_FILE"
echo ""

# Verifica se o script existe
if [ ! -f "$BOT_SCRIPT" ]; then
    echo "❌ Arquivo $BOT_SCRIPT não encontrado!"
    exit 1
fi

# Verifica se o .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "💡 Copie .env.example para .env e configure"
    exit 1
fi

# Testa o token do bot
echo "🔍 Testando token do bot..."
if ! python3 test-bot-token.py; then
    echo "❌ Token do bot inválido ou problema de conectividade"
    exit 1
fi

echo "✅ Token válido, iniciando bot..."
echo ""

# Função para executar o bot
run_bot() {
    local restart_count=0
    
    while [ $restart_count -lt $MAX_RESTARTS ]; do
        echo "🚀 Tentativa $(($restart_count + 1))/$MAX_RESTARTS"
        echo "⏰ $(date '+%Y-%m-%d %H:%M:%S') - Iniciando bot..."
        
        # Executa o bot
        python3 "$BOT_SCRIPT"
        exit_code=$?
        
        echo "⏰ $(date '+%Y-%m-%d %H:%M:%S') - Bot parou com código $exit_code"
        
        # Se foi interrompido pelo usuário (Ctrl+C), sai
        if [ $exit_code -eq 130 ]; then
            echo "🛑 Bot interrompido pelo usuário"
            break
        fi
        
        # Se foi um erro, tenta reiniciar
        if [ $exit_code -ne 0 ]; then
            restart_count=$(($restart_count + 1))
            
            if [ $restart_count -lt $MAX_RESTARTS ]; then
                echo "⚠️  Bot parou com erro, reiniciando em ${RESTART_DELAY}s..."
                sleep $RESTART_DELAY
            else
                echo "❌ Máximo de tentativas atingido"
                break
            fi
        else
            echo "✅ Bot parou normalmente"
            break
        fi
    done
}

# Trap para capturar Ctrl+C
trap 'echo ""; echo "🛑 Parando bot..."; exit 0' INT

# Executa o bot
run_bot

echo ""
echo "📋 Para ver os logs: tail -f $LOG_FILE"
echo "🔄 Para reiniciar: $0"
