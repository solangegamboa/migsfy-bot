import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.playlist.database_manager import DatabaseManager

class TestDatabaseManager:
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco temporário para testes"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        yield db
        
        # Cleanup
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
            'file_line': 'Artist - Album - Song'
        }
        
        # Salvar
        temp_db.save_download(data, 'SUCCESS')
        
        # Verificar
        assert temp_db.is_downloaded('Artist - Album - Song') == True
        assert temp_db.is_downloaded('Non-existent') == False
    
    def test_duplicate_normalized(self, temp_db):
        """Testa detecção por filename normalizado"""
        data = {
            'filename_normalized': 'normalized_test',
            'file_line': 'Test Line'
        }
        
        temp_db.save_download(data, 'SUCCESS')
        
        assert temp_db.is_duplicate_normalized('normalized_test') == True
        assert temp_db.is_duplicate_normalized('other') == False
    
    def test_duplicate_hash(self, temp_db):
        """Testa detecção por hash"""
        data = {
            'file_hash': 'abc123def456',
            'file_line': 'Hash Test'
        }
        
        temp_db.save_download(data, 'SUCCESS')
        
        assert temp_db.is_duplicate_hash('abc123def456') == True
        assert temp_db.is_duplicate_hash('different') == False
        assert temp_db.is_duplicate_hash('') == False
    
    def test_search_cache(self, temp_db):
        """Testa cache de buscas"""
        query_hash = 'test_hash_123'
        results = [{'filename': 'test.flac', 'username': 'user1'}]
        
        # Salvar no cache
        temp_db.save_search_cache(query_hash, 'test query', results, 1)
        
        # Recuperar do cache
        cached = temp_db.get_cached_search(query_hash)
        assert cached == results
        
        # Cache inexistente
        assert temp_db.get_cached_search('nonexistent') is None
    
    def test_cache_expiration(self, temp_db):
        """Testa expiração do cache"""
        query_hash = 'expire_test'
        results = [{'test': 'data'}]
        
        # Salvar com TTL muito baixo
        temp_db.save_search_cache(query_hash, 'expire test', results, ttl_hours=-1)
        
        # Deve retornar None (expirado)
        cached = temp_db.get_cached_search(query_hash)
        assert cached is None
    
    def test_cleanup_expired_cache(self, temp_db):
        """Testa limpeza de cache expirado"""
        # Adicionar cache expirado
        temp_db.save_search_cache('expired', 'old query', [], ttl_hours=-1)
        temp_db.save_search_cache('valid', 'new query', [], ttl_hours=24)
        
        # Limpar expirados
        temp_db.cleanup_expired_cache()
        
        # Verificar
        assert temp_db.get_cached_search('expired') is None
        assert temp_db.get_cached_search('valid') == []
    
    def test_stats(self, temp_db):
        """Testa estatísticas"""
        # Adicionar dados
        temp_db.save_download({'file_line': 'success1'}, 'SUCCESS')
        temp_db.save_download({'file_line': 'success2'}, 'SUCCESS')
        temp_db.save_download({'file_line': 'error1'}, 'ERROR')
        temp_db.save_search_cache('cache1', 'query', [], 24)
        
        stats = temp_db.get_stats()
        
        assert stats['SUCCESS'] == 2
        assert stats['ERROR'] == 1
        assert stats['cache_entries'] == 1
