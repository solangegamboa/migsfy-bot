# SLSKD MP3 Search & Download Tool

Ferramenta inteligente para buscar e baixar MP3s usando slskd (SoulSeek daemon).

## 🚀 Funcionalidades

- **Busca inteligente**: Prioriza busca por música sem artista para mais resultados
- **Verificação de usuário**: Confirma se usuário está online antes do download
- **Sistema de fallback**: Tenta usuários alternativos automaticamente
- **Filtros avançados**: Usa sintaxe correta do SoulSeek (wildcards, exclusões)
- **Melhoria de nomes**: Renomeia arquivos usando tags de metadados
- **Limpeza manual**: Remove downloads completados da fila
- **🆕 Histórico de downloads**: Evita downloads duplicados automaticamente
- **🆕 Gerenciamento de histórico**: Comandos para visualizar, limpar e forçar downloads

## 📋 Pré-requisitos

- Python 3.9+
- slskd rodando e configurado
- Bibliotecas Python (ver requirements.txt)

## 🔧 Instalação

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

4. **Configure o arquivo .env**:
   ```env
   SLSKD_HOST=192.168.15.100
   SLSKD_API_KEY=sua_chave_api_aqui
   SLSKD_URL_BASE=http://192.168.15.100:5030
   ```

## 🎵 Uso

### Busca básica:
```bash
python3 slskd-mp3-search.py "Artista - Música"
```

### Exemplos:
```bash
python3 slskd-mp3-search.py "Linkin Park - In the End"
python3 slskd-mp3-search.py "Maria Rita - Como Nossos Pais"
python3 slskd-mp3-search.py "Bohemian Rhapsody"
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

### Modo teste:
```bash
python3 slskd-mp3-search.py
```

## ⚙️ Configurações

### Variáveis de ambiente (.env):

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `SLSKD_HOST` | IP do servidor slskd | 192.168.15.100 |
| `SLSKD_API_KEY` | Chave da API do slskd | - |
| `SLSKD_URL_BASE` | URL base do slskd | http://host:5030 |
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

4. **🆕 Sistema de histórico**:
   - Salva automaticamente downloads bem-sucedidos
   - Evita downloads duplicados por padrão
   - Permite forçar downloads quando necessário
   - Histórico armazenado em `download_history.json`

## 🛠️ Funções úteis

### Limpeza manual de downloads:
```python
from slskd_mp3_search import manual_cleanup_downloads, connectToSlskd
slskd = connectToSlskd()
manual_cleanup_downloads(slskd)
```

### 🆕 Gerenciamento de histórico:
```python
from slskd_mp3_search import show_download_history, clear_download_history

# Mostrar histórico
show_download_history()

# Limpar histórico
clear_download_history()
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

## 🐛 Troubleshooting

### Erro de conexão:
- Verifique se slskd está rodando
- Confirme IP e porta no `.env`
- Teste a API key

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

## 📝 Licença

MIT License - veja LICENSE para detalhes.
