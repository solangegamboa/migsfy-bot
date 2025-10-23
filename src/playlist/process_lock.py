import os
import time
import fcntl
import signal
import logging
import psutil
from typing import Optional
from pathlib import Path

class ProcessLock:
    def __init__(self, lock_file: str, timeout: int = 3600):
        self.lock_file = lock_file
        self.lock_fd: Optional[int] = None
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    def acquire(self) -> bool:
        """Adquire lock exclusivo com detecção de locks órfãos"""
        try:
            # Verificar e limpar locks órfãos
            if self._is_stale_lock():
                self._cleanup_stale_lock()
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
            
            # Abrir arquivo de lock
            self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            
            # Tentar adquirir lock não-bloqueante
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Escrever informações detalhadas
            lock_info = f"{os.getpid()}\n{int(time.time())}\n{os.uname().nodename}\nplaylist_processor"
            os.write(self.lock_fd, lock_info.encode())
            os.fsync(self.lock_fd)
            
            self.logger.info(f"Process lock acquired: {self.lock_file} (PID: {os.getpid()})")
            return True
            
        except (OSError, IOError) as e:
            if self.lock_fd:
                os.close(self.lock_fd)
                self.lock_fd = None
            self.logger.warning(f"Failed to acquire lock: {e}")
            return False
    
    def release(self):
        """Libera lock com verificação de propriedade"""
        if self.lock_fd:
            try:
                # Verificar se ainda somos donos do lock
                if self._verify_ownership():
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                    os.close(self.lock_fd)
                    os.unlink(self.lock_file)
                    self.logger.info(f"Process lock released: {self.lock_file}")
                else:
                    self.logger.warning("Cannot release lock - not owned by this process")
            except (OSError, IOError) as e:
                self.logger.error(f"Error releasing lock: {e}")
            finally:
                self.lock_fd = None
    
    def is_locked(self) -> bool:
        """Verifica se processo está ativo (com detecção de órfãos)"""
        if not os.path.exists(self.lock_file):
            return False
            
        return not self._is_stale_lock()
    
    def _is_stale_lock(self) -> bool:
        """Verifica se lock é órfão"""
        if not os.path.exists(self.lock_file):
            return False
            
        try:
            with open(self.lock_file, 'r') as f:
                lines = f.read().strip().split('\n')
                
            if len(lines) < 2:
                return True  # Formato inválido
                
            pid = int(lines[0])
            timestamp = int(lines[1])
            hostname = lines[2] if len(lines) > 2 else ""
            process_name = lines[3] if len(lines) > 3 else ""
            
            # Verificar timeout
            if time.time() - timestamp > self.timeout:
                self.logger.warning(f"Lock timeout exceeded: {time.time() - timestamp}s")
                return True
            
            # Verificar se processo ainda existe
            if not psutil.pid_exists(pid):
                return True
                
            # Verificar se é nosso tipo de processo
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                if process_name not in cmdline and 'playlist_processor' not in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return True
                
            return False  # Lock válido
            
        except (ValueError, IOError, OSError) as e:
            self.logger.error(f"Error checking stale lock: {e}")
            return True  # Assumir órfão em caso de erro
    
    def _cleanup_stale_lock(self):
        """Remove lock órfão"""
        try:
            if os.path.exists(self.lock_file):
                os.unlink(self.lock_file)
                self.logger.info("Cleaned up stale lock file")
        except OSError as e:
            self.logger.error(f"Failed to cleanup stale lock: {e}")
    
    def _verify_ownership(self) -> bool:
        """Verifica se somos donos do lock"""
        try:
            with open(self.lock_file, 'r') as f:
                lines = f.read().strip().split('\n')
            return len(lines) > 0 and int(lines[0]) == os.getpid()
        except (ValueError, IOError, OSError):
            return False
    
    def get_lock_info(self) -> Optional[dict]:
        """Obtém informações do lock atual"""
        if not os.path.exists(self.lock_file):
            return None
            
        try:
            with open(self.lock_file, 'r') as f:
                lines = f.read().strip().split('\n')
                
            if len(lines) >= 2:
                return {
                    'pid': int(lines[0]),
                    'timestamp': int(lines[1]),
                    'hostname': lines[2] if len(lines) > 2 else 'unknown',
                    'process_name': lines[3] if len(lines) > 3 else 'unknown',
                    'age_seconds': int(time.time()) - int(lines[1])
                }
        except (ValueError, IOError, OSError):
            pass
            
        return None
    
    def force_release(self) -> bool:
        """Força liberação do lock (usar com cuidado)"""
        try:
            if os.path.exists(self.lock_file):
                os.unlink(self.lock_file)
                self.logger.warning("Lock forcefully released")
                return True
            return False
        except OSError as e:
            self.logger.error(f"Failed to force release lock: {e}")
            return False
    
    def __enter__(self):
        if not self.acquire():
            lock_info = self.get_lock_info()
            if lock_info:
                raise RuntimeError(f"Processo já rodando - PID: {lock_info['pid']}, Age: {lock_info['age_seconds']}s")
            else:
                raise RuntimeError("Não foi possível adquirir lock - processo já rodando")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
