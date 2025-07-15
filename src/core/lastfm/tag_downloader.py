#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para obter e baixar músicas populares de tags do Last.fm.
IMPORTANTE: Este módulo baixa APENAS tracks individuais, nunca álbuns completos.
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

def get_lastfm_network(use_oauth=True):
    """
    Inicializa e retorna uma conexão com a rede do Last.fm.
    
    Args:
        use_oauth (bool): Se True, usa autenticação OAuth; se False, usa apenas API key/secret
    
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
    
    # Tentar autenticação OAuth primeiro se solicitado
    if use_oauth:
        try:
            from .oauth_auth import get_oauth_network
            logger.info("🔐 Tentando autenticação OAuth...")
            oauth_network = get_oauth_network()
            if oauth_network:
                logger.info("✅ Autenticação OAuth bem-sucedida")
                return oauth_network
            else:
                logger.warning("⚠️ Falha na autenticação OAuth, usando API básica...")
        except ImportError:
            logger.warning("⚠️ Módulo OAuth não encontrado, usando API básica...")
        except Exception as e:
            logger.warning(f"⚠️ Erro na autenticação OAuth: {e}, usando API básica...")
    
    # Fallback para autenticação básica (apenas API key/secret)
    try:
        logger.info("🔑 Usando autenticação básica (API key/secret)")
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Testar a conexão com uma chamada simples
        try:
            network.get_top_tags(limit=1)
            logger.info("✅ Conexão básica com Last.fm API estabelecida com sucesso")
        except pylast.WSError as e:
            logger.error(f"❌ API key ou secret inválidos: {e}")
            return None
        
        return network
    
    except pylast.PyLastError as e:
        logger.error(f"❌ Erro ao inicializar a rede do Last.fm: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao conectar com Last.fm: {e}")
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

def _is_album_file(filename, directory_files_count=0):
    """
    Verifica se um arquivo parece ser parte de um álbum completo.
    
    Args:
        filename (str): Nome do arquivo
        directory_files_count (int): Número de arquivos MP3 no mesmo diretório
        
    Returns:
        bool: True se parece ser álbum, False se parece ser track individual
    """
    filename_lower = filename.lower()
    
    # Indicadores claros de álbum completo
    album_indicators = [
        'full album', 'complete album', 'entire album', 'whole album',
        'discography', 'collection', 'anthology', 'greatest hits',
        'best of', 'compilation', 'box set', 'complete works',
        'the complete', 'all songs', 'all tracks', 'full discography'
    ]
    
    # Verificar indicadores no nome do arquivo
    for indicator in album_indicators:
        if indicator in filename_lower:
            logger.warning(f"🚫 Arquivo rejeitado (indicador de álbum): '{indicator}' em '{filename}'")
            return True
    
    # Se há muitos arquivos no mesmo diretório, provavelmente é um álbum
    if directory_files_count > 8:
        logger.warning(f"🚫 Possível álbum detectado: {directory_files_count} arquivos MP3 no mesmo diretório")
        return True
    
    # Verificar padrões de numeração que indicam álbum (01-, 02-, etc.)
    track_number_patterns = [
        r'^\d{2}[-_\s]',  # 01-, 02_, 03 
        r'[-_\s]\d{2}[-_\s]',  # -01-, _02_, 03 
        r'track\s*\d+',  # track 1, track01
        r'cd\d+',  # cd1, cd2
        r'disc\s*\d+'  # disc 1, disc2
    ]
    
    for pattern in track_number_patterns:
        if re.search(pattern, filename_lower):
            logger.warning(f"🚫 Arquivo rejeitado (padrão de álbum): padrão '{pattern}' em '{filename}'")
            return True
    
    return False

def _search_single_track_only(slskd, query):
    """
    Busca e baixa APENAS uma track individual, com verificações rigorosas contra álbuns.
    Esta função implementa múltiplas camadas de proteção contra download de álbuns.
    
    Args:
        slskd: Cliente SLSKD conectado
        query (str): Query de busca no formato "Artista - Título"
        
    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    logger.info(f"🎯 BUSCA RESTRITA A TRACK INDIVIDUAL: '{query}'")
    logger.info("🚫 ÁLBUNS SERÃO AUTOMATICAMENTE REJEITADOS")
    
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
    
    # Criar variações de busca focadas em track individual
    variations = create_search_variations(query)
    
    # Filtrar variações que podem resultar em álbums
    filtered_variations = []
    for variation in variations:
        variation_lower = variation.lower()
        # Evitar termos que podem trazer álbuns
        avoid_terms = ['album', 'discography', 'collection', 'complete', 'full']
        if not any(term in variation_lower for term in avoid_terms):
            filtered_variations.append(variation)
    
    logger.info(f"📝 {len(filtered_variations)} variações filtradas para track individual")
    
    for i, search_term in enumerate(filtered_variations, 1):
        logger.info(f"📍 Tentativa {i}/{len(filtered_variations)}: '{search_term}'")
        
        try:
            logger.info(f"🔍 Buscando APENAS track individual: '{search_term}'")
            
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
            
            # Score mínimo mais alto para ser mais seletivo
            min_score = int(os.getenv('MIN_MP3_SCORE', 15))
            
            # Procurar o melhor arquivo MP3 individual com verificações rigorosas
            best_file, best_user, best_score = find_best_mp3(search_responses, query)
            
            if best_file and best_score > min_score:
                filename = best_file.get('filename', '')
                logger.info(f"🎵 Candidato encontrado (score: {best_score:.1f}):")
                logger.info(f"   👤 Usuário: {best_user}")
                logger.info(f"   📄 Arquivo: {filename}")
                logger.info(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                logger.info(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                
                # VERIFICAÇÃO 1: Analisar nome do arquivo
                if _is_album_file(filename):
                    logger.warning(f"🚫 REJEITADO: Arquivo parece ser álbum")
                    continue
                
                # VERIFICAÇÃO 2: Contar arquivos no mesmo diretório
                directory_path = os.path.dirname(filename)
                files_in_same_dir = []
                
                for response in search_responses:
                    if response.get('username') == best_user:
                        for file_info in response.get('files', []):
                            file_dir = os.path.dirname(file_info.get('filename', ''))
                            if file_dir == directory_path and file_info.get('filename', '').lower().endswith('.mp3'):
                                files_in_same_dir.append(file_info)
                
                # VERIFICAÇÃO 3: Verificar se há muitos arquivos no mesmo diretório
                if _is_album_file(filename, len(files_in_same_dir)):
                    logger.warning(f"🚫 REJEITADO: {len(files_in_same_dir)} arquivos MP3 no mesmo diretório (provável álbum)")
                    continue
                
                # VERIFICAÇÃO 4: Verificar tamanho do arquivo (álbuns tendem a ser muito grandes)
                file_size_mb = best_file.get('size', 0) / 1024 / 1024
                if file_size_mb > 100:  # Mais de 100MB provavelmente é álbum
                    logger.warning(f"🚫 REJEITADO: Arquivo muito grande ({file_size_mb:.1f} MB, provável álbum)")
                    continue
                
                # VERIFICAÇÃO 5: Verificar duração se disponível
                duration = best_file.get('length', 0)
                if duration > 3600:  # Mais de 1 hora provavelmente é álbum
                    logger.warning(f"🚫 REJEITADO: Duração muito longa ({duration/60:.1f} min, provável álbum)")
                    continue
                
                logger.info("✅ APROVADO: Arquivo passou em todas as verificações anti-álbum")
                
                # Tentar download da track individual
                success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                if success:
                    logger.info(f"✅ TRACK INDIVIDUAL baixada com sucesso: '{search_term}'!")
                    # Adicionar ao histórico com parâmetros corretos
                    add_to_download_history(query, best_file.get('filename', ''), best_user, best_file.get('size', 0))
                    return True
                else:
                    logger.warning(f"❌ Falha no download da track individual")
            else:
                logger.warning(f"❌ Nenhuma track adequada encontrada (melhor score: {best_score:.1f})")
            
            # Pausa entre tentativas
            if i < len(filtered_variations):
                logger.info("⏸️ Pausa entre buscas...")
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"❌ Erro na busca da track: {e}")
    
    logger.warning(f"❌ Não foi possível baixar a track individual: '{query}'")
    logger.info("💡 Todas as verificações anti-álbum foram aplicadas")
    return False

def download_tracks_by_tag(tag_name, limit=25, output_dir=None, skip_existing=True):
    """
    Baixa as músicas mais populares de uma tag do Last.fm.
    GARANTE que apenas tracks individuais sejam baixadas, nunca álbuns completos.
    
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
        add_to_download_history
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
    logger.info("🚫 MODO ANTI-ÁLBUM ATIVADO: Apenas tracks individuais serão baixadas")
    
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
        
        logger.info(f"[{i}/{len(top_tracks)}] Baixando TRACK INDIVIDUAL: '{query}'")
        
        try:
            # Usar busca restrita para APENAS tracks individuais
            result = _search_single_track_only(slskd, query)
            if result:
                successful += 1
                logger.info(f"✓ TRACK INDIVIDUAL baixada: '{query}'")
            else:
                failed += 1
                logger.warning(f"✗ Falha no download da track: '{query}'")
            
            # Pequena pausa entre downloads para não sobrecarregar o servidor
            time.sleep(2)
        except Exception as e:
            failed += 1
            logger.error(f"Erro ao processar '{query}': {e}")
    
    # Resumo final
    logger.info(f"\n📊 DOWNLOAD CONCLUÍDO - Tag: '{tag_name}'")
    logger.info(f"🎯 MODO: Apenas tracks individuais (álbuns rejeitados)")
    logger.info(f"📊 Total de músicas: {len(top_tracks)}")
    logger.info(f"✅ Downloads bem-sucedidos: {successful}")
    logger.info(f"❌ Downloads com falha: {failed}")
    logger.info(f"⏭️ Músicas puladas (já baixadas): {skipped}")
    
    # Restaurar diretório original
    os.chdir(original_dir)
    
    return (len(top_tracks), successful, failed, skipped)

def get_artist_top_tracks(artist_name, limit=30):
    """
    Obtém as músicas mais populares de um artista específico do Last.fm.
    
    Args:
        artist_name (str): Nome do artista
        limit (int): Número máximo de músicas para retornar
        
    Returns:
        list: Lista de tuplas (artista, título, playcount) das músicas mais populares
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
        # Obter o artista
        artist = network.get_artist(artist_name)
        
        # Obter as músicas mais populares do artista
        top_tracks = artist.get_top_tracks(limit=limit)
        
        # Formatar os resultados como tuplas (artista, título, playcount)
        results = []
        for track in top_tracks:
            artist_name_result = track.item.get_artist().get_name()
            title = track.item.get_title()
            playcount = track.weight if hasattr(track, 'weight') else 0
            results.append((artist_name_result, title, playcount))
        
        logger.info(f"Encontradas {len(results)} músicas para o artista '{artist_name}'")
        return results
    
    except pylast.WSError as e:
        if "Artist not found" in str(e):
            logger.error(f"❌ Artista '{artist_name}' não encontrado no Last.fm")
            logger.error("💡 Verifique a grafia do nome do artista")
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

def download_artist_top_tracks(artist_name, limit=30, output_dir=None, skip_existing=True):
    """
    Baixa as músicas mais populares de um artista do Last.fm.
    GARANTE que apenas tracks individuais sejam baixadas, nunca álbuns completos.
    
    Args:
        artist_name (str): Nome do artista
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
        add_to_download_history
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
    
    # Obter as músicas mais populares do artista
    logger.info(f"Obtendo as {limit} músicas mais populares do artista '{artist_name}'...")
    top_tracks = get_artist_top_tracks(artist_name, limit)
    
    if top_tracks is None:
        logger.error("Falha na autenticação ou configuração do Last.fm")
        os.chdir(original_dir)
        return None
    
    if not top_tracks:
        logger.error(f"Nenhuma música encontrada para o artista '{artist_name}'")
        os.chdir(original_dir)
        return (0, 0, 0, 0)
    
    logger.info(f"Encontradas {len(top_tracks)} músicas. Iniciando downloads...")
    logger.info("🚫 MODO ANTI-ÁLBUM ATIVADO: Apenas tracks individuais serão baixadas")
    
    # Criar diretório para o artista
    artist_dir = sanitize_filename(artist_name)
    os.makedirs(artist_dir, exist_ok=True)
    os.chdir(artist_dir)
    
    # Baixar cada música
    successful = 0
    failed = 0
    skipped = 0
    
    for i, (artist, title, playcount) in enumerate(top_tracks, 1):
        # Formatar a consulta como "Artista - Título"
        query = f"{artist} - {title}"
        
        # Verificar se já foi baixada anteriormente
        if skip_existing and is_duplicate_download(query):
            logger.info(f"[{i}/{len(top_tracks)}] Pulando (já baixada): '{query}' ({playcount:,} plays)")
            skipped += 1
            continue
        
        logger.info(f"[{i}/{len(top_tracks)}] Baixando TRACK INDIVIDUAL: '{query}' ({playcount:,} plays)")
        
        try:
            # Usar busca restrita para APENAS tracks individuais
            result = _search_single_track_only(slskd, query)
            if result:
                successful += 1
                logger.info(f"✓ TRACK INDIVIDUAL baixada: '{query}'")
            else:
                failed += 1
                logger.warning(f"✗ Falha no download da track: '{query}'")
            
            # Pequena pausa entre downloads
            time.sleep(2)
        except Exception as e:
            failed += 1
            logger.error(f"Erro ao processar '{query}': {e}")
    
    # Resumo final
    logger.info(f"\n📊 DOWNLOAD CONCLUÍDO - Artista: '{artist_name}'")
    logger.info(f"🎯 MODO: Apenas tracks individuais (álbuns rejeitados)")
    logger.info(f"📊 Total de músicas: {len(top_tracks)}")
    logger.info(f"✅ Downloads bem-sucedidos: {successful}")
    logger.info(f"❌ Downloads com falha: {failed}")
    logger.info(f"⏭️ Músicas puladas (já baixadas): {skipped}")
    
    # Restaurar diretório original
    os.chdir(original_dir)
    
    return (len(top_tracks), successful, failed, skipped)