#!/usr/bin/env python3

"""
Módulo para extração inteligente de nomes de álbuns
Usa music-tag quando disponível e análise de padrões como fallback
"""

import os
import re

# Verifica se music-tag está disponível
try:
    import music_tag
    MUSIC_TAG_AVAILABLE = True
except ImportError:
    MUSIC_TAG_AVAILABLE = False

def extract_album_name_from_path(directory_path: str) -> str:
    """Extrai nome do álbum do caminho do diretório (método básico)"""
    if not directory_path:
        return "Álbum Desconhecido"
    
    # Pega o último diretório do caminho
    album_name = os.path.basename(directory_path)
    
    # Se estiver vazio, pega o penúltimo
    if not album_name:
        parts = directory_path.rstrip('/\\').split('/')
        if len(parts) > 1:
            album_name = parts[-2]
    
    # Limita o tamanho
    if len(album_name) > 50:
        album_name = album_name[:47] + "..."
    
    return album_name or "Álbum Desconhecido"

def extract_album_name_from_metadata_file(file_path: str) -> str:
    """Extrai nome do álbum de um arquivo MP3 usando music-tag"""
    if not MUSIC_TAG_AVAILABLE or not os.path.exists(file_path):
        return None
    
    try:
        audio_file = music_tag.load_file(file_path)
        album = str(audio_file.get('album', '')).strip()
        
        if album and len(album) > 2:
            # Remove caracteres problemáticos
            clean_album = re.sub(r'[<>:"/\\|?*]', '', album)
            clean_album = re.sub(r'\s+', ' ', clean_album).strip()
            
            if len(clean_album) > 50:
                clean_album = clean_album[:47] + "..."
            
            return clean_album
        
        return None
        
    except Exception as e:
        print(f"Erro ao ler metadados de {file_path}: {e}")
        return None

def extract_album_name_from_pattern_analysis(candidate: dict) -> str:
    """Extrai nome do álbum usando análise de padrões nos caminhos e nomes"""
    try:
        files = candidate.get('files', [])
        if not files:
            return extract_album_name_from_path(candidate['directory'])
        
        album_names = []
        
        # Análise do diretório
        directory = candidate['directory']
        if directory:
            # Procura por padrões comuns de organização
            parts = directory.replace('\\', '/').split('/')
            
            for part in reversed(parts):
                if part and not part.lower() in ['music', 'mp3', 'flac', 'audio', 'downloads']:
                    # Remove anos e outros padrões comuns
                    clean_part = re.sub(r'\b(19|20)\d{2}\b', '', part).strip()
                    clean_part = re.sub(r'[\[\]()]', '', clean_part).strip()
                    clean_part = re.sub(r'\s+', ' ', clean_part).strip()
                    
                    # Remove padrões de qualidade
                    clean_part = re.sub(r'\b(320|256|192|128)\s*kbps?\b', '', clean_part, flags=re.IGNORECASE).strip()
                    clean_part = re.sub(r'\b(FLAC|MP3|V0|V2)\b', '', clean_part, flags=re.IGNORECASE).strip()
                    
                    if len(clean_part) > 3:  # Nome mínimo válido
                        album_names.append(clean_part)
                        break
        
        # Análise dos nomes dos arquivos
        for file_info in files[:3]:  # Analisa até 3 arquivos
            filename = file_info.get('filename', '')
            if not filename.lower().endswith(('.mp3', '.flac', '.wav')):
                continue
            
            basename = os.path.basename(filename)
            # Remove extensão e número da faixa
            clean_name = re.sub(r'\.(mp3|flac|wav)$', '', basename, flags=re.IGNORECASE)
            clean_name = re.sub(r'^\d+[\s\-\.]*', '', clean_name)  # Remove número da faixa
            
            # Procura por padrões como "Artist - Album - Track"
            if ' - ' in clean_name:
                parts = clean_name.split(' - ')
                if len(parts) >= 3:  # Artist - Album - Track
                    potential_album = parts[1].strip()
                    if len(potential_album) > 3:
                        album_names.append(potential_album)
                elif len(parts) == 2:  # Pode ser Album - Track
                    first_part = parts[0].strip()
                    if len(first_part) > 8:  # Provavelmente um álbum
                        album_names.append(first_part)
        
        # Escolhe o melhor nome
        if album_names:
            # Remove duplicatas mantendo ordem
            unique_names = []
            for name in album_names:
                if name not in unique_names and len(name.strip()) > 3:
                    unique_names.append(name.strip())
            
            if unique_names:
                # Pega o primeiro nome válido
                best_name = unique_names[0]
                
                # Limita o tamanho
                if len(best_name) > 50:
                    best_name = best_name[:47] + "..."
                
                return best_name
        
        # Fallback para nome do diretório
        return extract_album_name_from_path(candidate['directory'])
        
    except Exception as e:
        print(f"Erro na análise de padrões: {e}")
        return extract_album_name_from_path(candidate['directory'])

def extract_album_name_smart(candidate: dict, file_paths: list = None) -> str:
    """
    Extrai nome do álbum usando múltiplas estratégias:
    1. Metadados dos arquivos MP3 (se music-tag disponível e arquivos acessíveis)
    2. Análise de padrões nos caminhos e nomes
    3. Fallback para nome do diretório
    """
    
    # Estratégia 1: Tentar usar metadados se arquivos estão disponíveis
    if MUSIC_TAG_AVAILABLE and file_paths:
        for file_path in file_paths[:3]:  # Tenta até 3 arquivos
            if os.path.exists(file_path) and file_path.lower().endswith(('.mp3', '.flac')):
                album_name = extract_album_name_from_metadata_file(file_path)
                if album_name:
                    return album_name
    
    # Estratégia 2: Análise de padrões
    pattern_name = extract_album_name_from_pattern_analysis(candidate)
    if pattern_name and pattern_name != "Álbum Desconhecido":
        return pattern_name
    
    # Estratégia 3: Fallback para diretório
    return extract_album_name_from_path(candidate['directory'])

def clean_album_name(name: str) -> str:
    """Limpa e padroniza nome do álbum"""
    if not name:
        return "Álbum Desconhecido"
    
    # Remove caracteres problemáticos
    clean = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Remove padrões de qualidade comuns
    clean = re.sub(r'\b(320|256|192|128)\s*kbps?\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(FLAC|MP3|V0|V2|CD|Vinyl|Remaster|Remastered)\b', '', clean, flags=re.IGNORECASE)
    
    # Remove anos isolados
    clean = re.sub(r'\b(19|20)\d{2}\b', '', clean)
    
    # Remove colchetes e parênteses vazios
    clean = re.sub(r'\[\s*\]|\(\s*\)', '', clean)
    
    # Normaliza espaços
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Remove traços no início/fim
    clean = clean.strip(' -_.')
    
    if len(clean) < 3:
        return "Álbum Desconhecido"
    
    # Limita tamanho
    if len(clean) > 50:
        clean = clean[:47] + "..."
    
    return clean

# Função principal para uso externo
def get_album_name(candidate: dict, file_paths: list = None) -> str:
    """
    Função principal para extrair nome do álbum
    
    Args:
        candidate: Dicionário com informações do candidato (username, directory, files, etc.)
        file_paths: Lista opcional de caminhos para arquivos locais (para usar metadados)
    
    Returns:
        Nome do álbum extraído e limpo
    """
    raw_name = extract_album_name_smart(candidate, file_paths)
    return clean_album_name(raw_name)

if __name__ == "__main__":
    # Teste básico
    test_candidate = {
        'username': 'test_user',
        'directory': '/Music/Pink Floyd/The Dark Side of the Moon [1973] [320kbps]',
        'files': [
            {'filename': '/Music/Pink Floyd/The Dark Side of the Moon [1973] [320kbps]/01 - Speak to Me.mp3'},
            {'filename': '/Music/Pink Floyd/The Dark Side of the Moon [1973] [320kbps]/02 - Breathe.mp3'},
        ]
    }
    
    print("🧪 Teste do extrator de nomes de álbum:")
    print(f"Resultado: {get_album_name(test_candidate)}")
