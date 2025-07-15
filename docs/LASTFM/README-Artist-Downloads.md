# Last.fm Artist Downloads - Bot Telegram

## 🎤 Comando /lastfm_artist

### Funcionalidade
Baixa automaticamente as músicas mais populares de um artista específico usando dados do Last.fm.

### Uso Básico
```
/lastfm_artist <nome_do_artista>
```

### Uso Avançado
```
/lastfm_artist <nome_do_artista> <quantidade>
```

## 📋 Exemplos

### Exemplos Básicos (30 músicas)
```
/lastfm_artist Radiohead
/lastfm_artist The Beatles
/lastfm_artist Pink Floyd
/lastfm_artist Led Zeppelin
```

### Exemplos com Quantidade Personalizada
```
/lastfm_artist Radiohead 20
/lastfm_artist The Beatles 50
/lastfm_artist Queen 15
/lastfm_artist Nirvana 25
```

## ⚙️ Configurações

### Limites
- **Padrão**: 30 músicas por artista
- **Máximo**: 50 músicas por execução
- **Proteção**: Limite automático para evitar sobrecarga

### Comportamento
- **Automático**: Não pede confirmação
- **Inteligente**: Pula músicas já baixadas
- **Organizado**: Cria diretório com nome do artista
- **Seguro**: Apenas tracks individuais (nunca álbuns)

## 🚫 Proteção Anti-Álbum

### Verificações Ativas
1. **Nome do arquivo**: Rejeita indicadores de álbum
2. **Diretório**: Analisa quantidade de arquivos
3. **Padrões**: Detecta numeração sequencial
4. **Tamanho**: Rejeita arquivos muito grandes
5. **Duração**: Rejeita arquivos muito longos

### Garantia
**0% de chance** de baixar álbuns completos inadvertidamente.

## 📊 Relatório de Download

### Informações Fornecidas
```
🎤 Download concluído - Artista: Radiohead

📊 Estatísticas:
• Total de músicas: 30
• ✅ Downloads bem-sucedidos: 22
• ❌ Downloads com falha: 3
• ⏭️ Músicas já baixadas: 5
• 📈 Taxa de sucesso: 73.3%

🎉 22 novas músicas de Radiohead foram baixadas com sucesso!

🎯 Modo anti-álbum ativo: Apenas tracks individuais foram baixadas
📁 Localização: Diretório Radiohead
```

## 🔧 Troubleshooting

### Artista Não Encontrado
```
❌ Erro no download do artista "Nome Incorreto"

Possíveis causas:
• Artista não encontrado no Last.fm
• Credenciais do Last.fm não configuradas
• Servidor SLSKD offline
• Problema de conectividade

Dica: Verifique a grafia do nome do artista
```

**Soluções**:
- Verificar grafia exata do nome
- Usar nome em inglês se aplicável
- Tentar variações do nome

### Nenhuma Música Baixada
```
ℹ️ Nenhuma música nova foi baixada

Todas as 30 músicas já estavam no seu histórico de downloads.
```

**Soluções**:
- Usar comando `/clear_history` se necessário
- Tentar outro artista
- Aumentar o limite de músicas

## 🎯 Dicas de Uso

### Para Descobrir Música Nova
```
/lastfm_artist Arctic Monkeys 15
/lastfm_artist Tame Impala 20
/lastfm_artist Mac DeMarco 25
```

### Para Coleções Completas
```
/lastfm_artist Pink Floyd 50
/lastfm_artist The Beatles 50
/lastfm_artist Led Zeppelin 50
```

### Para Testes Rápidos
```
/lastfm_artist Coldplay 5
/lastfm_artist U2 10
```

## 🔄 Integração com Outros Comandos

### Verificar Histórico
```
/history
```

### Ver Tarefas Ativas
```
/tasks
```

### Limpar Histórico (se necessário)
```
/clear_history
```

## 📈 Vantagens

### Para o Usuário
- **Descoberta**: Encontra as melhores músicas de qualquer artista
- **Automático**: Processo sem intervenção manual
- **Organizado**: Cada artista em seu diretório
- **Inteligente**: Evita downloads duplicados

### Para o Sistema
- **Eficiente**: Usa dados do Last.fm para priorizar
- **Seguro**: Múltiplas proteções anti-álbum
- **Robusto**: Tratamento de erros completo
- **Transparente**: Logs detalhados de cada operação

## 🎵 Resultado Final

Após usar `/lastfm_artist Radiohead`, você terá:

```
Radiohead/
├── Creep.mp3
├── Paranoid Android.mp3
├── Karma Police.mp3
├── No Surprises.mp3
├── High and Dry.mp3
└── ... (até 30 músicas)
```

**Garantia**: Apenas as melhores e mais populares tracks do artista, organizadas e prontas para ouvir!