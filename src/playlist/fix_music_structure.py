#!/usr/bin/env python3
"""
Script para corrigir estrutura de pastas em /media/music usando dados da base SQLite
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from playlist.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MusicStructureFixer:
    def __init__(self, db_path="/app/data/downloads.db", music_path="/media/music"):
        self.db_manager = DatabaseManager(db_path)
        self.music_path = music_path
        
    def fix_all_structure(self):
        """Corrige estrutura de todos os arquivos em /media/music"""
        downloads = self.db_manager.get_successful_downloads()
        
        if not downloads:
            print("📭 Nenhum download encontrado na base")
            return
            
        print(f"🔧 Corrigindo estrutura de {len(downloads)} downloads")
        
        fixed = 0
        errors = 0
        
        for download in downloads:
            if self._fix_file_structure(download):
                fixed += 1
            else:
                errors += 1
                
        print(f"\n✅ Corrigidos: {fixed}")
        print(f"❌ Erros: {errors}")
        
    def _fix_file_structure(self, download):
        """Corrige estrutura de um arquivo específico"""
        filename = download.get('filename', '')
        file_line = download.get('file_line', '')
        
        if not filename or not file_line:
            return False
            
        # Parse da linha para extrair artista e álbum
        artist, album, song = self._parse_file_line(file_line)
        
        if not artist or not album:
            print(f"⚠️ Não foi possível extrair artista/álbum: {file_line}")
            return False
            
        # Nome do arquivo (apenas a parte final)
        file_name = os.path.basename(filename.replace('\\', '/'))
        
        # Procurar arquivo atual em /media/music
        current_file = self._find_file_in_music(file_name)
        
        if not current_file:
            print(f"❌ Arquivo não encontrado em /media/music: {file_name}")
            return False
            
        # Estrutura correta
        correct_artist = self._sanitize_name(artist)
        correct_album = self._sanitize_name(album)
        correct_path = Path(self.music_path) / correct_artist / correct_album
        correct_file = correct_path / file_name
        
        # Verificar se já está na estrutura correta
        if str(current_file) == str(correct_file):
            return True
            
        print(f"🔧 Corrigindo: {artist} - {album} - {file_name}")
        print(f"   De: {current_file}")
        print(f"   Para: {correct_file}")
        
        try:
            # Criar pastas se necessário
            correct_path.mkdir(parents=True, exist_ok=True)
            
            # Mover arquivo
            shutil.move(str(current_file), str(correct_file))
            
            # Remover pasta vazia se possível
            self._cleanup_empty_dirs(current_file.parent)
            
            print(f"✅ Movido com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao mover: {e}")
            return False
            
    def _find_file_in_music(self, file_name):
        """Procura arquivo em /media/music usando find"""
        try:
            # Extrair apenas o nome do arquivo
            base_name = os.path.basename(file_name.replace('\\', '/'))
            
            cmd = ["find", self.music_path, "-type", "f", "-name", f"*{base_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            files = result.stdout.strip().split('\n')
            return Path(files[0]) if files and files[0] else None
            
        except subprocess.CalledProcessError:
            return None
        
    def _cleanup_empty_dirs(self, path):
        """Remove pastas vazias"""
        try:
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                # Tentar remover pasta pai se também estiver vazia
                self._cleanup_empty_dirs(path.parent)
        except:
            pass
            
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
        
    def _sanitize_name(self, name):
        """Remove caracteres inválidos para nomes de pasta"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

def main():
    """Função principal"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/downloads.db")
    music_path = os.getenv("MUSIC_PATH", "/media/music")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de dados não encontrada: {db_path}")
        return
        
    if not os.path.exists(music_path):
        print(f"❌ Pasta de música não encontrada: {music_path}")
        return
        
    fixer = MusicStructureFixer(db_path, music_path)
    fixer.fix_all_structure()

if __name__ == "__main__":
    main()
