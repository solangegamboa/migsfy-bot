import pytest
import tempfile
import os
import time
import json
from unittest.mock import patch, Mock
from src.playlist.process_lock import ProcessLock

class TestProcessLock:
    
    @pytest.fixture
    def temp_lock_file(self):
        """Cria arquivo de lock temporário"""
        with tempfile.NamedTemporaryFile(suffix='.lock', delete=False) as f:
            lock_path = f.name
        
        os.unlink(lock_path)
        yield lock_path
        
        if os.path.exists(lock_path):
            os.unlink(lock_path)
    
    def test_acquire_and_release(self, temp_lock_file):
        """Testa aquisição e liberação de lock"""
        lock = ProcessLock(temp_lock_file)
        
        assert lock.acquire() == True
        assert os.path.exists(temp_lock_file)
        
        lock.release()
        assert not os.path.exists(temp_lock_file)
    
    def test_lock_info_details(self, temp_lock_file):
        """Testa informações detalhadas do lock"""
        lock = ProcessLock(temp_lock_file)
        lock.acquire()
        
        info = lock.get_lock_info()
        assert info is not None
        assert info['pid'] == os.getpid()
        assert 'timestamp' in info
        assert 'hostname' in info
        
        lock.release()
    
    def test_stale_lock_detection(self, temp_lock_file):
        """Testa detecção de lock órfão"""
        # Criar lock com PID inexistente
        lock_data = {
            'pid': 999999,
            'timestamp': time.time(),
            'hostname': 'test',
            'process_name': 'playlist_processor'
        }
        
        with open(temp_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        lock = ProcessLock(temp_lock_file)
        assert lock.is_locked() == False  # Deve detectar como órfão
    
    def test_timeout_detection(self, temp_lock_file):
        """Testa detecção de timeout"""
        lock = ProcessLock(temp_lock_file, timeout=1)  # 1 segundo
        
        # Criar lock antigo
        lock_data = {
            'pid': os.getpid(),
            'timestamp': time.time() - 2,  # 2 segundos atrás
            'hostname': 'test'
        }
        
        with open(temp_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        assert lock._is_stale_lock() == True
    
    def test_force_release(self, temp_lock_file):
        """Testa liberação forçada"""
        lock = ProcessLock(temp_lock_file)
        lock.acquire()
        
        assert lock.force_release() == True
        assert not os.path.exists(temp_lock_file)
    
    @patch('psutil.pid_exists')
    def test_process_verification(self, mock_pid_exists, temp_lock_file):
        """Testa verificação de processo"""
        mock_pid_exists.return_value = False
        
        lock_data = {
            'pid': 12345,
            'timestamp': time.time(),
            'hostname': 'test'
        }
        
        with open(temp_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        lock = ProcessLock(temp_lock_file)
        assert lock._is_stale_lock() == True
    
    def test_context_manager_with_info(self, temp_lock_file):
        """Testa context manager com informações detalhadas"""
        lock1 = ProcessLock(temp_lock_file)
        lock2 = ProcessLock(temp_lock_file)
        
        lock1.acquire()
        
        with pytest.raises(RuntimeError) as exc_info:
            with lock2:
                pass
        
        # Deve incluir informações do PID
        assert "PID:" in str(exc_info.value)
        
        lock1.release()
