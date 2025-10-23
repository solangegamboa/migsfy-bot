import os
import time
from typing import List, Dict, Optional
from slskd_api import SlskdClient
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager

class SlskdApiClient:
    def __init__(self, db_manager):
        # Configuração da API usando .env existente
        self.host = os.getenv('SLSKD_HOST', 'localhost')
        self.port = int(os.getenv('SLSKD_PORT', 5030))
        self.api_key = os.getenv('SLSKD_API_KEY', '')
        self.base_url = os.getenv('SLSKD_URL_BASE', f'http://{self.host}:{self.port}')
        
        # Inicializar componentes
        self.api = SlskdClient(host=self.host, port=self.port, api_key=self.api_key)
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager(db_manager)
        
        # Configurações
        self.max_retries = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
        self.server_overload_threshold = 5  # Falhas consecutivas
        self.consecutive_failures = 0
        
    def search_tracks_cached(self, query: str) -> List[Dict]:
        """Busca com cache e rate limiting"""
        def _search_function(q):
            return self._search_tracks_raw(q)
            
        return self.cache_manager.search_with_cache(query, _search_function)
    
    def _search_tracks_raw(self, query: str) -> List[Dict]:
        """Busca raw sem cache"""
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Executar busca
                results = self.api.searches.search_text(query)
                
                # Sucesso - resetar contadores
                self.rate_limiter.record_request()
                self.consecutive_failures = 0
                
                return self._process_search_results(results)
                
            except Exception as e:
                self.consecutive_failures += 1
                self.rate_limiter.record_failure()
                
                if "rate limit" in str(e).lower():
                    self.rate_limiter.handle_rate_limit_error()
                    continue
                    
                if attempt < self.max_retries:
                    self.rate_limiter.apply_backoff(attempt)
                    continue
                    
                # Última tentativa falhou
                if self.consecutive_failures >= self.server_overload_threshold:
                    print("Servidor possivelmente sobrecarregado. Pausando...")
                    time.sleep(600)  # 10 minutos
                    
                raise e
                
        return []
    
    def _process_search_results(self, raw_results) -> List[Dict]:
        """Processa resultados da API para formato padrão"""
        processed = []
        
        if not raw_results:
            return processed
            
        # Processar estrutura da API slskd
        for result in raw_results:
            if isinstance(result, dict):
                processed.append({
                    'username': result.get('username', ''),
                    'filename': result.get('filename', ''),
                    'size': result.get('size', 0),
                    'bitDepth': result.get('bitDepth', 0),
                    'sampleRate': result.get('sampleRate', 0),
                    'bitRate': result.get('bitRate', 0)
                })
                
        return processed
    
    def get_download_queue(self) -> List[Dict]:
        """Obtém fila de downloads"""
        try:
            return self.api.transfers.get_downloads()
        except Exception as e:
            print(f"Erro ao obter fila de downloads: {e}")
            return []
    
    def add_download(self, username: str, filename: str) -> Optional[str]:
        """Adiciona download à fila"""
        try:
            result = self.api.transfers.download(username=username, filename=filename)
            return result.get('id') if isinstance(result, dict) else None
        except Exception as e:
            print(f"Erro ao adicionar download: {e}")
            return None
    
    def remove_download(self, download_id: str) -> bool:
        """Remove download da fila"""
        try:
            self.api.transfers.cancel_download(download_id)
            return True
        except Exception as e:
            print(f"Erro ao remover download: {e}")
            return False
    
    def get_download_status(self, download_id: str) -> Optional[Dict]:
        """Obtém status de download específico"""
        try:
            return self.api.transfers.get_download(download_id)
        except Exception as e:
            print(f"Erro ao obter status: {e}")
            return None
    
    def is_server_overloaded(self) -> bool:
        """Detecta se servidor está sobrecarregado"""
        return self.consecutive_failures >= self.server_overload_threshold
    
    def get_connection_stats(self) -> Dict:
        """Estatísticas de conexão"""
        return {
            'host': self.host,
            'port': self.port,
            'consecutive_failures': self.consecutive_failures,
            'is_overloaded': self.is_server_overloaded(),
            'cache_stats': self.cache_manager.get_cache_stats()
        }
