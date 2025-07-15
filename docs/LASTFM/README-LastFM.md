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

# Opcionais para autenticação de usuário:
LASTFM_USERNAME=seu_usuario_lastfm
LASTFM_PASSWORD=sua_senha_lastfm
```

**Nota**: As credenciais de usuário são opcionais. Se não fornecidas, a API funcionará apenas com acesso público.

## 🎵 Como Usar

### Comando Básico

```bash
python3 src/cli/main.py --lastfm-tag "nome_da_tag"
```

### Exemplos Práticos

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

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `--limit N` | Limita o número de músicas | `--limit 20` |
| `--output-dir PATH` | Define diretório de saída | `--output-dir ./jazz` |
| `--no-skip-existing` | Inclui músicas já baixadas | `--no-skip-existing` |

## 🔧 Como Funciona

### 1. Descoberta de Músicas
- Conecta à API do Last.fm
- Busca as músicas mais populares para a tag especificada
- Ordena por popularidade (playcount)

### 2. Autenticação Obrigatória
- Requer credenciais válidas da API Last.fm
- Não funciona sem configuração adequada
- Falha com mensagens de erro claras se não autenticado

### 3. Download Otimizado
- Força download apenas de tracks individuais (nunca álbuns completos)
- Usa o sistema de busca inteligente existente
- Aplica verificação de duplicatas
- Organiza downloads por diretórios de tag

### 4. Organização Automática
- Cria diretório com nome da tag
- Sanitiza nomes de arquivos
- Mantém histórico de downloads

## 📊 Relatório de Downloads

Após cada execução, você verá um relatório detalhado:

```
📊 RELATÓRIO FINAL - Tag: 'rock'
✅ Downloads bem-sucedidos: 18
❌ Downloads com falha: 5
⏭️ Músicas puladas: 2
📊 Total processado: 25
```

## 🛠️ Troubleshooting

### Erro de Autenticação
```
❌ Falha na autenticação ou configuração do Last.fm
💡 Verifique suas credenciais no arquivo .env:
   - LASTFM_API_KEY
   - LASTFM_API_SECRET
💡 Obtenha suas credenciais em: https://www.last.fm/api/account/create
```
**Solução**: Verifique se `LASTFM_API_KEY` e `LASTFM_API_SECRET` estão configurados corretamente no `.env`

### Erro de API Key
```
❌ Credenciais do Last.fm não encontradas no arquivo .env
```
**Solução**: Verifique se `LASTFM_API_KEY` e `LASTFM_API_SECRET` estão configurados no `.env`

### Tag Não Encontrada
```
❌ Tag 'nome_tag' não encontrada no Last.fm
```
**Solução**: 
- Verifique a grafia da tag
- Tente tags mais populares como "rock", "pop", "jazz"
- Consulte a lista de tags populares nesta documentação

### API Indisponível
```
❌ Não foi possível conectar à API do Last.fm
```
**Solução**: 
- Verifique sua conexão com a internet
- Confirme se as credenciais estão corretas no arquivo .env
- Verifique se LASTFM_API_KEY e LASTFM_API_SECRET estão configurados

### Nenhuma Música Encontrada
```
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
- **Credenciais de usuário opcionais**: Para funcionalidades avançadas
- **Conexão com internet**: Para acessar a API do Last.fm
- **Tags válidas**: Use tags existentes no Last.fm

Sem essas configurações, o sistema falhará com mensagens de erro claras.

## 🚀 Próximos Passos

Após configurar o Last.fm, você pode:

1. **Explorar o Bot do Telegram**: Use `/lastfm rock` no bot
2. **Combinar com Spotify**: Use playlists + tags para descoberta completa
3. **Automatizar**: Crie scripts para baixar tags regularmente
4. **Personalizar**: Explore diferentes tags para descobrir seus gostos musicais

---

**💡 Dica**: Comece sempre com `--limit 5` ao testar uma nova tag para evitar downloads desnecessários!