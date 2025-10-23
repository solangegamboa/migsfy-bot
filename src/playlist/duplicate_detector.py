import re
import hashlib
import os
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

class DuplicateDetector:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def normalize_filename(self, filename: str) -> str:
        """Remove path, extensão e caracteres especiais"""
        if not filename:
            return ""
            
        # Remove path
        name = os.path.basename(filename)
        
        # Remove extensão
        name = os.path.splitext(name)[0]
        
        # Remove números de faixa no início (01, 02, etc)
        name = re.sub(r'^\d+[\s\-\.]*', '', name)
        
        # Remove números isolados no meio (Track 03 -> Track)
        name = re.sub(r'\b\d+\b', '', name)
        
        # Remove caracteres especiais e normaliza
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.lower().strip()
    
    def fuzzy_match_song(self, artist: str, song: str, threshold: float = 0.85) -> List[str]:
        """Busca músicas similares por fuzzy match"""
        if not artist or not song:
            return []
            
        search_text = f"{artist} {song}".lower()
        matches = []
        
        # Buscar no banco por similaridade
        import sqlite3
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_line FROM downloads WHERE status = 'SUCCESS'"
            )
            
            for row in cursor.fetchall():
                file_line = row[0].lower()
                similarity = SequenceMatcher(None, search_text, file_line).ratio()
                
                if similarity >= threshold:
                    matches.append(row[0])
                    
        return matches
    
    def calculate_file_hash(self, filepath: str) -> str:
        """Calcula hash MD5 do arquivo"""
        if not os.path.exists(filepath):
            return ""
            
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def is_similar_file(self, new_file: Dict, existing_files: List[Dict], threshold: float = 0.90) -> bool:
        """Verifica se arquivo é similar aos existentes"""
        new_name = self.normalize_filename(new_file.get('filename', ''))
        
        for existing in existing_files:
            existing_name = self.normalize_filename(existing.get('filename', ''))
            
            if not new_name or not existing_name:
                continue
                
            similarity = SequenceMatcher(None, new_name, existing_name).ratio()
            
            if similarity >= threshold:
                return True
                
        return False
    
    def check_all_duplicates(self, file_line: str, filename: str, artist: str, song: str) -> Tuple[bool, str]:
        """Verificação completa de duplicatas"""
        
        # 1. Verificar file_line exata
        if self.db_manager.is_downloaded(file_line):
            return True, "exact_line_match"
        
        # 2. Verificar filename normalizado
        filename_norm = self.normalize_filename(filename)
        if filename_norm and self.db_manager.is_duplicate_normalized(filename_norm):
            return True, "normalized_filename_match"
        
        # 3. Verificar fuzzy match artista+música
        similar_songs = self.fuzzy_match_song(artist, song, 0.85)
        if similar_songs:
            return True, "fuzzy_match"
        
        return False, "no_duplicate"
    
    def extract_artist_song(self, file_line: str) -> Tuple[str, str]:
        """Extrai artista e música da linha do arquivo"""
        parts = file_line.split(' - ')
        
        if len(parts) >= 3:
            # Formato: ARTISTA - ALBUM - MUSICA
            return parts[0].strip(), parts[2].strip()
        elif len(parts) == 2:
            # Formato: ARTISTA - MUSICA
            return parts[0].strip(), parts[1].strip()
        else:
            # Formato desconhecido
            return "", file_line.strip()
