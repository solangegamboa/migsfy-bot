#!/bin/bash

# Script para organizar arquivos já baixados
# Busca na base SQLite e move arquivos de /media/slskd para /media/music

echo "🗂️ Organizando arquivos já baixados..."

# Verificar se está no diretório correto
if [ ! -f "src/playlist/organize_downloaded.py" ]; then
    echo "❌ Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# Executar organizador
python3 src/playlist/organize_downloaded.py

echo "✅ Processo de organização concluído"
