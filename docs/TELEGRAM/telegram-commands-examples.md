# 🤖 Exemplos de Comandos do Telegram Bot

Este arquivo contém exemplos práticos de como usar o bot do Telegram.

## 🎵 Busca de Música

### Comando: `/search`

```
/search Radiohead - Creep
/search Linkin Park - In the End
/search Maria Rita - Como Nossos Pais
/search Bohemian Rhapsody
/search The Beatles - Hey Jude
```

**⚠️ Importante:** Sempre use o comando `/search` seguido do termo de busca.

## 💿 Busca de Álbum

### Comando: `/album`

```
/album Pink Floyd - The Dark Side of the Moon
/album Beatles - Abbey Road
/album Nirvana - Nevermind
/album Led Zeppelin - IV
/album Queen - A Night at the Opera
/album Radiohead - OK Computer
/album Miles Davis - Kind of Blue
/album Bob Dylan - Highway 61 Revisited
```

**💡 Dicas para álbuns:**
- Use o formato "Artista - Álbum"
- Álbuns famosos têm maior chance de sucesso
- O bot detecta automaticamente se é álbum ou música
- Álbuns baixam múltiplas faixas automaticamente

**⚠️ Importante:** Sempre use o comando `/album` seguido do nome do álbum.

## 🎵 Playlists do Spotify

### Comando: `/spotify`

#### Básico:
```
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
/spotify https://spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
/spotify spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
```

#### Com limite de faixas:
```
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M limit=10
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M limit=5
```

#### Com remoção da playlist:
```
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M remove=yes
```

#### Combinando opções:
```
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M limit=10 remove=yes
/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M limit=5 remove=yes
```

## 🏷️ Last.fm Integration

### Comando: `/lastfm_tag`

```
/lastfm_tag rock
/lastfm_tag jazz 50
/lastfm_tag "alternative rock" 30
/lastfm_tag metal 10
/lastfm_tag pop 25
/lastfm_tag blues 15
```

### Comando: `/lastfm_artist`

```
/lastfm_artist Radiohead
/lastfm_artist "The Beatles" 20
/lastfm_artist "Pink Floyd" 50
/lastfm_artist "Led Zeppelin" 30
/lastfm_artist Queen 25
/lastfm_artist "Bob Dylan" 15
```

**💡 Dicas para Last.fm:**
- Tags: máximo 100 músicas, padrão 25
- Artistas: máximo 50 músicas, padrão 30
- Use aspas para nomes com espaços
- Processo totalmente automático (não pergunta nada)
- Músicas já baixadas são puladas automaticamente

## 📋 Histórico

```
/history
/clear_history
```

## ℹ️ Informações

```
/start
/help
/status
```

## ❌ O que NÃO funciona mais

Estas mensagens são **COMPLETAMENTE IGNORADAS** (sem resposta):

```
❌ Radiohead - Creep                                    (ignorada)
❌ https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M  (ignorada)
❌ Linkin Park - In the End                             (ignorada)
❌ Qualquer texto que não seja comando                  (ignorada)
```

**Use sempre os comandos específicos:**

```
✅ /search Radiohead - Creep
✅ /spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
✅ /search Linkin Park - In the End
```

## 🔄 Fluxo de Uso Típico

1. **Iniciar conversa:**
   ```
   /start
   ```

2. **Ver ajuda:**
   ```
   /help
   ```

3. **Verificar status:**
   ```
   /status
   ```

4. **Buscar uma música:**
   ```
   /search Artista - Música
   ```

5. **Baixar playlist do Spotify:**
   ```
   /spotify https://open.spotify.com/playlist/ID
   ```

6. **Ver histórico:**
   ```
   /history
   ```

## 💡 Dicas

- **Sempre use comandos**: O bot não processa mensagens de texto livres
- **Mensagens ignoradas**: Textos que não sejam comandos são completamente ignorados (sem resposta)
- **Copie URLs completas**: Use URLs completas do Spotify para melhor compatibilidade
- **Use opções**: Combine `limit=N` e `remove=yes` conforme necessário
- **Verifique status**: Use `/status` se algo não estiver funcionando
- **Consulte histórico**: Use `/history` para ver downloads anteriores
- **Sem feedback de erro**: Se não há resposta, provavelmente você não usou um comando válido
