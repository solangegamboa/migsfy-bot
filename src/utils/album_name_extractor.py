#!/usr/bin/env python3

"""
Módulo para extração inteligente de nomes de álbuns
Usa music-tag quando disponível e análise de padrões como fallback
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verifica se music-tag está disponível
try:
    import music_tag
    MUSIC_TAG_AVAILABLE = True
    logger.info("music-tag disponível para leitura de metadados")
except ImportError:
    MUSIC_TAG_AVAILABLE = False
    logger.warning("music-tag não disponível - usando apenas análise de padrões")

def extract_album_from_metadata(file_path: str) -> Optional[str]:
    """
    Extrai nome do álbum de um arquivo de áudio usando music-tag
    
    Args:
        file_path: Caminho para o arquivo de áudio
        
    Returns:
        Nome do álbum ou None se não encontrado
    """
    if not MUSIC_TAG_AVAILABLE:
        return None
        
    if not os.path.exists(file_path):
        logger.debug(f"Arquivo não existe: {file_path}")
        return None
    
    # Verifica se é um arquivo de áudio suportado
    audio_extensions = ('.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma')
    if not file_path.lower().endswith(audio_extensions):
        return None
    
    try:
        logger.debug(f"Tentando ler metadados de: {file_path}")
        audio_file = music_tag.load_file(file_path)
        
        # Tenta diferentes tags de álbum
        album_tags = ['album', 'ALBUM', 'Album']
        album = None
        
        for tag in album_tags:
            try:
                album_value = audio_file.get(tag)
                if album_value:
                    album = str(album_value).strip()
                    if album and len(album) > 1:
                        break
            except:
                continue
        
        if album and len(album) > 1:
            # Limpa o nome do álbum
            clean_album = clean_album_name(album)
            if clean_album != "Álbum Desconhecido":
                logger.info(f"Álbum encontrado nos metadados: {clean_album}")
                return clean_album
        
        logger.debug(f"Nenhum álbum válido encontrado nos metadados de {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao ler metadados de {file_path}: {e}")
        return None

def extract_album_from_directory_structure(directory_path: str) -> Optional[str]:
    """
    Extrai nome do álbum da estrutura de diretórios
    Reconhece padrões como: Artist/Album, Music/Artist/Album, etc.
    """
    if not directory_path:
        return None
    
    try:
        # Normaliza o caminho
        path = directory_path.replace('\\', '/').rstrip('/')
        parts = [p for p in path.split('/') if p]
        
        if not parts:
            return None
        
        # Analisa as últimas partes do caminho
        for i in range(len(parts) - 1, max(-1, len(parts) - 4), -1):
            part = parts[i]
            
            # Pula diretórios comuns que não são álbuns
            skip_dirs = {
                'music', 'mp3', 'flac', 'audio', 'downloads', 'complete', 
                'shared', 'files', 'albums', 'collection', 'library'
            }
            
            if part.lower() in skip_dirs:
                continue
            
            # Remove padrões de ano e qualidade
            clean_part = re.sub(r'\[?\b(19|20)\d{2}\b\]?', '', part).strip()
            clean_part = re.sub(r'\[?\b(320|256|192|128)\s*kbps?\b\]?', '', clean_part, flags=re.IGNORECASE).strip()
            clean_part = re.sub(r'\[?\b(FLAC|MP3|V0|V2|CD|Vinyl)\b\]?', '', clean_part, flags=re.IGNORECASE).strip()
            clean_part = re.sub(r'[\[\](){}]', '', clean_part).strip()
            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
            clean_part = clean_part.strip(' -_.')
            
            if len(clean_part) > 3:  # Nome mínimo válido
                logger.debug(f"Álbum extraído do diretório: {clean_part}")
                return clean_part
        
        # Se não encontrou nada válido, usa o último diretório
        last_dir = parts[-1] if parts else ""
        if last_dir:
            clean_last = clean_album_name(last_dir)
            if clean_last != "Álbum Desconhecido":
                return clean_last
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao analisar estrutura de diretório {directory_path}: {e}")
        return None

def extract_album_from_filenames(files: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extrai nome do álbum analisando nomes de arquivos
    Procura por padrões como: Artist - Album - Track
    """
    if not files:
        return None
    
    album_candidates = []
    
    for file_info in files[:5]:  # Analisa até 5 arquivos
        filename = file_info.get('filename', '')
        if not filename:
            continue
        
        # Pega apenas o nome do arquivo
        basename = os.path.basename(filename)
        
        # Remove extensão
        name_without_ext = re.sub(r'\.(mp3|flac|m4a|ogg|wav|wma)$', '', basename, flags=re.IGNORECASE)
        
        # Remove número da faixa no início
        clean_name = re.sub(r'^\d+[\s\-\.]*', '', name_without_ext).strip()
        
        # Procura por padrões com separadores
        separators = [' - ', ' – ', ' — ', '_-_', ' | ']
        
        for sep in separators:
            if sep in clean_name:
                parts = clean_name.split(sep)
                
                if len(parts) >= 3:  # Artist - Album - Track
                    potential_album = parts[1].strip()
                    if len(potential_album) > 0:  # Aceita álbuns curtos como "IV"
                        album_candidates.append(potential_album)
                        
                elif len(parts) == 2:  # Pode ser Album - Track ou Artist - Track
                    first_part = parts[0].strip()
                    # Se a primeira parte é longa, provavelmente é um álbum
                    # Mas também aceita nomes curtos se não parecem ser artistas conhecidos
                    if len(first_part) > 8 or (len(first_part) >= 2 and not _looks_like_artist_name(first_part)):
                        album_candidates.append(first_part)
                break
    
    # Encontra o álbum mais comum
    if album_candidates:
        # Conta ocorrências
        album_count = {}
        for album in album_candidates:
            clean_album = clean_album_name(album)
            if clean_album != "Álbum Desconhecido":
                album_count[clean_album] = album_count.get(clean_album, 0) + 1
        
        if album_count:
            # Retorna o mais comum
            best_album = max(album_count.keys(), key=lambda x: album_count[x])
            logger.debug(f"Álbum extraído dos nomes de arquivo: {best_album}")
            return best_album
    
    return None

def _looks_like_artist_name(name: str) -> bool:
    """
    Verifica se um nome parece ser de um artista (heurística simples)
    """
    # Lista de padrões que geralmente indicam artistas
    artist_patterns = [
        r'\b(feat|ft|featuring)\b',  # featuring
        r'\b(and|&)\b',              # "Artist and Artist"
        r'\b(the)\b',                # "The Artist"
    ]
    
    name_lower = name.lower()
    
    for pattern in artist_patterns:
        if re.search(pattern, name_lower):
            return True
    
    # Se tem mais de 3 palavras, provavelmente é artista
    if len(name.split()) > 3:
        return True
    
    return False

def clean_album_name(name: str) -> str:
    """
    Limpa e padroniza nome do álbum
    
    Args:
        name: Nome bruto do álbum
        
    Returns:
        Nome limpo do álbum
    """
    if not name or not isinstance(name, str):
        return "Álbum Desconhecido"
    
    # Remove caracteres problemáticos para nomes de arquivo
    clean = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Remove padrões de qualidade comuns
    quality_patterns = [
        r'\b(320|256|192|128)\s*kbps?\b',
        r'\b(FLAC|MP3|V0|V2|CD|Vinyl|Digital)\b',
        r'\b(Remaster|Remastered|Deluxe|Special|Edition|Expanded)\b',
        r'\b(Stereo|Mono)\b'
    ]
    
    for pattern in quality_patterns:
        clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
    
    # Remove anos isolados (mas mantém se fizer parte do nome)
    clean = re.sub(r'\s*[\[\(]?\b(19|20)\d{2}\b[\]\)]?\s*', ' ', clean)
    
    # Remove colchetes e parênteses vazios ou com apenas espaços
    clean = re.sub(r'[\[\(]\s*[\]\)]', '', clean)
    
    # Remove múltiplos espaços e normaliza
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Remove caracteres no início/fim
    clean = clean.strip(' -_.,;:')
    
    # Verifica se sobrou algo válido
    if len(clean) < 2:
        return "Álbum Desconhecido"
    
    # Limita tamanho
    if len(clean) > 60:
        clean = clean[:57] + "..."
    
    return clean

def get_album_name(candidate: Dict[str, Any], file_paths: Optional[List[str]] = None) -> str:
    """
    Função principal para extrair nome do álbum usando múltiplas estratégias
    
    Args:
        candidate: Dicionário com informações do candidato (username, directory, files, etc.)
        file_paths: Lista opcional de caminhos para arquivos locais (para usar metadados)
    
    Returns:
        Nome do álbum extraído e limpo
    """
    logger.debug(f"Extraindo nome do álbum para: {candidate.get('directory', 'N/A')}")
    
    # Estratégia 1: Metadados de arquivos locais (se disponíveis) - PRIORIDADE MÁXIMA
    if MUSIC_TAG_AVAILABLE and file_paths:
        for file_path in file_paths[:3]:  # Tenta até 3 arquivos
            if os.path.exists(file_path):
                album_name = extract_album_from_metadata(file_path)
                if album_name:
                    logger.info(f"Álbum encontrado via metadados: {album_name}")
                    return album_name
    
    # Coleta resultados de múltiplas estratégias para comparar
    candidates_found = []
    
    # Estratégia 2: Análise dos nomes de arquivos remotos
    files = candidate.get('files', [])
    if files:
        album_name = extract_album_from_filenames(files)
        if album_name:
            candidates_found.append(('filename', album_name))
    
    # Estratégia 3: Estrutura de diretórios
    directory = candidate.get('directory', '')
    if directory:
        album_name = extract_album_from_directory_structure(directory)
        if album_name:
            candidates_found.append(('directory', album_name))
    
    # Escolhe o melhor candidato
    if candidates_found:
        # Prioriza nomes de arquivos se forem mais específicos que diretórios genéricos
        filename_candidates = [c for c in candidates_found if c[0] == 'filename']
        directory_candidates = [c for c in candidates_found if c[0] == 'directory']
        
        # Se temos candidatos de filename e eles não são genéricos, usa eles
        if filename_candidates:
            best_filename = filename_candidates[0][1]
            # Verifica se não é um nome genérico
            generic_names = {'collection', 'music', 'downloads', 'complete', 'shared', 'files'}
            if best_filename.lower() not in generic_names:
                logger.info(f"Álbum encontrado via análise de arquivos: {best_filename}")
                return best_filename
        
        # Senão, usa o melhor candidato de diretório
        if directory_candidates:
            best_directory = directory_candidates[0][1]
            # Verifica se não é um nome genérico
            generic_names = {'collection', 'music', 'downloads', 'complete', 'shared', 'files'}
            if best_directory.lower() not in generic_names:
                logger.info(f"Álbum encontrado via estrutura de diretório: {best_directory}")
                return best_directory
        
        # Se todos são genéricos, usa o primeiro disponível
        if candidates_found:
            result = candidates_found[0][1]
            logger.info(f"Álbum encontrado (genérico): {result}")
            return result
    
    # Estratégia 4: Fallback - nome do último diretório limpo
    if directory:
        last_dir = os.path.basename(directory.rstrip('/\\'))
        if last_dir:
            clean_name = clean_album_name(last_dir)
            if clean_name != "Álbum Desconhecido":
                logger.info(f"Álbum encontrado via fallback: {clean_name}")
                return clean_name
    
    logger.warning("Não foi possível determinar o nome do álbum")
    return "Álbum Desconhecido"

# Função de compatibilidade (mantém interface antiga)
def extract_album_name_smart(candidate: Dict[str, Any], file_paths: Optional[List[str]] = None) -> str:
    """Função de compatibilidade - usa get_album_name"""
    return get_album_name(candidate, file_paths)

if __name__ == "__main__":
    # Testes básicos
    print("🧪 Teste do extrator de nomes de álbum:")
    
    # Teste 1: Estrutura de diretório
    test_candidate1 = {
        'username': 'test_user',
        'directory': '/Music/Pink Floyd/The Dark Side of the Moon [1973] [320kbps]',
        'files': [
            {'filename': '01 - Speak to Me.mp3'},
            {'filename': '02 - Breathe.mp3'},
        ]
    }
    
    result1 = get_album_name(test_candidate1)
    print(f"Teste 1 - Resultado: '{result1}'")
    
    # Teste 2: Análise de nomes de arquivo
    test_candidate2 = {
        'username': 'test_user',
        'directory': '/shared/music/rock',
        'files': [
            {'filename': 'Pink Floyd - The Wall - Another Brick in the Wall.mp3'},
            {'filename': 'Pink Floyd - The Wall - Comfortably Numb.mp3'},
        ]
    }
    
    result2 = get_album_name(test_candidate2)
    print(f"Teste 2 - Resultado: '{result2}'")
    
    # Teste 3: Caso problemático
    test_candidate3 = {
        'username': 'test_user',
        'directory': '/downloads/complete',
        'files': [
            {'filename': 'track01.mp3'},
            {'filename': 'track02.mp3'},
        ]
    }
    
    result3 = get_album_name(test_candidate3)
    print(f"Teste 3 - Resultado: '{result3}'")
