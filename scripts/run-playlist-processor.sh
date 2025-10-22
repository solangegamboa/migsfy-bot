#!/bin/bash

# Script para executar o processador de playlists

cd /app || cd "$(dirname "$0")/.."

echo "🎵 Iniciando Processador de Playlists"
echo "📅 $(date)"

# Executa o processador em modo daemon
python3 src/playlist_processor.py --daemon