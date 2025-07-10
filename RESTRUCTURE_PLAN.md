# Plano de Reestruturação do Projeto

## 📁 Nova Estrutura Proposta

```
migsfy-bot/
├── src/                           # Código fonte principal
│   ├── __init__.py
│   ├── core/                      # Módulos principais
│   │   ├── __init__.py
│   │   ├── slskd_client.py        # Cliente SLSKD
│   │   ├── spotify_client.py      # Cliente Spotify
│   │   ├── search_engine.py       # Motor de busca
│   │   ├── download_manager.py    # Gerenciador de downloads
│   │   └── history_manager.py     # Gerenciador de histórico
│   ├── telegram/                  # Bot do Telegram
│   │   ├── __init__.py
│   │   ├── bot.py                 # Bot principal
│   │   ├── handlers/              # Handlers do bot
│   │   │   ├── __init__.py
│   │   │   ├── search_handler.py
│   │   │   ├── album_handler.py
│   │   │   └── playlist_handler.py
│   │   └── utils/                 # Utilitários do Telegram
│   │       ├── __init__.py
│   │       ├── permissions.py
│   │       └── formatting.py
│   ├── utils/                     # Utilitários gerais
│   │   ├── __init__.py
│   │   ├── album_name_extractor.py
│   │   ├── file_utils.py
│   │   └── config.py
│   └── cli/                       # Interface de linha de comando
│       ├── __init__.py
│       └── main.py                # Script principal CLI
├── tests/                         # Todos os testes
│   ├── __init__.py
│   ├── unit/                      # Testes unitários
│   │   ├── __init__.py
│   │   ├── test_slskd_client.py
│   │   ├── test_spotify_client.py
│   │   ├── test_search_engine.py
│   │   └── test_album_extractor.py
│   ├── integration/               # Testes de integração
│   │   ├── __init__.py
│   │   ├── test_telegram_bot.py
│   │   ├── test_album_search.py
│   │   └── test_playlist_download.py
│   └── fixtures/                  # Dados de teste
│       ├── __init__.py
│       ├── sample_responses.json
│       └── test_playlists.json
├── scripts/                       # Scripts auxiliares
│   ├── run-telegram-bot.sh
│   ├── run-telegram-bot-improved.sh
│   ├── test-docker.sh
│   └── docker-entrypoint.sh
├── docs/                          # Documentação
│   ├── README.md                  # README principal (movido)
│   ├── CHANGELOG/                 # Changelogs organizados
│   │   ├── CHANGELOG-AutoCleanup.md
│   │   ├── CHANGELOG-Album-Selection.md
│   │   ├── CHANGELOG-Cancel-Feature.md
│   │   └── ...
│   ├── TELEGRAM/                  # Docs específicas do Telegram
│   │   ├── README-Telegram.md
│   │   ├── README-Telegram-Groups.md
│   │   ├── TELEGRAM-ALBUM-EXAMPLE.md
│   │   └── telegram-commands-examples.md
│   └── DOCKER/                    # Docs específicas do Docker
│       ├── README-Docker.md
│       ├── DOCKER-PERMISSIONS.md
│       └── docker-compose.yml
├── config/                        # Arquivos de configuração
│   ├── .env.example
│   ├── .env.docker
│   └── docker-compose.override.yml.example
├── data/                          # Dados da aplicação (já existe)
│   └── ...
├── cache/                         # Cache da aplicação (já existe)
│   └── ...
├── logs/                          # Logs (novo)
│   ├── .gitkeep
│   └── README.md
├── requirements.txt               # Dependências Python
├── Dockerfile                     # Docker
├── Makefile                       # Comandos Make
├── .gitignore
├── .gitattributes
├── .dockerignore
└── README.md                      # README simplificado (link para docs/)
```

## 🔄 Passos da Migração

### 1. Criar estrutura de pastas
- [x] Criar pastas src/, tests/, scripts/, docs/, config/, logs/

### 2. Reorganizar código fonte
- [ ] Mover slskd-mp3-search.py → src/cli/main.py
- [ ] Mover telegram_bot.py → src/telegram/bot.py
- [ ] Mover album_name_extractor.py → src/utils/
- [ ] Quebrar código em módulos menores

### 3. Reorganizar testes
- [ ] Mover test-*.py → tests/integration/
- [ ] Criar testes unitários em tests/unit/
- [ ] Criar fixtures em tests/fixtures/

### 4. Reorganizar scripts
- [ ] Mover *.sh → scripts/
- [ ] Mover docker-entrypoint.sh → scripts/

### 5. Reorganizar documentação
- [ ] Mover README.md → docs/
- [ ] Mover CHANGELOG-*.md → docs/CHANGELOG/
- [ ] Mover README-Telegram*.md → docs/TELEGRAM/
- [ ] Mover README-Docker.md → docs/DOCKER/

### 6. Reorganizar configuração
- [ ] Mover .env.example → config/
- [ ] Mover .env.docker → config/
- [ ] Mover docker-compose.override.yml.example → config/

### 7. Criar logs/
- [ ] Criar pasta logs/ com .gitkeep
- [ ] Mover *.log → logs/

### 8. Atualizar imports e referências
- [ ] Atualizar imports nos arquivos Python
- [ ] Atualizar scripts shell
- [ ] Atualizar Dockerfile
- [ ] Atualizar Makefile
- [ ] Atualizar docker-compose.yml

## 🎯 Benefícios da Nova Estrutura

### ✅ Separação Clara
- **src/**: Todo código funcional
- **tests/**: Todos os testes separados
- **docs/**: Documentação organizada
- **scripts/**: Scripts auxiliares
- **config/**: Configurações centralizadas

### ✅ Modularização
- Código quebrado em módulos menores e específicos
- Facilita manutenção e testes
- Melhor reutilização de código

### ✅ Organização por Funcionalidade
- **core/**: Funcionalidades principais (SLSKD, Spotify, etc.)
- **telegram/**: Tudo relacionado ao bot
- **utils/**: Utilitários compartilhados
- **cli/**: Interface de linha de comando

### ✅ Testes Estruturados
- **unit/**: Testes de unidades individuais
- **integration/**: Testes de integração
- **fixtures/**: Dados de teste reutilizáveis

### ✅ Documentação Organizada
- Docs separadas por categoria
- Changelogs organizados
- Fácil navegação

## 🚀 Próximos Passos

1. **Executar migração**: Seguir os passos acima
2. **Testar**: Garantir que tudo funciona após migração
3. **Atualizar CI/CD**: Se houver pipelines, atualizar caminhos
4. **Documentar**: Atualizar README com nova estrutura
