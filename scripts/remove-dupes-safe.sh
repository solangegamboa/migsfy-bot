#!/bin/bash

# Script para remover arquivos duplicados listados em dupes.txt
# Versão segura com opção de simulação (dry run)

# Definir o arquivo de entrada (padrão ou fornecido como argumento)
DUPES_FILE="${1:-dupes.txt}"
DRY_RUN=0

# Função de ajuda
show_help() {
    echo "Uso: $0 [OPÇÕES] [ARQUIVO]"
    echo
    echo "Remove arquivos e diretórios listados em um arquivo (padrão: dupes.txt)"
    echo
    echo "Opções:"
    echo "  -h, --help     Mostra esta mensagem de ajuda"
    echo "  -d, --dry-run  Executa em modo de simulação (não remove arquivos)"
    echo
    echo "Exemplos:"
    echo "  $0                     # Remove arquivos listados em dupes.txt"
    echo "  $0 -d                  # Simula remoção de arquivos em dupes.txt"
    echo "  $0 outro-arquivo.txt   # Remove arquivos listados em outro-arquivo.txt"
    echo
}

# Processar argumentos
for arg in "$@"; do
    case $arg in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=1
            echo "Modo de simulação ativado (nenhum arquivo será removido)"
            ;;
        *)
            # Se não for uma opção e for o primeiro argumento não-opção, considera como arquivo
            if [[ ! "$arg" =~ ^- ]] && [ "$DUPES_FILE" = "dupes.txt" ]; then
                DUPES_FILE="$arg"
            fi
            ;;
    esac
done

# Verificar se o arquivo existe
if [ ! -f "$DUPES_FILE" ]; then
    echo "Erro: Arquivo $DUPES_FILE não encontrado!"
    echo "O script deve ser executado no mesmo diretório onde está o arquivo, ou especifique o caminho completo."
    exit 1
fi

# Contar o número de linhas no arquivo
TOTAL_LINES=$(wc -l < "$DUPES_FILE")
echo "Encontradas $TOTAL_LINES linhas no arquivo $DUPES_FILE"

# Se não for dry run, pedir confirmação
if [ $DRY_RUN -eq 0 ]; then
    echo "ATENÇÃO: Este script irá REMOVER PERMANENTEMENTE todos os arquivos e diretórios listados em $DUPES_FILE"
    echo "Você tem certeza que deseja continuar? (s/N)"
    read -r CONFIRM

    if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
        echo "Operação cancelada pelo usuário."
        exit 0
    fi
fi

# Contador para acompanhamento do progresso
COUNT=0
ERRORS=0
TOTAL_SIZE=0

# Processar cada linha do arquivo
while IFS= read -r line || [[ -n "$line" ]]; do
    # Ignorar linhas vazias
    if [ -z "$line" ]; then
        continue
    fi
    
    COUNT=$((COUNT + 1))
    
    # Verificar se o arquivo/diretório existe
    if [ -e "$line" ]; then
        # Calcular tamanho do arquivo/diretório
        if [ -d "$line" ]; then
            SIZE=$(du -sh "$line" 2>/dev/null | cut -f1)
            TYPE="diretório"
        else
            SIZE=$(ls -lh "$line" 2>/dev/null | awk '{print $5}')
            TYPE="arquivo"
        fi
        
        if [ $DRY_RUN -eq 1 ]; then
            echo "[$COUNT/$TOTAL_LINES] Simulando remoção de $TYPE: $line ($SIZE)"
        else
            echo "[$COUNT/$TOTAL_LINES] Removendo $TYPE: $line ($SIZE)"
            rm -rf "$line"
            
            # Verificar se a remoção foi bem-sucedida
            if [ $? -ne 0 ]; then
                echo "  Erro ao remover: $line"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    else
        echo "[$COUNT/$TOTAL_LINES] Arquivo não encontrado (ignorando): $line"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Mostrar progresso a cada 10 itens ou a cada 1% do total
    PROGRESS_INTERVAL=$((TOTAL_LINES / 100))
    if [ $PROGRESS_INTERVAL -lt 10 ]; then PROGRESS_INTERVAL=10; fi
    
    if [ $((COUNT % PROGRESS_INTERVAL)) -eq 0 ]; then
        echo "Progresso: $COUNT/$TOTAL_LINES ($(( (COUNT * 100) / TOTAL_LINES ))%)"
    fi
    
done < "$DUPES_FILE"

echo "Processo concluído!"
echo "Total de itens processados: $COUNT"
echo "Total de erros: $ERRORS"

if [ $DRY_RUN -eq 1 ]; then
    echo "Este foi apenas um teste - nenhum arquivo foi removido."
    echo "Para remover os arquivos, execute o script sem a opção --dry-run"
elif [ $ERRORS -gt 0 ]; then
    echo "Alguns itens não puderam ser removidos. Verifique as mensagens acima."
    exit 1
else
    echo "Todos os itens foram removidos com sucesso."
fi

exit 0
