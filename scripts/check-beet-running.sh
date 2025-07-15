#!/bin/bash

# Script simples para verificar se o processo beet está rodando
# Retorna 0 se estiver rodando, 1 se não estiver

BEET_PATH="/root/.local/bin/beet"

# Verifica se o processo beet está rodando
if pgrep -f "$BEET_PATH" > /dev/null 2>&1; then
    echo "Processo beet já está rodando (PID: $(pgrep -f "$BEET_PATH" | tr '\n' ' '))"
    exit 0
else
    echo "Processo beet não está rodando"
    exit 1
fi
