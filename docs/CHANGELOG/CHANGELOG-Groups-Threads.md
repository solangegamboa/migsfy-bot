# Changelog - Suporte a Grupos e Threads Específicas

## 🎯 Funcionalidade Implementada

Adicionado suporte para o bot do Telegram funcionar apenas em threads específicas de grupos, permitindo controle granular de onde o bot pode ser usado.

## 🔧 Modificações Realizadas

### 1. Bot Telegram (`telegram_bot.py`)

#### Novas configurações:
- `TELEGRAM_ALLOWED_GROUPS`: Lista de IDs de grupos permitidos
- `TELEGRAM_ALLOWED_THREADS`: Lista de threads específicas (formato: `grupo_id:thread_id`)

#### Modificações na classe `TelegramMusicBot`:
- **Novos métodos**:
  - `_get_allowed_groups()`: Processa lista de grupos permitidos
  - `_get_allowed_threads()`: Processa configuração de threads específicas
  - `info_command()`: Novo comando para descobrir IDs automaticamente

- **Método modificado**:
  - `_is_authorized()`: Lógica completa de autorização por tipo de chat
    - Chat privado: Verifica `TELEGRAM_ALLOWED_USERS`
    - Grupo com threads: Verifica grupo + thread específica
    - Grupo sem threads: Permite todo o grupo

#### Lógica de Autorização:

1. **Chat Privado**: Verifica apenas usuários permitidos
2. **Grupo com threads configuradas**: 
   - Grupo deve estar em `TELEGRAM_ALLOWED_GROUPS`
   - Thread deve estar em `TELEGRAM_ALLOWED_THREADS`
   - Mensagens no grupo principal são negadas
3. **Grupo sem threads configuradas**: Permite todo o grupo

### 2. Configurações (`.env.example`)

Adicionadas novas variáveis:
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890,-1009876543210
TELEGRAM_ALLOWED_THREADS=-1001234567890:123,-1001234567890:456
```

### 3. Documentação

#### Novos arquivos:
- `README-Telegram-Groups.md`: Guia completo de configuração
- `test-telegram-groups.py`: Script de teste para validar configurações
- `CHANGELOG-Groups-Threads.md`: Este arquivo

#### Arquivos atualizados:
- `README.md`: Seção sobre grupos e threads
- Tabela de configurações atualizada

## 🎮 Novo Comando

### `/info`
- Mostra informações do chat atual (IDs, tipo, thread)
- Gera configuração pronta para o `.env`
- Funciona em qualquer tipo de chat
- Essencial para descobrir IDs de grupos e threads

## 📋 Cenários de Uso

### Cenário 1: Thread específica apenas
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890
TELEGRAM_ALLOWED_THREADS=-1001234567890:123
```
- Bot funciona apenas na thread 123 do grupo -1001234567890
- Mensagens no grupo principal são ignoradas

### Cenário 2: Múltiplas threads
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890,-1002222222222
TELEGRAM_ALLOWED_THREADS=-1001234567890:123,-1001234567890:456,-1002222222222:789
```
- Thread 123 e 456 do primeiro grupo
- Thread 789 do segundo grupo

### Cenário 3: Grupo completo
```env
TELEGRAM_ALLOWED_GROUPS=-1001234567890
# Sem TELEGRAM_ALLOWED_THREADS
```
- Bot funciona em todo o grupo, incluindo todas as threads

## 🔍 Sistema de Logs

Adicionados logs detalhados para debug:
```
Verificando autorização - User: 123456789, Chat: -1001234567890, Type: supergroup
Thread ID da mensagem: 123
Threads permitidas para grupo -1001234567890: [123, 456]
Thread 123 está permitida
```

## 🧪 Testes

Script `test-telegram-groups.py` para validar:
- Parsing correto das configurações
- Simulação de cenários de autorização
- Detecção de configurações inconsistentes
- Tratamento robusto de erros

## 🚀 Como Usar

1. **Descobrir IDs**:
   ```
   /info
   ```

2. **Configurar .env**:
   ```env
   TELEGRAM_ALLOWED_GROUPS=-1001234567890
   TELEGRAM_ALLOWED_THREADS=-1001234567890:123
   ```

3. **Testar configuração**:
   ```bash
   python3 test-telegram-groups.py
   ```

4. **Reiniciar bot**:
   ```bash
   ./run-telegram-bot.sh
   ```

## ⚠️ Notas Importantes

- **Grupos devem estar em `TELEGRAM_ALLOWED_GROUPS`** para que threads funcionem
- **IDs de grupos são sempre negativos**
- **Mensagens no grupo principal são negadas** quando threads específicas estão configuradas
- **Comando `/info` funciona independente de autorização** para facilitar configuração inicial

## 🔄 Compatibilidade

- ✅ Mantém compatibilidade com configurações existentes
- ✅ Funciona com chats privados como antes
- ✅ Suporte a grupos completos como antes
- ✅ Nova funcionalidade de threads específicas

## 🐛 Tratamento de Erros

- Configurações malformadas são ignoradas silenciosamente
- Logs detalhados para troubleshooting
- Script de teste para validação prévia
- Fallbacks seguros para configurações vazias
