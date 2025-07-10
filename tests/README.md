# Testes

Esta pasta contém todos os testes do projeto migsfy-bot.

## 📁 Estrutura

```
tests/
├── unit/                  # Testes unitários
│   ├── test_slskd_client.py
│   ├── test_spotify_client.py
│   ├── test_search_engine.py
│   └── test_album_extractor.py
├── integration/           # Testes de integração
│   ├── test_telegram_bot.py
│   ├── test_album_search.py
│   └── test_playlist_download.py
├── fixtures/              # Dados de teste
│   ├── sample_responses.json
│   └── test_playlists.json
└── README.md             # Este arquivo
```

## 🧪 Tipos de Teste

### Testes Unitários (`unit/`)
- Testam componentes individuais isoladamente
- Rápidos de executar
- Não dependem de serviços externos
- Usam mocks e fixtures

### Testes de Integração (`integration/`)
- Testam a integração entre componentes
- Podem usar serviços externos (com cuidado)
- Mais lentos que testes unitários
- Testam fluxos completos

### Fixtures (`fixtures/`)
- Dados de teste reutilizáveis
- Respostas simuladas de APIs
- Arquivos de exemplo
- Configurações de teste

## 🚀 Executando Testes

### Todos os testes
```bash
python3 -m pytest tests/
```

### Apenas testes unitários
```bash
python3 -m pytest tests/unit/
```

### Apenas testes de integração
```bash
python3 -m pytest tests/integration/
```

### Teste específico
```bash
python3 -m pytest tests/unit/test_album_extractor.py
```

### Com cobertura
```bash
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Com marcadores
```bash
# Apenas testes rápidos
python3 -m pytest -m "not slow"

# Apenas testes do Telegram
python3 -m pytest -m telegram

# Apenas testes do Spotify
python3 -m pytest -m spotify
```

## 🏷️ Marcadores

Use marcadores para categorizar testes:

```python
import pytest

@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_integration():
    pass

@pytest.mark.telegram
def test_telegram_feature():
    pass
```

Marcadores disponíveis:
- `unit`: Testes unitários
- `integration`: Testes de integração
- `slow`: Testes que demoram para executar
- `telegram`: Testes do bot do Telegram
- `spotify`: Testes do Spotify
- `slskd`: Testes do SLSKD

## 📝 Convenções

### Nomenclatura
- Arquivos: `test_*.py`
- Classes: `TestNomeDoComponente`
- Métodos: `test_descricao_do_teste`

### Estrutura de Teste
```python
def test_nome_descritivo(self):
    # Arrange - Preparar dados
    input_data = "test data"
    expected = "expected result"
    
    # Act - Executar ação
    result = function_to_test(input_data)
    
    # Assert - Verificar resultado
    assert result == expected
```

### Fixtures
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## 🔧 Configuração

A configuração do pytest está em `pytest.ini` na raiz do projeto.

## 📊 Cobertura

Para gerar relatório de cobertura:

```bash
# Instalar pytest-cov se necessário
pip install pytest-cov

# Executar com cobertura
python3 -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# Ver relatório HTML
open htmlcov/index.html
```

## 🐛 Debugging

Para debuggar testes:

```bash
# Com output detalhado
python3 -m pytest tests/ -v -s

# Parar no primeiro erro
python3 -m pytest tests/ -x

# Executar apenas testes que falharam
python3 -m pytest tests/ --lf
```

## 📚 Recursos

- [Documentação do pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Mocking com pytest](https://docs.pytest.org/en/stable/how.html#monkeypatch)
