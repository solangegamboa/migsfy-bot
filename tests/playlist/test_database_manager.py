import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
from src.playlist.database_manager import DatabaseManager

class TestDatabaseManager:
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco temporário para testes"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        db.init_database()
        yield db
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_init_database(self, temp_db):
        """Testa inicialização do banco"""
        stats = temp_db.get_stats()
        assert isinstance(stats, dict)
        assert stats.get('cache_entries', 0) == 0
    
    def test_save_and_check_download(self, temp_db):
        """Testa salvar e verificar download"""
        data = {
            'id': 'test-123',
            'username': 'testuser',
            'filename': 'test.flac',
            'filename_normalized': 'test',
            'file_line': 'Artist - Album - Song',
            'file_size': 1024000,
            'file_hash': 'abc123'
        }
        
        temp_db.save_download(data, 'SUCCESS')
        
        assert temp_db.is_downloaded('Artist - Album - Song') == True
        assert temp_db.is_downloaded('Non-existent') == False
    
    def test_duplicate_detection_methods(self, temp_db):
        """Testa múltiplos métodos de detecção de duplicatas"""
        data = {
            'filename_normalized': 'normalized_test',
            'file_line': 'Test Line',
            'file_hash': 'hash123'
        }
        
        temp_db.save_download(data, 'SUCCESS')
        
        # Teste normalizado
        assert temp_db.is_duplicate_normalized('normalized_test') == True
        assert temp_db.is_duplicate_normalized('other') == False
        
        # Teste hash
        assert temp_db.is_duplicate_hash('hash123') == True
        assert temp_db.is_duplicate_hash('different') == False
    
    def test_fuzzy_match_duplicates(self, temp_db):
        """Testa detecção fuzzy de duplicatas"""
        temp_db.save_download({
            'file_line': 'Soundgarden - Superunknown - Black Hole Sun'
        }, 'SUCCESS')
        
        # Deve detectar variações similares
        assert temp_db.is_duplicate_fuzzy('Soundgarden', 'Black Hole Sun', 0.8) == True
        assert temp_db.is_duplicate_fuzzy('Different Artist', 'Different Song', 0.8) == False
    
    def test_search_cache_with_ttl(self, temp_db):
        """Testa cache com TTL"""
        query_hash = 'test_hash_123'
        results = [{'filename': 'test.flac', 'username': 'user1'}]
        
        # Salvar com TTL válido
        temp_db.save_search_cache(query_hash, 'test query', results, 24)
        cached = temp_db.get_cached_search(query_hash)
        assert cached == results
        
        # Salvar com TTL expirado
        temp_db.save_search_cache('expired', 'old query', [], -1)
        assert temp_db.get_cached_search('expired') is None
    
    def test_get_all_downloads(self, temp_db):
        """Testa recuperação de todos os downloads"""
        temp_db.save_download({'file_line': 'Song 1'}, 'SUCCESS')
        temp_db.save_download({'file_line': 'Song 2'}, 'ERROR')
        temp_db.save_download({'file_line': 'Song 3'}, 'NOT_FOUND')
        
        downloads = temp_db.get_all_downloads()
        assert len(downloads) == 3
        
        # Filtrar por status
        success_downloads = [d for d in downloads if d['status'] == 'SUCCESS']
        assert len(success_downloads) == 1
    
    def test_cleanup_operations(self, temp_db):
        """Testa operações de limpeza"""
        # Adicionar cache expirado
        temp_db.save_search_cache('expired1', 'old', [], -1)
        temp_db.save_search_cache('expired2', 'old', [], -1)
        temp_db.save_search_cache('valid', 'new', [], 24)
        
        cleaned = temp_db.cleanup_expired_cache()
        assert cleaned >= 2
        
        # Verificar que apenas válido permanece
        assert temp_db.get_cached_search('expired1') is None
        assert temp_db.get_cached_search('valid') == []
    
    def test_performance_with_large_dataset(self, temp_db):
        """Testa performance com dataset grande"""
        # Adicionar muitos registros
        for i in range(100):
            temp_db.save_download({
                'file_line': f'Artist {i} - Album {i} - Song {i}',
                'filename_normalized': f'song_{i}',
                'file_hash': f'hash_{i}'
            }, 'SUCCESS')
        
        # Testes de performance
        start_time = time.time()
        
        # Verificação de duplicata deve ser rápida
        assert temp_db.is_downloaded('Artist 50 - Album 50 - Song 50') == True
        assert temp_db.is_duplicate_normalized('song_75') == True
        assert temp_db.is_duplicate_hash('hash_25') == True
        
        elapsed = time.time() - start_time
        assert elapsed < 1.0  # Deve ser menor que 1 segundo
    
    def test_database_integrity(self, temp_db):
        """Testa integridade do banco"""
        # Adicionar dados com diferentes tipos
        temp_db.save_download({
            'file_line': 'Test Song',
            'file_size': None,  # NULL
            'file_hash': '',    # String vazia
            'filename_normalized': 'test'
        }, 'SUCCESS')
        
        # Deve lidar com valores NULL/vazios
        assert temp_db.is_downloaded('Test Song') == True
        assert temp_db.is_duplicate_hash('') == False  # String vazia não é duplicata
        assert temp_db.is_duplicate_hash(None) == False  # None não é duplicata
    
    def test_concurrent_access_simulation(self, temp_db):
        """Simula acesso concurrent ao banco"""
        # Simular múltiplas operações simultâneas
        for i in range(10):
            temp_db.save_download({'file_line': f'Concurrent {i}'}, 'SUCCESS')
            temp_db.save_search_cache(f'cache_{i}', f'query {i}', [], 1)
            temp_db.is_downloaded(f'Concurrent {i}')
            temp_db.get_cached_search(f'cache_{i}')
        
        # Verificar consistência
        stats = temp_db.get_stats()
        assert stats['SUCCESS'] == 10
        assert stats['cache_entries'] == 10
