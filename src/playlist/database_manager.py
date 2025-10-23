import sqlite3
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco SQLite com tabelas necessárias"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Tabela principal de downloads
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    filename TEXT,
                    filename_normalized TEXT,
                    file_line TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    requested_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Cache de buscas
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT,
                    results TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                );
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_filename_normalized ON downloads(filename_normalized);
                CREATE INDEX IF NOT EXISTS idx_file_line ON downloads(file_line);
                CREATE INDEX IF NOT EXISTS idx_status ON downloads(status);
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON search_cache(expires_at);
            """)
    
    def is_downloaded(self, file_line: str) -> bool:
        """Verificação básica por file_line"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE file_line = ? AND status = 'SUCCESS'",
                (file_line,)
            )
            return cursor.fetchone() is not None
    
    def is_duplicate_normalized(self, filename_norm: str) -> bool:
        """Verificação por filename normalizado"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE filename_normalized = ? AND status = 'SUCCESS'",
                (filename_norm,)
            )
            return cursor.fetchone() is not None
    
    def is_duplicate_hash(self, file_hash: str) -> bool:
        """Verificação por hash MD5"""
        if not file_hash:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE file_hash = ? AND status = 'SUCCESS'",
                (file_hash,)
            )
            return cursor.fetchone() is not None
    
    def save_download(self, data: Dict[str, Any], status: str):
        """Salva registro de download"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO downloads 
                (id, username, filename, filename_normalized, file_line, status, 
                 file_size, file_hash, requested_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('id', self._generate_id()),
                data.get('username', ''),
                data.get('filename', ''),
                data.get('filename_normalized', ''),
                data.get('file_line', ''),
                status,
                data.get('file_size', 0),
                data.get('file_hash', ''),
                data.get('requested_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))
    
    def get_cached_search(self, query_hash: str) -> Optional[List[Dict]]:
        """Busca resultado no cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT results, expires_at FROM search_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
                
            results_json, expires_at = row
            expires_dt = datetime.fromisoformat(expires_at)
            
            if datetime.now() > expires_dt:
                # Cache expirado
                conn.execute("DELETE FROM search_cache WHERE query_hash = ?", (query_hash,))
                return None
                
            return json.loads(results_json)
    
    def save_search_cache(self, query_hash: str, query_text: str, results: List[Dict], ttl_hours: int = 24):
        """Salva resultado no cache"""
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO search_cache 
                (query_hash, query_text, results, expires_at)
                VALUES (?, ?, ?, ?)
            """, (
                query_hash,
                query_text,
                json.dumps(results),
                expires_at.isoformat()
            ))
    
    def cleanup_expired_cache(self):
        """Remove cache expirado"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM search_cache WHERE expires_at < ?",
                (datetime.now().isoformat(),)
            )
    
    def get_stats(self) -> Dict[str, int]:
        """Estatísticas do banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM downloads 
                GROUP BY status
            """)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = row[1]
                
            # Cache stats
            cursor = conn.execute("SELECT COUNT(*) FROM search_cache")
            stats['cache_entries'] = cursor.fetchone()[0]
            
            return stats
    
    def _generate_id(self) -> str:
        """Gera ID único"""
        return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()
