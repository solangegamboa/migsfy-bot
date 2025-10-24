#!/bin/bash

# Script para corrigir estrutura de pastas em /media/music
# Usa dados da base SQLite para reorganizar arquivos já baixados

echo "🔧 Corrigindo estrutura de pastas em /media/music..."

# Verificar se está no diretório correto
if [ ! -f "src/playlist/fix_music_structure.py" ]; then
    echo "❌ Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# Executar corretor
python3 src/playlist/fix_music_structure.py

echo "✅ Correção de estrutura concluída"
