# SLSKD MP3 Search & Download Tool

Ferramenta inteligente para buscar e baixar MP3s usando slskd (SoulSeek daemon) com integração ao Spotify, Last.fm e bot do Telegram.

## 🚀 Início Rápido

### Instalação Local
```bash
# Clone o repositório
git clone <repository-url>
cd migsfy-bot

# Instale dependências
pip3 install -r requirements.txt

# Configure variáveis de ambiente
cp config/.env.example .env
# Edite o .env com suas configurações
```

### 🐳 Docker
```bash
# Configure e execute
cp config/.env.example .env
make build && make run
```

## 📖 Documentação Completa

A documentação completa está organizada na pasta `docs/`:

- **[📚 Documentação Principal](docs/README.md)** - Guia completo de uso
- **[🤖 Bot do Telegram](docs/TELEGRAM/)** - Configuração e uso do bot
- **[🏷️ Integração Last.fm](docs/LASTFM/)** - Descoberta de música por tags
  - **[🤖 Download Automático](docs/LASTFM/README-Auto-Download.md)** - Automação via cron
- **[🐳 Docker](docs/DOCKER/)** - Instalação e configuração Docker
- **[📝 Changelogs](docs/CHANGELOG/)** - Histórico de mudanças

## 🎯 Uso Básico

### CLI
```bash
# Buscar música
python3 src/cli/main.py "Artista - Música"

# Buscar álbum
python3 src/cli/main.py --album "Artista - Álbum"

# Baixar playlist Spotify
python3 src/cli/main.py --playlist "URL_PLAYLIST"

# Baixar por tag Last.fm
python3 src/cli/main.py --lastfm-tag "rock" --limit 25

# Baixar por artista Last.fm
python3 src/cli/main.py --lastfm-artist "Pink Floyd" --limit 30

# Download automático Last.fm (via script)
./scripts/lastfm-auto-download.sh
```

### Bot do Telegram
```bash
# Executar bot
./scripts/run-telegram-bot.sh

# Comandos do bot:
# /search Artista - Música
# /album Artista - Álbum
# /spotify URL_PLAYLIST
# /lastfm_tag rock 25
# /lastfm_artist "Pink Floyd" 30
```

## 📁 Estrutura do Projeto

```
migsfy-bot/
├── src/                    # Código fonte
│   ├── cli/               # Interface linha de comando
│   ├── core/              # Módulos principais
│   ├── telegram/          # Bot do Telegram
│   └── utils/             # Utilitários
├── tests/                 # Testes
├── docs/                  # Documentação
├── scripts/               # Scripts auxiliares
│   ├── lastfm-auto-download.sh  # Download automático Last.fm
│   └── run-telegram-bot.sh      # Executar bot Telegram
├── config/                # Configurações
└── logs/                  # Logs da aplicação
```

## 🛠️ Desenvolvimento

```bash
# Executar testes
python3 -m pytest tests/

# Executar testes específicos
python3 -m pytest tests/unit/
python3 -m pytest tests/integration/
```

## 🔄 Compatibilidade

O sistema implementa um mecanismo de importação flexível que permite:

- Funcionar com a estrutura modular (`src/cli/main.py`)
- Funcionar com o arquivo legado (`slskd-mp3-search.py`)
- Detectar automaticamente a estrutura disponível
- Garantir compatibilidade entre diferentes versões da instalação

Esta abordagem permite uma migração gradual para a nova estrutura modular sem quebrar instalações existentes.

## 📝 Licença

MIT License - veja LICENSE para detalhes.

---

**📚 Para documentação completa, exemplos detalhados e guias de configuração, acesse [docs/README.md](docs/README.md)**
