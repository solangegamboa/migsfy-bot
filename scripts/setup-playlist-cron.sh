#!/bin/bash

# Setup Playlist Processor Cron Job
# Configuração otimizada para produção

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CRON_USER="${CRON_USER:-root}"
LOG_DIR="${PROJECT_ROOT}/logs"
LOCK_DIR="${PROJECT_ROOT}/data"

# Criar diretórios necessários
mkdir -p "$LOG_DIR" "$LOCK_DIR"

# Configurações de horário otimizadas
CRON_SCHEDULE_MAIN="${CRON_SCHEDULE_MAIN:-*/30 * * * *}"      # A cada 30 minutos
CRON_SCHEDULE_CLEANUP="${CRON_SCHEDULE_CLEANUP:-0 2 * * *}"   # Limpeza diária às 2h
CRON_SCHEDULE_HEALTH="${CRON_SCHEDULE_HEALTH:-*/5 * * * *}"   # Health check a cada 5min

# Comandos otimizados
MAIN_CMD="cd $PROJECT_ROOT && python3 src/playlist/main.py"
CLEANUP_CMD="cd $PROJECT_ROOT && python3 src/playlist/main.py --cleanup"
HEALTH_CMD="cd $PROJECT_ROOT && python3 src/playlist/main.py --health-check"

# Configuração de logs com rotação
LOG_CONFIG=">> $LOG_DIR/playlist-processor.log 2>&1"
CLEANUP_LOG_CONFIG=">> $LOG_DIR/playlist-cleanup.log 2>&1"
HEALTH_LOG_CONFIG=">> $LOG_DIR/playlist-health.log 2>&1"

# Função para adicionar job ao cron
add_cron_job() {
    local schedule="$1"
    local command="$2"
    local log_config="$3"
    local description="$4"
    
    echo "# $description"
    echo "$schedule $command $log_config"
    echo ""
}

# Gerar configuração do cron
generate_cron_config() {
    cat << EOF
# Playlist Processor Cron Configuration
# Generated on $(date)
# Project: migsfy-bot

# Environment variables
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PYTHONPATH=$PROJECT_ROOT/src
LOG_LEVEL=INFO

EOF

    # Job principal - processamento de playlists
    add_cron_job "$CRON_SCHEDULE_MAIN" "$MAIN_CMD" "$LOG_CONFIG" \
        "Playlist Processor - Main execution every 30 minutes"
    
    # Job de limpeza - cache e logs antigos
    add_cron_job "$CRON_SCHEDULE_CLEANUP" "$CLEANUP_CMD" "$CLEANUP_LOG_CONFIG" \
        "Playlist Processor - Daily cleanup at 2 AM"
    
    # Job de health check - monitoramento
    add_cron_job "$CRON_SCHEDULE_HEALTH" "$HEALTH_CMD" "$HEALTH_LOG_CONFIG" \
        "Playlist Processor - Health check every 5 minutes"
    
    # Rotação de logs semanal
    add_cron_job "0 3 * * 0" \
        "find $LOG_DIR -name '*.log' -size +10M -exec logrotate -f {} \;" \
        ">> $LOG_DIR/logrotate.log 2>&1" \
        "Log rotation - Weekly cleanup of large log files"
}

# Função para instalar cron
install_cron() {
    local temp_cron=$(mktemp)
    
    echo "📋 Generating cron configuration..."
    generate_cron_config > "$temp_cron"
    
    echo "📋 Current cron configuration:"
    cat "$temp_cron"
    
    echo ""
    read -p "Install this cron configuration? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup existing cron
        crontab -l > "${LOG_DIR}/crontab-backup-$(date +%Y%m%d-%H%M%S).txt" 2>/dev/null || true
        
        # Install new cron
        crontab "$temp_cron"
        echo "✅ Cron configuration installed successfully"
        
        # Verify installation
        echo ""
        echo "📋 Installed cron jobs:"
        crontab -l | grep -E "(playlist|Playlist)" || echo "No playlist jobs found"
    else
        echo "❌ Installation cancelled"
    fi
    
    rm -f "$temp_cron"
}

# Função para remover cron
remove_cron() {
    echo "🗑️  Removing playlist processor cron jobs..."
    
    local temp_cron=$(mktemp)
    crontab -l 2>/dev/null | grep -v -E "(playlist|Playlist)" > "$temp_cron" || true
    
    if [[ -s "$temp_cron" ]]; then
        crontab "$temp_cron"
        echo "✅ Playlist processor cron jobs removed"
    else
        crontab -r 2>/dev/null || true
        echo "✅ All cron jobs removed (crontab was empty)"
    fi
    
    rm -f "$temp_cron"
}

# Função para mostrar status
show_status() {
    echo "📊 Playlist Processor Cron Status"
    echo "=================================="
    echo ""
    
    echo "📋 Current cron jobs:"
    crontab -l 2>/dev/null | grep -E "(playlist|Playlist)" || echo "No playlist jobs found"
    echo ""
    
    echo "📁 Log files:"
    ls -la "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"
    echo ""
    
    echo "🔒 Lock files:"
    ls -la "$LOCK_DIR"/*.lock 2>/dev/null || echo "No lock files found"
    echo ""
    
    echo "🏃 Running processes:"
    ps aux | grep -E "(playlist_processor|playlist/main)" | grep -v grep || echo "No processes running"
}

# Função para testar configuração
test_config() {
    echo "🧪 Testing playlist processor configuration..."
    
    # Testar comando principal
    echo "Testing main command..."
    if timeout 30 bash -c "$MAIN_CMD --dry-run" 2>/dev/null; then
        echo "✅ Main command test passed"
    else
        echo "❌ Main command test failed"
        return 1
    fi
    
    # Testar comando de limpeza
    echo "Testing cleanup command..."
    if timeout 10 bash -c "$CLEANUP_CMD --dry-run" 2>/dev/null; then
        echo "✅ Cleanup command test passed"
    else
        echo "❌ Cleanup command test failed"
        return 1
    fi
    
    # Testar health check
    echo "Testing health check command..."
    if timeout 10 bash -c "$HEALTH_CMD" 2>/dev/null; then
        echo "✅ Health check test passed"
    else
        echo "❌ Health check test failed"
        return 1
    fi
    
    echo "✅ All tests passed"
}

# Menu principal
show_help() {
    cat << EOF
Playlist Processor Cron Setup

Usage: $0 [COMMAND]

Commands:
    install     Install cron configuration
    remove      Remove cron configuration
    status      Show current status
    test        Test configuration
    help        Show this help

Environment Variables:
    CRON_SCHEDULE_MAIN     Main job schedule (default: */30 * * * *)
    CRON_SCHEDULE_CLEANUP  Cleanup job schedule (default: 0 2 * * *)
    CRON_SCHEDULE_HEALTH   Health check schedule (default: */5 * * * *)
    CRON_USER             Cron user (default: root)

Examples:
    # Install with default schedule
    $0 install
    
    # Install with custom schedule (every hour)
    CRON_SCHEDULE_MAIN="0 * * * *" $0 install
    
    # Check status
    $0 status
    
    # Test configuration
    $0 test

EOF
}

# Main
case "${1:-help}" in
    install)
        test_config && install_cron
        ;;
    remove)
        remove_cron
        ;;
    status)
        show_status
        ;;
    test)
        test_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
