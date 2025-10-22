#!/usr/bin/env python3

import os
import sys
import time
import sqlite3
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(__file__))

class PlaylistProcessor:
    def __init__(self, db_path="data/downloads.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Inicializa banco SQLite"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_hash TEXT UNIQUE,
                artist TEXT,
                album TEXT,
                title TEXT,
                original_line TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        parts = line.split(' - ')
        
        artist = parts[0].strip() if len(parts) > 0 else ""
        album = parts[1].strip() if len(parts) > 1 else ""
        title = parts[2].strip() if len(parts) > 2 else ""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO downloads 
            (track_hash, artist, album, title, original_line)
            VALUES (?, ?, ?, ?, ?)
        ''', (track_hash, artist, album, title, line))
        
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
    
    def download_track(self, slskd, line):
        """Baixa uma música forçando busca individual (nunca álbum)"""
        try:
            from cli.main import create_search_variations, wait_for_search_completion, find_best_mp3, smart_download_with_fallback
            import os
            
            # Força busca individual criando variações apenas para faixas
            variations = create_search_variations(line)
            
            for search_term in variations:
                try:
                    search_result = slskd.searches.search_text(search_term)
                    search_id = search_result.get("id")
                    
                    search_responses = wait_for_search_completion(
                        slskd, search_id, max_wait=int(os.getenv("SEARCH_WAIT_TIME", 25))
                    )
                    
                    if not search_responses:
                        continue
                    
                    # Busca apenas arquivos individuais, nunca álbuns
                    best_file, best_user, best_score = find_best_mp3(search_responses, line)
                    
                    if best_file and best_score > 15:
                        success = smart_download_with_fallback(
                            slskd, search_responses, best_file, best_user, line
                        )
                        if success:
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
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove a linha específica
            updated_lines = [line for line in lines if line.strip() != line_to_remove.strip()]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
                
            return True
        except Exception as e:
            print(f"❌ Erro ao remover linha: {e}")
            return False
    
    def process_playlist_file(self, file_path):
        """Processa um arquivo de playlist"""
        if not os.path.exists(file_path):
            return
            
        print(f"📖 Processando: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            
            # Tenta baixar
            success = self.download_track(slskd, line)
            
            if success:
                print(f"✅ Sucesso: {line}")
                self.mark_downloaded(line)
                self.remove_line_from_file(file_path, line)
                downloaded += 1
            else:
                print(f"❌ Falha: {line}")
            
            # Pausa entre downloads
            time.sleep(3)
        
        print(f"📊 {file_path}: {downloaded} baixadas, {skipped} puladas, {processed} processadas")
    
    def process_playlists_folder(self):
        """Processa todas as playlists na pasta data/playlists/"""
        playlists_dir = "data/playlists"
        
        if not os.path.exists(playlists_dir):
            print(f"📁 Pasta {playlists_dir} não encontrada")
            return
        
        txt_files = [f for f in os.listdir(playlists_dir) if f.endswith('.txt')]
        
        if not txt_files:
            print(f"📝 Nenhum arquivo .txt encontrado em {playlists_dir}")
            return
        
        print(f"🎵 Encontrados {len(txt_files)} arquivos de playlist")
        
        for txt_file in txt_files:
            file_path = os.path.join(playlists_dir, txt_file)
            self.process_playlist_file(file_path)
            time.sleep(5)  # Pausa entre arquivos
    
    def run_daemon(self):
        """Executa em modo daemon"""
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

def main():
    processor = PlaylistProcessor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        processor.run_daemon()
    else:
        processor.process_playlists_folder()

if __name__ == "__main__":
    main()