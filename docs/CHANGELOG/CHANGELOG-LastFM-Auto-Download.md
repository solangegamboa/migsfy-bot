# Changelog: Last.fm Automated Download Script

## 📅 Data: 15/07/2025

## 🎯 Resumo

Implementação de script bash para download automático de músicas do Last.fm baseado em tags configuradas, com execução programada via cron e monitoramento completo de recursos do sistema.

## ✨ Funcionalidades Implementadas

### 🤖 Automação Completa

- **Execução Programada**: Script projetado para execução via cron a cada 48 horas
- **Configuração Flexível**: Tags, limites e diretórios configuráveis via variáveis de ambiente
- **Processamento em Lote**: Processa múltiplas tags em sequência com pausas inteligentes
- **Monitoramento de Recursos**: Verifica espaço em disco e tamanho dos downloads
- **Relatórios Detalhados**: Logs estruturados com estatísticas completas

### 🔒 Controle de Execução

#### Sistema de Lock File
- **Prevenção de Execução Simultânea**: Lock file em `/tmp/lastfm_auto_download.lock`
- **Detecção de Processos Órfãos**: Remove lock files de processos mortos
- **Timeout de Segurança**: Lock files antigos (>2h) são removidos automaticamente
- **Limpeza Automática**: Trap para remoção do lock em caso de interrupção

#### Validação de Ambiente
- **Verificação de Diretórios**: Confirma existência do diretório do projeto
- **Validação de Credenciais**: Verifica LASTFM_API_KEY e LASTFM_API_SECRET
- **Carregamento Seguro**: Source do .env com proteção contra erros

### 📊 Sistema de Configuração

#### Variáveis de Ambiente Suportadas
```bash
# Tags para download automático (separadas por vírgula)
LASTFM_AUTO_TAGS="rock,pop,jazz,alternative rock,metal"

# Limite de músicas por tag
LASTFM_AUTO_LIMIT=15

# Diretório de saída
LASTFM_AUTO_OUTPUT_DIR="./downloads/lastfm_auto"

# Controle de duplicatas
LASTFM_AUTO_SKIP_EXISTING=true
```

#### Configuração Padrão Inteligente
- **Limite Padrão**: 15 músicas por tag (balanceio entre descoberta e recursos)
- **Diretório Padrão**: `./downloads/lastfm_auto` (organização separada)
- **Skip Existentes**: Habilitado por padrão (evita duplicatas)
- **Timeout por Tag**: 30 minutos máximo (1800 segundos)

### 🎵 Processamento de Tags

#### Execução Sequencial
- **Processamento Individual**: Cada tag é processada separadamente
- **Pausas Inteligentes**: 30 segundos entre tags para não sobrecarregar
- **Timeout por Tag**: Máximo de 30 minutos por tag
- **Sanitização**: Remove espaços em branco das tags automaticamente

#### Integração com CLI
- **Reutilização de Código**: Usa o CLI principal (`src/cli/main.py`)
- **Argumentos Dinâmicos**: Constrói argumentos baseado na configuração
- **Compatibilidade Total**: Funciona com todas as opções do CLI
- **Redirecionamento de Logs**: Saída capturada no log principal

### 📈 Sistema de Monitoramento

#### Logs Estruturados
```bash
[2025-07-15 14:30:15] 🚀 Iniciando download automático de tracks do Last.fm
[2025-07-15 14:30:16] 📋 Configurações:
[2025-07-15 14:30:16]    🏷️ Tags: rock,pop,jazz
[2025-07-15 14:30:16]    📊 Limite por tag: 15
[2025-07-15 14:30:16]    📁 Diretório: ./downloads/lastfm_auto
[2025-07-15 14:30:16] 🎵 Iniciando download de 3 tags...
```

#### Estatísticas por Tag
- **Extração Automática**: Captura estatísticas do output do CLI
- **Relatório Individual**: Mostra sucessos/falhas por tag
- **Tempo de Execução**: Cronometra duração de cada tag
- **Detecção de Erros**: Captura e reporta erros específicos

#### Monitoramento de Sistema
- **Espaço em Disco**: Verifica uso do disco onde estão os downloads
- **Tamanho dos Downloads**: Calcula tamanho total dos arquivos baixados
- **Alerta de Espaço**: Aviso quando uso do disco > 90%
- **Rotação de Logs**: Logs grandes (>10MB) são rotacionados automaticamente

### 🧹 Gerenciamento de Logs

#### Arquivo de Log Principal
- **Localização**: `$PROJECT_DIR/logs/lastfm_auto_download.log`
- **Formato Timestamped**: Cada linha com data/hora
- **Saída Dupla**: Exibe no terminal e salva no arquivo
- **Encoding UTF-8**: Suporte completo a emojis e caracteres especiais

#### Rotação e Limpeza
- **Rotação Automática**: Logs >10MB são rotacionados com timestamp
- **Limpeza de Logs Antigos**: Remove logs com mais de 30 dias
- **Preservação de Histórico**: Mantém logs recentes para troubleshooting
- **Formato de Rotação**: `lastfm_auto_download.log.YYYYMMDD_HHMMSS`

### 📊 Relatórios Finais

#### Estatísticas Consolidadas
```bash
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

#### Códigos de Saída
- **0**: Todos os downloads bem-sucedidos
- **1**: Alguns downloads falharam (mas script executou)
- **Outros**: Erros de configuração ou sistema

## 📁 Arquivo Criado

### `scripts/lastfm-auto-download.sh`
Script bash completo com 247 linhas implementando:

```bash
# Funções principais:
- log()                          # Logging com timestamp
- cleanup()                      # Limpeza de lock files
- Verificação de lock files      # Prevenção de execução simultânea
- Validação de ambiente          # Verificação de pré-requisitos
- Processamento de tags          # Loop principal de download
- Monitoramento de sistema       # Verificação de recursos
- Relatórios finais             # Estatísticas consolidadas
```

## 🔧 Configuração e Uso

### 1. Configuração no .env
```bash
# Adicionar ao arquivo .env
LASTFM_AUTO_TAGS="rock,pop,jazz,alternative rock,metal,blues,electronic"
LASTFM_AUTO_LIMIT=20
LASTFM_AUTO_OUTPUT_DIR="./downloads/auto"
LASTFM_AUTO_SKIP_EXISTING=true
```

### 2. Execução Manual
```bash
# Executar uma vez para testar
./scripts/lastfm-auto-download.sh

# Verificar logs
tail -f logs/lastfm_auto_download.log
```

### 3. Configuração do Cron
```bash
# Editar crontab
crontab -e

# Adicionar linha para execução a cada 48 horas (2 dias) às 2:00 AM
0 2 */2 * * /caminho/para/projeto/scripts/lastfm-auto-download.sh

# Ou a cada 24 horas às 3:00 AM
0 3 * * * /caminho/para/projeto/scripts/lastfm-auto-download.sh

# Verificar crontab
crontab -l
```

### 4. Monitoramento
```bash
# Ver logs em tempo real
tail -f logs/lastfm_auto_download.log

# Ver últimas execuções
tail -50 logs/lastfm_auto_download.log

# Verificar se está executando
ps aux | grep lastfm-auto-download

# Verificar lock file
ls -la /tmp/lastfm_auto_download.lock
```

## 🎯 Casos de Uso

### Descoberta Musical Automatizada
```bash
# Tags para descobrir novos gêneros
LASTFM_AUTO_TAGS="indie rock,dream pop,shoegaze,post rock,ambient"
LASTFM_AUTO_LIMIT=10
```

### Coleção Temática
```bash
# Música por décadas
LASTFM_AUTO_TAGS="80s,90s,2000s,2010s"
LASTFM_AUTO_LIMIT=25
```

### Exploração de Gêneros
```bash
# Subgêneros específicos
LASTFM_AUTO_TAGS="progressive rock,death metal,smooth jazz,deep house"
LASTFM_AUTO_LIMIT=15
```

### Música Internacional
```bash
# Tags em diferentes idiomas
LASTFM_AUTO_TAGS="rock nacional,mpb,bossa nova,samba,forró"
LASTFM_AUTO_LIMIT=20
```

## 🛡️ Tratamento de Erros

### Validação de Pré-requisitos
```bash
# Diretório do projeto não encontrado
❌ Diretório do projeto não encontrado: /caminho/inexistente
# Script termina com exit 1

# Arquivo .env ausente
❌ Arquivo .env não encontrado
# Script termina com exit 1

# Credenciais Last.fm ausentes
❌ Credenciais do Last.fm não configuradas no .env
💡 Configure LASTFM_API_KEY e LASTFM_API_SECRET
# Script termina com exit 1
```

### Configuração Ausente
```bash
# Nenhuma tag configurada
⚠️ Nenhuma tag configurada em LASTFM_AUTO_TAGS
💡 Configure tags separadas por vírgula no .env:
💡 LASTFM_AUTO_TAGS=rock,pop,jazz,alternative rock,metal
# Script termina com exit 0 (não é erro fatal)
```

### Falhas de Execução
```bash
# Timeout por tag (30 minutos)
❌ Falha ao processar tag 'rock' (1800s)
🔍 Últimos erros:
   ERROR: Connection timeout
   ❌ Não foi possível conectar ao SLSKD
```

### Problemas de Sistema
```bash
# Espaço em disco baixo
⚠️ AVISO: Uso do disco acima de 90%!

# Erro de permissão
❌ Erro ao criar diretório: Permission denied
```

## 📊 Benefícios da Implementação

### Para o Usuário
- **Descoberta Automática**: Novas músicas aparecem regularmente sem intervenção
- **Configuração Simples**: Apenas definir tags no .env e configurar cron
- **Controle Total**: Limites, diretórios e comportamento configuráveis
- **Monitoramento Transparente**: Logs detalhados de toda atividade
- **Segurança**: Não executa simultaneamente, evita sobrecarga

### Para o Sistema
- **Eficiência**: Execução programada em horários de baixo uso
- **Robustez**: Tratamento completo de erros e edge cases
- **Monitoramento**: Alertas de espaço em disco e recursos
- **Manutenção**: Rotação automática de logs e limpeza
- **Escalabilidade**: Suporta qualquer número de tags

### Para Administradores
- **Logs Estruturados**: Fácil troubleshooting e monitoramento
- **Configuração Centralizada**: Tudo no arquivo .env
- **Integração com Cron**: Execução automática sem supervisão
- **Relatórios Detalhados**: Estatísticas completas de cada execução
- **Controle de Recursos**: Monitoramento de espaço e performance

## 🔮 Possibilidades Futuras

### Melhorias Planejadas
1. **Notificações**: Envio de relatórios por email ou Telegram
2. **Configuração Dinâmica**: Mudança de tags sem reiniciar cron
3. **Balanceamento**: Distribuição inteligente de downloads por horário
4. **Métricas**: Dashboard web com estatísticas históricas
5. **Integração**: Sincronização com serviços de streaming

### Recursos Avançados
1. **Machine Learning**: Sugestão automática de novas tags baseada no histórico
2. **Análise de Tendências**: Descoberta de tags populares emergentes
3. **Otimização de Recursos**: Ajuste automático de limites baseado no espaço disponível
4. **Backup Automático**: Sincronização com cloud storage
5. **API REST**: Interface web para configuração e monitoramento

## 🧪 Cenários de Teste

### Teste 1: Execução Básica
```bash
# Configurar tags simples
LASTFM_AUTO_TAGS="rock,pop"
LASTFM_AUTO_LIMIT=5

# Executar script
./scripts/lastfm-auto-download.sh

# Verificar resultado
# Esperado: 2 tags processadas, 10 músicas total
```

### Teste 2: Prevenção de Execução Simultânea
```bash
# Terminal 1
./scripts/lastfm-auto-download.sh &

# Terminal 2 (imediatamente)
./scripts/lastfm-auto-download.sh
# Esperado: "Script já está executando"
```

### Teste 3: Recuperação de Lock Órfão
```bash
# Criar lock file órfão
echo "99999" > /tmp/lastfm_auto_download.lock

# Executar script
./scripts/lastfm-auto-download.sh
# Esperado: "Lock file órfão detectado. Removendo..."
```

### Teste 4: Validação de Configuração
```bash
# Remover credenciais do .env
unset LASTFM_API_KEY

# Executar script
./scripts/lastfm-auto-download.sh
# Esperado: Erro de credenciais ausentes
```

### Teste 5: Monitoramento de Recursos
```bash
# Executar com muitas tags
LASTFM_AUTO_TAGS="rock,pop,jazz,metal,electronic,hip hop,classical,blues"
LASTFM_AUTO_LIMIT=30

# Verificar relatório final
# Esperado: Estatísticas de espaço em disco e tamanho total
```

## 📚 Documentação Atualizada

### Arquivos Modificados
- `docs/LASTFM/README-LastFM.md`: Seção sobre automação adicionada
- `README.md`: Referência ao script de automação
- `docs/README.md`: Integração com documentação principal

### Novas Seções Adicionadas
- **🤖 Download Automático**: Configuração e uso do script
- **📊 Monitoramento**: Como acompanhar execuções automáticas
- **🔧 Configuração de Cron**: Setup para execução programada
- **📈 Relatórios**: Interpretação de logs e estatísticas

## 🎉 Conclusão

A implementação do script de download automático representa um marco na evolução do sistema:

### Conquistas Técnicas
- **Automação Completa**: Zero intervenção manual necessária
- **Robustez Industrial**: Tratamento de todos os cenários de erro
- **Monitoramento Profissional**: Logs e métricas de nível empresarial
- **Integração Perfeita**: Reutiliza toda infraestrutura existente

### Impacto para Usuários
- **Descoberta Contínua**: Novas músicas aparecem automaticamente
- **Configuração Simples**: Setup uma vez, funciona para sempre
- **Controle Total**: Flexibilidade completa de configuração
- **Transparência**: Visibilidade total do que está acontecendo

### Base para o Futuro
- **Arquitetura Escalável**: Suporta expansão para recursos avançados
- **Padrões Estabelecidos**: Modelo para futuras automações
- **Qualidade de Código**: Exemplo de boas práticas em bash scripting

---

**💡 Este script transforma o sistema de um downloader manual em uma plataforma de descoberta musical completamente automatizada, mantendo a simplicidade de configuração e adicionando monitoramento profissional.**