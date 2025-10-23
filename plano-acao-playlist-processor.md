# Plano de Ação - Playlist Processor Script

## 🎯 Objetivo
Criar script autônomo para processar playlists via SLSKD com downloads automáticos de arquivos FLAC.

## 📋 Estrutura do Script

### Arquivo Principal
```
src/playlist_processor.py
```

### Dependências Mínimas
- `sqlite3` (nativo Python)
- `slskd-api` (PyPI: https://pypi.org/project/slskd-api/)
- `os`, `time`, `json` (nativos)
- `python-dotenv` (para .env)

## 📦 Instalação de Dependências

### Biblioteca slskd-api
```bash
pip install slskd-api
```

**Documentação:** https://pypi.org/project/slskd-api/

### Exemplo de Uso
```python
from slskd_api import SlskdApi

# Conectar ao slskd
api = SlskdApi(host="localhost", port=5030, username="admin", password="password")

# Buscar músicas
results = api.searches.search_text("Soundgarden Black Hole Sun *.flac")

# Iniciar download
download_id = api.transfers.download(username="user123", filename="path/to/file.flac")

# Verificar status
status = api.transfers.get_download(download_id)

# Obter fila de downloads
queue = api.transfers.get_downloads()
```

## 🚫 Controle de Duplicatas e Performance

### 1. Verificação Avançada de Duplicatas
```python
# Verificar múltiplos critérios antes de buscar:
- file_line exata no SQLite
- filename normalizado (sem path/extensão)
- artista + música (fuzzy match 85%)
- hash MD5 de arquivos já baixados
```

### 2. Rate Limiting e Throttling
```python
# Limites para não sobrecarregar servidor:
- Máximo 1 busca por 10 segundos
- Máximo 1 download simultâneo
- Pausa de 30s entre arquivos .txt
- Pausa de 2 minutos se erro de conexão
```

### 3. Cache de Resultados de Busca
```sql
CREATE TABLE search_cache (
    query_hash TEXT PRIMARY KEY,
    results TEXT,  -- JSON dos resultados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

### 4. Detecção de Arquivos Similares
```python
# Antes de baixar, verificar se já existe similar:
def normalize_filename(filename):
    # Remove paths, extensões, caracteres especiais
    # Converte para lowercase
    # Remove números de faixa
    return clean_name

def is_duplicate_file(new_file, existing_files):
    # Fuzzy match com threshold 90%
    # Verifica duração similar (±5s)
    # Verifica tamanho similar (±10%)
```

## 🔧 Implementação por Etapas

### Etapa 1: Estrutura Base
```python
# Classe principal PlaylistProcessor
# Configuração via .env
# Cliente slskd-api (PyPI)
# Sistema de logs básico
```

### Etapa 2: Banco SQLite Expandido
```sql
-- Tabela principal de downloads
CREATE TABLE downloads (
    id TEXT PRIMARY KEY,
    username TEXT,
    filename TEXT,
    filename_normalized TEXT,  -- Para detecção de duplicatas
    file_line TEXT NOT NULL,
    status TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,           -- MD5 do arquivo baixado
    requested_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cache de buscas
CREATE TABLE search_cache (
    query_hash TEXT PRIMARY KEY,
    query_text TEXT,
    results TEXT,             -- JSON dos resultados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- Índices para performance
CREATE INDEX idx_filename_normalized ON downloads(filename_normalized);
CREATE INDEX idx_file_line ON downloads(file_line);
CREATE INDEX idx_status ON downloads(status);
CREATE INDEX idx_cache_expires ON search_cache(expires_at);
```

### Etapa 3: Processamento de Arquivos
```python
# Leitura de arquivos .txt em playlists/
# Parse de linhas: ARTISTA - ALBUM - MUSICA
# Validação de formato
```

### Etapa 4: Sistema de Busca
```python
# Padrão 1: "ARTISTA - ALBUM - MUSICA *.flac"
# Padrão 2: "ARTISTA - MUSICA *.flac"  
# Padrão 3: "MUSICA *.flac"
# Filtro anti-remix
# Priorização por qualidade (24bit/96kHz > 16bit/44.1kHz)
```

### Etapa 5: Gerenciamento de Downloads
```python
# Verificação de fila atual
# Prevenção de duplicatas
# Monitoramento de status (10s intervals)
# Timeout de 5 minutos
```

### Etapa 6: Controle de Processo
```python
# Lock file para evitar duplicação
# Cron job configuration
# Cleanup automático
```

## 🏗️ Arquitetura do Código

### Classes Principais
```python
class PlaylistProcessor:
    def __init__(self)
    def process_all_playlists(self)
    def process_playlist_file(self, filepath)
    def normalize_filename(self, filename)
    def is_duplicate_content(self, artist, song)
    def apply_rate_limiting(self)
    def handle_server_overload(self)
    
class SlskdApiClient:
    def __init__(self, host, port, username, password)  # slskd_api.SlskdApi()
    def search_tracks_cached(self, query)               # Com cache + rate limit
    def get_download_queue(self)                        # api.transfers.get_downloads()
    def add_download(self, username, filename)          # api.transfers.download()
    def remove_download(self, download_id)              # api.transfers.cancel_download()
    def get_download_status(self, download_id)          # api.transfers.get_download()
    def is_server_overloaded(self)                      # Detectar sobrecarga
    
class DatabaseManager:
    def __init__(self, db_path)
    def is_downloaded(self, file_line)                  # Verificação básica
    def is_duplicate_normalized(self, filename_norm)    # Por filename normalizado
    def is_duplicate_fuzzy(self, artist, song)          # Fuzzy match 85%
    def is_duplicate_hash(self, file_hash)              # Por hash MD5
    def save_download(self, data, status)
    def get_cached_search(self, query_hash)             # Cache de buscas
    def save_search_cache(self, query_hash, results)    # Salvar cache
    def cleanup_expired_cache(self)                     # Limpeza TTL
    def get_stats(self)
    
class ProcessLock:
    def __init__(self, lock_file)
    def acquire(self)
    def release(self)
    def is_locked(self)
    
class DuplicateDetector:
    def __init__(self, db_manager)
    def normalize_filename(self, filename)              # Remove path/ext/chars
    def fuzzy_match_song(self, artist, song, threshold=0.85)
    def calculate_file_hash(self, filepath)             # MD5 hash
    def is_similar_file(self, new_file, existing_files, threshold=0.90)
    def check_all_duplicates(self, file_line, filename, artist, song)
    
class RateLimiter:
    def __init__(self, min_interval=3)
    def wait_if_needed(self)                           # Aguarda intervalo mínimo
    def record_request(self)                           # Registra timestamp
    def handle_rate_limit_error(self)                  # Pausa em rate limit
    def apply_backoff(self, attempt)                   # Backoff exponencial
    
class CacheManager:
    def __init__(self, db_manager)
    def get_query_hash(self, query)                    # SHA256 da query
    def get_cached_results(self, query)                # Buscar no cache
    def save_results(self, query, results, ttl_hours=24)
    def is_cache_valid(self, cached_entry)             # Verificar TTL
    def cleanup_expired(self)                          # Limpeza automática
```

### Fluxo de Execução Detalhado

#### 1. Inicialização
```
1.1. Verificar lock de processo (exit se ativo)
1.2. Conectar slskd-api + SQLite
     → from slskd_api import SlskdApi
     → api = SlskdApi(host, port, username, password)
1.3. Listar arquivos .txt em playlists/
1.4. Criar lock de processo
```

#### 2. Processamento por Arquivo
```
2.1. Para cada arquivo .txt (com pausa de 30s entre arquivos):
   2.1.1. Ler linha por linha (ARTISTA - ALBUM - MUSICA)
   2.1.2. Verificação multi-nível de duplicatas:
         → Verificar file_line exata no SQLite
         → Verificar filename normalizado no SQLite
         → Verificar fuzzy match artista+música (85%)
         → Verificar hash MD5 se arquivo existe localmente
   2.1.3. Se qualquer verificação = TRUE: pular para próxima linha
   2.1.4. Se todas = FALSE: continuar para etapa 3 (Sistema de Busca)
```

#### 3. Sistema de Busca com Cache (3 Padrões)
```
3.0. Rate limiting: aguardar 3s desde última busca
3.1. Verificar cache de busca (query_hash)
     → Se cache válido (< 24h): usar resultados do cache
     → Se cache inválido: continuar para busca real
3.2. Padrão 1: api.searches.search_text("ARTISTA - ALBUM - MUSICA *.flac")
3.3. Se sem resultados → Padrão 2: api.searches.search_text("ARTISTA - MUSICA *.flac")
3.4. Se sem resultados → Padrão 3: api.searches.search_text("MUSICA *.flac")
3.5. Salvar resultados no cache (TTL 24h)
3.6. Se sem resultados → Salvar como NOT_FOUND no SQLite
```

#### 4. Filtros e Priorização Anti-Duplicata
```
4.1. Filtrar resultados (remover remix)
4.2. Verificar duplicatas por filename normalizado
4.3. Verificar arquivos similares já baixados (fuzzy 90%)
4.4. Priorizar por qualidade:
     → 24bit/96kHz (prioridade 1)
     → 16bit/44.1kHz (prioridade 2)
     → 24bit/qualquer (prioridade 3)
     → 16bit/qualquer (prioridade 4)
4.5. Selecionar melhor resultado não-duplicado
```

#### 5. Verificação de Fila Atual
```
5.1. Obter fila via api.transfers.get_downloads()
5.2. Verificar se usuário existe na fila
5.3. Verificar se arquivo específico existe na fila
     → Se EXISTS: ir para Fluxo de Status (6)
     → Se NOT_EXISTS: ir para Iniciar Download (7)
```

#### 6. Fluxo de Status (Arquivo já na Fila)
```
6.1. Verificar status atual:

STATUS: "Completed, Succeeded"
→ 6.1.1. Salvar no SQLite como SUCCESS
→ 6.1.2. Remover da fila slskd
→ 6.1.3. Remover linha do arquivo .txt
→ 6.1.4. Próxima música

STATUS: "Completed, Errored" | "Completed, Canceled"
→ 6.2.1. Salvar no SQLite como ERROR
→ 6.2.2. Remover da fila slskd
→ 6.2.3. Próxima música (manter linha no .txt)

STATUS: "InProgress"
→ 6.3.1. Ir para Monitoramento (8)

STATUS: "Queued, Remotely"
→ 6.4.1. Aguardar 1 minuto verificando status a cada 10s
→ 6.4.2. Se mudar status → Reavaliar novo status
→ 6.4.3. Se não mudar após 1 minuto → Tratar como ERROR
→ 6.4.4. Salvar no SQLite como ERROR
→ 6.4.5. Remover da fila slskd
→ 6.4.6. Próxima música (manter linha no .txt)
```

#### 7. Iniciar Download
```
7.1. Iniciar download via api.transfers.download(username, filename)
7.2. Obter download_id do retorno
7.3. Ir para Monitoramento (8)
```

#### 8. Monitoramento de Download
```
8.1. Loop de monitoramento (máx 5 minutos):
     8.1.1. Aguardar 10 segundos
     8.1.2. Verificar status via api.transfers.get_download(id)
     
     STATUS: "Completed, Succeeded"
     → 8.2.1. Salvar no SQLite como SUCCESS
     → 8.2.2. Remover da fila via api.transfers.cancel_download(id)
     → 8.2.3. Remover linha do arquivo .txt
     → 8.2.4. Break loop → Próxima música
     
     STATUS: "Completed, Errored" | "Completed, Canceled"
     → 8.3.1. Salvar no SQLite como ERROR
     → 8.3.2. Remover da fila via api.transfers.cancel_download(id)
     → 8.3.3. Break loop → Próxima música
     
     STATUS: "Queued, Remotely"
     → 8.4.1. Aguardar 1 minuto verificando a cada 10s
     → 8.4.2. Se mudar status → Reavaliar novo status no loop
     → 8.4.3. Se não mudar após 1 minuto → Tratar como ERROR
     → 8.4.4. Salvar no SQLite como ERROR
     → 8.4.5. Remover da fila via api.transfers.cancel_download(id)
     → 8.4.6. Break loop → Próxima música
     
     STATUS: "InProgress"
     → 8.5.1. Continue loop (aguardar mais 10s)
     
     TIMEOUT (5 minutos):
     → 8.6.1. Assumir SUCCESS
     → 8.6.2. Salvar no SQLite como SUCCESS
     → 8.6.3. Remover linha do arquivo .txt
     → 8.6.4. Break loop → Próxima música
```

#### 9. Finalização
```
9.1. Processar todas as linhas de todos os arquivos
9.2. Gerar relatório de estatísticas
9.3. Liberar lock de processo
9.4. Exit
```

### Estados do SQLite
```
SUCCESS: Download concluído com sucesso
ERROR: Falha no download (erro, cancelado, timeout de fila)
NOT_FOUND: Música não encontrada em nenhum padrão de busca
```

### Tratamento de Exceções com Throttling
```
- Conexão slskd-api perdida → Pausa 2min → Retry 3x → Exit
- SlskdApi timeout → Pausa 30s → Retry com backoff → Exit
- Rate limit atingido → Pausa 5min → Continue
- SQLite lock → Retry 5x → Exit  
- Arquivo .txt corrompido → Skip arquivo → Continue
- Processo já rodando → Exit imediato
- Servidor sobrecarregado → Pausa 10min → Continue
```

## 📁 Estrutura de Arquivos

### Diretórios
```
# Estrutura no container Docker:
/app/
├── src/
│   ├── playlist/
│   │   ├── __init__.py
│   │   ├── playlist_processor.py     # Script principal
│   │   ├── slskd_api_client.py      # Cliente slskd-api wrapper
│   │   ├── database_manager.py      # Gerenciador SQLite expandido
│   │   ├── duplicate_detector.py    # Detecção de duplicatas
│   │   ├── rate_limiter.py          # Controle de rate limiting
│   │   ├── cache_manager.py         # Gerenciamento de cache
│   │   └── process_lock.py          # Controle de processo
│   └── ...
├── data/
│   ├── playlists/                   # Arquivos .txt (volume)
│   └── downloads.db                 # Base SQLite (volume)
├── logs/
│   └── playlist-processor.log       # Logs (volume)
└── processor.lock                   # Lock file
```

### Configuração .env Expandida
```bash
# Usar .env existente e adicionar:
SLSKD_HOST=slskd
SLSKD_PORT=5030
SLSKD_USERNAME=admin
SLSKD_PASSWORD=password
PLAYLIST_PATH=/app/data/playlists
DATABASE_PATH=/app/data/downloads.db
LOG_LEVEL=INFO
RATE_LIMIT_SECONDS=3
CACHE_TTL_HOURS=24
```

### Estrutura de Volumes Docker
```
# Mapeamento de volumes no docker-compose existente:
./data/playlists/     → /app/data/playlists/     # Arquivos .txt
./data/downloads.db   → /app/data/downloads.db   # SQLite
./logs/              → /app/logs/               # Logs do processor
```

### Configuração .env - Reutilização + Adições

#### ✅ Variáveis Existentes (Reutilizar)
```bash
# SLSKD Configuration (JÁ EXISTE - REUTILIZAR)
SLSKD_HOST=192.168.15.100          # ✅ Usar para conexão
SLSKD_PORT=5030                    # ✅ Usar para conexão  
SLSKD_API_KEY=your_slskd_api_key   # ✅ Usar para autenticação
SLSKD_URL_BASE=http://192.168.15.100:5030  # ✅ Base URL

# Download Configuration (JÁ EXISTE - REUTILIZAR)
SEARCH_WAIT_TIME=25                # ✅ Usar como base para rate limiting
MIN_MP3_SCORE=15                   # ✅ Usar para filtros de qualidade

# Docker User Configuration (JÁ EXISTE - REUTILIZAR)
PUID=0                             # ✅ Manter configuração Docker
PGID=0                             # ✅ Manter configuração Docker
```

#### 🆕 Variáveis Novas (Adicionar ao .env)
```bash
# Playlist Processor Configuration (ADICIONAR)
PLAYLIST_PROCESSOR_ENABLED=true
PLAYLIST_PATH=/app/data/playlists
DATABASE_PATH=/app/data/downloads.db
PROCESSOR_LOCK_PATH=/app/processor.lock

# Rate Limiting & Performance (ADICIONAR)
RATE_LIMIT_SECONDS=3               # Intervalo entre buscas
CACHE_TTL_HOURS=24                 # TTL do cache de buscas
MAX_CONCURRENT_DOWNLOADS=1         # Downloads simultâneos
DUPLICATE_FUZZY_THRESHOLD=0.85     # Threshold fuzzy match

# Monitoring & Logs (ADICIONAR)
LOG_LEVEL=INFO
PLAYLIST_LOG_PATH=/app/logs/playlist-processor.log
ENABLE_PERFORMANCE_METRICS=true

# Retry & Backoff (ADICIONAR)
MAX_RETRY_ATTEMPTS=3
BACKOFF_BASE_SECONDS=30
SERVER_OVERLOAD_PAUSE_MINUTES=10
QUEUE_TIMEOUT_MINUTES=5

# File Processing (ADICIONAR)
FILE_PROCESSING_PAUSE_SECONDS=30   # Pausa entre arquivos .txt
NORMALIZE_FILENAMES=true
CALCULATE_FILE_HASHES=true
AUTO_CLEANUP_CACHE=true
```

#### 🔄 Mapeamento de Variáveis Existentes
```python
# Como reutilizar configurações existentes:
class SlskdApiClient:
    def __init__(self):
        # ✅ Reutilizar configuração SLSKD existente
        self.host = os.getenv('SLSKD_HOST')           # 192.168.15.100
        self.port = os.getenv('SLSKD_PORT')           # 5030
        self.api_key = os.getenv('SLSKD_API_KEY')     # Chave existente
        self.base_url = os.getenv('SLSKD_URL_BASE')   # URL base
        
        # 🆕 Usar novas configurações
        self.rate_limit = int(os.getenv('RATE_LIMIT_SECONDS', 3))
        
class RateLimiter:
    def __init__(self):
        # ✅ Adaptar SEARCH_WAIT_TIME existente (25s)
        base_wait = int(os.getenv('SEARCH_WAIT_TIME', 25))
        new_limit = int(os.getenv('RATE_LIMIT_SECONDS', 3))
        
        # Usar o maior valor para ser conservador
        self.interval = max(base_wait, new_limit)  # 25s (mais conservador)
        
class QualityFilter:
    def __init__(self):
        # ✅ Reutilizar MIN_MP3_SCORE existente
        self.min_score = int(os.getenv('MIN_MP3_SCORE', 15))
        # Aplicar para filtros FLAC também
```

## ⚙️ Configuração Docker Existente

### Integração com Docker Atual
```yaml
# Usar docker-compose.yml existente do projeto
# Adicionar serviço playlist-processor ao compose atual
services:
  playlist-processor:
    build: .
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - SLSKD_HOST=slskd
      - SLSKD_PORT=5030
    depends_on:
      - slskd
    command: python3 src/playlist/playlist_processor.py
```

### Dockerfile Existente
```dockerfile
# Usar Dockerfile atual do projeto
# Adicionar dependência slskd-api no requirements.txt
RUN pip install slskd-api

# Adicionar cron job no container existente
RUN echo "0 */1 * * * cd /app && python3 src/playlist/playlist_processor.py >> logs/playlist-processor.log 2>&1" >> /etc/crontab
```

### Configuração .env Expandida
```bash
# Usar .env existente e adicionar:
SLSKD_HOST=slskd
SLSKD_PORT=5030
SLSKD_USERNAME=admin
SLSKD_PASSWORD=password
PLAYLIST_PATH=/app/data/playlists
DATABASE_PATH=/app/data/downloads.db
LOG_LEVEL=INFO
RATE_LIMIT_SECONDS=3
CACHE_TTL_HOURS=24
```

### Cron no Container Existente
```bash
# Adicionar ao Dockerfile existente:
RUN echo "0 */1 * * * cd /app && python3 src/playlist/playlist_processor.py >> logs/playlist-processor.log 2>&1" >> /etc/crontab

# Ou executar manualmente no container:
docker-compose exec migsfy-bot crontab -e
# Adicionar: 0 */1 * * * cd /app && python3 src/playlist/playlist_processor.py >> logs/playlist-processor.log 2>&1
```

## 🔍 Critérios de Qualidade

### Prioridade de Download
1. **24-bit / 96kHz** (preferencial)
2. **16-bit / 44.1kHz** (padrão CD)
3. **24-bit / qualquer sample rate**
4. **16-bit / qualquer sample rate**
5. **Qualquer FLAC disponível**

### Filtros de Exclusão
- Arquivos com "remix" no título
- Formatos não-FLAC
- Arquivos corrompidos/incompletos

## 📊 Monitoramento e Logs

### Métricas Coletadas
- Total de arquivos processados
- Downloads bem-sucedidos
- Falhas por categoria
- Tempo médio de download
- Usuários mais ativos

### Logs Estruturados
```python
{
    "timestamp": "2025-10-23T13:43:48",
    "level": "INFO",
    "action": "download_completed",
    "file_line": "Soundgarden - A-Sides - Black Hole Sun",
    "username": "user123",
    "filename": "path/to/file.flac",
    "duration": 45.2,
    "file_size": 26440248
}
```

## 🚀 Cronograma de Desenvolvimento

### Semana 1: Base + Duplicatas
- [ ] Estrutura de classes base
- [ ] DatabaseManager expandido (SQLite)
- [ ] DuplicateDetector (normalização + fuzzy)
- [ ] Sistema de logs estruturado

### Semana 2: Performance + Cache
- [ ] RateLimiter (throttling + backoff)
- [ ] CacheManager (busca + TTL)
- [ ] SlskdApiClient com cache integrado
- [ ] Controle de duplicatas multi-nível

### Semana 3: Core + Monitoramento
- [ ] PlaylistProcessor principal
- [ ] Sistema de busca (3 padrões + cache)
- [ ] Monitoramento de downloads
- [ ] Tratamento de status especiais

### Semana 4: Deploy + Otimização
- [ ] ProcessLock robusto
- [ ] Configuração cron otimizada
- [ ] Testes de integração completos
- [ ] Documentação e métricas

## ✅ Critérios de Sucesso

- ✅ Zero dependências externas ao projeto
- ✅ Processamento sequencial sem sobreposição
- ✅ Persistência de dados em SQLite
- ✅ Logs detalhados para debugging
- ✅ Execução automática via cron
- ✅ Prevenção de downloads duplicados
- ✅ Priorização por qualidade de áudio
- ✅ Remoção automática de linhas processadas

## 🔧 Comandos de Execução

### Docker (Recomendado)
```bash
# Usar make commands existentes
make build && make run

# Executar processor manualmente no container
docker-compose exec migsfy-bot python3 src/playlist/playlist_processor.py

# Ver logs do processor
docker-compose logs -f migsfy-bot | grep playlist-processor

# Status check no container
docker-compose exec migsfy-bot python3 src/playlist/playlist_processor.py --status
```

### Local (Desenvolvimento)
```bash
# Manual
python3 src/playlist/playlist_processor.py

# Com logs
python3 src/playlist/playlist_processor.py --verbose

# Status check
python3 src/playlist/playlist_processor.py --status
```

---

**Próximo passo:** Implementar a estrutura base seguindo Clean Code principles.
