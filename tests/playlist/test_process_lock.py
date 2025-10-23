import pytest
import tempfile
import os
import time
from src.playlist.process_lock import ProcessLock

class TestProcessLock:
    
    @pytest.fixture
    def temp_lock_file(self):
        """Cria arquivo de lock temporário"""
        with tempfile.NamedTemporaryFile(suffix='.lock', delete=False) as f:
            lock_path = f.name
        
        # Remove o arquivo para que ProcessLock possa criá-lo
        os.unlink(lock_path)
        
        yield lock_path
        
        # Cleanup
        if os.path.exists(lock_path):
            os.unlink(lock_path)
    
    def test_acquire_and_release(self, temp_lock_file):
        """Testa aquisição e liberação de lock"""
        lock = ProcessLock(temp_lock_file)
        
        # Deve conseguir adquirir
        assert lock.acquire() == True
        assert os.path.exists(temp_lock_file)
        
        # Liberar
        lock.release()
        assert not os.path.exists(temp_lock_file)
    
    def test_double_acquire_fails(self, temp_lock_file):
        """Testa que segundo acquire falha"""
        lock1 = ProcessLock(temp_lock_file)
        lock2 = ProcessLock(temp_lock_file)
        
        # Primeiro deve conseguir
        assert lock1.acquire() == True
        
        # Segundo deve falhar
        assert lock2.acquire() == False
        
        # Cleanup
        lock1.release()
    
    def test_is_locked(self, temp_lock_file):
        """Testa verificação de lock ativo"""
        lock = ProcessLock(temp_lock_file)
        
        # Inicialmente não está locked
        assert lock.is_locked() == False
        
        # Após acquire, deve estar locked
        lock.acquire()
        assert lock.is_locked() == True
        
        # Após release, não deve estar locked
        lock.release()
        assert lock.is_locked() == False
    
    def test_context_manager(self, temp_lock_file):
        """Testa uso como context manager"""
        lock = ProcessLock(temp_lock_file)
        
        # Usar com context manager
        with lock:
            assert os.path.exists(temp_lock_file)
        
        # Após sair do contexto, deve estar liberado
        assert not os.path.exists(temp_lock_file)
    
    def test_context_manager_exception(self, temp_lock_file):
        """Testa context manager com exceção"""
        lock = ProcessLock(temp_lock_file)
        
        try:
            with lock:
                assert os.path.exists(temp_lock_file)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Mesmo com exceção, deve liberar o lock
        assert not os.path.exists(temp_lock_file)
    
    def test_context_manager_already_locked(self, temp_lock_file):
        """Testa context manager quando já está locked"""
        lock1 = ProcessLock(temp_lock_file)
        lock2 = ProcessLock(temp_lock_file)
        
        # Primeiro adquire o lock
        lock1.acquire()
        
        # Segundo deve falhar ao tentar usar context manager
        with pytest.raises(RuntimeError, match="processo já rodando"):
            with lock2:
                pass
        
        # Cleanup
        lock1.release()
    
    def test_orphaned_lock_cleanup(self, temp_lock_file):
        """Testa limpeza de lock órfão"""
        # Criar arquivo de lock com PID inexistente
        with open(temp_lock_file, 'w') as f:
            f.write("999999\n")  # PID que não existe
        
        lock = ProcessLock(temp_lock_file)
        
        # is_locked deve detectar que é órfão e limpar
        assert lock.is_locked() == False
        assert not os.path.exists(temp_lock_file)
    
    def test_corrupted_lock_file(self, temp_lock_file):
        """Testa arquivo de lock corrompido"""
        # Criar arquivo corrompido
        with open(temp_lock_file, 'w') as f:
            f.write("invalid content")
        
        lock = ProcessLock(temp_lock_file)
        
        # Deve detectar corrupção e limpar
        assert lock.is_locked() == False
        assert not os.path.exists(temp_lock_file)
