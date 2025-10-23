#!/bin/bash

# Script para retry de downloads falhados
# Executa a cada 24 horas via cron

echo "🔄 $(date): Iniciando retry de downloads falhados"

cd /app || exit 1

# Executa retry de downloads falhados
python3 src/playlist_processor.py --retry

echo "✅ $(date): Retry de downloads falhados concluído"