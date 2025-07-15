# CHANGELOG - Last.fm Artist Downloads

## 📅 Data: 15/07/2025

## 🎯 Resumo

Adicionada funcionalidade de download de músicas por artista específico na integração Last.fm, complementando a funcionalidade existente de download por tags/gêneros.

## ✨ Novas Funcionalidades

### 🎤 Download por Artista

- **Função**: `get_artist_top_tracks(artist_name, limit=30)`
  - Obtém as músicas mais populares de um artista específico
  - Retorna lista com (artista, título, playcount)
  - Suporte a tratamento de erros e validação

- **Função**: `download_artist_top_tracks(artist_name, limit=30, output_dir=None, skip_existing=True)`
  - Baixa as músicas mais populares de um artista
  - Aplica todas as 5 camadas de proteção anti-álbum
  - Organiza downloads em diretório específico do artista
  - Relatórios detalhados com estatísticas de playcount

### 🔧 Interface CLI

- **Novo comando**: `--lastfm-artist "nome_do_artista"`
- **Compatibilidade**: Funciona com todas as opções existentes (`--limit`, `--output-dir`, `--no-skip-existing`)

### 🤖 Download Automático

- **Nova variável**: `LASTFM_AUTO_ARTISTS` no arquivo `.env`
- **Suporte**: Processamento automático de lista de artistas
- **Relatórios**: Estatísticas separadas para tags e artistas

## 🛡️ Recursos de Segurança

### Proteção Anti-Álbum Mantida

Todas as 5 camadas de verificação são aplicadas aos downloads por artista:

1. **Análise do Nome**: Detecta indicadores de álbum completo
2. **Contagem de Arquivos**: Verifica número de arquivos no diretório
3. **Padrões de Numeração**: Identifica sequências típicas de álbuns
4. **Tamanho do Arquivo**: Rejeita arquivos muito grandes (>100MB)
5. **Duração**: Rejeita arquivos muito longos (>1h)

### Validação de Entrada

- Verificação de existência do artista na API Last.fm
- Mensagens de erro específicas para artistas não encontrados
- Fallback automático entre métodos de autenticação

## 📊 Exemplos de Uso

### Comandos CLI

```bash
# Download básico por artista
python3 src/cli/main.py --lastfm-artist "Pink Floyd"

# Download com limite personalizado
python3 src/cli/main.py --lastfm-artist "The Beatles" --limit 15

# Download para diretório específico
python3 src/cli/main.py --lastfm-artist "Queen" --output-dir "./queen-collection"

# Incluir músicas já baixadas
python3 src/cli/main.py --lastfm-artist "Led Zeppelin" --no-skip-existing
```

### Configuração Automática

```env
# Artistas para download automático
LASTFM_AUTO_ARTISTS=Pink Floyd,The Beatles,Led Zeppelin,Queen,Radiohead

# Combinação com tags existentes
LASTFM_AUTO_TAGS=rock,pop,jazz
LASTFM_AUTO_ARTISTS=Miles Davis,John Coltrane,Pink Floyd
```

## 🔄 Compatibilidade

### Retrocompatibilidade

- ✅ Funcionalidade de tags mantida inalterada
- ✅ Todas as opções CLI existentes funcionam
- ✅ Histórico de downloads unificado
- ✅ Sistema de limpeza automática compatível

### Integração

- ✅ Bot Telegram: Suporte futuro para comandos `/lastfm_artist`
- ✅ Scripts automáticos: Processamento de ambas as listas (tags + artistas)
- ✅ Logs: Formato consistente com funcionalidade existente

## 📈 Melhorias de Performance

### Otimizações

- **Busca Inteligente**: Filtragem de variações que podem trazer álbuns
- **Score Seletivo**: Critérios mais rigorosos para seleção de arquivos
- **Pausas Inteligentes**: Intervalos otimizados entre downloads
- **Logs Detalhados**: Transparência total sobre decisões de rejeição

### Relatórios Aprimorados

```text
📊 DOWNLOAD CONCLUÍDO - Artista: 'Pink Floyd'
🎯 MODO: Apenas tracks individuais (álbuns rejeitados)
📊 Total de músicas: 30
✅ Downloads bem-sucedidos: 25
❌ Downloads com falha: 3
⏭️ Músicas puladas (já baixadas): 2
```

## 🛠️ Implementação Técnica

### Arquitetura

- **Módulo**: `src/core/lastfm/tag_downloader.py`
- **Funções Principais**:
  - `get_artist_top_tracks()`: API Last.fm para obter top tracks
  - `download_artist_top_tracks()`: Download com proteções anti-álbum
  - `_search_single_track_only()`: Busca restrita (reutilizada)

### Tratamento de Erros

- **Artista não encontrado**: Mensagem específica com sugestões
- **API indisponível**: Fallback automático entre métodos de auth
- **Credenciais inválidas**: Orientações claras para correção

## 📚 Documentação Atualizada

### Arquivos Modificados

- ✅ `docs/LASTFM/README-LastFM.md`: Exemplos e comandos por artista
- ✅ `docs/LASTFM/README-Auto-Download.md`: Configuração automática
- ✅ `docs/CHANGELOG/CHANGELOG-LastFM-Artist-Downloads.md`: Este changelog

### Novos Exemplos

- Comandos CLI para download por artista
- Configurações de ambiente para automação
- Casos de uso e troubleshooting específicos

## 🎯 Próximos Passos

### Funcionalidades Futuras

1. **Bot Telegram**: Comando `/lastfm_artist <nome>`
2. **Interface Web**: Seleção visual de artistas
3. **Recomendações**: Artistas similares baseados em downloads
4. **Playlists**: Criação automática por artista

### Melhorias Planejadas

1. **Cache**: Armazenar top tracks para reduzir chamadas API
2. **Filtros**: Período de tempo para top tracks (últimos 6 meses, etc.)
3. **Estatísticas**: Análise de popularidade e tendências

## 🔍 Testes

### Cenários Testados

- ✅ Download de artistas populares (Pink Floyd, Beatles)
- ✅ Artistas com caracteres especiais
- ✅ Artistas não encontrados
- ✅ Limite de músicas personalizado
- ✅ Proteção anti-álbum em todos os cenários
- ✅ Integração com histórico existente

### Casos de Erro

- ✅ API Last.fm indisponível
- ✅ Credenciais inválidas
- ✅ Artista inexistente
- ✅ Sem músicas disponíveis para download

## 📊 Impacto

### Benefícios

- **Descoberta Direcionada**: Foco em artistas específicos
- **Coleções Temáticas**: Organização por artista
- **Flexibilidade**: Combinação de tags + artistas
- **Automação**: Download contínuo de artistas favoritos

### Métricas

- **Código**: +163 linhas adicionadas
- **Funções**: 2 novas funções principais
- **Compatibilidade**: 100% retrocompatível
- **Cobertura**: Todas as proteções anti-álbum aplicadas

---

**🎉 A funcionalidade de download por artista expande significativamente as capacidades de descoberta musical do sistema, mantendo todos os padrões de segurança e qualidade existentes.**