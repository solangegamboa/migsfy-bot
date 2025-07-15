# SLSKD MP3 Search & Download Tool

Ferramenta inteligente para buscar e baixar MP3s usando slskd (SoulSeek daemon) com integração ao Spotify e Last.fm.

## 🚀 Funcionalidades

- **Busca inteligente**: Prioriza busca por música sem artista para mais resultados
- **🆕 Busca por álbum**: Detecta e baixa álbuns completos automaticamente
- **Verificação de usuário**: Confirma se usuário está online antes do download
- **Sistema de fallback**: Tenta usuários alternativos automaticamente
- **Filtros avançados**: Usa sintaxe correta do SoulSeek (wildcards, exclusões)
- **Melhoria de nomes**: Renomeia arquivos usando tags de metadados
- **🆕 Limpeza automática**: Remove downloads completados da fila automaticamente
- **🆕 Monitoramento inteligente**: Monitora downloads e limpa automaticamente
- **🆕 Histórico de downloads**: Evita downloads duplicados automaticamente
- **🆕 Gerenciamento de histórico**: Comandos para visualizar, limpar e forçar downloads
- **🎵 Integração Spotify**: Baixa playlists completas do Spotify automaticamente
- **🗑️ Remoção automática**: Remove músicas da playlist após encontrá-las para download
- **🤖 Bot do Telegram**: Controle remoto via Telegram para busca e download
- **🏷️ Integração Last.fm**: Descoberta de música por tags e download automático

## 📋 Pré-requisitos

- Python 3.9+
- slskd rodando e configurado
- Bibliotecas Python (ver requirements.txt)
- **🆕 Conta Spotify Developer** (opcional, para playlists)

## 🔧 Instalação

### Instalação Local

1. **Clone o repositório**:
   ```bash
   git clone <repository-url>
   cd migsfy-bot
   ```

2. **Instale as dependências**:
   ```bash
   pip3 install slskd-api python-dotenv music-tag spotipy
   ```

3. **Configure as variáveis de ambiente**:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

### 🐳 Instalação com Docker

1. **Clone e configure**:
   ```bash
   git clone <repository-url>
   cd migsfy-bot
   cp .env.example .env
   # Edite o .env com suas configurações
   ```

2. **Configure PUID e PGID (opcional)**:
   ```bash
   # Por padrão usa root (PUID=0, PGID=0) para máxima compatibilidade
   # Para usar seu usuário local (opcional):
   echo "PUID=$(id -u)" >> .env
   echo "PGID=$(id -g)" >> .env
   ```

3. **Build e execute**:
   ```bash
   # Build da imagem
   make build
   
   # Execução interativa (com permissões corretas)
   make run
   
   # Ou comandos específicos
   make search    # Buscar música
   make playlist  # Download de playlist
   make history   # Ver histórico
   
   # Com docker-compose
   make up        # Background
   make up-fg     # Foreground
   ```

4. **Veja o [README-Docker.md](README-Docker.md) para instruções detalhadas**
5. **Veja o [DOCKER-PERMISSIONS.md](DOCKER-PERMISSIONS.md) para configuração de permissões**

4. **Configure o arquivo .env**:
   ```env
   # SLSKD Configuration
   SLSKD_HOST=192.168.15.100
   SLSKD_API_KEY=sua_chave_api_aqui
   SLSKD_URL_BASE=http://192.168.15.100:5030
   
   # Spotify API Configuration (opcional)
   SPOTIFY_CLIENT_ID=seu_client_id_aqui
   SPOTIFY_CLIENT_SECRET=seu_client_secret_aqui
   ```

5. **🆕 Configurar Spotify (opcional)**:
   - Acesse [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Crie um novo app
   - Configure Redirect URI: `http://localhost:8888/callback`
   - Copie Client ID e Client Secret para o .env

6. **🏷️ Configurar Last.fm (opcional)**:
   - Acesse [Last.fm API](https://www.last.fm/api/account/create)
   - Crie uma conta de API
   - Obtenha API Key e Shared Secret
   - Adicione as credenciais ao .env:
   ```env
   LASTFM_API_KEY=sua_api_key_aqui
   LASTFM_API_SECRET=seu_shared_secret_aqui
   ```
   
   **🔐 Autenticação OAuth (opcional)**:
   - Para recursos pessoais (scrobbling, músicas curtidas, top tracks)
   - Processo automático via navegador quando necessário
   - Session key armazenado localmente para reutilização
   - Teste a conexão: `python3 src/core/lastfm/oauth_auth.py`

## 🎵 Uso

### Busca básica:
```bash
python3 slskd-mp3-search.py "Artista - Música"
```

### 💿 Busca por álbum:
```bash
# Busca específica por álbum
python3 slskd-mp3-search.py --album "Pink Floyd - The Dark Side of the Moon"

# Detecção automática (palavras-chave: album, lp, ep, discography, etc.)
python3 slskd-mp3-search.py "Beatles - Abbey Road"
python3 slskd-mp3-search.py "Radiohead - OK Computer Album"
python3 slskd-mp3-search.py "Led Zeppelin Discography"
```

### Exemplos:
```bash
python3 slskd-mp3-search.py "Linkin Park - In the End"
python3 slskd-mp3-search.py "Maria Rita - Como Nossos Pais"
python3 slskd-mp3-search.py "Bohemian Rhapsody"
python3 slskd-mp3-search.py --album "Queen - A Night at the Opera"
```

### 🧹 Comandos de limpeza de downloads:
```bash
# Limpeza manual imediata
python3 slskd-mp3-search.py --cleanup

# Monitoramento contínuo (30 minutos)
python3 slskd-mp3-search.py --monitor

# Desabilitar limpeza automática (para qualquer comando)
python3 slskd-mp3-search.py "Artista - Música" --no-auto-cleanup
python3 slskd-mp3-search.py --playlist "URL" --no-auto-cleanup
```

### 🆕 Comandos de histórico:
```bash
# Visualizar histórico de downloads
python3 slskd-mp3-search.py --history

# Forçar download mesmo se já baixado
python3 slskd-mp3-search.py --force "Artista - Música"

# Remover entrada específica do histórico
python3 slskd-mp3-search.py --remove "Artista - Música"

# Limpar todo o histórico
python3 slskd-mp3-search.py --clear-history
```

### 🏷️ Comandos Last.fm:
```bash
# Baixar músicas populares por tag
python3 src/cli/main.py --lastfm-tag "rock" --limit 25

# Baixar músicas de diferentes gêneros
python3 src/cli/main.py --lastfm-tag "jazz" --limit 10
python3 src/cli/main.py --lastfm-tag "alternative rock" --limit 15
python3 src/cli/main.py --lastfm-tag "metal" --limit 20

# Baixar para diretório específico
python3 src/cli/main.py --lastfm-tag "pop" --limit 30 --output-dir "./downloads/pop"

# Incluir músicas já baixadas (não pular duplicatas)
python3 src/cli/main.py --lastfm-tag "rock" --no-skip-existing
```

### 🤖 Download Automático Last.fm:
```bash
# Executar script de automação uma vez
./scripts/lastfm-auto-download.sh

# Monitorar logs do download automático
tail -f logs/lastfm_auto_download.log

# Configurar no crontab para execução automática
crontab -e
# Adicionar: 0 2 */2 * * /caminho/para/projeto/scripts/lastfm-auto-download.sh
```

### 🎵 Comandos Spotify:
```bash
# Preview de playlist (sem baixar)
python3 slskd-mp3-search.py --preview "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Baixar playlist completa
python3 slskd-mp3-search.py --playlist "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Baixar automaticamente sem confirmação
python3 slskd-mp3-search.py --playlist "URL_DA_PLAYLIST" --auto

# Baixar apenas as primeiras 10 músicas
python3 slskd-mp3-search.py --playlist "URL_DA_PLAYLIST" --limit 10

# Baixar incluindo duplicatas (não pula músicas já baixadas)
python3 slskd-mp3-search.py --playlist "URL_DA_PLAYLIST" --no-skip

# Remover músicas da playlist após encontrá-las
python3 slskd-mp3-search.py --playlist "URL_DA_PLAYLIST" --remove-from-playlist

# Combinar opções
python3 slskd-mp3-search.py --playlist "URL_DA_PLAYLIST" --limit 5 --no-skip --auto --remove-from-playlist
```

### Formatos de URL Spotify aceitos:
```bash
# URL completa
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# URL curta
https://spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# URI do Spotify
spotify:playlist:37i9dQZF1DXcBWIGoYBM5M

# Apenas o ID
37i9dQZF1DXcBWIGoYBM5M
```

### Ajuda e comandos:
```bash
# Mostra ajuda e comandos disponíveis
python3 slskd-mp3-search.py
```

### 🤖 Bot do Telegram:
```bash
# Executar bot localmente
./run-telegram-bot.sh

# Com Docker
make telegram-bot

# Comandos do bot:
# /start - Iniciar bot
# /search <termo> - Buscar música
# /album <artista - álbum> - Buscar álbum (🆕 com seleção de candidatos!)
# /spotify <url> - Baixar playlist
# /history - Ver histórico
# /info - Informações do chat (IDs para configuração)
# Exemplo: /search Artista - Música
# Exemplo: /album Pink Floyd - The Dark Side of the Moon
# Exemplo: /spotify https://open.spotify.com/playlist/ID
```

### 🏢 Configuração para Grupos e Threads:
O bot pode ser configurado para funcionar apenas em threads específicas de grupos:

```env
# Grupos permitidos
TELEGRAM_ALLOWED_GROUPS=-1001234567890,-1009876543210

# Threads específicas (formato: grupo_id:thread_id)
TELEGRAM_ALLOWED_THREADS=-1001234567890:123,-1001234567890:456
```

**Use o comando `/info` para descobrir IDs automaticamente!**

Veja [README-Telegram-Groups.md](README-Telegram-Groups.md) para configuração detalhada.

## ⚙️ Configurações

### Variáveis de ambiente (.env):

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `SLSKD_HOST` | IP do servidor slskd | 192.168.15.100 |
| `SLSKD_API_KEY` | Chave da API do slskd | - |
| `SLSKD_URL_BASE` | URL base do slskd | http://host:5030 |
| `SPOTIFY_CLIENT_ID` | Client ID do Spotify | - |
| `SPOTIFY_CLIENT_SECRET` | Client Secret do Spotify | - |
| `SPOTIFY_REDIRECT_URI` | URI de redirecionamento | http://localhost:8888/callback |
| `LASTFM_API_KEY` | Chave da API do Last.fm | - |
| `LASTFM_API_SECRET` | Secret da API do Last.fm | - |
| `LASTFM_AUTO_TAGS` | Tags para download automático (separadas por vírgula) | rock,pop,jazz |
| `LASTFM_AUTO_LIMIT` | Limite de músicas por tag no download automático | 15 |
| `LASTFM_AUTO_OUTPUT_DIR` | Diretório para downloads automáticos | ./downloads/lastfm_auto |
| `LASTFM_AUTO_SKIP_EXISTING` | Pular músicas já baixadas no download automático | true |
| `TELEGRAM_BOT_TOKEN` | Token do bot do Telegram | - |
| `TELEGRAM_ALLOWED_USERS` | IDs dos usuários autorizados | - |
| `TELEGRAM_ALLOWED_GROUPS` | IDs dos grupos autorizados | - |
| `TELEGRAM_ALLOWED_THREADS` | Threads específicas (grupo:thread) | - |
| `MAX_SEARCH_VARIATIONS` | Máximo de variações de busca | 8 |
| `MIN_MP3_SCORE` | Score mínimo para MP3 | 15 |
| `SEARCH_WAIT_TIME` | Tempo limite de busca (s) | 25 |

## 🎯 Como funciona

1. **Estratégia de busca**:
   - Prioriza busca apenas pela música (mais resultados)
   - Depois tenta com artista + música
   - Para quando encontra >50 arquivos

2. **Seleção inteligente**:
   - Pontua arquivos por qualidade (bitrate, tamanho)
   - Prioriza 320kbps
   - Exclui samples e previews

3. **Download robusto**:
   - Verifica se usuário está online
   - Tenta usuários alternativos se necessário
   - Usa formato correto da API slskd

4. **🆕 Limpeza automática**:
   - Remove downloads completados da fila automaticamente
   - Monitora downloads em tempo real
   - Evita acúmulo de downloads antigos na interface
   - Pode ser desabilitada com `--no-auto-cleanup`

5. **🆕 Sistema de histórico**:
   - Salva automaticamente downloads bem-sucedidos
   - Evita downloads duplicados por padrão
   - Permite forçar downloads quando necessário
   - Histórico armazenado em `download_history.json`

6. **🎵 Integração Spotify**:
   - Extrai automaticamente faixas de playlists
   - Converte para formato "Artista - Música"
   - Suporte a playlists públicas e privadas (com autenticação)
   - Preview antes de baixar
   - Controle de limite e duplicatas

7. **🏷️ Integração Last.fm**:
   - Descobre músicas populares por tags/gêneros
   - Suporte a tags em português e inglês
   - Requer credenciais válidas da API Last.fm
   - Download automático de tracks individuais (nunca álbuns completos)
   - Organização automática por diretórios de tag

## 🛠️ Funções úteis

### 🧹 Limpeza automática de downloads:
```python
from slskd_mp3_search import auto_cleanup_completed_downloads, connectToSlskd
slskd = connectToSlskd()

# Limpeza automática silenciosa
auto_cleanup_completed_downloads(slskd, silent=True)

# Limpeza automática com feedback
auto_cleanup_completed_downloads(slskd, silent=False)
```

### Limpeza manual de downloads:
```python
from slskd_mp3_search import manual_cleanup_downloads, connectToSlskd
slskd = connectToSlskd()
manual_cleanup_downloads(slskd)
```

### 🔄 Monitoramento de downloads:
```python
from slskd_mp3_search import monitor_and_cleanup_downloads, connectToSlskd
slskd = connectToSlskd()

# Monitora por 10 minutos, limpeza a cada 15 segundos
monitor_and_cleanup_downloads(slskd, max_wait=600, check_interval=15)
```

### 🆕 Gerenciamento de histórico:
```python
from slskd_mp3_search import show_download_history, clear_download_history

# Mostrar histórico
show_download_history()

# Limpar histórico
clear_download_history()
```

### 🎵 Funções Spotify:
```python
from slskd_mp3_search import setup_spotify_client, get_playlist_tracks

# Configurar cliente
sp = setup_spotify_client()

# Obter faixas de playlist
tracks, name = get_playlist_tracks(sp, "playlist_id")
```

## 📁 Estrutura do projeto

```
/
├── slskd-mp3-search.py     # Script principal
├── download_history.json   # Histórico de downloads (criado automaticamente)
├── .env                    # Configurações (não commitado)
├── .env.example           # Template de configurações
├── .gitignore             # Arquivos ignorados pelo git
└── README.md              # Este arquivo
```

## 🔒 Segurança

- Chaves sensíveis ficam no arquivo `.env`
- `.env` está no `.gitignore` (não é commitado)
- Use `.env.example` como template
- Histórico de downloads é local e não contém informações sensíveis
- Credenciais Spotify são usadas apenas para leitura de playlists públicas

## 🐛 Troubleshooting

### Erro de conexão slskd:
- Verifique se slskd está rodando
- Confirme IP e porta no `.env`
- Teste a API key

### Erro Spotify:
- Verifique credenciais no `.env`
- Confirme que o app está ativo no Spotify Developer Dashboard
- Teste com playlist pública primeiro

### Sem resultados:
- Tente termos de busca mais simples
- Verifique conectividade do slskd com SoulSeek
- Ajuste `MIN_MP3_SCORE` no `.env`

### Downloads falham:
- Usuários podem estar offline
- Verifique logs do slskd
- Tente reiniciar o slskd

### 🆕 Problemas com histórico:
- Arquivo `download_history.json` corrompido: delete e será recriado
- Para ignorar histórico temporariamente: use `--force`
- Para limpar histórico: use `--clear-history`

### 🎵 Problemas com playlists:
- Playlist privada: configure credenciais Spotify
- URL inválida: use formato correto do Spotify
- Muitas faixas: use `--limit N` para testar primeiro

## 📝 Exemplos de Uso Completo

### Cenário 1: Download de playlist pequena
```bash
# Preview primeiro
python3 slskd-mp3-search.py --preview "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Download completo
python3 slskd-mp3-search.py --playlist "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Download automático (sem confirmação)
python3 slskd-mp3-search.py --playlist "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --auto
```

### Cenário 2: Playlist grande (teste limitado)
```bash
# Testar com 5 músicas primeiro
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --limit 5

# Se funcionou bem, baixar mais automaticamente
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --limit 20 --auto
```

### Cenário 3: Re-download de playlist
```bash
# Forçar download mesmo de músicas já baixadas
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --no-skip --auto
```

### Cenário 4: Download automatizado completo
```bash
# Download completo sem interação do usuário (com limpeza automática)
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --auto

# Download limitado e automatizado (com limpeza automática)
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --limit 10 --auto

# Download completo incluindo duplicatas, sem confirmação (com limpeza automática)
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --no-skip --auto

# Download com remoção automática da playlist (com limpeza automática)
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --auto --remove-from-playlist

# Download sem limpeza automática (para controle manual)
python3 slskd-mp3-search.py --playlist "URL_PLAYLIST" --auto --no-auto-cleanup
```

### Cenário 5: Limpeza e monitoramento
```bash
# Limpeza manual imediata
python3 slskd-mp3-search.py --cleanup

# Monitoramento contínuo por 30 minutos
python3 slskd-mp3-search.py --monitor

# Download individual sem limpeza automática
python3 slskd-mp3-search.py "Artista - Música" --no-auto-cleanup
```

## 🆕 Nova Funcionalidade: Seleção de Álbuns no Telegram

### 🎯 Seleção Inteligente de Álbuns
Agora ao usar o comando `/album` no bot do Telegram, você verá os **5 melhores álbuns encontrados** e poderá escolher qual baixar!

**Como funciona:**
1. `/album Pink Floyd - The Dark Side of the Moon`
2. Bot mostra lista com 5 opções ordenadas por qualidade
3. Cada opção mostra: nome, usuário, número de faixas, bitrate e tamanho
4. Você clica no botão do álbum desejado
5. Download é iniciado automaticamente

**Informações mostradas:**
- 📀 Nome do álbum
- 👤 Usuário que compartilha
- 🎵 Número de faixas
- 🎧 Bitrate médio (qualidade)
- 💾 Tamanho total

**Vantagens:**
- ✅ Controle total sobre qual versão baixar
- ✅ Comparação fácil entre opções
- ✅ Evita downloads de baixa qualidade
- ✅ Cancelamento a qualquer momento
- ✅ Feedback em tempo real
- ✅ **Nomes reais dos álbuns** extraídos automaticamente (não mais "Álbum Desconhecido")

Veja [CHANGELOG-Album-Selection.md](CHANGELOG-Album-Selection.md) para detalhes técnicos e [TELEGRAM-ALBUM-EXAMPLE.md](TELEGRAM-ALBUM-EXAMPLE.md) para exemplos visuais.

## 📝 Licença

MIT License - veja LICENSE para detalhes.
