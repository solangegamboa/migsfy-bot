#!/bin/bash

# Script para remover arquivos duplicados listados em dupes.txt
# ATENÇÃO: Este script remove permanentemente arquivos e diretórios!

# Definir o arquivo de entrada
DUPES_FILE="dupes.txt"

# Verificar se o arquivo existe
if [ ! -f "$DUPES_FILE" ]; then
    echo "Erro: Arquivo $DUPES_FILE não encontrado!"
    echo "O script deve ser executado no mesmo diretório onde está o arquivo dupes.txt"
    exit 1
fi

# Contar o número de linhas no arquivo
TOTAL_LINES=$(wc -l < "$DUPES_FILE")
echo "Encontradas $TOTAL_LINES linhas no arquivo $DUPES_FILE"

# Perguntar confirmação antes de prosseguir
echo "ATENÇÃO: Este script irá REMOVER PERMANENTEMENTE todos os arquivos e diretórios listados em $DUPES_FILE"
echo "Você tem certeza que deseja continuar? (s/N)"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

# Contador para acompanhamento do progresso
COUNT=0
ERRORS=0

# Processar cada linha do arquivo
while IFS= read -r line || [[ -n "$line" ]]; do
    # Ignorar linhas vazias
    if [ -z "$line" ]; then
        continue
    fi
    
    COUNT=$((COUNT + 1))
    
    # Verificar se o arquivo/diretório existe antes de tentar remover
    if [ -e "$line" ]; then
        echo "[$COUNT/$TOTAL_LINES] Removendo: $line"
        rm -rf "$line"
        
        # Verificar se a remoção foi bem-sucedida
        if [ $? -ne 0 ]; then
            echo "  Erro ao remover: $line"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "[$COUNT/$TOTAL_LINES] Arquivo não encontrado (ignorando): $line"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Mostrar progresso a cada 10 itens
    if [ $((COUNT % 10)) -eq 0 ]; then
        echo "Progresso: $COUNT/$TOTAL_LINES ($(( (COUNT * 100) / TOTAL_LINES ))%)"
    fi
    
done < "$DUPES_FILE"

echo "Processo concluído!"
echo "Total de itens processados: $COUNT"
echo "Total de erros: $ERRORS"

if [ $ERRORS -gt 0 ]; then
    echo "Alguns itens não puderam ser removidos. Verifique as mensagens acima."
    exit 1
else
    echo "Todos os itens foram removidos com sucesso."
    exit 0
fi
