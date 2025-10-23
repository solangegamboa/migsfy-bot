import pytest
import tempfile
import os
from unittest.mock import patch
from src.playlist.database_manager import DatabaseManager
from src.playlist.duplicate_detector import DuplicateDetector

class TestDuplicateDetector:
    
    @pytest.fixture
    def detector(self):
        """Cria detector com banco temporário"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        db.init_database()
        detector = DuplicateDetector(db)
        
        yield detector
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_normalize_filename(self, detector):
        """Testa normalização de filename"""
        test_cases = [
            ("/path/to/01 - Song Name.flac", "song name"),
            ("02. Artist - Song (Remix).mp3", "artist song remix"),
            ("Track 03 - Song@#$%Name.wav", "track song name"),
            ("", ""),
            ("Simple.flac", "simple"),
            ("01-Pink Floyd-Comfortably Numb.flac", "pink floyd comfortably numb")
        ]
        
        for input_name, expected in test_cases:
            result = detector.normalize_filename(input_name)
            assert result == expected
    
    def test_extract_artist_song(self, detector):
        """Testa extração de artista e música"""
        test_cases = [
            ("Pink Floyd - The Wall - Another Brick", ("Pink Floyd", "Another Brick")),
            ("Metallica - Master of Puppets", ("Metallica", "Master of Puppets")),
            ("Single Song Name", ("", "Single Song Name")),
            ("", ("", "")),
            ("Artist - Album - Song - Extra", ("Artist", "Song - Extra"))
        ]
        
        for file_line, expected in test_cases:
            result = detector.extract_artist_song(file_line)
            assert result == expected
    
    def test_fuzzy_match_song(self, detector):
        """Testa fuzzy matching de músicas"""
        # Adicionar música no banco
        detector.db_manager.save_download({
            'file_line': 'Pink Floyd - The Wall - Comfortably Numb'
        }, 'SUCCESS')
        
        # Testes de similaridade
        assert detector.fuzzy_match_song("Pink Floyd", "Comfortably Numb", 0.8) == True
        assert detector.fuzzy_match_song("Pink Floyd", "Comfortably Num", 0.8) == True  # Typo
        assert detector.fuzzy_match_song("Led Zeppelin", "Stairway to Heaven", 0.8) == False
        assert detector.fuzzy_match_song("Pink Floyd", "Different Song", 0.8) == False
    
    def test_calculate_file_hash(self, detector):
        """Testa cálculo de hash MD5"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content for hash")
            temp_path = f.name
        
        try:
            hash1 = detector.calculate_file_hash(temp_path)
            hash2 = detector.calculate_file_hash(temp_path)
            
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5
            assert detector.calculate_file_hash("/nonexistent") == ""
            
        finally:
            os.unlink(temp_path)
    
    def test_is_similar_file(self, detector):
        """Testa detecção de arquivos similares"""
        new_file = {'filename': 'Pink Floyd - Comfortably Numb.flac'}
        
        existing_files = [
            {'filename': 'Pink Floyd - Comfortably Numb (Live).flac'},
            {'filename': 'Led Zeppelin - Stairway to Heaven.flac'},
            {'filename': 'Pink Floyd - Comfortably Numb.mp3'}
        ]
        
        assert detector.is_similar_file(new_file, existing_files, 0.8) == True
        assert detector.is_similar_file(new_file, existing_files, 0.99) == True  # .mp3 match
    
    def test_check_all_duplicates_comprehensive(self, detector):
        """Testa verificação completa de duplicatas"""
        # Cenário 1: Sem duplicatas
        is_dup, reason = detector.check_all_duplicates(
            "New Song - New Album - New Track",
            "new_track.flac", 
            "New Artist",
            "New Song"
        )
        assert is_dup == False
        assert reason == "no_duplicate"
        
        # Cenário 2: Match exato
        detector.db_manager.save_download({
            'file_line': 'Exact Match - Album - Song'
        }, 'SUCCESS')
        
        is_dup, reason = detector.check_all_duplicates(
            "Exact Match - Album - Song",
            "song.flac",
            "Exact Match", 
            "Song"
        )
        assert is_dup == True
        assert reason == "exact_line_match"
        
        # Cenário 3: Match normalizado
        detector.db_manager.save_download({
            'filename_normalized': 'normalized song',
            'file_line': 'Some Line'
        }, 'SUCCESS')
        
        is_dup, reason = detector.check_all_duplicates(
            "Different Line",
            "01 - Normalized Song.flac",
            "Artist",
            "Song"
        )
        assert is_dup == True
        assert reason == "normalized_filename_match"
        
        # Cenário 4: Match por hash
        detector.db_manager.save_download({
            'file_hash': 'abc123hash',
            'file_line': 'Hash Test'
        }, 'SUCCESS')
        
        with patch.object(detector, 'calculate_file_hash', return_value='abc123hash'):
            is_dup, reason = detector.check_all_duplicates(
                "Hash Test Line",
                "/path/to/file.flac",
                "Artist",
                "Song"
            )
            assert is_dup == True
            assert reason == "file_hash_match"
    
    def test_performance_with_large_dataset(self, detector):
        """Testa performance com dataset grande"""
        # Adicionar muitos registros
        for i in range(100):
            detector.db_manager.save_download({
                'file_line': f'Artist {i} - Album {i} - Song {i}',
                'filename_normalized': f'song {i}',
                'file_hash': f'hash{i}'
            }, 'SUCCESS')
        
        # Teste de performance
        import time
        start_time = time.time()
        
        is_dup, reason = detector.check_all_duplicates(
            "Artist 50 - Album 50 - Song 50",
            "song_50.flac",
            "Artist 50",
            "Song 50"
        )
        
        elapsed = time.time() - start_time
        assert elapsed < 1.0  # Deve ser rápido
        assert is_dup == True
        assert reason == "exact_line_match"
    
    def test_edge_cases(self, detector):
        """Testa casos extremos"""
        # Strings vazias
        is_dup, reason = detector.check_all_duplicates("", "", "", "")
        assert is_dup == False
        
        # Strings muito longas
        long_string = "A" * 1000
        is_dup, reason = detector.check_all_duplicates(
            long_string, long_string, long_string, long_string
        )
        assert is_dup == False
        
        # Caracteres especiais
        special_chars = "Artíst - Álbum - Músíca çõm açéntos"
        is_dup, reason = detector.check_all_duplicates(
            special_chars, "special.flac", "Artíst", "Músíca"
        )
        assert is_dup == False
    
    def test_threshold_configuration(self, detector):
        """Testa configuração de threshold"""
        with patch.dict(os.environ, {'DUPLICATE_FUZZY_THRESHOLD': '0.9'}):
            detector_custom = DuplicateDetector(detector.db_manager)
            assert detector_custom.fuzzy_threshold == 0.9
        
        # Teste com threshold padrão
        assert detector.fuzzy_threshold == 0.85
