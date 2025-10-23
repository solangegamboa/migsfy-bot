"""
Playlist Processor Module

Módulo para processamento automático de playlists via SLSKD.
Inclui controle de duplicatas, rate limiting e cache inteligente.
"""

__version__ = "1.0.0"
__author__ = "Solia Assistant"

# Importar apenas classes já implementadas
from .database_manager import DatabaseManager
from .duplicate_detector import DuplicateDetector
from .process_lock import ProcessLock

__all__ = [
    "DatabaseManager",
    "DuplicateDetector", 
    "ProcessLock"
]
