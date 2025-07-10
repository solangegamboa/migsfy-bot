#!/bin/bash

echo "🐳 Testando configuração Docker para migsfy-bot"
echo "================================================"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado"
    echo "💡 Instale Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon não está rodando"
    echo "💡 Inicie o Docker Desktop"
    exit 1
fi

echo "✅ Docker está instalado e rodando"

# Verificar arquivos necessários
files=("Dockerfile" "docker-compose.yml" "requirements.txt" ".env.example")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file encontrado"
    else
        echo "❌ $file não encontrado"
    fi
done

# Verificar se .env existe
if [ -f ".env" ]; then
    echo "✅ .env configurado"
else
    echo "⚠️ .env não encontrado - copie de .env.example"
fi

# Verificar diretórios
dirs=("data" "cache")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Diretório $dir existe"
    else
        echo "📁 Criando diretório $dir"
        mkdir -p "$dir"
    fi
done

echo ""
echo "🚀 Comandos para testar:"
echo "  make build    # Construir imagem"
echo "  make run      # Executar interativamente"
echo "  make help     # Ver todos os comandos"
echo ""
echo "📖 Veja README-Docker.md para instruções completas"
