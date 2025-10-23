import os
import time
import fcntl
from typing import Optional

class ProcessLock:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.lock_fd: Optional[int] = None
        
    def acquire(self) -> bool:
        """Adquire lock exclusivo"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
            
            # Abrir arquivo de lock
            self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            
            # Tentar adquirir lock não-bloqueante
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Escrever PID no arquivo
            os.write(self.lock_fd, f"{os.getpid()}\n{int(time.time())}".encode())
            os.fsync(self.lock_fd)
            
            return True
            
        except (OSError, IOError):
            if self.lock_fd:
                os.close(self.lock_fd)
                self.lock_fd = None
            return False
    
    def release(self):
        """Libera lock"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                os.unlink(self.lock_file)
            except (OSError, IOError):
                pass
            finally:
                self.lock_fd = None
    
    def is_locked(self) -> bool:
        """Verifica se processo está ativo"""
        if not os.path.exists(self.lock_file):
            return False
            
        try:
            with open(self.lock_file, 'r') as f:
                content = f.read().strip().split('\n')
                if len(content) >= 1:
                    pid = int(content[0])
                    
                    # Verificar se processo ainda existe
                    try:
                        os.kill(pid, 0)  # Não mata, apenas verifica
                        return True
                    except OSError:
                        # Processo morto, remover lock órfão
                        os.unlink(self.lock_file)
                        return False
                        
        except (ValueError, IOError, OSError):
            # Arquivo corrompido, remover
            try:
                os.unlink(self.lock_file)
            except OSError:
                pass
                
        return False
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Não foi possível adquirir lock - processo já rodando")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
