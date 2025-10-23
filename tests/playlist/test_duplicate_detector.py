import pytest
import tempfile
import os
from src.playlist.database_manager import DatabaseManager
from src.playlist.duplicate_detector import DuplicateDetector

class TestDuplicateDetector:
    
    @pytest.fixture
    def detector(self):
        """Cria detector com banco temporário"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        detector = DuplicateDetector(db)
        
        yield detector
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_normalize_filename(self, detector):
        """Testa normalização de filename"""
        test_cases = [
            ("/path/to/01 - Song Name.flac", "song name"),
            ("02. Artist - Song (Remix).mp3", "artist song remix"),
            ("Track 03 - Song@#$%Name.wav", "track song name"),
            ("", ""),
            ("Simple.flac", "simple")
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
            ("", ("", ""))
        ]
        
        for file_line, expected in test_cases:
            result = detector.extract_artist_song(file_line)
            assert result == expected
    
    def test_calculate_file_hash(self, detector):
        """Testa cálculo de hash MD5"""
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            # Calcular hash
            hash1 = detector.calculate_file_hash(temp_path)
            hash2 = detector.calculate_file_hash(temp_path)
            
            # Hashes devem ser iguais
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 tem 32 caracteres
            
            # Arquivo inexistente
            assert detector.calculate_file_hash("/nonexistent/file") == ""
            
        finally:
            os.unlink(temp_path)
    
    def test_is_similar_file(self, detector):
        """Testa detecção de arquivos similares"""
        new_file = {'filename': 'Pink Floyd - Comfortably Numb.flac'}
        
        existing_files = [
            {'filename': 'Pink Floyd - Comfortably Numb (Live).flac'},  # Similar
            {'filename': 'Led Zeppelin - Stairway to Heaven.flac'},     # Diferente
            {'filename': 'Pink Floyd - Comfortably Numb.mp3'}          # Muito similar
        ]
        
        # Deve detectar similaridade
        assert detector.is_similar_file(new_file, existing_files, threshold=0.8) == True
        
        # Com threshold muito alto, deve detectar apenas o .mp3 (quase idêntico)
        assert detector.is_similar_file(new_file, existing_files, threshold=0.95) == True
    
    def test_check_all_duplicates_no_match(self, detector):
        """Testa verificação completa sem duplicatas"""
        is_dup, reason = detector.check_all_duplicates(
            "New Song - New Album - New Track",
            "new_track.flac", 
            "New Artist",
            "New Song"
        )
        
        assert is_dup == False
        assert reason == "no_duplicate"
    
    def test_check_all_duplicates_exact_match(self, detector):
        """Testa verificação com match exato"""
        # Adicionar música no banco
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
    
    def test_check_all_duplicates_normalized_match(self, detector):
        """Testa verificação com match normalizado"""
        # Adicionar música com filename normalizado
        detector.db_manager.save_download({
            'filename_normalized': 'normalized song name',
            'file_line': 'Some Line'
        }, 'SUCCESS')
        
        is_dup, reason = detector.check_all_duplicates(
            "Different Line",
            "01 - Normalized Song Name.flac",
            "Artist",
            "Song"
        )
        
        assert is_dup == True
        assert reason == "normalized_filename_match"
