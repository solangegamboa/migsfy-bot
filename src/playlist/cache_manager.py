import hashlib
import os
from typing import List, Dict, Optional
from datetime import datetime

class CacheManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.ttl_hours = int(os.getenv('CACHE_TTL_HOURS', 24))
        self.auto_cleanup = os.getenv('AUTO_CLEANUP_CACHE', 'true').lower() == 'true'
        
    def get_query_hash(self, query: str) -> str:
        """Gera hash SHA256 da query"""
        return hashlib.sha256(query.encode('utf-8')).hexdigest()
    
    def get_cached_results(self, query: str) -> Optional[List[Dict]]:
        """Busca resultados no cache"""
        query_hash = self.get_query_hash(query)
        
        # Cleanup automático se habilitado
        if self.auto_cleanup:
            self.cleanup_expired()
            
        return self.db_manager.get_cached_search(query_hash)
    
    def save_results(self, query: str, results: List[Dict], ttl_hours: int = None):
        """Salva resultados no cache"""
        query_hash = self.get_query_hash(query)
        ttl = ttl_hours or self.ttl_hours
        
        self.db_manager.save_search_cache(query_hash, query, results, ttl)
    
    def is_cache_valid(self, cached_entry: Dict) -> bool:
        """Verifica se entrada do cache é válida"""
        if not cached_entry:
            return False
            
        expires_at = cached_entry.get('expires_at')
        if not expires_at:
            return False
            
        try:
            expires_dt = datetime.fromisoformat(expires_at)
            return datetime.now() < expires_dt
        except (ValueError, TypeError):
            return False
    
    def cleanup_expired(self):
        """Remove cache expirado"""
        self.db_manager.cleanup_expired_cache()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Estatísticas do cache"""
        stats = self.db_manager.get_stats()
        return {
            'total_entries': stats.get('cache_entries', 0),
            'ttl_hours': self.ttl_hours,
            'auto_cleanup': self.auto_cleanup
        }
    
    def clear_cache(self):
        """Limpa todo o cache"""
        import sqlite3
        with sqlite3.connect(self.db_manager.db_path) as conn:
            conn.execute("DELETE FROM search_cache")
            
    def search_with_cache(self, query: str, search_function) -> List[Dict]:
        """Busca com cache automático"""
        # Tentar cache primeiro
        cached_results = self.get_cached_results(query)
        if cached_results is not None:
            print(f"Cache hit para query: {query[:50]}...")
            return cached_results
        
        # Cache miss - executar busca real
        print(f"Cache miss para query: {query[:50]}...")
        results = search_function(query)
        
        # Salvar no cache
        if results:
            self.save_results(query, results)
            
        return results
