#!/usr/bin/env python3

import hashlib
import os
import sqlite3
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(__file__))


class SingletonLock:
    def __init__(self, lockfile):
        self.lockfile = lockfile
        self.locked = False

    def acquire(self):
        if os.path.exists(self.lockfile):
            try:
                with open(self.lockfile, "r") as f:
                    pid = f.read().strip()

                # Verifica se o PID é válido
                if not pid or not pid.isdigit():
                    os.remove(self.lockfile)
                else:
                    try:
                        # Tenta verificar se o processo existe
                        os.kill(int(pid), 0)
                        # Se chegou aqui, processo existe
                        return False
                    except (OSError, ProcessLookupError):
                        # Processo não existe, remove lock
                        os.remove(self.lockfile)
            except (IOError, ValueError):
                # Arquivo corrompido, remove
                try:
                    os.remove(self.lockfile)
                except:
                    pass

        try:
            with open(self.lockfile, "w") as f:
                f.write(str(os.getpid()))
            self.locked = True
            return True
        except Exception:
            return False

    def release(self):
        if self.locked and os.path.exists(self.lockfile):
            os.remove(self.lockfile)
            self.locked = False


class PlaylistProcessor:
    def __init__(self, db_path="data/downloads.db"):
        self.db_path = db_path
        lockfile_path = (
            "/app/data/playlist_processor.lock"
            if os.path.exists("/app/data")
            else "data/playlist_processor.lock"
        )
        self.lock = SingletonLock(lockfile_path)
        self.init_database()

    def init_database(self):
        """Inicializa banco SQLite"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_hash TEXT UNIQUE,
                artist TEXT,
                album TEXT,
                title TEXT,
                original_line TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_hash TEXT UNIQUE,
                artist TEXT,
                album TEXT,
                title TEXT,
                original_line TEXT,
                failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0
            )
        """
        )

        conn.commit()
        conn.close()

    def get_track_hash(self, line):
        """Gera hash único para a música"""
        normalized = line.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_downloaded(self, line):
        """Verifica se música já foi baixada"""
        track_hash = self.get_track_hash(line)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM downloads WHERE track_hash = ?", (track_hash,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    def mark_downloaded(self, line):
        """Marca música como baixada"""
        track_hash = self.get_track_hash(line)
        parts = line.split(" - ")

        artist = parts[0].strip() if len(parts) > 0 else ""
        album = parts[1].strip() if len(parts) > 1 else ""
        title = parts[2].strip() if len(parts) > 2 else ""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO downloads 
            (track_hash, artist, album, title, original_line)
            VALUES (?, ?, ?, ?, ?)
        """,
            (track_hash, artist, album, title, line),
        )

        conn.commit()
        conn.close()

    def mark_as_failed(self, line):
        """Marca música como falhada no banco"""
        track_hash = self.get_track_hash(line)
        parts = line.split(" - ")

        artist = parts[0].strip() if len(parts) > 0 else ""
        album = parts[1].strip() if len(parts) > 1 else ""
        title = parts[2].strip() if len(parts) > 2 else ""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO failed_downloads 
            (track_hash, artist, album, title, original_line, retry_count)
            VALUES (?, ?, ?, ?, ?, 
                COALESCE((SELECT retry_count FROM failed_downloads WHERE track_hash = ?), 0) + 1)
        """,
            (track_hash, artist, album, title, line, track_hash),
        )

        conn.commit()
        conn.close()

    def connect_slskd(self):
        """Conecta ao slskd"""
        try:
            import slskd_api

            host = os.getenv("SLSKD_HOST", "192.168.15.100")
            api_key = os.getenv("SLSKD_API_KEY")
            url_base = os.getenv("SLSKD_URL_BASE", f"http://{host}:5030")

            if not api_key:
                print("❌ SLSKD_API_KEY não encontrada")
                return None

            slskd = slskd_api.SlskdClient(host=host, api_key=api_key, url_base=url_base)
            slskd.application.state()
            return slskd

        except Exception as e:
            print(f"❌ Erro ao conectar slskd: {e}")
            return None

    def show_download_queue(self, slskd):
        """Mostra fila de downloads atual"""
        try:
            print("🔍 Verificando fila de downloads...")
            downloads = slskd.transfers.get_all_downloads()

            if not downloads:
                print("📋 Fila de downloads vazia")
                return

            # Conta total de arquivos
            total_files = 0
            for download in downloads:
                directories = download.get('directories', [])
                for directory in directories:
                    files = directory.get('files', [])
                    total_files += len(files)

            print(f"📋 Fila de downloads ({total_files} arquivos):")
            print("=" * 60)

            file_counter = 0
            for download in downloads:
                dl_username = download.get('username', 'N/A')
                directories = download.get('directories', [])
                
                for directory in directories:
                    files = directory.get('files', [])
                    
                    for file_info in files:
                        file_counter += 1
                        dl_filename = file_info.get('filename', 'N/A')
                        dl_state = file_info.get('state', 'unknown').lower()
                        dl_size = file_info.get('size', 0)
                        
                        # Tamanho em MB
                        size_mb = dl_size / (1024 * 1024) if dl_size > 0 else 0
                        
                        status_emoji = {
                            'completed': '✅',
                            'complete': '✅', 
                            'finished': '✅',
                            'completed, succeeded': '✅',
                            'downloading': '📥',
                            'inprogress': '📥',
                            'queued': '⏳',
                            'queued, remotely': '⏳',
                            'pending': '⏳',
                            'failed': '❌',
                            'error': '❌',
                            'cancelled': '❌',
                            'completed, errored': '❌'
                        }.get(dl_state, '🔄')
                        
                        # Extrai apenas o nome do arquivo (última parte do path)
                        filename_short = dl_filename.split('\\')[-1] if dl_filename != 'N/A' else 'N/A'
                        
                        print(f"  {file_counter:2d}. {status_emoji} {filename_short}")
                        print(f"      Status: {dl_state} | Usuário: {dl_username}")
                        if size_mb > 0:
                            print(f"      Tamanho: {size_mb:.1f} MB")
                        print()

            print("=" * 60)

        except Exception as e:
            print(f"⚠️ Erro ao mostrar fila: {e}")
            import traceback
            print(f"🔍 Debug: {traceback.format_exc()}")

    def check_existing_download(self, slskd, line):
        """Verifica se música já está na fila de download"""
        try:
            downloads = slskd.transfers.get_all_downloads()

            for download in downloads:
                dl_username = download.get('username', '')
                directories = download.get('directories', [])
                
                for directory in directories:
                    files = directory.get('files', [])
                    
                    for file_info in files:
                        dl_filename = file_info.get('filename', '')
                        dl_state = file_info.get('state', '').lower()
                        
                        # Extrai apenas o nome do arquivo (última parte do path)
                        filename_only = dl_filename.split('\\')[-1] if dl_filename else ''
                        
                        # Busca por similaridade no nome do arquivo apenas
                        if any(word.lower() in filename_only.lower() for word in line.split() if len(word) > 3):
                            print(f"📥 Já na fila: {filename_only} - Status: {dl_state}")
                            
                            if dl_state in ['completed', 'complete', 'finished'] or 'completed, succeeded' in dl_state:
                                print(f"✅ Já completado na fila")
                                return True
                            elif dl_state in ['downloading', 'inprogress', 'queued', 'queued, remotely', 'pending']:
                                print(f"⏳ Já em download - aguardando...")
                                return self.wait_for_download_completion(slskd, dl_filename, dl_username)

            return False

        except Exception as e:
            print(f"⚠️ Erro ao verificar fila: {e}")
            return False

    def download_track(self, slskd, line):
        """Baixa uma música e aguarda confirmação de sucesso"""
        try:
            # Verifica se já está na fila
            if self.check_existing_download(slskd, line):
                return True

            import os

            from cli.main import (
                create_search_variations,
                find_best_mp3,
                smart_download_with_fallback,
                wait_for_search_completion,
            )

            variations = create_search_variations(line)

            for search_term in variations:
                try:
                    search_result = slskd.searches.search_text(search_term)
                    search_id = search_result.get("id")

                    search_responses = wait_for_search_completion(
                        slskd,
                        search_id,
                        max_wait=int(os.getenv("SEARCH_WAIT_TIME", 25)),
                    )

                    if not search_responses:
                        continue

                    best_file, best_user, best_score = find_best_mp3(
                        search_responses, line
                    )

                    if best_file and best_score > 15:
                        success = smart_download_with_fallback(
                            slskd, search_responses, best_file, best_user, line
                        )
                        if success:
                            # Aguarda confirmação de download
                            if self.wait_for_download_completion(
                                slskd, best_file.get("filename"), best_user
                            ):
                                return True

                except Exception:
                    continue

            return False

        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return False

    def remove_line_from_file(self, file_path, line_to_remove):
        """Remove linha específica do arquivo"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Remove a linha específica
            updated_lines = [
                line for line in lines if line.strip() != line_to_remove.strip()
            ]

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

            return True
        except Exception as e:
            print(f"❌ Erro ao remover linha: {e}")
            return False

    def find_download_in_queue(self, slskd, filename, username):
        """Procura download específico na fila por usuário e arquivo"""
        try:
            downloads = slskd.transfers.get_all_downloads()

            for download in downloads:
                dl_username = download.get('username', '')
                directories = download.get('directories', [])
                
                for directory in directories:
                    files = directory.get('files', [])
                    
                    for file_info in files:
                        dl_filename = file_info.get('filename', '')
                        dl_state = file_info.get('state', '').lower()
                        
                        # Extrai apenas o nome do arquivo (última parte do path)
                        dl_filename_only = dl_filename.split('\\')[-1] if dl_filename else ''
                        filename_only = filename.split('\\')[-1] if filename else ''
                        
                        # Match apenas por nome do arquivo
                        filename_match = (dl_filename_only.lower() == filename_only.lower() or
                                        dl_filename_only.lower() in filename_only.lower() or
                                        filename_only.lower() in dl_filename_only.lower())
                        
                        if filename_match:
                            return file_info, dl_state

            return None, None

        except Exception as e:
            print(f"⚠️ Erro ao procurar na fila: {e}")
            return None, None

    def wait_for_download_completion(self, slskd, filename, username, max_wait=300):
        """Aguarda confirmação de download completado"""
        print(f"⏳ Aguardando confirmação: {os.path.basename(filename)} de {username}")

        start_time = time.time()
        check_interval = 5

        while time.time() - start_time < max_wait:
            try:
                download, dl_state = self.find_download_in_queue(
                    slskd, filename, username
                )

                if download:
                    dl_filename = download.get("filename", "")
                    print(
                        f"📥 Encontrado na fila: {os.path.basename(dl_filename)} - Status: {dl_state}"
                    )

                    if (
                        dl_state in ["completed", "complete", "finished"]
                        or "completed, succeeded" in dl_state
                    ):
                        print(
                            f"✅ Download confirmado: {os.path.basename(dl_filename)}"
                        )
                        return True
                    elif (
                        dl_state in ["failed", "error", "cancelled"]
                        or "completed, errored" in dl_state
                    ):
                        print(f"❌ Download falhou: {dl_state}")
                        return False
                    else:
                        print(
                            f"⏳ Em progresso: {dl_state} ({int(time.time() - start_time)}s)"
                        )
                else:
                    print(
                        f"🔍 Não encontrado na fila ({int(time.time() - start_time)}s)"
                    )

                time.sleep(check_interval)

            except Exception as e:
                print(f"⚠️ Erro ao verificar downloads: {e}")
                time.sleep(check_interval)

        # Verifica uma última vez após timeout
        download, dl_state = self.find_download_in_queue(slskd, filename, username)
        if download and (
            dl_state in ["completed", "complete", "finished"]
            or "completed, succeeded" in dl_state
        ):
            print(f"✅ Download completado após timeout")
            return True

        print(f"⏰ Timeout - assumindo falha no download")
        return False

    def add_to_failed_file(self, original_file, line):
        """Adiciona música ao arquivo de falhas"""
        try:
            base_name = os.path.splitext(original_file)[0]
            failed_file = f"{base_name}_failed.txt"

            with open(failed_file, "a", encoding="utf-8") as f:
                f.write(f"{line}\n")

            print(f"📝 Adicionado ao arquivo de falhas: {failed_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar à lista de falhas: {e}")
            return False

    def process_playlist_file(self, file_path):
        """Processa um arquivo de playlist"""
        if not os.path.exists(file_path):
            return

        print(f"📖 Processando: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"❌ Erro ao ler {file_path}: {e}")
            return

        if not lines:
            print(f"📝 Arquivo vazio: {file_path}")
            return

        slskd = self.connect_slskd()
        if not slskd:
            return

        # Mostra fila atual no início
        print(f"\n📋 Verificando fila de downloads antes de processar...")
        self.show_download_queue(slskd)
        print()

        processed = 0
        downloaded = 0
        skipped = 0

        for line in lines:
            processed += 1

            # Verifica se já foi baixada
            if self.is_downloaded(line):
                print(f"⏭️ [{processed}] Já baixada: {line}")
                self.remove_line_from_file(file_path, line)
                skipped += 1
                continue

            print(f"🎵 [{processed}] Baixando: {line}")

            # Tenta baixar e aguarda confirmação
            success = self.download_track(slskd, line)

            if success:
                print(f"✅ Sucesso confirmado: {line}")
                self.mark_downloaded(line)
                self.remove_line_from_file(file_path, line)
                downloaded += 1
            else:
                print(f"❌ Falha confirmada: {line}")
                self.mark_as_failed(line)
                self.add_to_failed_file(file_path, line)
                self.remove_line_from_file(file_path, line)

            # Pausa entre downloads
            time.sleep(60)

        print(
            f"📊 {file_path}: {downloaded} baixadas, {skipped} puladas, {processed} processadas"
        )

    def process_playlists_folder(self, include_failed=False):
        """Processa todas as playlists procurando em várias pastas"""
        possible_dirs = ["data/playlists", "playlists", "/app/playlists"]
        playlists_dir = None

        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                playlists_dir = dir_path
                break

        if not playlists_dir:
            print(
                f"📁 Nenhuma pasta de playlists encontrada: {', '.join(possible_dirs)}"
            )
            return

        print(f"📁 Usando pasta: {playlists_dir}")

        if include_failed:
            txt_files = [
                f for f in os.listdir(playlists_dir) if f.endswith("_failed.txt")
            ]
            print("🔄 Processando arquivos de falhas")
        else:
            txt_files = [
                f
                for f in os.listdir(playlists_dir)
                if f.endswith(".txt") and not f.endswith("_failed.txt")
            ]

        if not txt_files:
            file_type = "falhas" if include_failed else "playlist"
            print(f"📝 Nenhum arquivo de {file_type} encontrado em {playlists_dir}")
            return

        file_type = "falhas" if include_failed else "playlist"
        print(f"🎵 Encontrados {len(txt_files)} arquivos de {file_type}")

        for txt_file in txt_files:
            file_path = os.path.join(playlists_dir, txt_file)
            self.process_playlist_file(file_path)
            time.sleep(5)  # Pausa entre arquivos

    def get_failed_tracks(self, max_retries=3):
        """Obtém músicas falhadas para retry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT original_line FROM failed_downloads 
            WHERE retry_count < ? 
            ORDER BY failed_at ASC
        """,
            (max_retries,),
        )

        tracks = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tracks

    def remove_from_failed(self, line):
        """Remove música da lista de falhas após sucesso"""
        track_hash = self.get_track_hash(line)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM failed_downloads WHERE track_hash = ?", (track_hash,)
        )

        conn.commit()
        conn.close()

    def retry_failed_downloads(self):
        """Tenta novamente downloads que falharam"""
        print("🔄 Iniciando retry de downloads falhados")

        failed_tracks = self.get_failed_tracks()
        if not failed_tracks:
            print("✅ Nenhuma música falhada para retry")
            return

        print(f"📋 {len(failed_tracks)} músicas para retry")

        slskd = self.connect_slskd()
        if not slskd:
            return

        successful = 0
        failed = 0

        for i, line in enumerate(failed_tracks, 1):
            print(f"\n🔄 [{i}/{len(failed_tracks)}] Retry: {line}")

            if self.is_downloaded(line):
                print(f"✅ Já baixada - removendo da lista de falhas")
                self.remove_from_failed(line)
                successful += 1
                continue

            success = self.download_track(slskd, line)

            if success:
                print(f"✅ Retry bem-sucedido: {line}")
                self.mark_downloaded(line)
                self.remove_from_failed(line)
                successful += 1
            else:
                print(f"❌ Retry falhou: {line}")
                self.mark_as_failed(line)
                failed += 1

            time.sleep(60)

        print(f"\n📊 Retry concluído: {successful} sucessos, {failed} falhas")

    def run_daemon(self):
        """Executa em modo daemon"""
        if not self.lock.acquire():
            print("❌ Outra instância já está rodando")
            return

        try:
            print("🔄 Iniciando processador de playlists em modo daemon")

            while True:
                try:
                    self.process_playlists_folder()
                    print("⏰ Aguardando 30 minutos...")
                    time.sleep(1800)  # 30 minutos
                except KeyboardInterrupt:
                    print("\n🛑 Daemon interrompido")
                    break
                except Exception as e:
                    print(f"❌ Erro no daemon: {e}")
                    time.sleep(300)  # 5 minutos em caso de erro
        finally:
            self.lock.release()


def main():
    # Verifica se é para forçar limpeza do lock
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        lockfile_path = (
            "/app/data/playlist_processor.lock"
            if os.path.exists("/app/data")
            else "data/playlist_processor.lock"
        )
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)
            print("✅ Lock file removido")
        else:
            print("ℹ️ Nenhum lock file encontrado")
        return

    processor = PlaylistProcessor()

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        processor.run_daemon()
    elif len(sys.argv) > 1 and sys.argv[1] == "--failed":
        if not processor.lock.acquire():
            print("❌ Outra instância já está rodando")
            print("💡 Use --cleanup para remover lock órfão")
            return
        try:
            processor.process_playlists_folder(include_failed=True)
        finally:
            processor.lock.release()
    elif len(sys.argv) > 1 and sys.argv[1] == "--retry":
        if not processor.lock.acquire():
            print("❌ Outra instância já está rodando")
            print("💡 Use --cleanup para remover lock órfão")
            return
        try:
            processor.retry_failed_downloads()
        finally:
            processor.lock.release()
    elif len(sys.argv) > 1 and sys.argv[1] == "--queue":
        slskd = processor.connect_slskd()
        if slskd:
            processor.show_download_queue(slskd)
        return
    else:
        if not processor.lock.acquire():
            print("❌ Outra instância já está rodando")
            print("💡 Use --cleanup para remover lock órfão")
            return
        try:
            processor.process_playlists_folder()
        finally:
            processor.lock.release()


if __name__ == "__main__":
    main()
