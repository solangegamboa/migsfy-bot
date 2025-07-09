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

Estas mensagens **NÃO** funcionam mais:

```
❌ Radiohead - Creep
❌ https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
❌ Linkin Park - In the End
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
- **Copie URLs completas**: Use URLs completas do Spotify para melhor compatibilidade
- **Use opções**: Combine `limit=N` e `remove=yes` conforme necessário
- **Verifique status**: Use `/status` se algo não estiver funcionando
- **Consulte histórico**: Use `/history` para ver downloads anteriores
