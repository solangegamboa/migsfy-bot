"""
Testes unitários para o extrator de nomes de álbum.
"""

import pytest
import sys
import os

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.album_name_extractor import (
    extract_album_name_from_path,
    extract_album_name_from_pattern_analysis,
    clean_album_name,
    get_album_name
)


class TestAlbumNameExtractor:
    """Testes para as funções de extração de nomes de álbum."""
    
    @pytest.mark.unit
    @pytest.mark.album
    def test_extract_album_name_from_path_simple(self):
        """Testa extração de nome de álbum de caminho simples."""
        # Arrange
        path = "/Music/Artist/Album Name"
        
        # Act
        result = extract_album_name_from_path(path)
        
        # Assert
        assert result == "Album Name"
    
    @pytest.mark.unit
    @pytest.mark.album
    def test_extract_album_name_from_path_with_year(self):
        """Testa extração de álbum com ano no caminho."""
        # Arrange
        path = "/Music/Pink Floyd/The Dark Side of the Moon [1973]"
        
        # Act
        result = extract_album_name_from_path(path)
        
        # Assert
        assert result == "The Dark Side of the Moon [1973]"
    
    def test_extract_album_name_from_path_empty(self):
        """Testa extração com caminho vazio."""
        # Arrange
        path = ""
        
        # Act
        result = extract_album_name_from_path(path)
        
        # Assert
        assert result == "Álbum Desconhecido"
    
    def test_clean_album_name_removes_quality_info(self):
        """Testa limpeza de informações de qualidade."""
        # Arrange
        name = "Album Name [320kbps] (FLAC)"
        
        # Act
        result = clean_album_name(name)
        
        # Assert
        assert result == "Album Name"
    
    def test_clean_album_name_removes_year(self):
        """Testa remoção de ano isolado."""
        # Arrange
        name = "Album Name 2023"
        
        # Act
        result = clean_album_name(name)
        
        # Assert
        assert result == "Album Name"
    
    def test_clean_album_name_empty_input(self):
        """Testa limpeza com entrada vazia."""
        # Arrange
        name = ""
        
        # Act
        result = clean_album_name(name)
        
        # Assert
        assert result == "Álbum Desconhecido"
    
    def test_clean_album_name_too_short(self):
        """Testa limpeza com nome muito curto."""
        # Arrange
        name = "AB"
        
        # Act
        result = clean_album_name(name)
        
        # Assert
        assert result == "Álbum Desconhecido"
    
    def test_extract_album_name_from_pattern_analysis(self):
        """Testa análise de padrões em candidato."""
        # Arrange
        candidate = {
            'username': 'test_user',
            'directory': '/Music/Pink Floyd/The Dark Side of the Moon',
            'files': [
                {'filename': '01 - Speak to Me.mp3'},
                {'filename': '02 - Breathe.mp3'},
            ]
        }
        
        # Act
        result = extract_album_name_from_pattern_analysis(candidate)
        
        # Assert
        assert result == "The Dark Side of the Moon"
    
    @pytest.mark.unit
    @pytest.mark.album
    def test_get_album_name_integration(self):
        """Testa função principal de extração."""
        # Arrange
        candidate = {
            'username': 'test_user',
            'directory': '/Music/Artist/Great Album [2023] [320kbps]',
            'files': [
                {'filename': 'Artist - Great Album - 01 - Song One.mp3'},
                {'filename': 'Artist - Great Album - 02 - Song Two.mp3'},
            ]
        }
        
        # Act
        result = get_album_name(candidate)
        
        # Assert
        assert "Great Album" in result
        assert "320kbps" not in result  # Deve ser removido pela limpeza
    
    @pytest.mark.unit
    @pytest.mark.album
    @pytest.mark.parametrize("path,expected", [
        ("/Music/Artist/Album", "Album"),
        ("/Music/Artist/My Great Album", "My Great Album"),
        ("/Music/Various Artists/Compilation Vol. 1", "Compilation Vol. 1"),
        ("", "Álbum Desconhecido"),
    ])
    def test_extract_album_name_from_path_parametrized(self, path, expected):
        """Testa extração com múltiplos casos parametrizados."""
        # Act
        result = extract_album_name_from_path(path)
        
        # Assert
        assert result == expected
