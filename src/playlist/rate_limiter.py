import time
import os
from typing import Optional

class RateLimiter:
    def __init__(self, min_interval: int = None):
        # Usar configuração existente como base
        base_wait = int(os.getenv('SEARCH_WAIT_TIME', 25))
        new_limit = int(os.getenv('RATE_LIMIT_SECONDS', 3))
        
        # Usar o maior valor para ser conservador
        self.min_interval = min_interval or max(base_wait, new_limit)
        self.last_request_time: Optional[float] = None
        self.consecutive_failures = 0
        
    def wait_if_needed(self):
        """Aguarda intervalo mínimo entre requests"""
        if self.last_request_time is None:
            self.last_request_time = time.time()
            return
            
        elapsed = time.time() - self.last_request_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def record_request(self):
        """Registra timestamp do request"""
        self.last_request_time = time.time()
        self.consecutive_failures = 0
    
    def handle_rate_limit_error(self):
        """Pausa em caso de rate limit"""
        pause_minutes = int(os.getenv('SERVER_OVERLOAD_PAUSE_MINUTES', 10))
        print(f"Rate limit detectado. Pausando por {pause_minutes} minutos...")
        time.sleep(pause_minutes * 60)
        
    def apply_backoff(self, attempt: int):
        """Backoff exponencial para falhas"""
        base_seconds = int(os.getenv('BACKOFF_BASE_SECONDS', 30))
        max_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
        
        if attempt > max_attempts:
            raise Exception(f"Máximo de {max_attempts} tentativas excedido")
            
        # Backoff exponencial: 30s, 60s, 120s
        backoff_time = base_seconds * (2 ** (attempt - 1))
        print(f"Tentativa {attempt}/{max_attempts}. Aguardando {backoff_time}s...")
        time.sleep(backoff_time)
        
    def record_failure(self):
        """Registra falha consecutiva"""
        self.consecutive_failures += 1
        
        # Se muitas falhas, aplicar pausa maior
        if self.consecutive_failures >= 3:
            overload_pause = int(os.getenv('SERVER_OVERLOAD_PAUSE_MINUTES', 10))
            print(f"Muitas falhas consecutivas. Pausando por {overload_pause} minutos...")
            time.sleep(overload_pause * 60)
            self.consecutive_failures = 0
