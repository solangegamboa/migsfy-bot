import pytest
import time
import os
from unittest.mock import patch
from src.playlist.rate_limiter import RateLimiter

class TestRateLimiter:
    
    def test_init_with_env_vars(self):
        """Testa inicialização com variáveis de ambiente"""
        with patch.dict(os.environ, {'SEARCH_WAIT_TIME': '10', 'RATE_LIMIT_SECONDS': '5'}):
            limiter = RateLimiter()
            # Deve usar o maior valor (10s)
            assert limiter.min_interval == 10
    
    def test_init_with_custom_interval(self):
        """Testa inicialização com intervalo customizado"""
        limiter = RateLimiter(min_interval=15)
        assert limiter.min_interval == 15
    
    def test_wait_if_needed_first_request(self):
        """Testa primeiro request sem espera"""
        limiter = RateLimiter(min_interval=1)
        
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Primeiro request não deve esperar
        assert elapsed < 0.1
        assert limiter.last_request_time is not None
    
    def test_wait_if_needed_rate_limiting(self):
        """Testa rate limiting entre requests"""
        limiter = RateLimiter(min_interval=1)
        
        # Primeiro request
        limiter.wait_if_needed()
        
        # Segundo request imediato deve esperar
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Deve ter esperado aproximadamente 1 segundo
        assert 0.9 <= elapsed <= 1.2
    
    def test_record_request(self):
        """Testa registro de request"""
        limiter = RateLimiter()
        
        limiter.record_request()
        
        assert limiter.last_request_time is not None
        assert limiter.consecutive_failures == 0
    
    def test_handle_rate_limit_error(self):
        """Testa tratamento de rate limit (mock do sleep)"""
        with patch.dict(os.environ, {'SERVER_OVERLOAD_PAUSE_MINUTES': '1'}):
            with patch('time.sleep') as mock_sleep:
                limiter = RateLimiter()
                limiter.handle_rate_limit_error()
                
                # Deve ter pausado por 1 minuto (60 segundos)
                mock_sleep.assert_called_once_with(60)
    
    def test_apply_backoff(self):
        """Testa backoff exponencial"""
        with patch.dict(os.environ, {'BACKOFF_BASE_SECONDS': '2', 'MAX_RETRY_ATTEMPTS': '3'}):
            with patch('time.sleep') as mock_sleep:
                limiter = RateLimiter()
                
                # Tentativa 1: 2s
                limiter.apply_backoff(1)
                mock_sleep.assert_called_with(2)
                
                # Tentativa 2: 4s
                limiter.apply_backoff(2)
                mock_sleep.assert_called_with(4)
                
                # Tentativa 3: 8s
                limiter.apply_backoff(3)
                mock_sleep.assert_called_with(8)
    
    def test_apply_backoff_max_attempts(self):
        """Testa exceção quando excede tentativas"""
        with patch.dict(os.environ, {'MAX_RETRY_ATTEMPTS': '2'}):
            limiter = RateLimiter()
            
            with pytest.raises(Exception, match="Máximo de 2 tentativas excedido"):
                limiter.apply_backoff(3)
    
    def test_record_failure(self):
        """Testa registro de falhas"""
        limiter = RateLimiter()
        
        # Registrar falhas
        limiter.record_failure()
        assert limiter.consecutive_failures == 1
        
        limiter.record_failure()
        assert limiter.consecutive_failures == 2
    
    def test_record_failure_overload_pause(self):
        """Testa pausa por sobrecarga após muitas falhas"""
        with patch.dict(os.environ, {'SERVER_OVERLOAD_PAUSE_MINUTES': '1'}):
            with patch('time.sleep') as mock_sleep:
                limiter = RateLimiter()
                
                # 3 falhas consecutivas devem triggerar pausa
                limiter.record_failure()
                limiter.record_failure()
                limiter.record_failure()  # Esta deve pausar
                
                # Deve ter pausado e resetado contador
                mock_sleep.assert_called_once_with(60)
                assert limiter.consecutive_failures == 0
