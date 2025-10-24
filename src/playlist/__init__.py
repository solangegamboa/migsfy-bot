"""
Playlist Processor Module

Módulo para processamento automático de playlists via SLSKD.
Inclui controle de duplicatas, rate limiting e cache inteligente.
"""

__version__ = "1.0.0"
__author__ = "Solia Assistant"

# Importar classes implementadas
from .database_manager import DatabaseManager
from .duplicate_detector import DuplicateDetector
from .file_organizer import FileOrganizer
from .process_lock import ProcessLock
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager
from .slskd_api_client import SlskdApiClient
from .playlist_processor import PlaylistProcessor

__all__ = [
    "DatabaseManager",
    "DuplicateDetector",
    "FileOrganizer", 
    "ProcessLock",
    "RateLimiter",
    "CacheManager",
    "SlskdApiClient",
    "PlaylistProcessor"
]
