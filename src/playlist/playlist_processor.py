import glob
import os
import time
from typing import Dict, List, Optional, Tuple

from .database_manager import DatabaseManager
from .duplicate_detector import DuplicateDetector
from .file_organizer import FileOrganizer
from .process_lock import ProcessLock
from .slskd_api_client import SlskdApiClient


class PlaylistProcessor:
    def __init__(self):
        # Configurações do .env
        self.playlist_path = os.getenv("PLAYLIST_PATH", "/app/data/playlists")
        self.db_path = os.getenv("DATABASE_PATH", "/app/data/downloads.db")
        self.lock_path = os.getenv("PROCESSOR_LOCK_PATH", "/app/processor.lock")
        self.file_pause = int(os.getenv("FILE_PROCESSING_PAUSE_SECONDS", 30))
        self.queue_timeout = int(os.getenv("QUEUE_TIMEOUT_MINUTES", 5))

        # Inicializar componentes
        self.db_manager = DatabaseManager(self.db_path)
        self.duplicate_detector = DuplicateDetector(self.db_manager)
        self.slskd_client = SlskdApiClient(self.db_manager)
        self.process_lock = ProcessLock(self.lock_path)
        self.file_organizer = FileOrganizer()

        # Estatísticas
        self.stats = {
            "files_processed": 0,
            "lines_processed": 0,
            "downloads_started": 0,
            "downloads_completed": 0,
            "duplicates_found": 0,
            "errors": 0,
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
                        print(
                            f"⏸️ Pausando {self.file_pause}s antes do próximo arquivo..."
                        )
                        time.sleep(self.file_pause)

                self._print_final_stats()

        except RuntimeError as e:
            print(f"🔒 {e}")
        except Exception as e:
            print(f"❌ Erro durante processamento: {e}")
            self.stats["errors"] += 1

    def process_playlist_file(self, file_path: str):
        """Processa um arquivo de playlist específico"""
        print(f"\n📄 Processando: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            if not lines:
                print("⚠️ Arquivo vazio, deletando...")
                os.remove(file_path)
                return

            processed_lines = []

            for line in lines:
                self.stats["lines_processed"] += 1

                if self._process_single_line(line):
                    # Linha processada com sucesso, não adicionar de volta
                    continue
                else:
                    # Manter linha no arquivo (erro ou não encontrado)
                    processed_lines.append(line)

            # Verificar se todas as linhas foram processadas
            if not processed_lines:
                print("✅ Todas as linhas processadas, deletando arquivo...")
                os.remove(file_path)
            else:
                # Reescrever arquivo apenas com linhas não processadas
                self._update_playlist_file(file_path, processed_lines)

            self.stats["files_processed"] += 1

        except Exception as e:
            print(f"❌ Erro ao processar arquivo {file_path}: {e}")
            self.stats["errors"] += 1

    def _process_single_line(self, file_line: str) -> bool:
        """Processa uma linha individual. Retorna True se processada com sucesso"""
        print(f"🔍 Processando: {file_line}")

        # Extrair artista e música
        artist, song = self.duplicate_detector.extract_artist_song(file_line)

        # Verificar se já foi baixado com SUCESSO (remove linha)
        if self.db_manager.is_downloaded(file_line):
            print(f"✅ Duplicata confirmada - removendo linha: {file_line}")
            self.stats["duplicates_found"] += 1
            return True  # Remove linha (já baixado com sucesso)

        # Verificar se já tentou e falhou (NOT_FOUND) - não remove linha mas pula processamento
        if self.db_manager.is_failed_download(file_line):
            print(f"⏭️ Já tentado anteriormente (não encontrado): {file_line}")
            return False  # Manter linha para tentar depois

        # Buscar música
        download_result = self._search_and_download(file_line, artist, song)

        if download_result == "SUCCESS":
            return True  # Remove linha (sucesso)
        elif download_result == "NOT_FOUND":
            # Salvar como NOT_FOUND no banco mas manter linha
            self.db_manager.save_download(
                {"file_line": file_line, "filename": "", "username": ""}, "NOT_FOUND"
            )
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
            f"{song} *.flac" if song else file_line + " *.flac",
        ]

        for pattern in search_patterns:
            print(f"🔎 Buscando: {pattern}")

            try:
                results = self.slskd_client.search_tracks_cached(pattern)

                if not results:
                    continue

                # Se encontrou mais de 10 resultados, usar e parar
                if len(results) >= 10:
                    print(f"✅ Encontrados {len(results)} resultados - usando melhor")
                    return self._try_download_with_fallback(file_line, results)

                # Filtrar e priorizar resultados
                if results:
                    return self._try_download_with_fallback(file_line, results)

            except Exception as e:
                print(f"❌ Erro na busca: {e}")
                self.stats["errors"] += 1
                return "ERROR"

        print(f"❌ Música não encontrada: {file_line}")
        return "NOT_FOUND"

    def _parse_file_line(self, file_line: str) -> tuple:
        """Extrai artista, álbum e música da linha do arquivo"""
        parts = file_line.strip().split(" - ")

        if len(parts) >= 3:
            artist = parts[0].strip()
            # Junta todas as partes do meio como álbum
            album = " - ".join(parts[1:-1]).strip()
            song = parts[-1].strip()
        elif len(parts) == 2:
            artist = parts[0].strip()
            album = ""
            song = parts[1].strip()
        else:
            artist = ""
            album = ""
            song = file_line.strip()

        return artist, album, song

    def _try_download_with_fallback(self, file_line: str, results: List[Dict]) -> str:
        """Tenta baixar com fallback para próximas opções se falhar"""
        # Extrair artista, album e música para verificação
        artist, album, song = self._parse_file_line(file_line)
        sorted_results = self._get_sorted_results(results, artist, album, song)
        failed_users = set()

        for i, result in enumerate(sorted_results):
            username = result.get("username")

            # Pular usuários que já falharam
            if username in failed_users:
                continue

            print(f"🎯 Tentativa {i+1}: {result.get('filename', 'N/A')}")
            print(
                f"   User: {username} - Quality: {result.get('bitDepth')}bit/{result.get('sampleRate')}Hz"
            )

            download_result = self._initiate_download(file_line, result)

            if download_result == "SUCCESS":
                return "SUCCESS"
            elif download_result == "ERROR":
                failed_users.add(username)
                print(f"⚠️ Usuário {username} falhou, tentando outro usuário...")
                continue

        print(f"❌ Todas as tentativas falharam")
        return "ERROR"

    def _get_sorted_results(
        self, results: List[Dict], artist: str = "", album: str = "", song: str = ""
    ) -> List[Dict]:
        """Ordena resultados por qualidade seguindo critérios do plano"""
        # Filtrar remixes e live
        filtered = [
            r
            for r in results
            if "remix" not in r.get("filename", "").lower()
            and "live" not in r.get("filename", "").lower()
        ]
        print(f"🎯 Após filtrar remixes e live: {len(filtered)} resultados")

        # Filtrar usuários online primeiro
        print(f"🎯 DEBUG: Verificando usuários online...")
        online_users = set()
        unique_users = set(r.get("username", "") for r in filtered)
        print(f"🎯 Encontrados {len(unique_users)} usuários únicos")

        for username in unique_users:
            if username and self.slskd_client.is_user_online(username):
                online_users.add(username)

        print(f"🎯 Usuários online: {len(online_users)} de {len(unique_users)}")

        # Filtrar apenas resultados de usuários online
        online_results = [r for r in filtered if r.get("username", "") in online_users]
        print(
            f"🎯 Arquivos de usuários online: {len(online_results)} de {len(filtered)}"
        )

        # Se não há usuários online, usar todos
        if not online_results:
            print(f"🎯 DEBUG: Nenhum usuário online, usando todos os resultados")
            online_results = filtered

        def calculate_score(result):
            """Calcula score total baseado nos critérios"""
            filename = result.get("filename", "").lower()
            score = 0

            # 1 - MUSICA: 1 ponto
            if song and song.lower() in filename:
                score += 1

            # 2 - ALBUM: +2 pontos
            if album and album.lower() in filename:
                score += 2

            # 3 - ARTISTA: +4 pontos
            if artist and artist.lower() in filename:
                score += 4

            # 4 - bitDepth: 24bit = +3, 16bit = +2, outros = +1
            bit_depth = result.get("bitDepth", 0)
            if bit_depth == 24:
                score += 3
            elif bit_depth == 16:
                score += 2
            elif bit_depth > 0:
                score += 1

            # 5 - sampleRate: 96000 = +3, outros = +1
            sample_rate = result.get("sampleRate", 0)
            if sample_rate == 96000:
                score += 3
            elif sample_rate > 0:
                score += 1

            # 6 - Arquivo não locked: +10 pontos
            if not result.get("isLocked", True):
                score += 10

            return score

        # Agrupar por usuário para diversificar
        user_groups = {}
        for result in online_results:
            username = result.get("username", "")
            if username not in user_groups:
                user_groups[username] = []
            user_groups[username].append(result)

        # Ordenar cada grupo por score total
        for username in user_groups:
            user_groups[username].sort(key=calculate_score, reverse=True)

        # Intercalar resultados de diferentes usuários
        sorted_results = []
        max_per_user = (
            max(len(files) for files in user_groups.values()) if user_groups else 0
        )

        for i in range(max_per_user):
            for username, files in user_groups.items():
                if i < len(files):
                    sorted_results.append(files[i])

        # Debug: mostrar top 5 com classificação detalhada
        print(f"🎯 Top 5 resultados por classificação:")
        for i, result in enumerate(sorted_results[:5]):
            filename = result.get("filename", "")
            filename_only = filename.split("\\")[-1] if filename else ""
            total_score = calculate_score(result)

            # Detalhar pontuação
            filename_lower = filename.lower()
            song_pts = 1 if song and song.lower() in filename_lower else 0
            album_pts = 2 if album and album.lower() in filename_lower else 0
            artist_pts = 4 if artist and artist.lower() in filename_lower else 0

            # BitDepth pontuação
            bit_depth = result.get("bitDepth", 0)
            if bit_depth == 24:
                bitdepth_pts = 3
            elif bit_depth == 16:
                bitdepth_pts = 2
            elif bit_depth > 0:
                bitdepth_pts = 1
            else:
                bitdepth_pts = 0

            # SampleRate pontuação
            sample_rate = result.get("sampleRate", 0)
            if sample_rate == 96000:
                freq_pts = 3
            elif sample_rate > 0:
                freq_pts = 1
            else:
                freq_pts = 0

            # isLocked pontuação
            locked_pts = 10 if not result.get("isLocked", True) else 0

            print(f"  {i+1}. Score {total_score}: {filename_only}")
            print(
                f"     Música({song_pts}) + Álbum({album_pts}) + Artista({artist_pts}) + BitDepth({bitdepth_pts}) + Freq({freq_pts}) + Unlocked({locked_pts})"
            )
            print(
                f"     User: {result.get('username')} - {result.get('bitDepth')}bit/{result.get('sampleRate')}Hz - Locked: {result.get('isLocked', True)}"
            )

        return sorted_results

    def _initiate_download(self, file_line: str, result: Dict) -> str:
        """Inicia download e monitora. Retorna: SUCCESS, ERROR"""
        username = result.get("username", "")
        filename = result.get("filename", "")

        print(f"⬇️ Iniciando download: {filename} de {username}")

        # Verificar se já está na fila
        queue = self.slskd_client.get_download_queue()
        existing_download = self._find_existing_download(queue, username, filename)

        if existing_download:
            print(f"📋 Download já na fila: {existing_download.get('id')}")
            return self._monitor_download(file_line, existing_download, result)

        # Adicionar à fila
        download_id = self.slskd_client.add_download(
            username, filename, result.get("size", 0)
        )

        if not download_id:
            print(f"❌ Falha ao adicionar download à fila")
            return "ERROR"

        self.stats["downloads_started"] += 1

        # Monitorar download
        download_info = {"id": download_id, "username": username, "filename": filename}
        return self._monitor_download(file_line, download_info, result)

    def _find_existing_download(
        self, queue: List[Dict], username: str, filename: str
    ) -> Optional[Dict]:
        """Encontra download existente na fila"""
        for user_data in queue:
            if user_data.get("username") == username:
                directories = user_data.get("directories", [])
                for directory in directories:
                    files = directory.get("files", [])
                    for file_info in files:
                        if file_info.get("filename") == filename:
                            return file_info
        return None

    def _monitor_download(
        self, file_line: str, download_info: Dict, result: Dict
    ) -> str:
        """Monitora download até conclusão"""
        download_id = download_info.get("id")
        timeout_seconds = self.queue_timeout * 60
        start_time = time.time()

        print(f"👀 Monitorando download: {download_id}")

        while time.time() - start_time < timeout_seconds:
            try:
                status = self.slskd_client.get_download_status(download_id)

                if not status:
                    time.sleep(10)
                    continue

                state = status.get("state", "")
                print(f"📊 Status: {state}")

                if state == "Completed, Succeeded":
                    self._handle_download_success(file_line, download_info, result)
                    return "SUCCESS"

                elif state in ["Completed, Errored", "Completed, Cancelled"]:
                    self._handle_download_error(file_line, download_info, state)
                    return "ERROR"

                elif state == "Queued, Remotely":
                    # Aguardar 1 minuto para mudança de status
                    if not self._wait_for_queue_change(download_id, 60):
                        self._handle_download_error(
                            file_line, download_info, "Queue timeout"
                        )
                        return "ERROR"

                elif state == "InProgress":
                    # Continuar monitorando
                    pass

                time.sleep(10)

            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                self.stats["errors"] += 1
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
                state = status.get("state", "") if status else ""

                if state != "Queued, Remotely":
                    return True  # Status mudou

                time.sleep(10)

            except Exception:
                return False

        return False  # Timeout sem mudança

    def _handle_download_success(
        self, file_line: str, download_info: Dict, result: Dict
    ):
        """Trata sucesso do download"""
        print(f"✅ Download concluído com sucesso")

        # Extrair informações para organização
        artist, album, song = self._parse_file_line(file_line)
        filename = download_info.get("filename", "")
        
        # Organizar arquivo baixado
        if artist and album and filename:
            organize_success = self.file_organizer.organize_file(filename, artist, album)
            if organize_success:
                print(f"📁 Arquivo organizado: {artist}/{album}/{os.path.basename(filename)}")
            else:
                print(f"⚠️ Falha ao organizar arquivo: {filename}")

        # Salvar no banco
        self.db_manager.save_download(
            {
                "id": download_info.get("id"),
                "username": download_info.get("username"),
                "filename": download_info.get("filename"),
                "filename_normalized": self.duplicate_detector.normalize_filename(
                    download_info.get("filename", "")
                ),
                "file_line": file_line,
                "file_size": result.get("size", 0),
            },
            "SUCCESS",
        )

        # Remover da fila
        self.slskd_client.remove_download(download_info.get("id"))

        self.stats["downloads_completed"] += 1

    def _handle_download_error(
        self, file_line: str, download_info: Dict, error_reason: str
    ):
        """Trata erro do download"""
        print(f"❌ Download falhou: {error_reason}")

        # Salvar erro no banco
        self.db_manager.save_download(
            {
                "id": download_info.get("id"),
                "username": download_info.get("username"),
                "filename": download_info.get("filename"),
                "file_line": file_line,
            },
            "ERROR",
        )

        # Remover da fila
        self.slskd_client.remove_download(download_info.get("id"))

        self.stats["errors"] += 1

    def _update_playlist_file(self, file_path: str, remaining_lines: List[str]):
        """Atualiza arquivo removendo linhas processadas"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for line in remaining_lines:
                    f.write(line + "\n")

            print(f"📝 Arquivo atualizado: {len(remaining_lines)} linhas restantes")

        except Exception as e:
            print(f"❌ Erro ao atualizar arquivo: {e}")

    def _print_final_stats(self):
        """Imprime estatísticas finais"""
        print("\n" + "=" * 50)
        print("📊 ESTATÍSTICAS FINAIS")
        print("=" * 50)
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
            if status != "cache_entries":
                print(f"   {status}: {count}")

        print("=" * 50)
