# Last.fm Automated Download Guide

## 🤖 Visão Geral

O script `lastfm-auto-download.sh` permite download automático de músicas do Last.fm baseado em tags configuradas, ideal para descoberta musical contínua sem intervenção manual.

## 🚀 Configuração Rápida

### 1. Configurar Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```env
# Tags para download automático (separadas por vírgula)
LASTFM_AUTO_TAGS=rock,pop,jazz,alternative rock,metal,blues,electronic

# Limite de músicas por tag (padrão: 15)
LASTFM_AUTO_LIMIT=20

# Diretório de saída (padrão: ./downloads/lastfm_auto)
LASTFM_AUTO_OUTPUT_DIR=./downloads/auto

# Pular músicas já baixadas (padrão: true)
LASTFM_AUTO_SKIP_EXISTING=true
```

### 2. Testar Execução Manual

```bash
# Executar uma vez para testar
./scripts/lastfm-auto-download.sh

# Monitorar logs em tempo real
tail -f logs/lastfm_auto_download.log
```

### 3. Configurar Execução Automática

```bash
# Editar crontab
crontab -e

# Executar a cada 48 horas às 2:00 AM
0 2 */2 * * /caminho/completo/para/projeto/scripts/lastfm-auto-download.sh

# Ou diariamente às 3:00 AM
0 3 * * * /caminho/completo/para/projeto/scripts/lastfm-auto-download.sh
```

## 📊 Monitoramento

### Verificar Status

```bash
# Ver logs em tempo real
tail -f logs/lastfm_auto_download.log

# Ver últimas execuções
tail -50 logs/lastfm_auto_download.log

# Verificar se está executando
ps aux | grep lastfm-auto-download

# Verificar lock file
ls -la /tmp/lastfm_auto_download.lock
```

### Exemplo de Relatório

```
📊 RELATÓRIO FINAL - Download Automático Last.fm
================================================
🕐 Duração total: 1847s (30min)
🏷️ Total de tags: 5
✅ Tags processadas com sucesso: 4
❌ Tags com falha: 1
📁 Diretório de saída: ./downloads/lastfm_auto
💾 Uso do disco: 45%
📦 Tamanho total dos downloads: 2.3GB
```

## 🎯 Casos de Uso

### Descoberta Musical Diária

```env
# Configuração para descoberta diária
LASTFM_AUTO_TAGS=indie,alternative,electronic,ambient
LASTFM_AUTO_LIMIT=10
```

```bash
# Cron para execução diária às 3:00 AM
0 3 * * * /caminho/para/projeto/scripts/lastfm-auto-download.sh
```

### Coleção por Gêneros

```env
# Configuração para coleção ampla
LASTFM_AUTO_TAGS=rock,pop,jazz,metal,classical,blues,hip hop,electronic
LASTFM_AUTO_LIMIT=25
LASTFM_AUTO_OUTPUT_DIR=./music_collection
```

```bash
# Cron para execução semanal aos domingos às 2:00 AM
0 2 * * 0 /caminho/para/projeto/scripts/lastfm-auto-download.sh
```

### Música Internacional

```env
# Configuração para música brasileira e internacional
LASTFM_AUTO_TAGS=rock nacional,mpb,bossa nova,samba,forró,tango,reggae
LASTFM_AUTO_LIMIT=15
```

## 🛡️ Recursos de Segurança

### Prevenção de Execução Simultânea

- **Lock Files**: Impede múltiplas execuções simultâneas
- **Detecção de Processos**: Remove lock files órfãos automaticamente
- **Timeout de Segurança**: Lock files antigos (>2h) são removidos

### Monitoramento de Recursos

- **Espaço em Disco**: Verifica uso do disco e alerta quando >90%
- **Tamanho dos Downloads**: Calcula e reporta tamanho total
- **Rotação de Logs**: Logs grandes (>10MB) são rotacionados automaticamente

## 🔧 Troubleshooting

### Script Não Executa

```bash
# Verificar permissões
chmod +x scripts/lastfm-auto-download.sh

# Verificar se o arquivo .env existe
ls -la .env

# Verificar credenciais Last.fm
grep LASTFM .env
```

### Falhas de Download

```bash
# Verificar logs de erro
grep "❌\|ERROR" logs/lastfm_auto_download.log

# Verificar conectividade SLSKD
curl -H "X-API-Key: $SLSKD_API_KEY" "$SLSKD_URL_BASE/api/v0/session"

# Testar tag manualmente
python3 src/cli/main.py --lastfm-tag "rock" --limit 5
```

### Problemas de Cron

```bash
# Verificar se cron está rodando
sudo systemctl status cron

# Verificar logs do cron
sudo tail -f /var/log/cron

# Testar comando do cron manualmente
/caminho/completo/para/projeto/scripts/lastfm-auto-download.sh
```

### Espaço em Disco

```bash
# Verificar espaço disponível
df -h

# Verificar tamanho do diretório de downloads
du -sh ./downloads/lastfm_auto

# Limpar downloads antigos se necessário
find ./downloads/lastfm_auto -name "*.mp3" -mtime +30 -delete
```

## 📈 Otimização

### Configuração Eficiente

```env
# Para descoberta rápida (poucos downloads)
LASTFM_AUTO_TAGS=indie,alternative
LASTFM_AUTO_LIMIT=5

# Para coleção ampla (muitos downloads)
LASTFM_AUTO_TAGS=rock,pop,jazz,metal,electronic,hip hop,classical,blues
LASTFM_AUTO_LIMIT=30

# Para teste (muito poucos downloads)
LASTFM_AUTO_TAGS=rock
LASTFM_AUTO_LIMIT=3
```

### Horários Recomendados

```bash
# Horário de baixo uso (madrugada)
0 2 * * * /caminho/para/projeto/scripts/lastfm-auto-download.sh

# Horário de baixo uso (final de semana)
0 3 * * 6 /caminho/para/projeto/scripts/lastfm-auto-download.sh

# Horário personalizado (meio-dia aos domingos)
0 12 * * 0 /caminho/para/projeto/scripts/lastfm-auto-download.sh
```

## 🔄 Manutenção

### Limpeza Regular

```bash
# Limpar logs antigos (executado automaticamente pelo script)
find logs/ -name "lastfm_auto_download.log.*" -mtime +30 -delete

# Verificar tamanho dos logs
ls -lh logs/lastfm_auto_download.log*

# Rotacionar log manualmente se necessário
mv logs/lastfm_auto_download.log logs/lastfm_auto_download.log.$(date +%Y%m%d_%H%M%S)
```

### Backup de Configuração

```bash
# Backup do arquivo .env
cp .env .env.backup.$(date +%Y%m%d)

# Backup do crontab
crontab -l > crontab.backup.$(date +%Y%m%d)
```

## 📚 Integração com Outras Funcionalidades

### Combinação com Bot Telegram

O download automático funciona independentemente do bot, mas você pode:

1. Usar o bot para downloads manuais específicos
2. Verificar o histórico via bot: `/history`
3. Monitorar downloads em tempo real

### Combinação com Spotify

```bash
# Primeiro: Download automático Last.fm (descoberta)
./scripts/lastfm-auto-download.sh

# Depois: Download manual de playlists Spotify específicas
python3 src/cli/main.py --playlist "URL_PLAYLIST"
```

### Histórico Unificado

Todos os downloads (automáticos e manuais) são registrados no mesmo histórico:

```bash
# Ver histórico completo
python3 src/cli/main.py --history

# Forçar re-download se necessário
python3 src/cli/main.py --force "Artista - Música"
```

## 🎉 Dicas Avançadas

### Tags Estratégicas

```env
# Para descobrir subgêneros
LASTFM_AUTO_TAGS=progressive rock,death metal,smooth jazz,deep house

# Para música por década
LASTFM_AUTO_TAGS=60s,70s,80s,90s,2000s

# Para música por país/região
LASTFM_AUTO_TAGS=british rock,american folk,brazilian music,french electronic
```

### Configuração Sazonal

```bash
# Verão: música mais animada
# Inverno: música mais calma
# Ajustar LASTFM_AUTO_TAGS conforme a estação
```

### Monitoramento Avançado

```bash
# Criar script de monitoramento personalizado
#!/bin/bash
LAST_EXECUTION=$(stat -c %Y /tmp/lastfm_auto_download.lock 2>/dev/null || echo "0")
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - LAST_EXECUTION))

if [[ $TIME_DIFF -gt 172800 ]]; then  # 48 horas
    echo "⚠️ Download automático não executou nas últimas 48h"
fi
```

---

**💡 O download automático é uma ferramenta poderosa para descoberta musical contínua. Configure uma vez e desfrute de novas músicas regularmente!**