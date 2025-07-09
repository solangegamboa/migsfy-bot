# 🤖 SLSKD Music Bot - Telegram Edition

Bot do Telegram para controlar remotamente o SLSKD MP3 Search & Download Tool. Permite buscar músicas e baixar playlists do Spotify diretamente pelo Telegram.

## 🚀 Quick Start

### 1. Criar Bot no Telegram

1. **Abra o Telegram e procure por @BotFather**
2. **Envie `/newbot`**
3. **Escolha um nome para seu bot** (ex: "SLSKD Music Bot")
4. **Escolha um username** (ex: "slskd_music_bot")
5. **Copie o token fornecido**

### 2. Configuração

```bash
# Configure o .env
cp .env.example .env

# Adicione suas credenciais
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### 3. Execução

```bash
# Localmente
./run-telegram-bot.sh

# Com Docker
make telegram-bot

# Com docker-compose
docker-compose up telegram-bot
```

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Token do bot (obrigatório)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# IDs dos usuários autorizados (opcional)
# Se não especificado, permite todos os usuários
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Outras configurações (mesmo do script principal)
SLSKD_HOST=192.168.15.100
SLSKD_API_KEY=sua_chave_api
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
```

### Obter ID do Usuário

Para descobrir seu ID do Telegram:

1. **Envie uma mensagem para @userinfobot**
2. **Copie o ID fornecido**
3. **Adicione ao TELEGRAM_ALLOWED_USERS**

## 🎵 Comandos do Bot

### Comandos Básicos

- `/start` - Inicia o bot e mostra boas-vindas
- `/help` - Lista todos os comandos disponíveis
- `/status` - Mostra status dos serviços (slskd, Spotify)

### Busca de Música

```
# Comando específico (OBRIGATÓRIO)
/search Radiohead - Creep
/search Linkin Park - In the End
```

### Playlists do Spotify

```
# Download básico (OBRIGATÓRIO usar /spotify)
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Com opções
/spotify URL limit=10
/spotify URL remove=yes
/spotify URL limit=5 remove=yes
```

### Histórico

- `/history` - Mostra histórico de downloads
- `/clear_history` - Limpa histórico (com confirmação)

**⚠️ IMPORTANTE:** O bot agora funciona APENAS com comandos específicos. Não é possível enviar mensagens de texto livres.

## 🔧 Funcionalidades

### 🎯 Busca Inteligente

- **Busca automática**: Envie "Artista - Música" ou use `/search`
- **Feedback em tempo real**: Mostra progresso da busca
- **Integração completa**: Usa todas as funcionalidades do script principal

### 🎵 Playlists do Spotify

- **Download automático**: Processa todas as faixas da playlist
- **Progresso em tempo real**: Atualiza status durante download
- **Opções avançadas**: Limite de faixas, remoção da playlist
- **Relatório final**: Estatísticas completas do download

### 🔒 Segurança

- **Lista de usuários autorizados**: Apenas usuários específicos podem usar
- **Validação de comandos**: Verifica permissões antes de executar
- **Logs detalhados**: Registra todas as ações

### 📊 Monitoramento

- **Status dos serviços**: Verifica conectividade com slskd e Spotify
- **Histórico completo**: Acesso ao histórico de downloads
- **Feedback visual**: Emojis e formatação para melhor UX

## 🐳 Docker

### Execução com Docker

```bash
# Build da imagem
make build

# Executar bot
make telegram-bot

# Ou diretamente
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  migsfy-bot --telegram-bot
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  telegram-bot:
    build: .
    container_name: migsfy-telegram-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    command: ["--telegram-bot"]
```

```bash
# Iniciar
docker-compose up telegram-bot -d

# Ver logs
docker-compose logs -f telegram-bot
```

## 📱 Exemplos de Uso

### Busca Simples

```
Usuário: /search Radiohead - Creep
Bot: 🔍 Buscando: Radiohead - Creep
Bot: ✅ Busca iniciada: Radiohead - Creep
     💡 Download em andamento no slskd
```

### Playlist do Spotify

```
Usuário: /spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
Bot: 🎵 Processando playlist...
Bot: 🎵 Today's Top Hits
     📊 50 faixas
     ⏳ Iniciando downloads...
Bot: 📍 [1/50] Artist - Song...
     ✅ Sucessos: 1 | ⏭️ Puladas: 0 | ❌ Falhas: 0
```

### Comandos com Opções

```
Usuário: /spotify https://spotify.com/playlist/ID limit=5 remove=yes
Bot: 🎵 My Playlist
     📊 5 faixas (de 50 total)
     🗑️ Faixas encontradas serão removidas da playlist
     ⏳ Iniciando downloads...
```

### Mensagem Não Reconhecida

```
Usuário: Radiohead - Creep
Bot: ❓ Comando não reconhecido
     
     Use apenas os comandos disponíveis:
     
     🎵 Para buscar música:
     /search <termo>
     
     🎵 Para playlist do Spotify:
     /spotify <url>
     
     💡 Digite /help para ver todos os comandos disponíveis.
```

## 🛠️ Desenvolvimento

### Estrutura do Código

```python
class TelegramMusicBot:
    def __init__(self):
        # Inicialização e conexão com serviços
    
    async def start_command(self, update, context):
        # Comando /start
    
    async def handle_message(self, update, context):
        # Processa mensagens de texto
    
    async def _handle_music_search(self, update, search_term):
        # Executa busca de música
    
    async def _handle_playlist_download(self, update, url, options):
        # Processa download de playlist
```

### Logs

```bash
# Ver logs em tempo real
tail -f telegram_bot.log

# Com Docker
docker-compose logs -f telegram-bot
```

### Debug

```bash
# Modo debug local
DEBUG=true python3 telegram_bot.py

# Shell interativo no Docker
make shell
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Bot não responde**:
   ```bash
   # Verificar token
   grep TELEGRAM_BOT_TOKEN .env
   
   # Testar conectividade
   curl -s "https://api.telegram.org/bot$TOKEN/getMe"
   ```

2. **Usuário não autorizado**:
   ```bash
   # Verificar ID do usuário
   grep TELEGRAM_ALLOWED_USERS .env
   
   # Obter ID: envie mensagem para @userinfobot
   ```

3. **Serviços não conectam**:
   ```bash
   # Verificar configuração
   python3 -c "from telegram_bot import TelegramMusicBot; bot = TelegramMusicBot()"
   ```

4. **Spotify não funciona**:
   ```bash
   # Verificar credenciais
   grep SPOTIFY_ .env
   
   # Testar autenticação
   /status
   ```

### Logs de Erro

```bash
# Logs detalhados
export LOG_LEVEL=DEBUG
python3 telegram_bot.py

# Verificar conectividade
/status
```

## 📝 Notas

- **Rate Limiting**: O bot respeita limites do Telegram API
- **Processamento Assíncrono**: Downloads de playlist são executados em background
- **Persistência**: Histórico e cache são mantidos entre reinicializações
- **Segurança**: Apenas usuários autorizados podem usar o bot
- **Integração**: Usa todas as funcionalidades do script principal

## 🎯 Casos de Uso

1. **Controle Remoto**: Controlar downloads de qualquer lugar
2. **Compartilhamento**: Múltiplos usuários podem usar o mesmo bot
3. **Automação**: Integrar com outros bots ou scripts
4. **Monitoramento**: Acompanhar downloads em tempo real
5. **Conveniência**: Interface amigável via Telegram

O bot está **100% funcional** e pronto para uso! 🚀
