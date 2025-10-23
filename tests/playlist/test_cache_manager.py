import pytest
import tempfile
import os
from unittest.mock import patch
from src.playlist.database_manager import DatabaseManager
from src.playlist.cache_manager import CacheManager

class TestCacheManager:
    
    @pytest.fixture
    def cache_manager(self):
        """Cria CacheManager com banco temporário"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        cache = CacheManager(db)
        
        yield cache
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_get_query_hash(self, cache_manager):
        """Testa geração de hash da query"""
        hash1 = cache_manager.get_query_hash("test query")
        hash2 = cache_manager.get_query_hash("test query")
        hash3 = cache_manager.get_query_hash("different query")
        
        # Hashes iguais para queries iguais
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 tem 64 caracteres
        
        # Hashes diferentes para queries diferentes
        assert hash1 != hash3
    
    def test_save_and_get_cached_results(self, cache_manager):
        """Testa salvar e recuperar resultados do cache"""
        query = "test search query"
        results = [{'filename': 'test.flac', 'username': 'user1'}]
        
        # Salvar no cache
        cache_manager.save_results(query, results, ttl_hours=1)
        
        # Recuperar do cache
        cached = cache_manager.get_cached_results(query)
        assert cached == results
        
        # Query diferente não deve ter cache
        assert cache_manager.get_cached_results("different query") is None
    
    def test_cache_with_custom_ttl(self, cache_manager):
        """Testa cache com TTL customizado"""
        with patch.dict(os.environ, {'CACHE_TTL_HOURS': '12'}):
            cache_manager_custom = CacheManager(cache_manager.db_manager)
            assert cache_manager_custom.ttl_hours == 12
    
    def test_search_with_cache_hit(self, cache_manager):
        """Testa busca com cache hit"""
        query = "cached query"
        expected_results = [{'test': 'data'}]
        
        # Pré-popular cache
        cache_manager.save_results(query, expected_results)
        
        # Mock da função de busca (não deve ser chamada)
        def mock_search(q):
            pytest.fail("Search function should not be called on cache hit")
        
        results = cache_manager.search_with_cache(query, mock_search)
        assert results == expected_results
    
    def test_search_with_cache_miss(self, cache_manager):
        """Testa busca com cache miss"""
        query = "uncached query"
        search_results = [{'filename': 'found.flac'}]
        
        # Mock da função de busca
        def mock_search(q):
            assert q == query
            return search_results
        
        results = cache_manager.search_with_cache(query, mock_search)
        
        # Deve retornar resultados da busca
        assert results == search_results
        
        # Deve ter salvo no cache
        cached = cache_manager.get_cached_results(query)
        assert cached == search_results
    
    def test_search_with_cache_empty_results(self, cache_manager):
        """Testa busca com resultados vazios"""
        query = "empty query"
        
        def mock_search(q):
            return []
        
        results = cache_manager.search_with_cache(query, mock_search)
        assert results == []
        
        # Resultados vazios não devem ser cacheados
        cached = cache_manager.get_cached_results(query)
        assert cached is None
    
    def test_get_cache_stats(self, cache_manager):
        """Testa estatísticas do cache"""
        # Adicionar alguns itens
        cache_manager.save_results("query1", [{'test': '1'}])
        cache_manager.save_results("query2", [{'test': '2'}])
        
        stats = cache_manager.get_cache_stats()
        
        assert stats['total_entries'] == 2
        assert stats['ttl_hours'] == cache_manager.ttl_hours
        assert isinstance(stats['auto_cleanup'], bool)
    
    def test_clear_cache(self, cache_manager):
        """Testa limpeza completa do cache"""
        # Adicionar itens
        cache_manager.save_results("query1", [{'test': '1'}])
        cache_manager.save_results("query2", [{'test': '2'}])
        
        # Verificar que existem
        assert cache_manager.get_cache_stats()['total_entries'] == 2
        
        # Limpar cache
        cache_manager.clear_cache()
        
        # Verificar que foi limpo
        assert cache_manager.get_cache_stats()['total_entries'] == 0
    
    def test_auto_cleanup_enabled(self, cache_manager):
        """Testa cleanup automático habilitado"""
        with patch.dict(os.environ, {'AUTO_CLEANUP_CACHE': 'true'}):
            cache_manager_auto = CacheManager(cache_manager.db_manager)
            
            with patch.object(cache_manager_auto, 'cleanup_expired') as mock_cleanup:
                # get_cached_results deve triggerar cleanup
                cache_manager_auto.get_cached_results("test")
                
                mock_cleanup.assert_called_once()
    
    def test_auto_cleanup_disabled(self, cache_manager):
        """Testa cleanup automático desabilitado"""
        with patch.dict(os.environ, {'AUTO_CLEANUP_CACHE': 'false'}):
            with patch.object(cache_manager, 'cleanup_expired') as mock_cleanup:
                cache_manager_manual = CacheManager(cache_manager.db_manager)
                
                # get_cached_results não deve triggerar cleanup
                cache_manager_manual.get_cached_results("test")
                
                mock_cleanup.assert_not_called()
