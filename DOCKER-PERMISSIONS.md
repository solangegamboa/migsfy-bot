# Configuração de Permissões Docker (PUID/PGID)

## 🔐 O que são PUID e PGID?

PUID (Process User ID) e PGID (Process Group ID) são variáveis que permitem que o container Docker execute com as mesmas permissões do seu usuário local, evitando problemas de permissão com arquivos criados pelo container.

## 🎯 Por que usar?

Sem PUID/PGID:
- Arquivos criados pelo container pertencem ao usuário `root`
- Você pode não conseguir editar/deletar esses arquivos
- Problemas de permissão ao acessar volumes montados

Com PUID/PGID:
- Arquivos criados têm as mesmas permissões do seu usuário
- Sem problemas de permissão
- Melhor integração com o sistema host

## 🔧 Como descobrir seus IDs

### No Linux/macOS:
```bash
# Descobrir seu PUID
id -u

# Descobrir seu PGID  
id -g

# Ver ambos
id
```

### Exemplo de saída:
```bash
$ id
uid=1000(usuario) gid=1000(usuario) groups=1000(usuario),4(adm),24(cdrom)...
```
Neste caso: PUID=1000, PGID=1000

## ⚙️ Configuração

### 1. No arquivo .env:
```env
# Docker User Configuration
PUID=1000
PGID=1000
```

### 2. Ou via variáveis de ambiente:
```bash
export PUID=$(id -u)
export PGID=$(id -g)
docker-compose up
```

### 3. Ou diretamente no docker-compose:
```bash
PUID=$(id -u) PGID=$(id -g) docker-compose up
```

## 🚀 Exemplos de Uso

### Uso básico:
```bash
# Definir variáveis
export PUID=1000
export PGID=1000

# Executar
docker-compose up
```

### Uso com IDs automáticos:
```bash
# Usar seus IDs atuais automaticamente
PUID=$(id -u) PGID=$(id -g) docker-compose up
```

### Uso com usuário específico:
```bash
# Usar IDs de outro usuário
PUID=1001 PGID=1001 docker-compose up
```

## 🔍 Verificação

Para verificar se está funcionando:

1. **Execute o container:**
   ```bash
   docker-compose up -d
   ```

2. **Crie um arquivo de teste:**
   ```bash
   docker exec migsfy-bot touch /app/data/teste.txt
   ```

3. **Verifique as permissões:**
   ```bash
   ls -la data/teste.txt
   ```

4. **Deve mostrar seu usuário como proprietário:**
   ```bash
   -rw-r--r-- 1 seuusuario seugrupo 0 Jan 1 12:00 data/teste.txt
   ```

## 🛠️ Troubleshooting

### Problema: Arquivos ainda são criados como root
**Solução:** Verifique se as variáveis estão sendo passadas corretamente:
```bash
docker exec migsfy-bot env | grep -E "PUID|PGID"
```

### Problema: Container não inicia
**Solução:** Verifique se os IDs existem no sistema:
```bash
getent passwd 1000
getent group 1000
```

### Problema: Permissões negadas
**Solução:** Reconstrua o container:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## 📝 Valores Padrão

Se não especificado:
- PUID padrão: 1000
- PGID padrão: 1000

Estes são os valores mais comuns para o primeiro usuário em sistemas Linux.

## ⚠️ Notas Importantes

1. **Root (PUID=0):** O container executará como root se PUID=0
2. **Reconstrução:** Mudanças em PUID/PGID podem exigir rebuild do container
3. **Volumes:** Certifique-se de que os diretórios montados têm as permissões corretas
4. **Backup:** Faça backup dos dados antes de alterar permissões

## 🔗 Integração com Makefile

Você pode adicionar ao Makefile:

```makefile
# Obter IDs automaticamente
get-ids:
	@echo "PUID=$(shell id -u)"
	@echo "PGID=$(shell id -g)"

# Executar com IDs corretos
run-with-permissions:
	PUID=$(shell id -u) PGID=$(shell id -g) docker-compose up

# Build com permissões
build-with-permissions:
	PUID=$(shell id -u) PGID=$(shell id -g) docker-compose build
```
