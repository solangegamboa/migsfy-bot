import os
import glob
import time
from typing import List, Dict, Optional, Tuple
from .database_manager import DatabaseManager
from .duplicate_detector import DuplicateDetector
from .process_lock import ProcessLock
from .slskd_api_client import SlskdApiClient

class PlaylistProcessor:
    def __init__(self):
        # Configurações do .env
        self.playlist_path = os.getenv('PLAYLIST_PATH', '/app/data/playlists')
        self.db_path = os.getenv('DATABASE_PATH', '/app/data/downloads.db')
        self.lock_path = os.getenv('PROCESSOR_LOCK_PATH', '/app/processor.lock')
        self.file_pause = int(os.getenv('FILE_PROCESSING_PAUSE_SECONDS', 30))
        self.queue_timeout = int(os.getenv('QUEUE_TIMEOUT_MINUTES', 5))
        
        # Inicializar componentes
        self.db_manager = DatabaseManager(self.db_path)
        self.duplicate_detector = DuplicateDetector(self.db_manager)
        self.slskd_client = SlskdApiClient(self.db_manager)
        self.process_lock = ProcessLock(self.lock_path)
        
        # Estatísticas
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'downloads_started': 0,
            'downloads_completed': 0,
            'duplicates_found': 0,
            'errors': 0
        }
    
    def process_all_playlists(self):
        """Processa todas as playlists na pasta"""
        try:
            with self.process_lock:
                print("🎵 Iniciando processamento de playlists...")
                
                # Listar arquivos .txt
                playlist_files = glob.glob(os.path.join(self.playlist_path, "*.txt"))
                
                if not playlist_files:
                    print("❌ Nenhum arquivo .txt encontrado em", self.playlist_path)
                    return
                
                print(f"📁 Encontrados {len(playlist_files)} arquivos para processar")
                
                for file_path in playlist_files:
                    self.process_playlist_file(file_path)
                    
                    # Pausa entre arquivos
                    if self.file_pause > 0:
                        print(f"⏸️ Pausando {self.file_pause}s antes do próximo arquivo...")
                        time.sleep(self.file_pause)
                
                self._print_final_stats()
                
        except RuntimeError as e:
            print(f"🔒 {e}")
        except Exception as e:
            print(f"❌ Erro durante processamento: {e}")
            self.stats['errors'] += 1
    
    def process_playlist_file(self, file_path: str):
        """Processa um arquivo de playlist específico"""
        print(f"\n📄 Processando: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if not lines:
                print("⚠️ Arquivo vazio, pulando...")
                return
            
            processed_lines = []
            
            for line in lines:
                self.stats['lines_processed'] += 1
                
                if self._process_single_line(line):
                    # Linha processada com sucesso, não adicionar de volta
                    continue
                else:
                    # Manter linha no arquivo (erro ou não encontrado)
                    processed_lines.append(line)
            
            # Reescrever arquivo apenas com linhas não processadas
            self._update_playlist_file(file_path, processed_lines)
            self.stats['files_processed'] += 1
            
        except Exception as e:
            print(f"❌ Erro ao processar arquivo {file_path}: {e}")
            self.stats['errors'] += 1
    
    def _process_single_line(self, file_line: str) -> bool:
        """Processa uma linha individual. Retorna True se processada com sucesso"""
        print(f"🔍 Processando: {file_line}")
        
        # Extrair artista e música
        artist, song = self.duplicate_detector.extract_artist_song(file_line)
        
        # Verificar duplicatas
        is_duplicate, reason = self.duplicate_detector.check_all_duplicates(
            file_line, "", artist, song
        )
        
        if is_duplicate:
            print(f"⚠️ Duplicata detectada ({reason}): {file_line}")
            self.stats['duplicates_found'] += 1
            return True  # Remove linha (já temos)
        
        # Buscar música
        download_result = self._search_and_download(file_line, artist, song)
        
        if download_result == "SUCCESS":
            return True  # Remove linha (sucesso)
        elif download_result == "NOT_FOUND":
            # Salvar como NOT_FOUND no banco mas manter linha
            self.db_manager.save_download({
                'file_line': file_line,
                'filename': '',
                'username': ''
            }, 'NOT_FOUND')
            return False  # Manter linha
        else:
            # Erro - manter linha para tentar depois
            return False
    
    def _search_and_download(self, file_line: str, artist: str, song: str) -> str:
        """Busca e inicia download. Retorna: SUCCESS, NOT_FOUND, ERROR"""
        
        # Padrões de busca progressivos
        search_patterns = [
            f"{artist} - {song} *.flac" if artist and song else file_line + " *.flac",
            f"{artist} - {song} *.flac" if artist else f"{song} *.flac",
            f"{song} *.flac" if song else file_line + " *.flac"
        ]
        
        for pattern in search_patterns:
            print(f"🔎 Buscando: {pattern}")
            
            try:
                results = self.slskd_client.search_tracks_cached(pattern)
                
                if not results:
                    continue
                
                # Filtrar e priorizar resultados
                best_result = self._select_best_result(results)
                
                if best_result:
                    return self._initiate_download(file_line, best_result)
                    
            except Exception as e:
                print(f"❌ Erro na busca: {e}")
                self.stats['errors'] += 1
                return "ERROR"
        
        print(f"❌ Música não encontrada: {file_line}")
        return "NOT_FOUND"
    
    def _select_best_result(self, results: List[Dict]) -> Optional[Dict]:
        """Seleciona melhor resultado baseado na qualidade"""
        if not results:
            return None
        
        # Filtrar remixes
        filtered = [r for r in results if 'remix' not in r.get('filename', '').lower()]
        
        if not filtered:
            filtered = results  # Se só tem remix, usar mesmo assim
        
        # Priorizar por qualidade
        def quality_score(result):
            bit_depth = result.get('bitDepth', 0)
            sample_rate = result.get('sampleRate', 0)
            
            # Prioridade 1: 24bit/96kHz
            if bit_depth == 24 and sample_rate == 96000:
                return 4
            # Prioridade 2: 16bit/44.1kHz
            elif bit_depth == 16 and sample_rate == 44100:
                return 3
            # Prioridade 3: 24bit/qualquer
            elif bit_depth == 24:
                return 2
            # Prioridade 4: 16bit/qualquer
            elif bit_depth == 16:
                return 1
            else:
                return 0
        
        # Ordenar por qualidade (maior score primeiro)
        sorted_results = sorted(filtered, key=quality_score, reverse=True)
        
        return sorted_results[0] if sorted_results else None
    
    def _initiate_download(self, file_line: str, result: Dict) -> str:
        """Inicia download e monitora. Retorna: SUCCESS, ERROR"""
        username = result.get('username', '')
        filename = result.get('filename', '')
        
        print(f"⬇️ Iniciando download: {filename} de {username}")
        
        # Verificar se já está na fila
        queue = self.slskd_client.get_download_queue()
        existing_download = self._find_existing_download(queue, username, filename)
        
        if existing_download:
            print(f"📋 Download já na fila: {existing_download.get('id')}")
            return self._monitor_download(file_line, existing_download, result)
        
        # Adicionar à fila
        download_id = self.slskd_client.add_download(username, filename)
        
        if not download_id:
            print(f"❌ Falha ao adicionar download à fila")
            return "ERROR"
        
        self.stats['downloads_started'] += 1
        
        # Monitorar download
        download_info = {'id': download_id, 'username': username, 'filename': filename}
        return self._monitor_download(file_line, download_info, result)
    
    def _find_existing_download(self, queue: List[Dict], username: str, filename: str) -> Optional[Dict]:
        """Encontra download existente na fila"""
        for user_data in queue:
            if user_data.get('username') == username:
                directories = user_data.get('directories', [])
                for directory in directories:
                    files = directory.get('files', [])
                    for file_info in files:
                        if file_info.get('filename') == filename:
                            return file_info
        return None
    
    def _monitor_download(self, file_line: str, download_info: Dict, result: Dict) -> str:
        """Monitora download até conclusão"""
        download_id = download_info.get('id')
        timeout_seconds = self.queue_timeout * 60
        start_time = time.time()
        
        print(f"👀 Monitorando download: {download_id}")
        
        while time.time() - start_time < timeout_seconds:
            try:
                status = self.slskd_client.get_download_status(download_id)
                
                if not status:
                    time.sleep(10)
                    continue
                
                state = status.get('state', '')
                print(f"📊 Status: {state}")
                
                if state == "Completed, Succeeded":
                    self._handle_download_success(file_line, download_info, result)
                    return "SUCCESS"
                
                elif state in ["Completed, Errored", "Completed, Canceled"]:
                    self._handle_download_error(file_line, download_info, state)
                    return "ERROR"
                
                elif state == "Queued, Remotely":
                    # Aguardar 1 minuto para mudança de status
                    if not self._wait_for_queue_change(download_id, 60):
                        self._handle_download_error(file_line, download_info, "Queue timeout")
                        return "ERROR"
                
                elif state == "InProgress":
                    # Continuar monitorando
                    pass
                
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                self.stats['errors'] += 1
                return "ERROR"
        
        # Timeout - assumir sucesso
        print(f"⏰ Timeout atingido, assumindo sucesso")
        self._handle_download_success(file_line, download_info, result)
        return "SUCCESS"
    
    def _wait_for_queue_change(self, download_id: str, timeout_seconds: int) -> bool:
        """Aguarda mudança de status da fila remota"""
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                status = self.slskd_client.get_download_status(download_id)
                state = status.get('state', '') if status else ''
                
                if state != "Queued, Remotely":
                    return True  # Status mudou
                
                time.sleep(10)
                
            except Exception:
                return False
        
        return False  # Timeout sem mudança
    
    def _handle_download_success(self, file_line: str, download_info: Dict, result: Dict):
        """Trata sucesso do download"""
        print(f"✅ Download concluído com sucesso")
        
        # Salvar no banco
        self.db_manager.save_download({
            'id': download_info.get('id'),
            'username': download_info.get('username'),
            'filename': download_info.get('filename'),
            'filename_normalized': self.duplicate_detector.normalize_filename(
                download_info.get('filename', '')
            ),
            'file_line': file_line,
            'file_size': result.get('size', 0)
        }, 'SUCCESS')
        
        # Remover da fila
        self.slskd_client.remove_download(download_info.get('id'))
        
        self.stats['downloads_completed'] += 1
    
    def _handle_download_error(self, file_line: str, download_info: Dict, error_reason: str):
        """Trata erro do download"""
        print(f"❌ Download falhou: {error_reason}")
        
        # Salvar erro no banco
        self.db_manager.save_download({
            'id': download_info.get('id'),
            'username': download_info.get('username'),
            'filename': download_info.get('filename'),
            'file_line': file_line
        }, 'ERROR')
        
        # Remover da fila
        self.slskd_client.remove_download(download_info.get('id'))
        
        self.stats['errors'] += 1
    
    def _update_playlist_file(self, file_path: str, remaining_lines: List[str]):
        """Atualiza arquivo removendo linhas processadas"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for line in remaining_lines:
                    f.write(line + '\n')
            
            print(f"📝 Arquivo atualizado: {len(remaining_lines)} linhas restantes")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar arquivo: {e}")
    
    def _print_final_stats(self):
        """Imprime estatísticas finais"""
        print("\n" + "="*50)
        print("📊 ESTATÍSTICAS FINAIS")
        print("="*50)
        print(f"📁 Arquivos processados: {self.stats['files_processed']}")
        print(f"📝 Linhas processadas: {self.stats['lines_processed']}")
        print(f"⬇️ Downloads iniciados: {self.stats['downloads_started']}")
        print(f"✅ Downloads concluídos: {self.stats['downloads_completed']}")
        print(f"🔄 Duplicatas encontradas: {self.stats['duplicates_found']}")
        print(f"❌ Erros: {self.stats['errors']}")
        
        # Estatísticas do banco
        db_stats = self.db_manager.get_stats()
        print(f"💾 Total no banco: {sum(db_stats.values())}")
        for status, count in db_stats.items():
            if status != 'cache_entries':
                print(f"   {status}: {count}")
        
        print("="*50)
