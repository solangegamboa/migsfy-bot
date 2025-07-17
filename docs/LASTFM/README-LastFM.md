# Last.fm Integration Guide

## 🏷️ Visão Geral

A integração com Last.fm permite descobrir e baixar músicas populares baseadas em tags/gêneros musicais. Esta funcionalidade é ideal para descobrir novas músicas dentro de estilos específicos.

## 🚀 Configuração

### 1. Obter Credenciais da API Last.fm

1. Acesse [Last.fm API](https://www.last.fm/api/account/create)
2. Crie uma conta de desenvolvedor
3. Registre uma nova aplicação
4. Obtenha sua **API Key** e **Shared Secret**

### 2. Configurar Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Last.fm API Configuration
LASTFM_API_KEY=sua_api_key_aqui
LASTFM_API_SECRET=seu_shared_secret_aqui
```

**Nota**: Apenas API Key e Secret são necessários. A autenticação de usuário foi removida para simplificar a configuração.

## 🎵 Como Usar

### Comandos Básicos

#### Download por Tags/Gêneros

```bash
python3 src/cli/main.py --lastfm-tag "nome_da_tag"
```

#### Download por Artista

```bash
python3 src/cli/main.py --lastfm-artist "nome_do_artista"
```

### Exemplos Práticos

#### Downloads por Tag

```bash
# Baixar 25 músicas de rock (padrão)
python3 src/cli/main.py --lastfm-tag "rock"

# Baixar 10 músicas de jazz
python3 src/cli/main.py --lastfm-tag "jazz" --limit 10

# Baixar músicas de rock alternativo para diretório específico
python3 src/cli/main.py --lastfm-tag "alternative rock" --limit 15 --output-dir "./downloads/alt-rock"

# Incluir músicas já baixadas anteriormente
python3 src/cli/main.py --lastfm-tag "metal" --no-skip-existing

# Baixar muitas músicas de pop
python3 src/cli/main.py --lastfm-tag "pop" --limit 50 --output-dir "./pop-collection"
```

#### Downloads por Artista

```bash
# Baixar 30 músicas mais populares do Pink Floyd (padrão)
python3 src/cli/main.py --lastfm-artist "Pink Floyd"

# Baixar 15 músicas mais populares dos Beatles
python3 src/cli/main.py --lastfm-artist "The Beatles" --limit 15

# Baixar músicas do Radiohead para diretório específico
python3 src/cli/main.py --lastfm-artist "Radiohead" --limit 20 --output-dir "./downloads/radiohead"

# Incluir músicas já baixadas anteriormente
python3 src/cli/main.py --lastfm-artist "Led Zeppelin" --no-skip-existing

# Baixar muitas músicas de um artista
python3 src/cli/main.py --lastfm-artist "Queen" --limit 50 --output-dir "./queen-collection"
```

## 🏷️ Tags Populares Suportadas

### Gêneros Principais

- `rock` - Rock clássico e moderno
- `pop` - Música pop mainstream
- `jazz` - Jazz clássico e contemporâneo
- `metal` - Heavy metal e subgêneros
- `alternative rock` - Rock alternativo
- `electronic` - Música eletrônica
- `hip hop` - Hip hop e rap
- `indie` - Música independente
- `classical` - Música clássica
- `blues` - Blues tradicional e moderno

### Tags em Português

- `rock nacional` - Rock brasileiro
- `mpb` - Música Popular Brasileira
- `samba` - Samba tradicional
- `bossa nova` - Bossa nova clássica
- `forró` - Forró tradicional

### Tags Específicas

- `90s` - Música dos anos 90
- `80s` - Música dos anos 80
- `acoustic` - Música acústica
- `instrumental` - Música instrumental
- `live` - Gravações ao vivo

## ⚙️ Opções de Comando

| Opção                | Descrição                  | Exemplo               |
| -------------------- | -------------------------- | --------------------- |
| `--limit N`          | Limita o número de músicas | `--limit 20`          |
| `--output-dir PATH`  | Define diretório de saída  | `--output-dir ./jazz` |
| `--no-skip-existing` | Inclui músicas já baixadas | `--no-skip-existing`  |

## 🔧 Como Funciona

### 1. Descoberta de Músicas

- Conecta à API do Last.fm usando OAuth (preferencial) ou API básica
- Busca as músicas mais populares para a tag especificada
- Ordena por popularidade (playcount)
- Suporte a fallback automático entre métodos de autenticação
- Compatibilidade com múltiplas estruturas de código (modular e legada)

### 2. Autenticação Flexível

- **OAuth (Recomendado)**: Acesso completo a recursos pessoais
- **API Básica**: Funciona apenas com API Key e Secret
- **Fallback Automático**: Se OAuth falhar, usa API básica automaticamente
- Mensagens de erro claras para problemas de configuração

### 3. Proteção Anti-Álbum Rigorosa

O sistema implementa **5 camadas de verificação** para garantir que apenas tracks individuais sejam baixadas:

#### Verificação 1: Análise do Nome do Arquivo

- Detecta indicadores como "full album", "complete album", "discography"
- Rejeita automaticamente arquivos com termos suspeitos

#### Verificação 2: Contagem de Arquivos no Diretório

- Conta arquivos MP3 no mesmo diretório do usuário
- Rejeita se há mais de 8 arquivos (provável álbum)

#### Verificação 3: Padrões de Numeração

- Detecta padrões como "01-", "02\_", "track 1", "cd1"
- Identifica numeração sequencial típica de álbuns

#### Verificação 4: Tamanho do Arquivo

- Rejeita arquivos maiores que 100MB
- Álbuns completos tendem a ser muito grandes

#### Verificação 5: Duração

- Rejeita arquivos com mais de 1 hora de duração
- Indica compilações ou álbuns completos

### 4. Download Otimizado

- **Busca Inteligente**: Filtra variações de busca que podem trazer álbuns
- **Score Seletivo**: Usa score mínimo mais alto para ser mais criterioso
- **Verificação Múltipla**: Cada arquivo passa por todas as 5 verificações
- **Logs Detalhados**: Transparência total sobre rejeições

### 5. Organização Automática

- Cria diretório com nome da tag sanitizado
- Mantém histórico de downloads para evitar duplicatas
- Relatórios detalhados de sucesso/falha
- Pausa inteligente entre downloads

## 📊 Relatório de Downloads

Após cada execução, você verá um relatório detalhado:

```text
📊 RELATÓRIO FINAL - Tag: 'rock'
✅ Downloads bem-sucedidos: 18
❌ Downloads com falha: 5
⏭️ Músicas puladas: 2
📊 Total processado: 25
```

## 🛠️ Troubleshooting

### Erro de Autenticação

```text
❌ Falha na autenticação ou configuração do Last.fm
💡 Verifique suas credenciais no arquivo .env:
   - LASTFM_API_KEY
   - LASTFM_API_SECRET
💡 Obtenha suas credenciais em: https://www.last.fm/api/account/create
```

**Solução**: Verifique se `LASTFM_API_KEY` e `LASTFM_API_SECRET` estão configurados corretamente no `.env`

### Erro de API Key

```text
❌ Credenciais do Last.fm não encontradas no arquivo .env
```

**Solução**: Verifique se `LASTFM_API_KEY` e `LASTFM_API_SECRET` estão configurados no `.env`

### Tag Não Encontrada

```text
❌ Tag 'nome_tag' não encontrada no Last.fm
```

**Solução**:

- Verifique a grafia da tag
- Tente tags mais populares como "rock", "pop", "jazz"
- Consulte a lista de tags populares nesta documentação

### Artista Não Encontrado

```text
❌ Artista 'nome_artista' não encontrado no Last.fm
```

**Solução**:

- Verifique a grafia do nome do artista
- Tente variações do nome (com/sem "The", abreviações)
- Use nomes em inglês para artistas internacionais

### API Indisponível

```text
❌ Não foi possível conectar à API do Last.fm
```

**Solução**:

- Verifique sua conexão com a internet
- Confirme se as credenciais estão corretas no arquivo .env
- Verifique se LASTFM_API_KEY e LASTFM_API_SECRET estão configurados

### Nenhuma Música Encontrada

```text
❌ Nenhuma música encontrada para a tag 'tag_inexistente'
```

**Solução**:

- Use tags mais populares
- Verifique se a tag existe no Last.fm
- Tente variações da tag (inglês/português)

## 🎯 Dicas de Uso

### Para Descobrir Novas Músicas

```bash
# Comece com limite baixo para testar
python3 src/cli/main.py --lastfm-tag "indie" --limit 5

# Se gostar, aumente o limite
python3 src/cli/main.py --lastfm-tag "indie" --limit 25
```

### Para Coleções Temáticas

```bash
# Crie coleções organizadas por década
python3 src/cli/main.py --lastfm-tag "80s" --output-dir "./80s-hits" --limit 30
python3 src/cli/main.py --lastfm-tag "90s" --output-dir "./90s-hits" --limit 30
```

### Para Explorar Gêneros

```bash
# Explore subgêneros específicos
python3 src/cli/main.py --lastfm-tag "progressive rock" --limit 15
python3 src/cli/main.py --lastfm-tag "death metal" --limit 10
python3 src/cli/main.py --lastfm-tag "smooth jazz" --limit 20
```

## 🔄 Integração com Outras Funcionalidades

### Combinando com Histórico

```bash
# Ver histórico antes de baixar
python3 src/cli/main.py --history

# Baixar nova tag
python3 src/cli/main.py --lastfm-tag "blues" --limit 15

# Forçar re-download se necessário
python3 src/cli/main.py --force "Artista - Música"
```

### Limpeza Automática

O sistema de limpeza automática funciona normalmente com downloads do Last.fm:

- Downloads completados são removidos da fila automaticamente
- Use `--no-auto-cleanup` se quiser controle manual

## 🔒 Requisitos de Autenticação

A funcionalidade Last.fm requer configuração adequada para funcionar:

- **API Key obrigatória**: Sem ela, nenhuma funcionalidade funcionará
- **Shared Secret obrigatório**: Necessário para autenticação
- **Conexão com internet**: Para acessar a API do Last.fm
- **Tags válidas**: Use tags existentes no Last.fm

Sem essas configurações, o sistema falhará com mensagens de erro claras.

## 🤖 Download Automático

### Script de Automação

O sistema inclui um script bash para download automático de músicas baseado em tags configuradas, ideal para descoberta musical contínua.

#### Configuração

Adicione as seguintes variáveis ao seu arquivo `.env`:

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

#### Execução Manual

```bash
# Executar uma vez para testar
./scripts/lastfm-auto-download.sh

# Monitorar logs em tempo real
tail -f logs/lastfm_auto_download.log
```

#### Execução Automática (Cron)

```bash
# Editar crontab
crontab -e

# Executar a cada 48 horas às 2:00 AM
0 2 */2 * * /caminho/para/projeto/scripts/lastfm-auto-download.sh

# Ou diariamente às 3:00 AM
0 3 * * * /caminho/para/projeto/scripts/lastfm-auto-download.sh
```

#### Recursos do Script

- **Prevenção de Execução Simultânea**: Lock files impedem conflitos
- **Processamento Sequencial**: Cada tag é processada individualmente
- **Monitoramento de Recursos**: Verifica espaço em disco e tamanho dos downloads
- **Logs Detalhados**: Relatórios completos com estatísticas por tag
- **Rotação de Logs**: Logs grandes são rotacionados automaticamente
- **Tratamento de Erros**: Recuperação automática de falhas temporárias

#### Exemplo de Relatório

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

## 🚀 Próximos Passos

Após configurar o Last.fm, você pode:

1. **Explorar o Bot do Telegram**: Use `/lastfm rock` no bot
2. **Combinar com Spotify**: Use playlists + tags para descoberta completa
3. **Configurar Automação**: Use o script para descoberta musical contínua
4. **Personalizar**: Explore diferentes tags para descobrir seus gostos musicais

---

**💡 Dica**: Comece sempre com `--limit 5` ao testar uma nova tag para evitar downloads desnecessários!
