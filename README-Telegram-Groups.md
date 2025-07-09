# Configuração de Grupos e Threads - Bot Telegram

Este documento explica como configurar o bot do Telegram para funcionar em grupos específicos e threads específicas.

## 🎯 Funcionalidades

- **Chat privado**: Controle por usuário individual
- **Grupos completos**: Permite uso em todo o grupo
- **Threads específicas**: Permite uso apenas em threads específicas de um grupo
- **Comando /info**: Descobre IDs de grupos e threads automaticamente

## ⚙️ Configuração no .env

### Variáveis de ambiente:

```env
# Usuários permitidos em chat privado (separados por vírgula)
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Grupos permitidos (separados por vírgula)
TELEGRAM_ALLOWED_GROUPS=-1001234567890,-1009876543210

# Threads específicas permitidas (formato: grupo_id:thread_id)
TELEGRAM_ALLOWED_THREADS=-1001234567890:123,-1001234567890:456
```

## 🔍 Como descobrir IDs

### Método 1: Comando /info

1. Adicione o bot ao grupo/thread desejada
2. Execute o comando `/info` no local onde quer usar o bot
3. O bot retornará todas as informações necessárias para configuração

### Método 2: Manual

1. **ID do usuário**: Use @userinfobot no Telegram
2. **ID do grupo**: Adicione @RawDataBot ao grupo
3. **ID da thread**: Envie uma mensagem na thread e use @RawDataBot

## 📋 Cenários de Configuração

### Cenário 1: Chat privado apenas
```env
TELEGRAM_ALLOWED_USERS=123456789,987654321
# Não configure TELEGRAM_ALLOWED_GROUPS nem TELEGRAM_ALLOWED_THREADS
```

### Cenário 2: Grupo completo
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890
# Permite uso em todo o grupo, incluindo todas as threads
```

### Cenário 3: Thread específica apenas
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890
TELEGRAM_ALLOWED_THREADS=-1001234567890:123
```
**Importante**: O grupo deve estar em `TELEGRAM_ALLOWED_GROUPS` para que as threads funcionem.

### Cenário 4: Múltiplas threads em múltiplos grupos
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890,-1009876543210
TELEGRAM_ALLOWED_THREADS=-1001234567890:123,-1001234567890:456,-1009876543210:789
```

### Cenário 5: Combinação completa
```env
TELEGRAM_ALLOWED_USERS=123456789,987654321
TELEGRAM_ALLOWED_GROUPS=-1001234567890
TELEGRAM_ALLOWED_THREADS=-1001234567890:123
```
Permite:
- Chats privados com usuários 123456789 e 987654321
- Thread 123 do grupo -1001234567890
- Todo o resto do grupo -1001234567890 (exceto outras threads específicas)

## 🚨 Regras Importantes

### Prioridade de Autorização:

1. **Chat privado**: Verifica apenas `TELEGRAM_ALLOWED_USERS`
2. **Grupo com threads configuradas**: 
   - Grupo deve estar em `TELEGRAM_ALLOWED_GROUPS`
   - Thread deve estar em `TELEGRAM_ALLOWED_THREADS`
   - Mensagens no grupo principal são **negadas**
3. **Grupo sem threads configuradas**: Permite todo o grupo

### Comportamento por Tipo:

| Tipo de Chat | Configuração | Comportamento |
|--------------|--------------|---------------|
| Privado | `TELEGRAM_ALLOWED_USERS` | Verifica apenas usuário |
| Grupo | `TELEGRAM_ALLOWED_GROUPS` apenas | Permite todo o grupo |
| Grupo | `TELEGRAM_ALLOWED_GROUPS` + `TELEGRAM_ALLOWED_THREADS` | Permite apenas threads específicas |
| Thread | Herda configuração do grupo pai | Verifica se thread está permitida |

## 🛠️ Exemplos Práticos

### Exemplo 1: Bot para thread de música apenas

1. Crie uma thread "🎵 Música" no seu grupo
2. Execute `/info` na thread
3. Copie a configuração sugerida para o .env:
   ```env
   TELEGRAM_ALLOWED_GROUPS=-1001234567890
   TELEGRAM_ALLOWED_THREADS=-1001234567890:123
   ```
4. Reinicie o bot

### Exemplo 2: Bot para múltiplas threads de diferentes grupos

```env
TELEGRAM_ALLOWED_GROUPS=-1001111111111,-1002222222222
TELEGRAM_ALLOWED_THREADS=-1001111111111:100,-1001111111111:200,-1002222222222:300
```

Permite:
- Thread 100 do grupo -1001111111111
- Thread 200 do grupo -1001111111111  
- Thread 300 do grupo -1002222222222

## 🔧 Troubleshooting

### Bot não responde no grupo:
1. Verifique se o grupo está em `TELEGRAM_ALLOWED_GROUPS`
2. Execute `/info` para confirmar IDs
3. Verifique logs do bot para mensagens de debug

### Bot não responde na thread:
1. Confirme que a thread está em `TELEGRAM_ALLOWED_THREADS`
2. Confirme que o grupo pai está em `TELEGRAM_ALLOWED_GROUPS`
3. Execute `/info` na thread para verificar IDs

### Mensagens de debug:
O bot registra informações de autorização nos logs:
```
Verificando autorização - User: 123456789, Chat: -1001234567890, Type: supergroup
Thread ID da mensagem: 123
Threads permitidas para grupo -1001234567890: [123, 456]
Thread 123 está permitida
```

## 📝 Notas Técnicas

- **IDs negativos**: Grupos sempre têm IDs negativos
- **Threads**: Nem todas as mensagens têm `message_thread_id`
- **Supergrupos**: Tratados como grupos normais
- **Canais**: Não são suportados atualmente

## 🔄 Atualizando Configurações

1. Edite o arquivo `.env`
2. Reinicie o bot:
   ```bash
   # Local
   ./run-telegram-bot.sh
   
   # Docker
   make telegram-bot
   ```
3. Teste com `/info` nos locais desejados
