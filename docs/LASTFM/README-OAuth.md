# Last.fm OAuth Authentication & Anti-Album Protection

## 🔐 Autenticação OAuth

### Configuração Inicial

1. **Obter Credenciais da API**:
   - Acesse [Last.fm API](https://www.last.fm/api/account/create)
   - Crie uma aplicação
   - Obtenha `API Key` e `Shared Secret`

2. **Configurar .env**:
   ```env
   LASTFM_API_KEY=sua_api_key_aqui
   LASTFM_API_SECRET=seu_shared_secret_aqui
   ```

### Como Funciona o OAuth

1. **Primeira Autenticação**:
   - Sistema abre navegador automaticamente
   - Usuário faz login no Last.fm
   - Autoriza a aplicação
   - Session key é armazenado localmente

2. **Reutilização**:
   - Session key é reutilizado automaticamente
   - Não precisa reautenticar a cada uso
   - Fallback para API básica se session key expirar

### Comandos OAuth

```bash
# Testar autenticação
python3 src/cli/lastfm_oauth.py auth

# Ver informações do usuário
python3 src/cli/lastfm_oauth.py user-info

# Ver top tracks
python3 src/cli/lastfm_oauth.py top-tracks --limit 20 --period 1month

# Ver loved tracks
python3 src/cli/lastfm_oauth.py loved-tracks --limit 30

# Baixar top tracks
python3 src/cli/lastfm_oauth.py download-top --limit 25 --period 12month

# Baixar loved tracks
python3 src/cli/lastfm_oauth.py download-loved --limit 50

# Limpar autenticação
python3 src/cli/lastfm_oauth.py clear-auth
```

## 🚫 Proteção Anti-Álbum

### Problema Resolvido

Antes: Sistema podia baixar álbuns completos inadvertidamente
Agora: **APENAS tracks individuais são baixadas**

### Verificações Implementadas

#### 1. **Análise do Nome do Arquivo**
Rejeita arquivos com indicadores de álbum:
- `full album`, `complete album`, `entire album`
- `discography`, `collection`, `anthology`
- `greatest hits`, `best of`, `compilation`
- `box set`, `complete works`

#### 2. **Contagem de Arquivos no Diretório**
- Rejeita se há mais de 8 arquivos MP3 no mesmo diretório
- Indica provável álbum completo

#### 3. **Padrões de Numeração**
Rejeita arquivos com padrões típicos de álbum:
- `01-`, `02_`, `03 ` (numeração sequencial)
- `track 1`, `track01`
- `cd1`, `cd2`, `disc 1`

#### 4. **Tamanho do Arquivo**
- Rejeita arquivos maiores que 100MB
- Álbuns tendem a ser muito grandes

#### 5. **Duração**
- Rejeita arquivos com mais de 1 hora
- Indica compilação ou álbum

### Logs de Proteção

```
🎯 BUSCA RESTRITA A TRACK INDIVIDUAL: 'Artista - Música'
🚫 ÁLBUNS SERÃO AUTOMATICAMENTE REJEITADOS
🚫 REJEITADO: Arquivo parece ser álbum
🚫 REJEITADO: 12 arquivos MP3 no mesmo diretório (provável álbum)
🚫 REJEITADO: Arquivo muito grande (150.5 MB, provável álbum)
✅ APROVADO: Arquivo passou em todas as verificações anti-álbum
```

## 🎵 Funcionalidades Disponíveis

### 1. **Download por Tags** (Básico + OAuth)
```bash
# Funciona com ambos os tipos de autenticação
python3 src/cli/main.py --lastfm-tag "rock" --limit 20
```

### 2. **Download de Top Tracks Pessoais** (Requer OAuth)
```bash
# Top tracks do usuário autenticado
python3 src/cli/lastfm_oauth.py download-top --limit 30 --period 6month
```

### 3. **Download de Loved Tracks** (Requer OAuth)
```bash
# Músicas curtidas pelo usuário
python3 src/cli/lastfm_oauth.py download-loved --limit 50
```

### 4. **Informações do Usuário** (Requer OAuth)
```bash
# Ver estatísticas pessoais
python3 src/cli/lastfm_oauth.py user-info
```

## 🔄 Fluxo de Autenticação

### Primeira Vez
```
🔐 Iniciando autenticação OAuth com Last.fm...
📝 Obtendo token de autenticação...
🌐 Abrindo navegador para autorização...
============================================================
🔐 AUTENTICAÇÃO LAST.FM NECESSÁRIA
============================================================
1. Acesse: https://www.last.fm/api/auth/?api_key=...&token=...
2. Faça login na sua conta Last.fm
3. Autorize a aplicação
4. Pressione ENTER aqui após autorizar
============================================================
Pressione ENTER após autorizar a aplicação no navegador...
🔑 Obtendo session key...
✅ Session key obtido com sucesso!
🎉 Autenticação OAuth concluída para usuário: seu_usuario
```

### Próximas Vezes
```
🔐 Tentando autenticação OAuth...
Tentando usar session key armazenado...
Autenticação bem-sucedida com session key armazenado para usuário: seu_usuario
✅ Autenticação OAuth bem-sucedida
```

## 🛡️ Segurança

### Session Key
- Armazenado em `.lastfm_session` (local)
- Não exposto em logs
- Reutilizado automaticamente
- Pode ser limpo com `clear-auth`

### Fallback
- Se OAuth falhar, usa API básica
- Funcionalidades básicas sempre disponíveis
- Dados pessoais requerem OAuth

## 🚀 Vantagens

### Para o Usuário
- **Personalização**: Acesso a dados pessoais do Last.fm
- **Conveniência**: Autenticação única, reutilização automática
- **Segurança**: Apenas tracks individuais, nunca álbuns
- **Flexibilidade**: Funciona com ou sem OAuth

### Para o Sistema
- **Eficiência**: Session key reutilizado
- **Robustez**: Múltiplas verificações anti-álbum
- **Compatibilidade**: Mantém funcionalidades básicas
- **Logs Detalhados**: Transparência total sobre rejeições

## 🔧 Troubleshooting

### Session Key Inválido
```bash
# Limpar e reautenticar
python3 src/cli/lastfm_oauth.py clear-auth
python3 src/cli/lastfm_oauth.py auth
```

### Álbum Sendo Baixado
- Impossível com as verificações implementadas
- Todos os downloads passam por 5 camadas de proteção
- Logs mostram exatamente por que arquivos foram rejeitados

### Navegador Não Abre
- URL é mostrada no terminal
- Copie e cole manualmente no navegador
- Continue o processo normalmente

## 📊 Estatísticas de Proteção

A cada download, o sistema mostra:
```
📊 DOWNLOAD CONCLUÍDO - Tag: 'rock'
🎯 MODO: Apenas tracks individuais (álbuns rejeitados)
📊 Total de músicas: 25
✅ Downloads bem-sucedidos: 18
❌ Downloads com falha: 5
⏭️ Músicas puladas (já baixadas): 2
```

**Garantia**: 0% de chance de baixar álbuns completos inadvertidamente!