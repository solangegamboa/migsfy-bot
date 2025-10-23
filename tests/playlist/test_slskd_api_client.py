import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.playlist.database_manager import DatabaseManager
from src.playlist.slskd_api_client import SlskdApiClient

class TestSlskdApiClient:
    
    @pytest.fixture
    def mock_api_client(self):
        """Cria SlskdApiClient com API mockada"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        db.init_database()
        
        with patch('slskd_api.SlskdApi') as mock_slskd:
            mock_api_instance = Mock()
            mock_slskd.return_value = mock_api_instance
            
            client = SlskdApiClient(db)
            client.api = mock_api_instance
            
            yield client, mock_api_instance
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_init_with_env_vars(self):
        """Testa inicialização com variáveis de ambiente"""
        env_vars = {
            'SLSKD_HOST': 'test-host',
            'SLSKD_PORT': '9999',
            'SLSKD_API_KEY': 'test-key',
            'SLSKD_URL_BASE': 'http://test-host:9999'
        }
        
        with patch.dict(os.environ, env_vars):
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                db_path = f.name
            
            db = DatabaseManager(db_path)
            db.init_database()
            
            with patch('slskd_api.SlskdApi'):
                client = SlskdApiClient(db)
                
                assert client.host == 'test-host'
                assert client.port == 9999
                assert client.api_key == 'test-key'
    
    def test_search_tracks_basic(self, mock_api_client):
        """Testa busca básica de tracks"""
        client, mock_api = mock_api_client
        
        # Mock dos resultados
        mock_results = [
            {
                'username': 'user1',
                'filename': '/music/Artist/Album/01 - Song.flac',
                'size': 45000000,
                'bitrate': 1411,
                'sample_rate': 44100,
                'bit_depth': 16
            }
        ]
        
        mock_api.searches.search_text.return_value = mock_results
        
        results = client.search_tracks("Artist Song *.flac")
        
        assert len(results) == 1
        assert results[0]['username'] == 'user1'
        mock_api.searches.search_text.assert_called_once_with("Artist Song *.flac")
    
    def test_search_tracks_with_cache(self, mock_api_client):
        """Testa busca com cache"""
        client, mock_api = mock_api_client
        
        # Primeira busca - deve chamar API
        mock_results = [{'filename': 'test.flac', 'username': 'user1'}]
        mock_api.searches.search_text.return_value = mock_results
        
        results1 = client.search_tracks_cached("test query")
        assert results1 == mock_results
        assert mock_api.searches.search_text.call_count == 1
        
        # Segunda busca - deve usar cache
        results2 = client.search_tracks_cached("test query")
        assert results2 == mock_results
        assert mock_api.searches.search_text.call_count == 1  # Não deve chamar novamente
    
    def test_search_with_multiple_patterns(self, mock_api_client):
        """Testa busca com múltiplos padrões"""
        client, mock_api = mock_api_client
        
        # Primeira busca falha, segunda sucede
        mock_api.searches.search_text.side_effect = [[], [{'filename': 'found.flac'}]]
        
        results = client.search_with_patterns("Artist", "Album", "Song")
        
        assert len(results) == 1
        assert results[0]['filename'] == 'found.flac'
        assert mock_api.searches.search_text.call_count == 2
    
    def test_filter_results_quality(self, mock_api_client):
        """Testa filtro de qualidade"""
        client, mock_api = mock_api_client
        
        results = [
            {'filename': 'song.mp3', 'size': 5000000},      # Não FLAC
            {'filename': 'song_remix.flac', 'size': 45000000},  # Remix
            {'filename': 'song.flac', 'size': 45000000},    # OK
            {'filename': 'song_24bit.flac', 'size': 80000000}  # Alta qualidade
        ]
        
        filtered = client.filter_results(results)
        
        # Deve manter apenas FLACs não-remix
        assert len(filtered) == 2
        filenames = [r['filename'] for r in filtered]
        assert 'song.flac' in filenames
        assert 'song_24bit.flac' in filenames
    
    def test_prioritize_by_quality(self, mock_api_client):
        """Testa priorização por qualidade"""
        client, mock_api = mock_api_client
        
        results = [
            {'filename': 'song_16bit.flac', 'size': 45000000},   # 16-bit
            {'filename': 'song_24bit.flac', 'size': 80000000},   # 24-bit (melhor)
            {'filename': 'song_low.flac', 'size': 20000000}      # Baixa qualidade
        ]
        
        prioritized = client.prioritize_by_quality(results)
        
        # 24-bit deve vir primeiro
        assert prioritized[0]['filename'] == 'song_24bit.flac'
    
    def test_get_download_queue(self, mock_api_client):
        """Testa obtenção da fila de downloads"""
        client, mock_api = mock_api_client
        
        mock_queue = [
            {'id': 'dl1', 'filename': 'song1.flac', 'status': 'InProgress'},
            {'id': 'dl2', 'filename': 'song2.flac', 'status': 'Queued'}
        ]
        
        mock_api.transfers.get_downloads.return_value = mock_queue
        
        queue = client.get_download_queue()
        
        assert len(queue) == 2
        assert queue[0]['id'] == 'dl1'
    
    def test_add_download(self, mock_api_client):
        """Testa adição de download"""
        client, mock_api = mock_api_client
        
        mock_api.transfers.download.return_value = {'id': 'new_download_123'}
        
        download_id = client.add_download('user1', '/path/to/song.flac')
        
        assert download_id == 'new_download_123'
        mock_api.transfers.download.assert_called_once_with(
            username='user1', 
            filename='/path/to/song.flac'
        )
    
    def test_get_download_status(self, mock_api_client):
        """Testa obtenção de status de download"""
        client, mock_api = mock_api_client
        
        mock_status = {
            'id': 'dl123',
            'status': 'Completed, Succeeded',
            'filename': 'song.flac'
        }
        
        mock_api.transfers.get_download.return_value = mock_status
        
        status = client.get_download_status('dl123')
        
        assert status['status'] == 'Completed, Succeeded'
        mock_api.transfers.get_download.assert_called_once_with('dl123')
    
    def test_remove_download(self, mock_api_client):
        """Testa remoção de download"""
        client, mock_api = mock_api_client
        
        client.remove_download('dl123')
        
        mock_api.transfers.cancel_download.assert_called_once_with('dl123')
    
    def test_error_handling(self, mock_api_client):
        """Testa tratamento de erros"""
        client, mock_api = mock_api_client
        
        # Simular erro na API
        mock_api.searches.search_text.side_effect = Exception("API Error")
        
        results = client.search_tracks("test query")
        
        # Deve retornar lista vazia em caso de erro
        assert results == []
    
    def test_rate_limiting_integration(self, mock_api_client):
        """Testa integração com rate limiting"""
        client, mock_api = mock_api_client
        
        with patch.object(client.rate_limiter, 'wait_if_needed') as mock_wait:
            client.search_tracks("test query")
            
            # Deve ter aplicado rate limiting
            mock_wait.assert_called_once()
    
    def test_server_overload_detection(self, mock_api_client):
        """Testa detecção de sobrecarga do servidor"""
        client, mock_api = mock_api_client
        
        # Simular muitas falhas consecutivas
        mock_api.searches.search_text.side_effect = Exception("Server Error")
        
        # Múltiplas tentativas devem triggerar detecção de sobrecarga
        for _ in range(5):
            client.search_tracks("test")
        
        # Verificar se rate limiter registrou as falhas
        assert client.rate_limiter.consecutive_failures > 0
                assert client.port == 9999
                assert client.api_key == 'test-key'
                assert client.base_url == 'http://test-host:9999'
            
            os.unlink(db_path)
    
    def test_process_search_results(self, mock_api_client):
        """Testa processamento de resultados de busca"""
        client, _ = mock_api_client
        
        raw_results = [
            {
                'username': 'user1',
                'filename': 'song1.flac',
                'size': 1000000,
                'bitDepth': 24,
                'sampleRate': 96000,
                'bitRate': 2304
            },
            {
                'username': 'user2',
                'filename': 'song2.flac',
                'size': 500000,
                'bitDepth': 16,
                'sampleRate': 44100
            }
        ]
        
        processed = client._process_search_results(raw_results)
        
        assert len(processed) == 2
        assert processed[0]['username'] == 'user1'
        assert processed[0]['bitDepth'] == 24
        assert processed[1]['bitRate'] == 0  # Campo ausente deve ser 0
    
    def test_search_tracks_cached_hit(self, mock_api_client):
        """Testa busca com cache hit"""
        client, mock_api = mock_api_client
        
        query = "test query"
        cached_results = [{'filename': 'cached.flac'}]
        
        # Pré-popular cache
        client.cache_manager.save_results(query, cached_results)
        
        results = client.search_tracks_cached(query)
        
        # Deve retornar do cache
        assert results == cached_results
        
        # API não deve ter sido chamada
        mock_api.searches.search_text.assert_not_called()
    
    def test_search_tracks_cached_miss(self, mock_api_client):
        """Testa busca com cache miss"""
        client, mock_api = mock_api_client
        
        query = "uncached query"
        api_results = [{'username': 'user1', 'filename': 'found.flac'}]
        
        # Mock da resposta da API
        mock_api.searches.search_text.return_value = api_results
        
        with patch.object(client.rate_limiter, 'wait_if_needed'):
            with patch.object(client.rate_limiter, 'record_request'):
                results = client.search_tracks_cached(query)
        
        # Deve ter chamado a API
        mock_api.searches.search_text.assert_called_once_with(query)
        
        # Deve ter processado os resultados
        assert len(results) == 1
        assert results[0]['filename'] == 'found.flac'
    
    def test_search_with_rate_limit_error(self, mock_api_client):
        """Testa busca com erro de rate limit"""
        client, mock_api = mock_api_client
        
        # Mock rate limit error seguido de sucesso
        mock_api.searches.search_text.side_effect = [
            Exception("Rate limit exceeded"),
            [{'username': 'user1', 'filename': 'success.flac'}]
        ]
        
        with patch.object(client.rate_limiter, 'wait_if_needed'):
            with patch.object(client.rate_limiter, 'handle_rate_limit_error'):
                with patch.object(client.rate_limiter, 'record_request'):
                    results = client._search_tracks_raw("test query")
        
        # Deve ter tentado 2 vezes
        assert mock_api.searches.search_text.call_count == 2
        
        # Deve ter retornado resultado da segunda tentativa
        assert len(results) == 1
        assert results[0]['filename'] == 'success.flac'
    
    def test_get_download_queue(self, mock_api_client):
        """Testa obtenção da fila de downloads"""
        client, mock_api = mock_api_client
        
        expected_queue = [{'id': '123', 'filename': 'test.flac'}]
        mock_api.transfers.get_downloads.return_value = expected_queue
        
        queue = client.get_download_queue()
        
        assert queue == expected_queue
        mock_api.transfers.get_downloads.assert_called_once()
    
    def test_add_download(self, mock_api_client):
        """Testa adição de download"""
        client, mock_api = mock_api_client
        
        mock_api.transfers.download.return_value = {'id': 'download-123'}
        
        download_id = client.add_download('user1', 'song.flac')
        
        assert download_id == 'download-123'
        mock_api.transfers.download.assert_called_once_with(
            username='user1', 
            filename='song.flac'
        )
    
    def test_remove_download(self, mock_api_client):
        """Testa remoção de download"""
        client, mock_api = mock_api_client
        
        success = client.remove_download('download-123')
        
        assert success == True
        mock_api.transfers.cancel_download.assert_called_once_with('download-123')
    
    def test_get_download_status(self, mock_api_client):
        """Testa obtenção de status de download"""
        client, mock_api = mock_api_client
        
        expected_status = {'id': '123', 'state': 'InProgress'}
        mock_api.transfers.get_download.return_value = expected_status
        
        status = client.get_download_status('123')
        
        assert status == expected_status
        mock_api.transfers.get_download.assert_called_once_with('123')
    
    def test_is_server_overloaded(self, mock_api_client):
        """Testa detecção de sobrecarga do servidor"""
        client, _ = mock_api_client
        
        # Inicialmente não sobrecarregado
        assert client.is_server_overloaded() == False
        
        # Simular falhas consecutivas
        client.consecutive_failures = 5
        assert client.is_server_overloaded() == True
    
    def test_get_connection_stats(self, mock_api_client):
        """Testa estatísticas de conexão"""
        client, _ = mock_api_client
        
        stats = client.get_connection_stats()
        
        assert 'host' in stats
        assert 'port' in stats
        assert 'consecutive_failures' in stats
        assert 'is_overloaded' in stats
        assert 'cache_stats' in stats
        
        assert stats['consecutive_failures'] == 0
        assert stats['is_overloaded'] == False
