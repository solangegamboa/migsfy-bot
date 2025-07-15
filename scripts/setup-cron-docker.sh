#!/bin/bash

# Script para configurar cron no Docker para downloads automáticos do Last.fm
# Este script deve ser executado dentro do container Docker

set -euo pipefail

echo "🐳 Configurando cron para downloads automáticos do Last.fm no Docker..."

# Verificar se estamos em um container Docker
if [[ ! -f /.dockerenv ]]; then
    echo "⚠️ Este script deve ser executado dentro de um container Docker"
    echo "💡 Para uso local, configure o cron manualmente:"
    echo "💡 crontab -e"
    echo "💡 Adicione: 0 2 */2 * * /caminho/para/scripts/lastfm-auto-download.sh"
    exit 1
fi

# Instalar cron se não estiver instalado
if ! command -v cron >/dev/null 2>&1; then
    echo "📦 Instalando cron..."
    apt-get update -qq
    apt-get install -y -qq cron
fi

# Criar diretórios necessários
mkdir -p /app/logs

# Verificar se o arquivo de crontab existe
if [[ ! -f "/app/scripts/crontab-lastfm" ]]; then
    echo "❌ Arquivo crontab-lastfm não encontrado"
    exit 1
fi

# Instalar crontab
echo "⚙️ Instalando configuração do cron..."
crontab /app/scripts/crontab-lastfm

# Verificar instalação
echo "✅ Crontab instalado:"
crontab -l

# Iniciar serviço cron
echo "🚀 Iniciando serviço cron..."
service cron start

# Verificar status
if service cron status >/dev/null 2>&1; then
    echo "✅ Serviço cron iniciado com sucesso"
else
    echo "❌ Falha ao iniciar serviço cron"
    exit 1
fi

# Criar script de teste
echo "🧪 Criando script de teste..."
cat > /app/scripts/test-lastfm-cron.sh << 'EOF'
#!/bin/bash
echo "🧪 Testando configuração do cron Last.fm..."
echo "📅 Data atual: $(date)"
echo "📋 Crontab ativo:"
crontab -l
echo ""
echo "🔍 Verificando arquivos necessários:"
echo "   Script principal: $(ls -la /app/scripts/lastfm-auto-download.sh 2>/dev/null || echo 'AUSENTE')"
echo "   Arquivo .env: $(ls -la /app/.env 2>/dev/null || echo 'AUSENTE')"
echo "   Diretório logs: $(ls -ld /app/logs 2>/dev/null || echo 'AUSENTE')"
echo ""
echo "🏷️ Configuração Last.fm:"
if [[ -f "/app/.env" ]]; then
    grep -E "LASTFM_AUTO_" /app/.env || echo "   Nenhuma configuração LASTFM_AUTO_ encontrada"
else
    echo "   Arquivo .env não encontrado"
fi
echo ""
echo "✅ Teste concluído"
EOF

chmod +x /app/scripts/test-lastfm-cron.sh

echo ""
echo "🎉 Configuração do cron concluída!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure as variáveis no arquivo .env:"
echo "      LASTFM_AUTO_TAGS=rock,pop,jazz"
echo "      LASTFM_AUTO_LIMIT=15"
echo "      LASTFM_API_KEY=sua_chave"
echo "      LASTFM_API_SECRET=seu_secret"
echo ""
echo "   2. Teste a configuração:"
echo "      /app/scripts/test-lastfm-cron.sh"
echo ""
echo "   3. Teste o script manualmente:"
echo "      /app/scripts/lastfm-auto-download.sh"
echo ""
echo "   4. O cron executará automaticamente a cada 48 horas às 02:00"
echo ""
echo "📊 Para monitorar:"
echo "   tail -f /app/logs/lastfm_auto_download.log"
echo "   tail -f /app/logs/cron.log"