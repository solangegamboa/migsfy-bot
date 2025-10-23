# Troubleshooting do Bot do Telegram no Docker

## Problema Resolvido

O bot do Telegram não estava funcionando no Docker devido a problemas de importação e configuração do Python path.

## Correções Implementadas

### 1. Correção do Docker Entrypoint
- **Arquivo**: `scripts/docker-entrypoint.sh`
- **Mudança**: Alterado comando de execução de `python3 src/telegram/bot.py` para `python3 -m src.telegram.bot`
- **Motivo**: Execução como módulo garante que as importações funcionem corretamente

### 2. Configuração do PYTHONPATH no Dockerfile
- **Arquivo**: `Dockerfile`
- **Adicionado**: `ENV PYTHONPATH=/app/src:/app`
- **Motivo**: Garante que o Python encontre os módulos corretamente

### 3. Melhoria das Importações no Bot
- **Arquivo**: `src/telegram/bot.py`
- **Mudança**: Sistema de importação mais robusto com múltiplos fallbacks
- **Benefício**: Funciona tanto no Docker quanto localmente

### 4. Script de Execução Dedicado
- **Arquivo**: `scripts/run-telegram-bot.sh`
- **Funcionalidade**: Script específico para executar o bot com configurações corretas
- **Uso**: Pode ser usado tanto no Docker quanto localmente

### 5. Makefile para Gerenciamento
- **Arquivo**: `Makefile`
- **Comandos**: Facilita build, execução e debug do Docker
- **Destaque**: `make telegram-bot` executa apenas o bot

## Como Usar

### Opção 1: Docker Compose (Recomendado)
```bash
# Construir e executar
make build && make run

# Verificar logs do bot
make logs-telegram

# Verificar se o bot está funcionando
make test
```

### Opção 2: Execução Manual do Bot
```bash
# Apenas o bot do Telegram
make telegram-bot

# Ou usando docker run diretamente
docker run -it --rm \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  migsfy-bot --telegram-bot
```

### Opção 3: Script Dedicado
```bash
# No Docker
docker exec migsfy-bot /app/scripts/run-telegram-bot.sh

# Localmente
./scripts/run-telegram-bot.sh
```

## Verificação de Funcionamento

### 1. Verificar se o Container Está Rodando
```bash
docker ps | grep migsfy-bot
```

### 2. Verificar Logs do Bot
```bash
# Logs gerais
docker logs migsfy-bot

# Logs específicos do Telegram
docker exec migsfy-bot tail -f /app/logs/telegram-bot.log
```

### 3. Testar Importações
```bash
docker exec migsfy-bot python3 -c "from src.telegram.bot import TelegramMusicBot; print('✅ Bot OK')"
```

### 4. Verificar Configuração
```bash
# Verificar se o token está configurado
docker exec migsfy-bot grep TELEGRAM_BOT_TOKEN /app/.env

# Verificar se as dependências estão instaladas
docker exec migsfy-bot python3 -c "import telegram; print('✅ python-telegram-bot OK')"
```

## Comandos de Debug

### Entrar no Container
```bash
make shell
# ou
docker exec -it migsfy-bot bash
```

### Executar Bot Manualmente (Debug)
```bash
# Dentro do container
cd /app
export PYTHONPATH=/app/src:/app
python3 -m src.telegram.bot
```

### Verificar Estrutura de Arquivos
```bash
docker exec migsfy-bot find /app -name "*.py" | grep -E "(bot|telegram)"
```

## Problemas Comuns

### 1. "No module named 'src.telegram.bot'"
- **Causa**: PYTHONPATH não configurado
- **Solução**: Verificar se `ENV PYTHONPATH=/app/src:/app` está no Dockerfile

### 2. "TELEGRAM_BOT_TOKEN não encontrado"
- **Causa**: Arquivo .env não montado ou token não configurado
- **Solução**: Verificar se o volume está montado e o token está no .env

### 3. "python-telegram-bot não encontrado"
- **Causa**: Dependência não instalada
- **Solução**: Reconstruir a imagem Docker (`make rebuild`)

### 4. Bot não responde a comandos
- **Causa**: Configuração de usuários/grupos permitidos
- **Solução**: Verificar `TELEGRAM_ALLOWED_USERS` e `TELEGRAM_ALLOWED_GROUPS` no .env

## Estrutura de Logs

```
/app/logs/
├── telegram-bot.log          # Logs do bot do Telegram
├── playlist-processor.log    # Logs do processador de playlists
└── retry-failed.log         # Logs de retry de downloads
```

## Configurações Importantes no .env

```bash
# Token do bot (obrigatório)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Usuários permitidos (IDs separados por vírgula)
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Grupos permitidos (IDs separados por vírgula)
TELEGRAM_ALLOWED_GROUPS=-1001234567890

# Threads específicas (formato: grupo_id:thread_id)
TELEGRAM_ALLOWED_THREADS=-1001234567890:123
```

## Teste de Funcionamento Completo

```bash
# 1. Construir e executar
make build && make run

# 2. Aguardar alguns segundos
sleep 10

# 3. Verificar se está rodando
make status

# 4. Verificar logs
make logs-telegram

# 5. Testar importação
make test

# 6. Enviar comando /start para o bot no Telegram
```

Se todos os passos funcionarem, o bot estará operacional no Docker.
