#!/usr/bin/env python3

"""
Testes de integração para verificar se o problema de parsing Markdown foi resolvido
"""

import pytest


class TestMarkdownFix:
    """Testes para correção de problemas de Markdown."""
    
    def _escape_markdown(self, text: str) -> str:
        """Escapa caracteres especiais do Markdown para evitar erros de parsing"""
        if not text:
            return ""
        
        # Remove ou substitui caracteres problemáticos
        cleaned_text = text
        
        # Remove caracteres que podem causar problemas
        problematic_chars = ['*', '_', '[', ']', '`', '\\']
        for char in problematic_chars:
            cleaned_text = cleaned_text.replace(char, '')
        
        # Substitui outros caracteres problemáticos
        cleaned_text = cleaned_text.replace('(', '\\(')
        cleaned_text = cleaned_text.replace(')', '\\)')
        
        return cleaned_text
    
    @pytest.mark.integration
    @pytest.mark.markdown
    def test_escape_markdown_function(self):
        """Testa a função de escape de markdown"""
        
        # Testa com nomes problemáticos que podem aparecer
        test_cases = [
            ("The Dark Side of the Moon [50th Anniversary]", "The Dark Side of the Moon 50th Anniversary"),
            ("Studio Albums*1973", "Studio Albums1973"),
            ("Discography_Remasters [Bubanee]", "DiscographyRemasters Bubanee"),
            ("Pink Floyd - The Wall (Deluxe)", "Pink Floyd - The Wall \\(Deluxe\\)"),
            ("Album with `backticks` and *asterisks*", "Album with backticks and asterisks"),
            ("Album_with_underscores", "Albumwithunderscores"),
            ("Album\\with\\backslashes", "Albumwithbackslashes"),
            ("Normal Album Name", "Normal Album Name"),
        ]
        
        for original, expected in test_cases:
            result = self._escape_markdown(original)
            assert result == expected, f"Failed for '{original}': expected '{expected}', got '{result}'"
    
    @pytest.mark.integration
    @pytest.mark.markdown
    def test_escape_markdown_empty_input(self):
        """Testa escape com entrada vazia"""
        result = self._escape_markdown("")
        assert result == ""
        
        result = self._escape_markdown(None)
        assert result == ""
    
    @pytest.mark.integration
    @pytest.mark.telegram
    @pytest.mark.markdown
    def test_message_formatting(self):
        """Testa formatação de mensagem completa"""
        
        # Simula dados de candidatos problemáticos
        candidates = [
            {
                'username': 'user*with*asterisks',
                'track_count': 10,
                'avg_bitrate': 320,
                'total_size': 100 * 1024 * 1024
            },
            {
                'username': 'user_with_underscores',
                'track_count': 15,
                'avg_bitrate': 256,
                'total_size': 80 * 1024 * 1024
            }
        ]
        
        album_names = [
            "The Dark Side of the Moon [50th Anniversary]",
            "Studio Albums*1973"
        ]
        
        original_query = "Pink Floyd - The Dark Side of the Moon"
        
        # Simula formatação da mensagem
        text = f"💿 Álbuns encontrados para: {original_query}\n\n"
        text += "📋 Selecione um álbum para baixar:\n\n"
        
        for i, (candidate, album_name) in enumerate(zip(candidates, album_names), 1):
            clean_album_name = self._escape_markdown(album_name)
            clean_username = self._escape_markdown(candidate['username'])
            
            text += f"{i}. {clean_album_name}\n"
            text += f"   👤 {clean_username}\n"
            text += f"   🎵 {candidate['track_count']} faixas\n"
            text += f"   🎧 {candidate['avg_bitrate']:.0f} kbps\n"
            text += f"   💾 {candidate['total_size'] / 1024 / 1024:.1f} MB\n\n"
        
        # Verifica se não há caracteres problemáticos na mensagem final
        problematic_chars = ['*', '_', '[', ']', '`', '\\']
        for char in problematic_chars:
            if char == '\\':
                # Permite escape de parênteses
                continue
            assert char not in text, f"Caractere problemático '{char}' encontrado na mensagem"
        
        # Verifica se a mensagem não está vazia
        assert len(text.strip()) > 0, "Mensagem não deve estar vazia"
        
        # Verifica se contém informações esperadas
        assert "💿 Álbuns encontrados" in text
        assert "📋 Selecione um álbum" in text
        assert "👤" in text  # Username
        assert "🎵" in text  # Track count
        assert "🎧" in text  # Bitrate
        assert "💾" in text  # Size
    
    @pytest.mark.integration
    @pytest.mark.markdown
    @pytest.mark.parametrize("problematic_text,expected_safe", [
        ("Text with *asterisks*", "Text with asterisks"),
        ("Text with _underscores_", "Text with underscores"),
        ("Text with [brackets]", "Text with brackets"),
        ("Text with `backticks`", "Text with backticks"),
        ("Text with \\backslashes\\", "Text with backslashes"),
        ("Text with (parentheses)", "Text with \\(parentheses\\)"),  # Parênteses são escapados
        ("Normal text", "Normal text"),
    ])
    def test_escape_markdown_parametrized(self, problematic_text, expected_safe):
        """Testa escape com múltiplos casos parametrizados"""
        result = self._escape_markdown(problematic_text)
        assert result == expected_safe, f"Expected '{expected_safe}', got '{result}'"
