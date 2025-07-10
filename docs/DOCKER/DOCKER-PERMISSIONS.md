# Configuração de Permissões Docker (PUID/PGID)

## 🔐 O que são PUID e PGID?

PUID (Process User ID) e PGID (Process Group ID) são variáveis que controlam com quais permissões o container Docker executa. Por padrão, este projeto usa **root (PUID=0, PGID=0)** para simplicidade e compatibilidade.

## 🎯 Configuração Padrão (Root)

**Padrão atual: PUID=0, PGID=0 (usuário root)**

Vantagens do root:
- ✅ Sem problemas de permissão
- ✅ Funciona em qualquer ambiente
- ✅ Configuração mais simples
- ✅ Compatível com todos os sistemas de arquivos

## 🔧 Como usar

### 1. Uso padrão (recomendado):
```bash
# Usar como root (padrão)
docker-compose up
```

### 2. Usar com usuário específico (opcional):
```bash
# Usar seu usuário local
PUID=$(id -u) PGID=$(id -g) docker-compose up

# Ou definir no .env
echo "PUID=$(id -u)" >> .env
echo "PGID=$(id -g)" >> .env
```

## ⚙️ Configuração no .env

### Padrão (root):
```env
# Docker User Configuration (padrão)
PUID=0
PGID=0
```

### Usuário personalizado:
```env
# Docker User Configuration (seu usuário)
PUID=1000
PGID=1000
```

## 🚀 Exemplos de Uso

### Uso básico (root):
```bash
# Executar como root (mais simples)
docker-compose up
make up
```

### Uso com usuário específico:
```bash
# Descobrir seus IDs
id -u  # PUID
id -g  # PGID

# Executar com seus IDs
PUID=1000 PGID=1000 docker-compose up
```

## 🔍 Verificação

Para verificar como está executando:

```bash
# Ver variáveis no container
docker exec migsfy-bot env | grep -E "PUID|PGID"

# Ver usuário atual no container
docker exec migsfy-bot whoami

# Ver permissões dos arquivos
docker exec migsfy-bot ls -la /app/data/
```

## 🛠️ Quando usar cada opção

### Use Root (PUID=0, PGID=0) quando:
- ✅ Quer simplicidade máxima
- ✅ Não se importa com permissões de arquivos
- ✅ Está em ambiente controlado/isolado
- ✅ Tem problemas de permissão com outros usuários

### Use usuário específico quando:
- ✅ Quer arquivos com suas permissões
- ✅ Está em ambiente compartilhado
- ✅ Precisa editar arquivos criados pelo container
- ✅ Segue práticas de segurança mais rigorosas

## 📝 Valores Padrão

**Novos padrões:**
- PUID padrão: **0** (root)
- PGID padrão: **0** (root)

**Valores anteriores:**
- PUID anterior: 1000
- PGID anterior: 1000

## ⚠️ Notas de Segurança

### Root (padrão):
- ⚠️ Container executa com privilégios de root
- ✅ Mais simples de configurar
- ✅ Sem problemas de permissão
- ⚠️ Menos seguro em teoria, mas isolado no container

### Usuário específico:
- ✅ Mais seguro (princípio do menor privilégio)
- ⚠️ Pode ter problemas de permissão
- ⚠️ Configuração mais complexa

## 🔗 Comandos Úteis

```bash
# Ver IDs atuais do sistema
make show-ids

# Executar com root (padrão)
make up

# Executar com usuário específico
PUID=$(id -u) PGID=$(id -g) make up

# Build sem cache
make build-no-cache

# Shell interativo
make shell
```

## 🐛 Troubleshooting

### Problema: Arquivos com permissões erradas
**Solução:** Use root (padrão) ou ajuste PUID/PGID:
```bash
# Voltar para root
export PUID=0 PGID=0
docker-compose up

# Ou usar seu usuário
export PUID=$(id -u) PGID=$(id -g)
docker-compose up
```

### Problema: Container não inicia
**Solução:** Reconstrua com root:
```bash
docker-compose down
export PUID=0 PGID=0
make build-no-cache
docker-compose up
```
