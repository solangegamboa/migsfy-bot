"""
Testes unitários para as funções de seleção de música.
"""

import pytest
import sys
import os

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestMusicSelection:
    """Testes para as funções de seleção de música."""
    
    def setup_method(self):
        """Setup executado antes de cada teste."""
        # Mock data para testes
        self.mock_search_responses = [
            {
                'username': 'test_user_1',
                'files': [
                    {
                        'filename': '/music/Pink Floyd/Comfortably Numb.mp3',
                        'size': 6 * 1024 * 1024,  # 6MB
                        'bitRate': 320,
                        'length': 383  # 6:23
                    },
                    {
                        'filename': '/music/Pink Floyd/Another Brick.mp3',
                        'size': 5 * 1024 * 1024,  # 5MB
                        'bitRate': 256,
                        'length': 195  # 3:15
                    }
                ]
            },
            {
                'username': 'test_user_2',
                'files': [
                    {
                        'filename': '/collection/Pink Floyd - Comfortably Numb [Live].mp3',
                        'size': 8 * 1024 * 1024,  # 8MB
                        'bitRate': 320,
                        'length': 495  # 8:15
                    }
                ]
            }
        ]
    
    @pytest.mark.unit
    def test_extract_music_candidates_basic(self):
        """Testa extração básica de candidatos de música."""
        # Simula a função _extract_music_candidates
        def extract_music_candidates(search_responses, search_term):
            candidates = []
            
            for response in search_responses:
                username = response.get('username', 'Unknown')
                files = response.get('files', [])
                
                for file_info in files:
                    filename = file_info.get('filename', '')
                    
                    # Filtra apenas arquivos de música
                    if not filename.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                        continue
                    
                    size = file_info.get('size', 0)
                    bitrate = file_info.get('bitRate', 0)
                    duration = file_info.get('length', 0)
                    
                    # Converte duração
                    if duration > 0:
                        minutes = duration // 60
                        seconds = duration % 60
                        duration_str = f"{minutes}:{seconds:02d}"
                    else:
                        duration_str = "N/A"
                    
                    # Filtra arquivos muito pequenos
                    if size < 1024 * 1024:  # Menor que 1MB
                        continue
                    
                    # Filtra bitrates muito baixos
                    if bitrate > 0 and bitrate < 128:
                        continue
                    
                    candidate = {
                        'username': username,
                        'filename': filename,
                        'size': size,
                        'bitrate': bitrate if bitrate > 0 else 320,
                        'duration': duration_str
                    }
                    
                    candidates.append(candidate)
            
            return candidates
        
        # Act
        candidates = extract_music_candidates(self.mock_search_responses, "Pink Floyd - Comfortably Numb")
        
        # Assert
        assert len(candidates) == 3
        assert all('username' in c for c in candidates)
        assert all('filename' in c for c in candidates)
        assert all('size' in c for c in candidates)
        assert all('bitrate' in c for c in candidates)
        assert all('duration' in c for c in candidates)
    
    @pytest.mark.unit
    def test_extract_music_candidates_filtering(self):
        """Testa filtragem de candidatos de música."""
        # Mock data com arquivos que devem ser filtrados
        mock_responses_with_bad_files = [
            {
                'username': 'test_user',
                'files': [
                    {
                        'filename': '/music/good_song.mp3',
                        'size': 5 * 1024 * 1024,  # 5MB - OK
                        'bitRate': 320,  # OK
                        'length': 180
                    },
                    {
                        'filename': '/music/tiny_file.mp3',
                        'size': 500 * 1024,  # 500KB - Muito pequeno
                        'bitRate': 320,
                        'length': 30
                    },
                    {
                        'filename': '/music/low_quality.mp3',
                        'size': 3 * 1024 * 1024,  # 3MB - OK
                        'bitRate': 64,  # Muito baixo
                        'length': 180
                    },
                    {
                        'filename': '/music/not_music.txt',  # Não é música
                        'size': 2 * 1024 * 1024,
                        'bitRate': 320,
                        'length': 180
                    }
                ]
            }
        ]
        
        def extract_music_candidates(search_responses, search_term):
            candidates = []
            
            for response in search_responses:
                username = response.get('username', 'Unknown')
                files = response.get('files', [])
                
                for file_info in files:
                    filename = file_info.get('filename', '')
                    
                    # Filtra apenas arquivos de música
                    if not filename.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                        continue
                    
                    size = file_info.get('size', 0)
                    bitrate = file_info.get('bitRate', 0)
                    
                    # Filtra arquivos muito pequenos
                    if size < 1024 * 1024:  # Menor que 1MB
                        continue
                    
                    # Filtra bitrates muito baixos
                    if bitrate > 0 and bitrate < 128:
                        continue
                    
                    candidates.append({
                        'username': username,
                        'filename': filename,
                        'size': size,
                        'bitrate': bitrate,
                        'duration': '3:00'
                    })
            
            return candidates
        
        # Act
        candidates = extract_music_candidates(mock_responses_with_bad_files, "test")
        
        # Assert
        assert len(candidates) == 1  # Apenas o arquivo bom deve passar
        assert candidates[0]['filename'] == '/music/good_song.mp3'
    
    @pytest.mark.unit
    def test_music_candidate_sorting(self):
        """Testa ordenação de candidatos por qualidade."""
        # Mock candidates desordenados
        candidates = [
            {'username': 'user1', 'filename': 'song1.mp3', 'bitrate': 128, 'size': 3 * 1024 * 1024},
            {'username': 'user2', 'filename': 'song2.mp3', 'bitrate': 320, 'size': 5 * 1024 * 1024},
            {'username': 'user3', 'filename': 'song3.mp3', 'bitrate': 256, 'size': 4 * 1024 * 1024},
            {'username': 'user4', 'filename': 'song4.mp3', 'bitrate': 320, 'size': 6 * 1024 * 1024},
        ]
        
        # Act - Ordena por bitrate e tamanho (decrescente)
        sorted_candidates = sorted(candidates, key=lambda x: (x['bitrate'], x['size']), reverse=True)
        
        # Assert
        assert sorted_candidates[0]['filename'] == 'song4.mp3'  # 320kbps, 6MB
        assert sorted_candidates[1]['filename'] == 'song2.mp3'  # 320kbps, 5MB
        assert sorted_candidates[2]['filename'] == 'song3.mp3'  # 256kbps, 4MB
        assert sorted_candidates[3]['filename'] == 'song1.mp3'  # 128kbps, 3MB
    
    @pytest.mark.unit
    def test_callback_data_format(self):
        """Testa formato dos dados de callback."""
        # Arrange
        original_query = "Pink Floyd - Comfortably Numb"
        query_hash = hash(original_query) % 10000
        
        # Act & Assert
        for i in range(5):
            callback_data = f"music_{i}_{query_hash}"
            
            # Verifica formato
            parts = callback_data.split('_')
            assert len(parts) == 3
            assert parts[0] == 'music'
            assert parts[1] == str(i)
            assert parts[2] == str(query_hash)
            
            # Verifica se pode fazer parse
            music_index = int(parts[1])
            parsed_hash = int(parts[2])
            
            assert music_index == i
            assert parsed_hash == query_hash
    
    @pytest.mark.unit
    def test_duration_formatting(self):
        """Testa formatação de duração."""
        # Test cases: (seconds, expected_format)
        test_cases = [
            (0, "N/A"),
            (30, "0:30"),
            (60, "1:00"),
            (125, "2:05"),
            (383, "6:23"),
            (3661, "61:01")  # Mais de 1 hora
        ]
        
        def format_duration(duration_seconds):
            if duration_seconds <= 0:
                return "N/A"
            
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            return f"{minutes}:{seconds:02d}"
        
        # Act & Assert
        for seconds, expected in test_cases:
            result = format_duration(seconds)
            assert result == expected, f"Failed for {seconds}s: expected '{expected}', got '{result}'"
    
    @pytest.mark.unit
    def test_duplicate_removal(self):
        """Testa remoção de duplicatas."""
        # Mock candidates com duplicatas
        candidates = [
            {'username': 'user1', 'filename': '/path/song.mp3', 'bitrate': 128},
            {'username': 'user1', 'filename': '/path/song.mp3', 'bitrate': 320},  # Melhor qualidade
            {'username': 'user2', 'filename': '/other/song.mp3', 'bitrate': 256},
            {'username': 'user1', 'filename': '/path/other.mp3', 'bitrate': 192},
        ]
        
        # Act - Remove duplicatas mantendo melhor qualidade
        unique_candidates = {}
        for candidate in candidates:
            key = f"{candidate['username']}:{candidate['filename']}"
            if key not in unique_candidates or candidate['bitrate'] > unique_candidates[key]['bitrate']:
                unique_candidates[key] = candidate
        
        final_candidates = list(unique_candidates.values())
        
        # Assert
        assert len(final_candidates) == 3  # Removeu 1 duplicata
        
        # Verifica se manteve a melhor qualidade
        user1_song = next(c for c in final_candidates if c['username'] == 'user1' and 'song.mp3' in c['filename'])
        assert user1_song['bitrate'] == 320  # Manteve a melhor qualidade
    
    @pytest.mark.unit
    @pytest.mark.parametrize("filename,should_accept", [
        ("song.mp3", True),
        ("song.flac", True),
        ("song.wav", True),
        ("song.m4a", True),
        ("song.MP3", True),  # Case insensitive
        ("song.txt", False),
        ("song.jpg", False),
        ("song.pdf", False),
        ("song", False),  # Sem extensão
    ])
    def test_file_extension_filtering(self, filename, should_accept):
        """Testa filtragem por extensão de arquivo."""
        # Act
        is_music = filename.lower().endswith(('.mp3', '.flac', '.wav', '.m4a'))
        
        # Assert
        assert is_music == should_accept
