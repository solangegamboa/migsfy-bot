#!/bin/bash

# Script para iniciar o playlist processor
echo "🎵 Iniciando Playlist Processor..."

# Navegar para o diretório da aplicação
cd /app

# Executar o playlist processor
python3 src/playlist/main.py

echo "✅ Playlist Processor finalizado"
