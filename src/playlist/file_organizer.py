import os
import shutil
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileOrganizer:
    def __init__(self, slskd_path="/media/slskd", music_path="/media/music"):
        self.slskd_path = slskd_path
        self.music_path = music_path
    
    def organize_file(self, filename, artist, album):
        """Organiza arquivo baixado para estrutura ARTISTA/ALBUM/musica.ext"""
        try:
            # Extrai nome do arquivo do filename completo
            file_name = os.path.basename(filename)
            
            # Procura arquivo usando find
            found_file = self._find_file(file_name)
            if not found_file:
                logger.error(f"Arquivo não encontrado: {file_name}")
                return False
            
            # Cria estrutura de pastas
            artist_path = Path(self.music_path) / self._sanitize_name(artist)
            album_path = artist_path / self._sanitize_name(album)
            
            artist_path.mkdir(parents=True, exist_ok=True)
            album_path.mkdir(parents=True, exist_ok=True)
            
            # Move arquivo
            dest_file = album_path / file_name
            shutil.move(found_file, dest_file)
            
            logger.info(f"Arquivo movido: {found_file} -> {dest_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao organizar arquivo {filename}: {e}")
            return False
    
    def _find_file(self, file_name):
        """Procura arquivo usando find command"""
        try:
            # Extrair apenas o nome do arquivo (última parte após \ ou /)
            base_name = os.path.basename(file_name.replace('\\', '/'))
            
            cmd = ["find", self.slskd_path, "-type", "f", "-name", f"*{base_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            files = result.stdout.strip().split('\n')
            return files[0] if files and files[0] else None
            
        except subprocess.CalledProcessError:
            return None
    
    def _sanitize_name(self, name):
        """Remove caracteres inválidos para nomes de pasta"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
