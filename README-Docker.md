# 🐳 SLSKD MP3 Search & Download Tool - Docker Edition

Esta é a versão containerizada do SLSKD MP3 Search & Download Tool, permitindo execução em qualquer ambiente com Docker.

## 🚀 Quick Start

### 1. Preparação

```bash
# Clone o repositório
git clone <repository-url>
cd migsfy-bot

# Configure suas credenciais
cp .env.example .env
# Edite o .env com suas configurações
```

### 2. Build da Imagem

```bash
# Usando Makefile (recomendado)
make build

# Ou usando Docker diretamente
docker build -t migsfy-bot .
```

### 3. Execução

```bash
# Busca simples
make search

# Download de playlist Spotify
make playlist

# Ver histórico
make history

# Modo interativo
make run
```

## 📋 Comandos Disponíveis

### Usando Makefile (Recomendado)

```bash
make build      # Constrói a imagem Docker
make run        # Executa o container interativamente
make search     # Busca por uma música
make playlist   # Baixa playlist do Spotify
make history    # Mostra histórico de downloads
make shell      # Abre shell interativo no container
make up         # Inicia com docker-compose
make down       # Para serviços docker-compose
make logs       # Visualiza logs
make clean      # Limpa recursos Docker
make help       # Mostra ajuda
```

### Usando Docker Diretamente

```bash
# Buscar uma música
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  migsfy-bot "Artista - Música"

# Download de playlist Spotify
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  migsfy-bot --playlist "URL_PLAYLIST" --auto

# Ver histórico
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  migsfy-bot --history
```

### Usando Docker Compose

```bash
# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

## ⚙️ Configuração

### Arquivo .env

```env
# SLSKD Configuration
SLSKD_HOST=192.168.15.100  # ou 'slskd' se usando docker-compose
SLSKD_API_KEY=sua_chave_api_aqui
SLSKD_URL_BASE=http://192.168.15.100:5030

# Spotify API Configuration
SPOTIFY_CLIENT_ID=seu_client_id_aqui
SPOTIFY_CLIENT_SECRET=seu_client_secret_aqui
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### Volumes

O container usa os seguintes volumes para persistência:

- `./data:/app/data` - Dados da aplicação
- `./cache:/app/cache` - Cache do Spotify e temporários
- `./.env:/app/.env:ro` - Configurações (somente leitura)

## 🔧 Desenvolvimento

### Build de Desenvolvimento

```bash
# Build com cache
docker build --no-cache -t migsfy-bot:dev .

# Executar em modo desenvolvimento
docker run --rm -it \
  -v $(pwd):/app \
  -v $(pwd)/.env:/app/.env:ro \
  --entrypoint bash \
  migsfy-bot:dev
```

### Debug

```bash
# Shell interativo
make shell

# Ou com docker
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  --entrypoint bash \
  migsfy-bot
```

## 🐳 Docker Compose com SLSKD

Para executar o SLSKD junto com o bot:

```yaml
# Descomente a seção slskd no docker-compose.yml
services:
  slskd:
    image: slskd/slskd:latest
    container_name: slskd
    restart: unless-stopped
    ports:
      - "5030:5030"
      - "50300:50300"
    volumes:
      - ./slskd-config:/app/config
      - ./slskd-downloads:/app/downloads
      - ./slskd-shared:/app/shared
```

Então ajuste o .env:
```env
SLSKD_HOST=slskd
SLSKD_URL_BASE=http://slskd:5030
```

## 📊 Exemplos de Uso

### Busca Simples
```bash
make search
# Digite: "Radiohead - Creep"
```

### Playlist Spotify Completa
```bash
make playlist
# Digite: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
```

### Comandos Avançados
```bash
# Playlist com limite e remoção automática
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  migsfy-bot --playlist "URL" --limit 10 --auto --remove-from-playlist
```

## 🔒 Segurança

- Container executa como usuário não-root (UID 1000)
- Arquivo .env montado como somente leitura
- Dados persistidos em volumes externos
- Imagem baseada em Python slim (menor superfície de ataque)

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de permissão nos volumes**:
   ```bash
   sudo chown -R 1000:1000 data cache
   ```

2. **Arquivo .env não encontrado**:
   ```bash
   cp .env.example .env
   # Configure suas credenciais
   ```

3. **SLSKD não acessível**:
   - Verifique se SLSKD_HOST está correto
   - Se usando docker-compose, use `slskd` como hostname

4. **Spotify não funciona**:
   - Verifique credenciais no .env
   - Certifique-se que redirect_uri está configurado

### Logs e Debug

```bash
# Ver logs do container
make logs

# Shell para debug
make shell

# Verificar configuração
docker run --rm -it \
  -v $(pwd)/.env:/app/.env:ro \
  migsfy-bot --help
```

## 📝 Notas

- O cache do Spotify é persistido no volume `./cache`
- O histórico de downloads fica em `./data`
- Para usar com SLSKD em outro container, ajuste `SLSKD_HOST=slskd`
- A primeira execução com Spotify pode solicitar autenticação no navegador
