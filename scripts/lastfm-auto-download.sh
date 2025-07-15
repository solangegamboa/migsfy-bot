#!/bin/bash

# Script para download automático de tracks do Last.fm baseado em tags configuradas
# Executa a cada 48 horas via cron
# Autor: migsfy-bot
# Data: $(date +%Y-%m-%d)

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/lastfm_auto_download.log"
LOCK_FILE="/tmp/lastfm_auto_download.lock"
MAX_LOCK_AGE=7200  # 2 horas em segundos

# Função de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para limpeza
cleanup() {
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log "🧹 Lock file removido"
    fi
}

# Trap para limpeza em caso de interrupção
trap cleanup EXIT INT TERM

# Verificar se já está executando
if [[ -f "$LOCK_FILE" ]]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    LOCK_TIME=$(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo "0")
    CURRENT_TIME=$(date +%s)
    LOCK_AGE=$((CURRENT_TIME - LOCK_TIME))
    
    if [[ -n "$LOCK_PID" ]] && kill -0 "$LOCK_PID" 2>/dev/null; then
        if [[ $LOCK_AGE -lt $MAX_LOCK_AGE ]]; then
            log "⚠️ Script já está executando (PID: $LOCK_PID). Saindo."
            exit 0
        else
            log "🕐 Lock file antigo detectado (${LOCK_AGE}s). Removendo..."
            rm -f "$LOCK_FILE"
        fi
    else
        log "🗑️ Lock file órfão detectado. Removendo..."
        rm -f "$LOCK_FILE"
    fi
fi

# Criar lock file
echo $$ > "$LOCK_FILE"

log "🚀 Iniciando download automático de tracks do Last.fm"
log "📁 Diretório do projeto: $PROJECT_DIR"

# Verificar se o diretório do projeto existe
if [[ ! -d "$PROJECT_DIR" ]]; then
    log "❌ Diretório do projeto não encontrado: $PROJECT_DIR"
    exit 1
fi

# Mudar para o diretório do projeto
cd "$PROJECT_DIR"

# Verificar se o arquivo .env existe
if [[ ! -f ".env" ]]; then
    log "❌ Arquivo .env não encontrado"
    exit 1
fi

# Carregar variáveis do .env
set -a
source .env
set +a

# Verificar credenciais do Last.fm
if [[ -z "${LASTFM_API_KEY:-}" ]] || [[ -z "${LASTFM_API_SECRET:-}" ]]; then
    log "❌ Credenciais do Last.fm não configuradas no .env"
    log "💡 Configure LASTFM_API_KEY e LASTFM_API_SECRET"
    exit 1
fi

# Obter lista de tags do .env (separadas por vírgula)
LASTFM_AUTO_TAGS="${LASTFM_AUTO_TAGS:-}"
if [[ -z "$LASTFM_AUTO_TAGS" ]]; then
    log "⚠️ Nenhuma tag configurada em LASTFM_AUTO_TAGS"
    log "💡 Configure tags separadas por vírgula no .env:"
    log "💡 LASTFM_AUTO_TAGS=rock,pop,jazz,alternative rock,metal"
    exit 0
fi

# Configurações de download
LASTFM_AUTO_LIMIT="${LASTFM_AUTO_LIMIT:-15}"
LASTFM_AUTO_SKIP_EXISTING="${LASTFM_AUTO_SKIP_EXISTING:-true}"

log "📋 Configurações:"
log "   🏷️ Tags: $LASTFM_AUTO_TAGS"
log "   📊 Limite por tag: $LASTFM_AUTO_LIMIT"
log "   📁 Diretório: diretório atual (padrão)"
log "   ⏭️ Pular existentes: $LASTFM_AUTO_SKIP_EXISTING"

# Converter tags em array
IFS=',' read -ra TAGS_ARRAY <<< "$LASTFM_AUTO_TAGS"

# Contadores
TOTAL_TAGS=${#TAGS_ARRAY[@]}
SUCCESSFUL_TAGS=0
FAILED_TAGS=0
TOTAL_DOWNLOADS=0
TOTAL_SUCCESSFUL=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0

log "🎵 Iniciando download de $TOTAL_TAGS tags..."

# Processar cada tag
for i in "${!TAGS_ARRAY[@]}"; do
    TAG="${TAGS_ARRAY[$i]}"
    # Remover espaços em branco
    TAG=$(echo "$TAG" | xargs)
    
    if [[ -z "$TAG" ]]; then
        continue
    fi
    
    TAG_NUM=$((i + 1))
    log ""
    log "🏷️ [$TAG_NUM/$TOTAL_TAGS] Processando tag: '$TAG'"
    
    # Preparar argumentos para o script Python
    PYTHON_ARGS=(
        "src/cli/main.py"
        "--lastfm-tag"
        "$TAG"
        "--limit"
        "$LASTFM_AUTO_LIMIT"
    )
    
    # Adicionar --no-skip-existing se configurado
    if [[ "$LASTFM_AUTO_SKIP_EXISTING" != "true" ]]; then
        PYTHON_ARGS+=("--no-skip-existing")
    fi
    
    # Executar download
    START_TIME=$(date +%s)
    
    if timeout 1800 python3 "${PYTHON_ARGS[@]}" >> "$LOG_FILE" 2>&1; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        log "✅ Tag '$TAG' processada com sucesso (${DURATION}s)"
        SUCCESSFUL_TAGS=$((SUCCESSFUL_TAGS + 1))
        
        # Tentar extrair estatísticas do log (últimas linhas)
        STATS=$(tail -20 "$LOG_FILE" | grep -E "(Downloads bem-sucedidos|Downloads com falha|Músicas puladas)" | tail -3 || true)
        if [[ -n "$STATS" ]]; then
            log "📊 Estatísticas da tag '$TAG':"
            echo "$STATS" | while read -r line; do
                log "   $line"
            done
        fi
        
    else
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        log "❌ Falha ao processar tag '$TAG' (${DURATION}s)"
        FAILED_TAGS=$((FAILED_TAGS + 1))
        
        # Log das últimas linhas de erro
        ERROR_LINES=$(tail -10 "$LOG_FILE" | grep -E "(ERROR|❌)" | tail -3 || true)
        if [[ -n "$ERROR_LINES" ]]; then
            log "🔍 Últimos erros:"
            echo "$ERROR_LINES" | while read -r line; do
                log "   $line"
            done
        fi
    fi
    
    # Pausa entre tags para não sobrecarregar
    if [[ $TAG_NUM -lt $TOTAL_TAGS ]]; then
        log "⏸️ Pausa de 30s antes da próxima tag..."
        sleep 30
    fi
done

# Calcular estatísticas finais
END_SCRIPT_TIME=$(date +%s)
SCRIPT_START_TIME=$(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo "$END_SCRIPT_TIME")
TOTAL_SCRIPT_DURATION=$((END_SCRIPT_TIME - SCRIPT_START_TIME))

log ""
log "📊 RELATÓRIO FINAL - Download Automático Last.fm"
log "=" | tr ' ' '='
log "🕐 Duração total: ${TOTAL_SCRIPT_DURATION}s ($(($TOTAL_SCRIPT_DURATION / 60))min)"
log "🏷️ Total de tags: $TOTAL_TAGS"
log "✅ Tags processadas com sucesso: $SUCCESSFUL_TAGS"
log "❌ Tags com falha: $FAILED_TAGS"
log "📁 Diretório de saída: diretório atual (padrão)"

# Verificar espaço em disco
if command -v df >/dev/null 2>&1; then
    DISK_USAGE=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    log "💾 Uso do disco: ${DISK_USAGE}%"
    
    if [[ $DISK_USAGE -gt 90 ]]; then
        log "⚠️ AVISO: Uso do disco acima de 90%!"
    fi
fi

# Verificar tamanho do diretório de downloads
if command -v du >/dev/null 2>&1; then
    DOWNLOAD_SIZE=$(du -sh "$PROJECT_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    log "📦 Tamanho total do projeto: $DOWNLOAD_SIZE"
fi

# Status final
if [[ $FAILED_TAGS -eq 0 ]]; then
    log "🎉 Todos os downloads concluídos com sucesso!"
    EXIT_CODE=0
else
    log "⚠️ Alguns downloads falharam. Verifique os logs acima."
    EXIT_CODE=1
fi

# Limpeza de logs antigos (manter últimos 30 dias)
find "$PROJECT_DIR/logs" -name "lastfm_auto_download.log.*" -mtime +30 -delete 2>/dev/null || true

# Rotacionar log se muito grande (>10MB)
if [[ -f "$LOG_FILE" ]] && [[ $(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]]; then
    mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S)"
    log "🔄 Log rotacionado devido ao tamanho"
fi

log "🏁 Script finalizado com código de saída: $EXIT_CODE"

exit $EXIT_CODE