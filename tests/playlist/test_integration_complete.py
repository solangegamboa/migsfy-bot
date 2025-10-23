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

from playlist.playlist_processor import PlaylistProcessor
from playlist.database_manager import DatabaseManager
from playlist.process_lock import ProcessLock
from playlist.slskd_api_client import SlskdApiClient
from playlist.duplicate_detector import DuplicateDetector
from playlist.rate_limiter import RateLimiter
from playlist.cache_manager import CacheManager


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
    
    def test_full_workflow_success(self, temp_env, sample_playlist, mock_slskd_api):
        """Teste do fluxo completo com sucesso"""
        
        # Setup
        db_manager = DatabaseManager(temp_env['db_path'])
        db_manager.init_database()
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            # Configurar environment variables
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'SLSKD_API_KEY': 'test_key',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path'],
                'RATE_LIMIT_SECONDS': '1',
                'CACHE_TTL_HOURS': '1'
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                
                # Executar processamento
                result = processor.process_all_playlists()
                
                # Verificações
                assert result['success'] is True
                assert result['processed_files'] > 0
                assert result['total_downloads'] > 0
                
                # Verificar banco de dados
                downloads = db_manager.get_all_downloads()
                assert len(downloads) > 0
                
                # Verificar que algumas músicas foram processadas
                success_downloads = [d for d in downloads if d['status'] == 'SUCCESS']
                assert len(success_downloads) > 0
    
    def test_duplicate_detection_workflow(self, temp_env, mock_slskd_api):
        """Teste do fluxo de detecção de duplicatas"""
        
        # Criar playlist com duplicatas
        playlist_file = temp_env['playlist_dir'] / "duplicates.txt"
        content = [
            "Soundgarden - Superunknown - Black Hole Sun",
            "Soundgarden - Superunknown - Black Hole Sun",  # Duplicata exata
            "Soundgarden - Singles - Black Hole Sun",       # Duplicata similar
        ]
        playlist_file.write_text('\n'.join(content))
        
        # Setup
        db_manager = DatabaseManager(temp_env['db_path'])
        db_manager.init_database()
        
        # Adicionar entrada prévia no banco
        db_manager.save_download({
            'id': 'existing_1',
            'username': 'user1',
            'filename': '/music/Soundgarden/Black Hole Sun.flac',
            'file_line': 'Soundgarden - Superunknown - Black Hole Sun',
            'status': 'SUCCESS'
        })
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path']
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                result = processor.process_all_playlists()
                
                # Verificar que duplicatas foram detectadas
                downloads = db_manager.get_all_downloads()
                
                # Deve ter apenas 1 entrada (a original)
                # As duplicatas devem ter sido puladas
                assert len(downloads) == 1
                assert result['skipped_duplicates'] >= 2
    
    def test_rate_limiting_workflow(self, temp_env, sample_playlist, mock_slskd_api):
        """Teste do fluxo com rate limiting"""
        
        start_time = time.time()
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path'],
                'RATE_LIMIT_SECONDS': '2'  # 2 segundos entre requests
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                result = processor.process_all_playlists()
                
                # Verificar que rate limiting foi aplicado
                elapsed_time = time.time() - start_time
                expected_min_time = (result['total_searches'] - 1) * 2  # 2s entre cada busca
                
                assert elapsed_time >= expected_min_time
                assert result['success'] is True
    
    def test_process_lock_workflow(self, temp_env, sample_playlist):
        """Teste do fluxo com process lock"""
        
        lock = ProcessLock(temp_env['lock_path'])
        
        # Primeiro processo adquire lock
        assert lock.acquire() is True
        
        # Segundo processo não consegue adquirir
        lock2 = ProcessLock(temp_env['lock_path'])
        assert lock2.acquire() is False
        
        # Verificar informações do lock
        lock_info = lock.get_lock_info()
        assert lock_info is not None
        assert lock_info['pid'] == os.getpid()
        
        # Liberar lock
        lock.release()
        
        # Agora segundo processo consegue adquirir
        assert lock2.acquire() is True
        lock2.release()
    
    def test_error_handling_workflow(self, temp_env, sample_playlist):
        """Teste do fluxo com tratamento de erros"""
        
        # Mock API que falha
        mock_api = Mock()
        mock_api.search_tracks.side_effect = Exception("API Error")
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_api
            
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path']
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                result = processor.process_all_playlists()
                
                # Deve falhar graciosamente
                assert result['success'] is False
                assert result['errors'] > 0
                assert 'error_details' in result
    
    def test_cache_workflow(self, temp_env, sample_playlist, mock_slskd_api):
        """Teste do fluxo com cache"""
        
        db_manager = DatabaseManager(temp_env['db_path'])
        db_manager.init_database()
        cache_manager = CacheManager(db_manager)
        
        # Primeira busca - deve chamar API
        query = "Soundgarden Black Hole Sun *.flac"
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            # Primeira execução
            results1 = cache_manager.get_cached_results(query)
            if not results1:
                results1 = mock_slskd_api.search_tracks(query)
                cache_manager.save_results(query, results1)
            
            # Segunda execução - deve usar cache
            results2 = cache_manager.get_cached_results(query)
            
            assert results1 == results2
            assert mock_slskd_api.search_tracks.call_count == 1  # Chamado apenas uma vez
    
    def test_database_consistency(self, temp_env, sample_playlist, mock_slskd_api):
        """Teste de consistência do banco de dados"""
        
        db_manager = DatabaseManager(temp_env['db_path'])
        db_manager.init_database()
        
        # Simular múltiplas execuções
        for i in range(3):
            with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
                mock_slskd_class.return_value = mock_slskd_api
                
                env_vars = {
                    'SLSKD_HOST': 'localhost',
                    'SLSKD_PORT': '5030',
                    'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                    'DATABASE_PATH': temp_env['db_path']
                }
                
                with patch.dict(os.environ, env_vars):
                    processor = PlaylistProcessor()
                    processor.process_all_playlists()
        
        # Verificar consistência
        downloads = db_manager.get_all_downloads()
        
        # Não deve haver duplicatas no banco
        file_lines = [d['file_line'] for d in downloads]
        assert len(file_lines) == len(set(file_lines))
        
        # Verificar integridade dos dados
        for download in downloads:
            assert download['id'] is not None
            assert download['file_line'] is not None
            assert download['status'] in ['SUCCESS', 'ERROR', 'NOT_FOUND']
    
    def test_performance_metrics(self, temp_env, sample_playlist, mock_slskd_api):
        """Teste de métricas de performance"""
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path'],
                'ENABLE_PERFORMANCE_METRICS': 'true'
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                result = processor.process_all_playlists()
                
                # Verificar métricas
                assert 'performance_metrics' in result
                metrics = result['performance_metrics']
                
                assert 'total_execution_time' in metrics
                assert 'average_search_time' in metrics
                assert 'cache_hit_rate' in metrics
                assert 'database_operations' in metrics
                
                # Verificar valores razoáveis
                assert metrics['total_execution_time'] > 0
                assert 0 <= metrics['cache_hit_rate'] <= 1
    
    def test_cleanup_workflow(self, temp_env):
        """Teste do fluxo de limpeza"""
        
        db_manager = DatabaseManager(temp_env['db_path'])
        db_manager.init_database()
        
        # Adicionar dados antigos
        old_timestamp = int(time.time()) - (30 * 24 * 3600)  # 30 dias atrás
        
        # Cache expirado
        db_manager.save_search_cache(
            'old_query_hash',
            {'results': []},
            ttl_hours=-1  # Já expirado
        )
        
        # Downloads antigos
        db_manager.save_download({
            'id': 'old_download',
            'username': 'user1',
            'filename': 'old_file.flac',
            'file_line': 'Old - Song - Title',
            'status': 'SUCCESS',
            'created_at': old_timestamp
        })
        
        env_vars = {
            'DATABASE_PATH': temp_env['db_path'],
            'AUTO_CLEANUP_CACHE': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            processor = PlaylistProcessor()
            cleanup_result = processor.cleanup()
            
            # Verificar limpeza
            assert cleanup_result['cache_cleaned'] > 0
            assert cleanup_result['success'] is True
    
    @pytest.mark.slow
    def test_stress_test(self, temp_env, mock_slskd_api):
        """Teste de stress com muitas músicas"""
        
        # Criar playlist grande
        playlist_file = temp_env['playlist_dir'] / "stress_test.txt"
        
        # 100 músicas diferentes
        content = []
        for i in range(100):
            content.append(f"Artist{i} - Album{i} - Song{i}")
        
        playlist_file.write_text('\n'.join(content))
        
        with patch('playlist.slskd_api_client.SlskdApi') as mock_slskd_class:
            mock_slskd_class.return_value = mock_slskd_api
            
            env_vars = {
                'SLSKD_HOST': 'localhost',
                'SLSKD_PORT': '5030',
                'PLAYLIST_PATH': str(temp_env['playlist_dir']),
                'DATABASE_PATH': temp_env['db_path'],
                'RATE_LIMIT_SECONDS': '0.1'  # Rate limiting mínimo para teste
            }
            
            with patch.dict(os.environ, env_vars):
                processor = PlaylistProcessor()
                
                start_time = time.time()
                result = processor.process_all_playlists()
                execution_time = time.time() - start_time
                
                # Verificar que processou todas as músicas
                assert result['processed_lines'] == 100
                assert execution_time < 300  # Menos de 5 minutos
                
                # Verificar uso de memória (aproximado)
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                assert memory_mb < 500  # Menos de 500MB


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
