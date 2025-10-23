"""
Testes de Integração Completos - Playlist Processor
Testa todo o fluxo end-to-end do sistema
"""

import pytest
import tempfile
import os
import time
import sqlite3
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Imports do sistema
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.playlist.playlist_processor import PlaylistProcessor
from src.playlist.database_manager import DatabaseManager
from src.playlist.process_lock import ProcessLock
from src.playlist.slskd_api_client import SlskdApiClient
from src.playlist.duplicate_detector import DuplicateDetector
from src.playlist.rate_limiter import RateLimiter
from src.playlist.cache_manager import CacheManager


class TestPlaylistProcessorIntegration:
    """Testes de integração completos"""
    
    @pytest.fixture
    def temp_env(self):
        """Ambiente temporário para testes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Estrutura de diretórios
            playlist_dir = temp_path / "playlists"
            data_dir = temp_path / "data"
            logs_dir = temp_path / "logs"
            
            playlist_dir.mkdir()
            data_dir.mkdir()
            logs_dir.mkdir()
            
            # Arquivos de configuração
            db_path = data_dir / "downloads.db"
            lock_path = data_dir / "processor.lock"
            
            yield {
                'temp_dir': temp_path,
                'playlist_dir': playlist_dir,
                'data_dir': data_dir,
                'logs_dir': logs_dir,
                'db_path': str(db_path),
                'lock_path': str(lock_path)
            }
    
    @pytest.fixture
    def sample_playlist(self, temp_env):
        """Playlist de exemplo para testes"""
        playlist_file = temp_env['playlist_dir'] / "test_playlist.txt"
        
        content = [
            "Soundgarden - Superunknown - Black Hole Sun",
            "Pearl Jam - Ten - Alive",
            "Nirvana - Nevermind - Smells Like Teen Spirit",
            "Alice in Chains - Dirt - Man in the Box",
            "Stone Temple Pilots - Core - Interstate Love Song"
        ]
        
        playlist_file.write_text('\n'.join(content))
        return str(playlist_file)
    
    @pytest.fixture
    def mock_slskd_api(self):
        """Mock do SLSKD API com respostas realistas"""
        mock_api = Mock()
        
        # Mock search results
        mock_search_results = [
            {
                'username': 'user1',
                'filename': '/music/Soundgarden/Superunknown/01 - Black Hole Sun.flac',
                'size': 45000000,
                'bitrate': 1411,
                'sample_rate': 44100,
                'bit_depth': 16
            },
            {
                'username': 'user2', 
                'filename': '/music/Pearl Jam/Ten/02 - Alive.flac',
                'size': 52000000,
                'bitrate': 1411,
                'sample_rate': 44100,
                'bit_depth': 16
            }
        ]
        
        mock_api.search_tracks.return_value = mock_search_results
        
        # Mock download queue
        mock_api.get_download_queue.return_value = []
        
        # Mock download initiation
        mock_api.add_download.return_value = {'id': 'download_123'}
        
        # Mock download status
        mock_api.get_download_status.return_value = {
            'id': 'download_123',
            'status': 'Completed, Succeeded',
            'filename': '/music/Soundgarden/Superunknown/01 - Black Hole Sun.flac'
        }
        
        return mock_api
    
    def test_basic_functionality(self, temp_env):
        """Teste básico de funcionalidade"""
        # Teste simples para verificar se os imports funcionam
        db_manager = DatabaseManager(temp_env['db_path'])
        assert db_manager is not None
        
        lock = ProcessLock(temp_env['lock_path'])
        assert lock is not None
        
        # Teste de aquisição de lock
        assert lock.acquire() == True
        lock.release()
    
    def test_database_operations(self, temp_env):
        """Teste de operações do banco"""
        db_manager = DatabaseManager(temp_env['db_path'])
        
        # Salvar download
        data = {
            'id': 'test-123',
            'username': 'testuser',
            'filename': 'test.flac',
            'file_line': 'Test - Song - Title'
        }
        
        db_manager.save_download(data, 'SUCCESS')
        
        # Verificar se foi salvo
        assert db_manager.is_downloaded('Test - Song - Title') == True
        assert db_manager.is_downloaded('Non-existent') == False
    
    def test_duplicate_detection_integration(self, temp_env):
        """Teste de integração da detecção de duplicatas"""
        db_manager = DatabaseManager(temp_env['db_path'])
        detector = DuplicateDetector(db_manager)
        
        # Adicionar música no banco
        db_manager.save_download({
            'file_line': 'Soundgarden - Superunknown - Black Hole Sun'
        }, 'SUCCESS')
        
        # Testar detecção
        is_dup, reason = detector.check_all_duplicates(
            'Soundgarden - Superunknown - Black Hole Sun',
            'black_hole_sun.flac',
            'Soundgarden',
            'Black Hole Sun'
        )
        
        assert is_dup == True
        assert reason == 'exact_line_match'
    
    def test_cache_integration(self, temp_env):
        """Teste de integração do cache"""
        db_manager = DatabaseManager(temp_env['db_path'])
        cache_manager = CacheManager(db_manager)
        
        # Salvar no cache
        query = "test query"
        results = [{'filename': 'test.flac'}]
        
        cache_manager.save_results(query, results)
        
        # Recuperar do cache
        cached = cache_manager.get_cached_results(query)
        assert cached == results
    
    def test_rate_limiter_integration(self, temp_env):
        """Teste de integração do rate limiter"""
        limiter = RateLimiter(min_interval=0.1)  # Intervalo pequeno para teste
        
        start_time = time.time()
        
        # Primeira chamada
        limiter.wait_if_needed()
        
        # Segunda chamada deve esperar
        limiter.wait_if_needed()
        
        elapsed = time.time() - start_time
        assert elapsed >= 0.1  # Deve ter esperado pelo menos o intervalo
    
    def test_process_lock_integration(self, temp_env):
        """Teste de integração do process lock"""
        lock1 = ProcessLock(temp_env['lock_path'])
        lock2 = ProcessLock(temp_env['lock_path'])
        
        # Primeiro lock deve conseguir
        assert lock1.acquire() == True
        
        # Segundo lock deve falhar
        assert lock2.acquire() == False
        
        # Verificar informações do lock
        info = lock1.get_lock_info()
        assert info is not None
        assert info['pid'] == os.getpid()
        
        # Liberar
        lock1.release()
        
        # Agora segundo deve conseguir
        assert lock2.acquire() == True
        lock2.release()
    
    @pytest.mark.slow
    def test_performance_basic(self, temp_env):
        """Teste básico de performance"""
        db_manager = DatabaseManager(temp_env['db_path'])
        
        # Adicionar muitos registros
        start_time = time.time()
        
        for i in range(100):
            db_manager.save_download({
                'file_line': f'Artist {i} - Album {i} - Song {i}'
            }, 'SUCCESS')
        
        elapsed = time.time() - start_time
        
        # Deve ser rápido (menos de 2 segundos para 100 registros)
        assert elapsed < 2.0
        
        # Verificar que todos foram salvos
        stats = db_manager.get_stats()
        assert stats['SUCCESS'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
