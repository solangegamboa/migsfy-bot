#!/usr/bin/env python3
"""
Script para organizar arquivos já baixados usando dados da base SQLite
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from playlist.database_manager import DatabaseManager
from playlist.file_organizer import FileOrganizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DownloadedFilesOrganizer:
    def __init__(self, db_path="/app/data/downloads.db"):
        self.db_manager = DatabaseManager(db_path)
        self.file_organizer = FileOrganizer()
        
    def organize_all_downloaded(self):
        """Organiza todos os arquivos baixados com sucesso"""
        downloads = self.db_manager.get_successful_downloads()
        
        if not downloads:
            print("📭 Nenhum download encontrado na base")
            return
            
        print(f"📦 Encontrados {len(downloads)} downloads para organizar")
        
        organized = 0
        failed = 0
        
        for download in downloads:
            if self._organize_download(download):
                organized += 1
            else:
                failed += 1
                
        print(f"\n✅ Organizados: {organized}")
        print(f"❌ Falharam: {failed}")
        
    def _organize_download(self, download):
        """Organiza um download específico"""
        filename = download.get('filename', '')
        file_line = download.get('file_line', '')
        
        if not filename or not file_line:
            return False
            
        # Parse da linha para extrair artista e álbum
        artist, album, song = self._parse_file_line(file_line)
        
        if not artist or not album:
            print(f"⚠️ Não foi possível extrair artista/álbum: {file_line}")
            return False
            
        print(f"🎵 Organizando: {artist} - {album} - {song}")
        
        success = self.file_organizer.organize_file(filename, artist, album)
        
        if success:
            print(f"✅ Organizado: {os.path.basename(filename)}")
        else:
            print(f"❌ Falhou: {os.path.basename(filename)}")
            
        return success
        
    def _parse_file_line(self, file_line):
        """Extrai artista, álbum e música da linha do arquivo"""
        try:
            parts = file_line.strip().split(' - ')
            if len(parts) >= 3:
                artist = parts[0].strip()
                album = parts[1].strip()
                song = ' - '.join(parts[2:]).strip()
                return artist, album, song
        except:
            pass
            
        return "", "", ""

def main():
    """Função principal"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/downloads.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de dados não encontrada: {db_path}")
        return
        
    organizer = DownloadedFilesOrganizer(db_path)
    organizer.organize_all_downloaded()

if __name__ == "__main__":
    main()
