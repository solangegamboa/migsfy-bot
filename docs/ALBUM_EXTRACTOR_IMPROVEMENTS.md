# Melhorias no Extrator de Nomes de Álbum

## 📋 Resumo das Melhorias

O módulo `album_name_extractor.py` foi completamente reescrito para resolver o problema de sempre retornar "Álbum Desconhecido". As melhorias incluem:

### 🎯 Estratégias Múltiplas de Extração

1. **Metadados de Arquivos (Prioridade Máxima)**
   - Usa a biblioteca `music-tag` para ler metadados ID3
   - Suporta MP3, FLAC, M4A, OGG, WAV, WMA
   - Tenta múltiplas tags de álbum (album, ALBUM, Album)

2. **Análise de Nomes de Arquivos**
   - Detecta padrões: `Artist - Album - Track`
   - Suporta múltiplos separadores: ` - `, ` – `, ` — `, `_-_`, ` | `
   - Aceita álbuns com nomes curtos (ex: "IV", "1984")
   - Usa heurísticas para distinguir artistas de álbuns

3. **Estrutura de Diretórios**
   - Analisa caminhos como `/Music/Artist/Album`
   - Remove automaticamente padrões de qualidade: `[320kbps]`, `[FLAC]`
   - Remove anos: `[1973]`, `(2023)`
   - Ignora diretórios genéricos: `music`, `downloads`, `complete`

4. **Priorização Inteligente**
   - Metadados têm prioridade absoluta
   - Nomes de arquivos são priorizados sobre diretórios genéricos
   - Sistema de fallback robusto

### 🧹 Limpeza Avançada de Nomes

- Remove caracteres problemáticos: `<>:"/\|?*`
- Remove padrões de qualidade: `320kbps`, `FLAC`, `V0`, `V2`
- Remove informações extras: `Remaster`, `Deluxe`, `Special Edition`
- Normaliza espaços e remove caracteres no início/fim
- Limita tamanho para evitar nomes muito longos

### 📊 Logging Detalhado

- Logs informativos sobre qual estratégia foi usada
- Logs de debug para troubleshooting
- Warnings quando não consegue determinar o álbum

## 🧪 Resultados dos Testes

```
📁 Teste 1: Estrutura de diretório organizada
   /Music/Pink Floyd/The Dark Side of the Moon [1973] [320kbps]
   Resultado: 'The Dark Side of the Moon' ✅

🎵 Teste 2: Padrão Artist - Album - Track
   Led Zeppelin - IV - Black Dog.mp3
   Resultado: 'IV' ✅

💿 Teste 3: Padrão Album - Track
   Kind of Blue - So What.mp3
   Resultado: 'Kind of Blue' ✅

🔊 Teste 4: Diretório com informações de qualidade
   /FLAC/Beatles/Abbey Road [1969] [FLAC] [Remastered]
   Resultado: 'Abbey Road Remastered' ✅

🔀 Teste 5: Múltiplos tipos de separadores
   Metallica – Master of Puppets – Battery.mp3
   Resultado: 'Master of Puppets' ✅

📂 Teste 6: Estrutura de diretório aninhada
   /Music/Rock/Classic Rock/Queen/A Night at the Opera (1975)
   Resultado: 'A Night at the Opera' ✅
```

## 🔧 Configuração

### Dependências

A biblioteca `music-tag` já está incluída no `requirements.txt`:

```
music-tag>=0.4.3
```

### Instalação

```bash
pip3 install music-tag
```

### Uso no Código

```python
from utils.album_name_extractor import get_album_name

# Para candidatos remotos (SoulSeek)
candidate = {
    'username': 'user123',
    'directory': '/Music/Artist/Album [2023]',
    'files': [
        {'filename': 'Artist - Album - Track1.mp3'},
        {'filename': 'Artist - Album - Track2.mp3'}
    ]
}

album_name = get_album_name(candidate)

# Para arquivos locais (com metadados)
local_files = ['/path/to/track1.mp3', '/path/to/track2.mp3']
album_name = get_album_name(candidate, local_files)
```

## 🐛 Correções de Bugs

### Problema do Import

O import do módulo no bot do Telegram foi corrigido:

```python
# Antes (com erro)
from album_name_extractor import get_album_name

# Depois (corrigido)
import sys
import os
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)
from album_name_extractor import get_album_name
```

### Tratamento de Erros

- Try/catch robusto para leitura de metadados
- Fallbacks para quando `music-tag` não está disponível
- Logs de erro detalhados para debugging

## 📈 Melhorias de Performance

- Analisa apenas os primeiros 3-5 arquivos por candidato
- Cache implícito através de análise inteligente
- Evita processamento desnecessário com verificações rápidas

## 🔮 Próximos Passos

1. **Cache de Metadados**: Implementar cache para evitar re-leitura
2. **Machine Learning**: Usar ML para melhorar detecção de padrões
3. **API Externa**: Integração com APIs como MusicBrainz para validação
4. **Configuração**: Permitir configurar prioridades das estratégias

## 🧪 Como Testar

Execute os scripts de teste incluídos:

```bash
# Teste com casos simulados
python3 test_album_extractor.py

# Teste com arquivos MP3 reais (se disponíveis)
python3 test_real_files.py
```

## 📝 Notas Técnicas

- **Compatibilidade**: Mantém interface antiga para não quebrar código existente
- **Extensibilidade**: Fácil adicionar novas estratégias de extração
- **Robustez**: Múltiplos fallbacks garantem que sempre retorna um resultado
- **Logging**: Sistema de logs configurável para debugging e monitoramento
