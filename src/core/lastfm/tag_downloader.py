#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para obter e baixar músicas populares de tags do Last.fm.
"""

import os
import sys
import pylast
from dotenv import load_dotenv
import logging
import time
import re

# Configurar logging
logger = logging.getLogger('lastfm_downloader')

def sanitize_filename(name):
    """Remove caracteres inválidos para nomes de arquivos."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_lastfm_network():
    """
    Inicializa e retorna uma conexão com a rede do Last.fm.
    
    Returns:
        pylast.LastFMNetwork: Objeto de conexão com a API do Last.fm
        None: Se as credenciais não forem encontradas ou ocorrer um erro
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter credenciais do Last.fm
    api_key = os.getenv("LASTFM_API_KEY")
    api_secret = os.getenv("LASTFM_API_SECRET")
    username = os.getenv("LASTFM_USERNAME")
    password = os.getenv("LASTFM_PASSWORD")
    
    if not api_key or not api_secret:
        logger.error("Credenciais do Last.fm não encontradas no arquivo .env")
        return None
    
    try:
        # Criar hash da senha se fornecida
        password_hash = None
        if username and password:
            password_hash = pylast.md5(password)
        
        # Inicializar a rede do Last.fm
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username,
            password_hash=password_hash
        )
        
        return network
    
    except Exception as e:
        logger.error(f"Erro ao inicializar a rede do Last.fm: {e}")
        return None

def get_top_tracks_by_tag(tag_name, limit=25):
    """
    Obtém as músicas mais populares para uma tag específica do Last.fm.
    
    Args:
        tag_name (str): Nome da tag (ex: "rock alternativo")
        limit (int): Número máximo de músicas para retornar
        
    Returns:
        list: Lista de tuplas (artista, título) das músicas mais populares
    """
    network = get_lastfm_network()
    if not network:
        return []
    
    try:
        # Obter a tag
        tag = network.get_tag(tag_name)
        
        # Obter as músicas mais populares para a tag
        top_tracks = tag.get_top_tracks(limit=limit)
        
        # Formatar os resultados como tuplas (artista, título)
        results = []
        for track in top_tracks:
            artist = track.item.get_artist().get_name()
            title = track.item.get_title()
            results.append((artist, title))
            
        return results
    
    except pylast.PyLastError as e:
        logger.error(f"Erro ao acessar a API do Last.fm: {e}")
        return []
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return []

def download_tracks_by_tag(tag_name, limit=25, output_dir=None, skip_existing=True):
    """
    Baixa as músicas mais populares de uma tag do Last.fm.
    
    Args:
        tag_name (str): Nome da tag (ex: "rock alternativo")
        limit (int): Número máximo de músicas para baixar
        output_dir (str): Diretório de saída para os downloads
        skip_existing (bool): Se True, pula músicas já baixadas anteriormente
        
    Returns:
        tuple: (total, successful, failed, skipped) contagem de downloads
    """
    # Importar funções necessárias
    from cli.main import search_and_download, is_duplicate_download
    
    # Definir diretório de saída se especificado
    original_dir = os.getcwd()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)
    
    # Obter as músicas mais populares para a tag
    logger.info(f"Obtendo as {limit} músicas mais populares para a tag '{tag_name}'...")
    top_tracks = get_top_tracks_by_tag(tag_name, limit)
    
    if not top_tracks:
        logger.error(f"Nenhuma música encontrada para a tag '{tag_name}'")
        os.chdir(original_dir)
        return (0, 0, 0, 0)
    
    logger.info(f"Encontradas {len(top_tracks)} músicas. Iniciando downloads...")
    
    # Criar diretório para a tag
    tag_dir = sanitize_filename(tag_name)
    os.makedirs(tag_dir, exist_ok=True)
    os.chdir(tag_dir)
    
    # Baixar cada música
    successful = 0
    failed = 0
    skipped = 0
    
    for i, (artist, title) in enumerate(top_tracks, 1):
        # Formatar a consulta como "Artista - Título"
        query = f"{artist} - {title}"
        
        # Verificar se já foi baixada anteriormente
        if skip_existing and is_duplicate_download(query):
            logger.info(f"[{i}/{len(top_tracks)}] Pulando (já baixada): '{query}'")
            skipped += 1
            continue
        
        logger.info(f"[{i}/{len(top_tracks)}] Baixando '{query}'")
        
        try:
            # Chamar a função de download
            if search_and_download(query):
                successful += 1
                logger.info(f"✓ Download concluído: '{query}'")
            else:
                failed += 1
                logger.warning(f"✗ Falha no download: '{query}'")
            
            # Pequena pausa entre downloads para não sobrecarregar o servidor
            time.sleep(2)
        except Exception as e:
            failed += 1
            logger.error(f"Erro ao processar '{query}': {e}")
    
    # Resumo final
    logger.info(f"\nDownload concluído para a tag '{tag_name}'")
    logger.info(f"Total de músicas: {len(top_tracks)}")
    logger.info(f"Downloads bem-sucedidos: {successful}")
    logger.info(f"Downloads com falha: {failed}")
    logger.info(f"Músicas puladas (já baixadas): {skipped}")
    
    # Restaurar diretório original
    os.chdir(original_dir)
    
    return (len(top_tracks), successful, failed, skipped)
