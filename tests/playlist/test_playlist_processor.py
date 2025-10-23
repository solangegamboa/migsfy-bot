import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.playlist.playlist_processor import PlaylistProcessor

class TestPlaylistProcessor:
    
    @pytest.fixture
    def mock_processor(self):
        """Cria PlaylistProcessor com componentes mockados"""
        with patch('src.playlist.playlist_processor.DatabaseManager') as mock_db:
            with patch('src.playlist.playlist_processor.DuplicateDetector') as mock_dup:
                with patch('src.playlist.playlist_processor.SlskdApiClient') as mock_api:
                    with patch('src.playlist.playlist_processor.ProcessLock') as mock_lock:
                        
                        # Configurar mocks
                        mock_db_instance = Mock()
                        mock_dup_instance = Mock()
                        mock_api_instance = Mock()
                        mock_lock_instance = Mock()
                        
                        mock_db.return_value = mock_db_instance
                        mock_dup.return_value = mock_dup_instance
                        mock_api.return_value = mock_api_instance
                        mock_lock.return_value = mock_lock_instance
                        
                        # Configurar context manager do lock
                        mock_lock_instance.__enter__ = Mock(return_value=mock_lock_instance)
                        mock_lock_instance.__exit__ = Mock(return_value=None)
                        
                        processor = PlaylistProcessor()
                        
                        yield processor, {
                            'db': mock_db_instance,
                            'dup': mock_dup_instance,
                            'api': mock_api_instance,
                            'lock': mock_lock_instance
                        }
    
    def test_init_with_env_vars(self):
        """Testa inicialização com variáveis de ambiente"""
        env_vars = {
            'PLAYLIST_PATH': '/test/playlists',
            'DATABASE_PATH': '/test/db.sqlite',
            'PROCESSOR_LOCK_PATH': '/test/lock.file',
            'FILE_PROCESSING_PAUSE_SECONDS': '60',
            'QUEUE_TIMEOUT_MINUTES': '10'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.playlist.playlist_processor.DatabaseManager'):
                with patch('src.playlist.playlist_processor.DuplicateDetector'):
                    with patch('src.playlist.playlist_processor.SlskdApiClient'):
                        with patch('src.playlist.playlist_processor.ProcessLock'):
                            processor = PlaylistProcessor()
                            
                            assert processor.playlist_path == '/test/playlists'
                            assert processor.db_path == '/test/db.sqlite'
                            assert processor.lock_path == '/test/lock.file'
                            assert processor.file_pause == 60
                            assert processor.queue_timeout == 10
    
    def test_process_single_line_duplicate(self, mock_processor):
        """Testa processamento de linha duplicada"""
        processor, mocks = mock_processor
        
        # Configurar mocks
        mocks['dup'].extract_artist_song.return_value = ("Artist", "Song")
        mocks['dup'].check_all_duplicates.return_value = (True, "exact_match")
        
        result = processor._process_single_line("Artist - Album - Song")
        
        # Deve retornar True (remove linha)
        assert result == True
        assert processor.stats['duplicates_found'] == 1
    
    def test_process_single_line_not_found(self, mock_processor):
        """Testa processamento de linha não encontrada"""
        processor, mocks = mock_processor
        
        # Configurar mocks
        mocks['dup'].extract_artist_song.return_value = ("Artist", "Song")
        mocks['dup'].check_all_duplicates.return_value = (False, "no_duplicate")
        
        with patch.object(processor, '_search_and_download', return_value="NOT_FOUND"):
            result = processor._process_single_line("Artist - Album - Song")
        
        # Deve retornar False (manter linha)
        assert result == False
        mocks['db'].save_download.assert_called_once()
    
    def test_process_single_line_success(self, mock_processor):
        """Testa processamento de linha com sucesso"""
        processor, mocks = mock_processor
        
        # Configurar mocks
        mocks['dup'].extract_artist_song.return_value = ("Artist", "Song")
        mocks['dup'].check_all_duplicates.return_value = (False, "no_duplicate")
        
        with patch.object(processor, '_search_and_download', return_value="SUCCESS"):
            result = processor._process_single_line("Artist - Album - Song")
        
        # Deve retornar True (remove linha)
        assert result == True
    
    def test_select_best_result_quality_priority(self, mock_processor):
        """Testa seleção do melhor resultado por qualidade"""
        processor, _ = mock_processor
        
        results = [
            {'filename': 'song1.flac', 'bitDepth': 16, 'sampleRate': 44100},  # Prioridade 2
            {'filename': 'song2.flac', 'bitDepth': 24, 'sampleRate': 96000},  # Prioridade 1
            {'filename': 'song3.flac', 'bitDepth': 24, 'sampleRate': 48000},  # Prioridade 3
        ]
        
        best = processor._select_best_result(results)
        
        # Deve selecionar 24bit/96kHz
        assert best['filename'] == 'song2.flac'
        assert best['bitDepth'] == 24
        assert best['sampleRate'] == 96000
    
    def test_select_best_result_filter_remix(self, mock_processor):
        """Testa filtro de remix"""
        processor, _ = mock_processor
        
        results = [
            {'filename': 'song (remix).flac', 'bitDepth': 24, 'sampleRate': 96000},
            {'filename': 'song.flac', 'bitDepth': 16, 'sampleRate': 44100},
        ]
        
        best = processor._select_best_result(results)
        
        # Deve filtrar remix e selecionar o normal
        assert best['filename'] == 'song.flac'
        assert 'remix' not in best['filename'].lower()
    
    def test_find_existing_download(self, mock_processor):
        """Testa busca de download existente na fila"""
        processor, _ = mock_processor
        
        queue = [
            {
                'username': 'user1',
                'directories': [
                    {
                        'files': [
                            {'id': '123', 'filename': 'song1.flac'},
                            {'id': '456', 'filename': 'song2.flac'}
                        ]
                    }
                ]
            }
        ]
        
        # Encontrar existente
        existing = processor._find_existing_download(queue, 'user1', 'song1.flac')
        assert existing['id'] == '123'
        
        # Não encontrar
        not_found = processor._find_existing_download(queue, 'user1', 'nonexistent.flac')
        assert not_found is None
    
    def test_wait_for_queue_change_success(self, mock_processor):
        """Testa aguardar mudança de status da fila com sucesso"""
        processor, mocks = mock_processor
        
        # Mock status mudando de "Queued, Remotely" para "InProgress"
        mocks['api'].get_download_status.side_effect = [
            {'state': 'Queued, Remotely'},
            {'state': 'InProgress'}
        ]
        
        result = processor._wait_for_queue_change('download-123', 30)
        
        assert result == True
        assert mocks['api'].get_download_status.call_count == 2
    
    def test_wait_for_queue_change_timeout(self, mock_processor):
        """Testa timeout na mudança de status da fila"""
        processor, mocks = mock_processor
        
        # Mock status sempre "Queued, Remotely"
        mocks['api'].get_download_status.return_value = {'state': 'Queued, Remotely'}
        
        with patch('time.sleep'):  # Acelerar teste
            result = processor._wait_for_queue_change('download-123', 1)  # 1 segundo timeout
        
        assert result == False
    
    def test_handle_download_success(self, mock_processor):
        """Testa tratamento de sucesso do download"""
        processor, mocks = mock_processor
        
        download_info = {'id': '123', 'username': 'user1', 'filename': 'song.flac'}
        result = {'size': 1000000}
        
        mocks['dup'].normalize_filename.return_value = 'song'
        
        processor._handle_download_success('Artist - Song', download_info, result)
        
        # Verificar salvamento no banco
        mocks['db'].save_download.assert_called_once()
        save_args = mocks['db'].save_download.call_args[0]
        assert save_args[1] == 'SUCCESS'  # Status
        
        # Verificar remoção da fila
        mocks['api'].remove_download.assert_called_once_with('123')
        
        # Verificar estatísticas
        assert processor.stats['downloads_completed'] == 1
    
    def test_handle_download_error(self, mock_processor):
        """Testa tratamento de erro do download"""
        processor, mocks = mock_processor
        
        download_info = {'id': '123', 'username': 'user1', 'filename': 'song.flac'}
        
        processor._handle_download_error('Artist - Song', download_info, 'Connection failed')
        
        # Verificar salvamento do erro
        mocks['db'].save_download.assert_called_once()
        save_args = mocks['db'].save_download.call_args[0]
        assert save_args[1] == 'ERROR'  # Status
        
        # Verificar remoção da fila
        mocks['api'].remove_download.assert_called_once_with('123')
        
        # Verificar estatísticas
        assert processor.stats['errors'] == 1
    
    def test_update_playlist_file(self, mock_processor):
        """Testa atualização do arquivo de playlist"""
        processor, _ = mock_processor
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_path = f.name
        
        try:
            # Atualizar com apenas 2 linhas
            remaining_lines = ["Line 1", "Line 3"]
            processor._update_playlist_file(temp_path, remaining_lines)
            
            # Verificar conteúdo
            with open(temp_path, 'r') as f:
                content = f.read().strip()
                assert content == "Line 1\nLine 3"
                
        finally:
            os.unlink(temp_path)
