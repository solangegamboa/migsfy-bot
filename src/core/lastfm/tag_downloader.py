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
    Inicializa e retorna uma conexão com a rede do Last.fm usando apenas API key e secret.
    
    Returns:
        pylast.LastFMNetwork: Objeto de conexão com a API do Last.fm
        None: Se as credenciais não forem encontradas ou ocorrer um erro
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter credenciais do Last.fm
    api_key = os.getenv("LASTFM_API_KEY")
    api_secret = os.getenv("LASTFM_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("Credenciais do Last.fm não encontradas no arquivo .env")
        logger.error("💡 Configure LASTFM_API_KEY e LASTFM_API_SECRET no arquivo .env")
        logger.error("💡 Obtenha suas credenciais em: https://www.last.fm/api/account/create")
        return None
    
    try:
        # Inicializar a rede do Last.fm apenas com API key e secret
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Testar a conexão com uma chamada simples
        try:
            network.get_top_tags(limit=1)
            logger.info("Conexão com Last.fm API estabelecida com sucesso")
        except pylast.WSError as e:
            logger.error(f"API key ou secret inválidos: {e}")
            return None
        
        return network
    
    except pylast.PyLastError as e:
        logger.error(f"Erro ao inicializar a rede do Last.fm: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao conectar com Last.fm: {e}")
        return None

def get_top_tracks_by_tag(tag_name, limit=25):
    """
    Obtém as músicas mais populares para uma tag específica do Last.fm.
    
    Args:
        tag_name (str): Nome da tag (ex: "rock alternativo")
        limit (int): Número máximo de músicas para retornar
        
    Returns:
        list: Lista de tuplas (artista, título) das músicas mais populares
        None: Se houver erro de autenticação ou API indisponível
    """
    # Tentar usar a API do Last.fm
    network = get_lastfm_network()
    
    # Se não conseguir conectar à API, retornar erro
    if not network:
        logger.error("❌ Não foi possível conectar à API do Last.fm")
        logger.error("💡 Verifique suas credenciais LASTFM_API_KEY e LASTFM_API_SECRET no arquivo .env")
        logger.error("💡 Obtenha suas credenciais em: https://www.last.fm/api/account/create")
        return None
    
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
        
        logger.info(f"Encontradas {len(results)} músicas para a tag '{tag_name}'")
        return results
    
    except pylast.WSError as e:
        if "Tag not found" in str(e):
            logger.error(f"❌ Tag '{tag_name}' não encontrada no Last.fm")
            logger.error("💡 Tente tags populares como: rock, pop, jazz, metal, alternative rock")
        else:
            logger.error(f"❌ Erro na API do Last.fm: {e}")
            if "Invalid API key" in str(e) or "Invalid method signature" in str(e):
                logger.error("💡 Verifique suas credenciais LASTFM_API_KEY e LASTFM_API_SECRET no arquivo .env")
        return None
    except pylast.PyLastError as e:
        logger.error(f"❌ Erro ao acessar a API do Last.fm: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return None



def download_tracks_by_tag(tag_name, limit=25, output_dir=None, skip_existing=True):
    """
    Baixa as músicas mais populares de uma tag do Last.fm.
    Força o download apenas de tracks individuais, nunca álbuns completos.
    
    Args:
        tag_name (str): Nome da tag (ex: "rock alternativo")
        limit (int): Número máximo de músicas para baixar
        output_dir (str): Diretório de saída para os downloads
        skip_existing (bool): Se True, pula músicas já baixadas anteriormente
        
    Returns:
        tuple: (total, successful, failed, skipped) contagem de downloads
    """
    # Importar funções necessárias
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    from cli.main import (
        is_duplicate_download, 
        connectToSlskd,
        create_search_variations,
        wait_for_search_completion,
        find_best_mp3,
        smart_download_with_fallback,
        add_to_download_history,
        smart_mp3_search
    )
    
    # Conectar ao SLSKD
    slskd = connectToSlskd()
    if not slskd:
        logger.error("Não foi possível conectar ao servidor SLSKD")
        return (0, 0, 0, 0)
    
    # Definir diretório de saída se especificado
    original_dir = os.getcwd()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)
    
    # Obter as músicas mais populares para a tag
    logger.info(f"Obtendo as {limit} músicas mais populares para a tag '{tag_name}'...")
    top_tracks = get_top_tracks_by_tag(tag_name, limit)
    
    if top_tracks is None:
        logger.error(f"Falha na autenticação ou configuração do Last.fm")
        os.chdir(original_dir)
        return None
    
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
            # Usar busca inteligente para tracks individuais
            result = smart_mp3_search(slskd, query)
            if result:
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

def _search_single_track_only(slskd, query):
    """
    Busca e baixa apenas uma track individual, nunca álbuns completos.
    Esta função força o download de tracks unitárias, ignorando detecção de álbuns.
    
    Args:
        slskd: Cliente SLSKD conectado
        query (str): Query de busca no formato "Artista - Título"
        
    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    logger.info(f"🎯 Busca forçada por TRACK INDIVIDUAL: '{query}'")
    
    # Importar funções necessárias localmente para evitar problemas de importação circular
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    from cli.main import (
        create_search_variations,
        wait_for_search_completion,
        find_best_mp3,
        smart_download_with_fallback,
        add_to_download_history,
        extract_artist_and_song
    )
    
    # Extrair artista e música
    artist, song = extract_artist_and_song(query)
    if artist and song:
        logger.info(f"🎤 Artista: '{artist}' | 🎵 Música: '{song}'")
    
    # Criar variações de busca
    variations = create_search_variations(query)
    logger.info(f"📝 {len(variations)} variações criadas para track individual")
    
    for i, search_term in enumerate(variations, 1):
        logger.info(f"📍 Tentativa {i}/{len(variations)}: '{search_term}'")
        
        try:
            logger.info(f"🔍 Buscando track: '{search_term}'")
            
            # Executar busca
            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get('id')
            
            # Aguardar conclusão da busca
            search_responses = wait_for_search_completion(slskd, search_id, max_wait=int(os.getenv('SEARCH_WAIT_TIME', 25)))
            
            if not search_responses:
                logger.warning("❌ Nenhuma resposta")
                continue
            
            # Contar total de arquivos encontrados
            total_files = sum(len(response.get('files', [])) for response in search_responses)
            logger.info(f"📊 Total de arquivos encontrados: {total_files}")
            
            if total_files == 0:
                continue
            
            # Score mínimo configurável (mais baixo para tracks individuais)
            min_score = int(os.getenv('MIN_MP3_SCORE', 10))
            
            # Procurar o melhor arquivo MP3 individual
            best_file, best_user, best_score = find_best_mp3(search_responses, query)
            
            if best_file and best_score > min_score:
                logger.info(f"🎵 Melhor track encontrada (score: {best_score:.1f}):")
                logger.info(f"   👤 Usuário: {best_user}")
                logger.info(f"   📄 Arquivo: {best_file.get('filename')}")
                logger.info(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                logger.info(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                
                # Verificar se o arquivo parece ser de um álbum completo
                filename = best_file.get('filename', '').lower()
                
                # Indicadores de que pode ser parte de um álbum
                album_indicators = [
                    'full album', 'complete album', 'entire album', 'whole album',
                    'discography', 'collection', 'anthology', 'greatest hits',
                    'best of', 'compilation', 'box set'
                ]
                
                # Se o nome do arquivo contém indicadores de álbum, pular
                is_album_file = any(indicator in filename for indicator in album_indicators)
                
                # Também verificar se o diretório contém muitos arquivos (possível álbum)
                directory_path = os.path.dirname(best_file.get('filename', ''))
                files_in_same_dir = []
                
                for response in search_responses:
                    if response.get('username') == best_user:
                        for file_info in response.get('files', []):
                            file_dir = os.path.dirname(file_info.get('filename', ''))
                            if file_dir == directory_path and file_info.get('filename', '').lower().endswith('.mp3'):
                                files_in_same_dir.append(file_info)
                
                # Se há muitos arquivos no mesmo diretório, pode ser um álbum
                if len(files_in_same_dir) > 8:  # Mais de 8 tracks no mesmo diretório = provável álbum
                    logger.warning(f"⚠️ Possível álbum detectado ({len(files_in_same_dir)} tracks no mesmo diretório)")
                    logger.info(f"🎯 Forçando download apenas da track individual: '{query}'")
                
                if is_album_file:
                    logger.warning(f"⚠️ Arquivo parece ser álbum completo, pulando: {filename}")
                    continue
                
                # Tentar download da track individual
                success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                if success:
                    logger.info(f"✅ Track individual baixada com sucesso: '{search_term}'!")
                    # Adicionar ao histórico
                    add_to_download_history(query)
                    return True
                else:
                    logger.warning(f"❌ Falha no download da track individual")
            else:
                logger.warning(f"❌ Nenhuma track adequada encontrada (melhor score: {best_score:.1f})")
            
            # Pausa entre tentativas
            if i < len(variations):
                logger.info("⏸️ Pausa entre buscas...")
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"❌ Erro na busca da track: {e}")
    
    logger.warning(f"❌ Não foi possível baixar a track individual: '{query}'")
    return False