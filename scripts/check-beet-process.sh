#!/bin/bash

# Script para verificar e gerenciar o processo beet import
# Verifica se o processo específico de importação do beet está rodando antes de iniciar

BEET_PATH="/root/.local/bin/beet"
BEET_COMMAND="$BEET_PATH import -s /media/devmon/SOLAR/media/slskd/ -ql /home/solange/Projects/Github/cron.log"

# Função para verificar se o processo específico está rodando
check_beet_process() {
    # Verifica se o processo beet com os parâmetros específicos está rodando
    if pgrep -f "$BEET_COMMAND" > /dev/null 2>&1; then
        return 0  # Processo específico está rodando
    else
        return 1  # Processo específico não está rodando
    fi
}

# Função para iniciar o beet com os parâmetros específicos
start_beet() {
    echo "Iniciando processo de importação do beet..."
    $BEET_PATH import -s /media/devmon/SOLAR/media/slskd/ -ql /home/solange/Projects/Github/cron.log &
    echo "Processo de importação do beet iniciado com PID: $!"
}

# Função principal
main() {
    echo "Verificando se o processo de importação do beet está rodando..."
    
    if check_beet_process; then
        echo "✓ Processo de importação do beet já está rodando"
        echo "PIDs encontrados:"
        pgrep -f "$BEET_COMMAND" | while read pid; do
            echo "  PID: $pid"
            ps -p $pid -o cmd= | sed 's/^/  Comando: /'
        done
        exit 0
    else
        echo "✗ Processo de importação do beet não está rodando"
        
        # Verifica se o executável existe
        if [[ ! -x "$BEET_PATH" ]]; then
            echo "Erro: $BEET_PATH não encontrado ou não é executável"
            exit 1
        fi
        
        # Verifica se o diretório de origem existe
        if [[ ! -d "/media/devmon/SOLAR/media/slskd/" ]]; then
            echo "Erro: Diretório de origem não encontrado"
            exit 1
        fi
        
        # Inicia o processo de importação do beet
        start_beet
    fi
}

# Executa a função principal
main
