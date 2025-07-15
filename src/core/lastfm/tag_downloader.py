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
        # Inicializar a rede do Last.fm sem autenticação de usuário primeiro
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Testar a conexão com uma chamada simples
        try:
            network.get_top_tags(limit=1)
            logger.info("Conexão básica com Last.fm API estabelecida com sucesso")
        except pylast.WSError as e:
            logger.error(f"API key ou secret inválidos: {e}")
            return None
        
        # Se chegou até aqui, a conexão básica está funcionando
        # Agora tenta adicionar autenticação de usuário se fornecida
        if username and password:
            try:
                password_hash = pylast.md5(password)
                network = pylast.LastFMNetwork(
                    api_key=api_key,
                    api_secret=api_secret,
                    username=username,
                    password_hash=password_hash
                )
                # Testar autenticação de usuário
                network.get_authenticated_user()
                logger.info("Autenticação de usuário Last.fm bem-sucedida")
            except pylast.WSError as e:
                logger.warning(f"Falha na autenticação de usuário Last.fm: {e}. Usando apenas API key.")
                # Volta para a conexão básica sem autenticação de usuário
                network = pylast.LastFMNetwork(
                    api_key=api_key,
                    api_secret=api_secret
                )
        
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
    """
    # Tentar usar a API do Last.fm
    network = get_lastfm_network()
    
    # Se não conseguir conectar à API, usar dados mockados para testes
    if not network:
        logger.warning("Usando dados mockados para testes (API do Last.fm indisponível)")
        return _get_mock_tracks_for_tag(tag_name, limit)
    
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
            logger.error(f"Tag '{tag_name}' não encontrada no Last.fm")
        else:
            logger.error(f"Erro na API do Last.fm: {e}")
        # Fallback para dados mockados
        return _get_mock_tracks_for_tag(tag_name, limit)
    except pylast.PyLastError as e:
        logger.error(f"Erro ao acessar a API do Last.fm: {e}")
        # Fallback para dados mockados
        return _get_mock_tracks_for_tag(tag_name, limit)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        # Fallback para dados mockados
        return _get_mock_tracks_for_tag(tag_name, limit)

def _get_mock_tracks_for_tag(tag_name, limit=25):
    """
    Retorna uma lista mockada de músicas para uma tag específica.
    Usado quando a API do Last.fm não está disponível.
    
    Args:
        tag_name (str): Nome da tag
        limit (int): Número máximo de músicas para retornar
        
    Returns:
        list: Lista de tuplas (artista, título) das músicas
    """
    # Dicionário de músicas populares por tag
    mock_data = {
        "rock": [
            ("Queen", "Bohemian Rhapsody"),
            ("Led Zeppelin", "Stairway to Heaven"),
            ("Pink Floyd", "Comfortably Numb"),
            ("The Beatles", "Hey Jude"),
            ("AC/DC", "Back in Black"),
            ("Guns N' Roses", "Sweet Child o' Mine"),
            ("Nirvana", "Smells Like Teen Spirit"),
            ("The Rolling Stones", "Paint It Black"),
            ("Eagles", "Hotel California"),
            ("Metallica", "Nothing Else Matters"),
            ("Deep Purple", "Smoke on the Water"),
            ("The Who", "Baba O'Riley"),
            ("Bon Jovi", "Livin' on a Prayer"),
            ("Aerosmith", "Dream On"),
            ("Lynyrd Skynyrd", "Sweet Home Alabama"),
            ("The Doors", "Riders on the Storm"),
            ("Creedence Clearwater Revival", "Fortunate Son"),
            ("Queen", "We Will Rock You"),
            ("Black Sabbath", "Paranoid"),
            ("Jimi Hendrix", "All Along the Watchtower"),
            ("Bruce Springsteen", "Born to Run"),
            ("The Police", "Every Breath You Take"),
            ("U2", "With or Without You"),
            ("Fleetwood Mac", "Go Your Own Way"),
            ("Red Hot Chili Peppers", "Under the Bridge")
        ],
        "pop": [
            ("Michael Jackson", "Billie Jean"),
            ("Madonna", "Like a Prayer"),
            ("Whitney Houston", "I Will Always Love You"),
            ("ABBA", "Dancing Queen"),
            ("Britney Spears", "Baby One More Time"),
            ("Beyoncé", "Crazy in Love"),
            ("Taylor Swift", "Shake It Off"),
            ("Adele", "Rolling in the Deep"),
            ("Ed Sheeran", "Shape of You"),
            ("Katy Perry", "Roar"),
            ("Lady Gaga", "Bad Romance"),
            ("Justin Bieber", "Sorry"),
            ("Rihanna", "Umbrella"),
            ("Bruno Mars", "Uptown Funk"),
            ("Ariana Grande", "Thank U, Next"),
            ("The Weeknd", "Blinding Lights"),
            ("Dua Lipa", "Don't Start Now"),
            ("Mariah Carey", "All I Want for Christmas Is You"),
            ("Elton John", "Tiny Dancer"),
            ("Prince", "Purple Rain"),
            ("George Michael", "Careless Whisper"),
            ("Cyndi Lauper", "Girls Just Want to Have Fun"),
            ("Backstreet Boys", "I Want It That Way"),
            ("Spice Girls", "Wannabe"),
            ("Justin Timberlake", "Can't Stop the Feeling!")
        ],
        "jazz": [
            ("Miles Davis", "So What"),
            ("John Coltrane", "Giant Steps"),
            ("Dave Brubeck", "Take Five"),
            ("Louis Armstrong", "What a Wonderful World"),
            ("Duke Ellington", "Take the A Train"),
            ("Thelonious Monk", "Round Midnight"),
            ("Charlie Parker", "Ornithology"),
            ("Ella Fitzgerald", "Summertime"),
            ("Billie Holiday", "Strange Fruit"),
            ("Herbie Hancock", "Cantaloupe Island"),
            ("Chet Baker", "My Funny Valentine"),
            ("Nina Simone", "Feeling Good"),
            ("Dizzy Gillespie", "A Night in Tunisia"),
            ("Bill Evans", "Waltz for Debby"),
            ("Stan Getz", "The Girl from Ipanema"),
            ("Wes Montgomery", "Four on Six"),
            ("Charles Mingus", "Goodbye Pork Pie Hat"),
            ("Art Blakey", "Moanin'"),
            ("Sonny Rollins", "St. Thomas"),
            ("Oscar Peterson", "C Jam Blues"),
            ("Cannonball Adderley", "Mercy, Mercy, Mercy"),
            ("Sarah Vaughan", "Misty"),
            ("Wynton Marsalis", "Black Codes"),
            ("Pat Metheny", "Bright Size Life"),
            ("Diana Krall", "The Look of Love")
        ],
        "metal": [
            ("Metallica", "Master of Puppets"),
            ("Black Sabbath", "Iron Man"),
            ("Iron Maiden", "The Number of the Beast"),
            ("Judas Priest", "Breaking the Law"),
            ("Slayer", "Raining Blood"),
            ("Megadeth", "Symphony of Destruction"),
            ("Pantera", "Walk"),
            ("Dio", "Holy Diver"),
            ("Motörhead", "Ace of Spades"),
            ("Slipknot", "Duality"),
            ("System of a Down", "Chop Suey!"),
            ("Rammstein", "Du Hast"),
            ("Tool", "Schism"),
            ("Dream Theater", "Pull Me Under"),
            ("Opeth", "Blackwater Park"),
            ("Lamb of God", "Redneck"),
            ("Mastodon", "Blood and Thunder"),
            ("Gojira", "Flying Whales"),
            ("Meshuggah", "Bleed"),
            ("Nightwish", "Wishmaster"),
            ("Blind Guardian", "Mirror Mirror"),
            ("Children of Bodom", "Downfall"),
            ("In Flames", "Cloud Connected"),
            ("Amon Amarth", "Twilight of the Thunder God"),
            ("Sabaton", "Ghost Division")
        ],
        "alternative rock": [
            ("Radiohead", "Creep"),
            ("Nirvana", "Come as You Are"),
            ("The Cure", "Just Like Heaven"),
            ("R.E.M.", "Losing My Religion"),
            ("Pearl Jam", "Black"),
            ("Red Hot Chili Peppers", "Californication"),
            ("Pixies", "Where Is My Mind?"),
            ("Soundgarden", "Black Hole Sun"),
            ("The Smiths", "There Is a Light That Never Goes Out"),
            ("Sonic Youth", "Teen Age Riot"),
            ("Beck", "Loser"),
            ("Smashing Pumpkins", "1979"),
            ("Weezer", "Buddy Holly"),
            ("Foo Fighters", "Everlong"),
            ("Rage Against the Machine", "Killing in the Name"),
            ("Jane's Addiction", "Been Caught Stealing"),
            ("Stone Temple Pilots", "Plush"),
            ("Alice in Chains", "Man in the Box"),
            ("Oasis", "Wonderwall"),
            ("Blur", "Song 2"),
            ("The White Stripes", "Seven Nation Army"),
            ("The Strokes", "Last Nite"),
            ("Arctic Monkeys", "Do I Wanna Know?"),
            ("Muse", "Supermassive Black Hole"),
            ("Arcade Fire", "Wake Up")
        ]
    }
    
    # Normalizar a tag para comparação
    normalized_tag = tag_name.lower()
    
    # Procurar a tag mais próxima
    if normalized_tag in mock_data:
        tracks = mock_data[normalized_tag]
    else:
        # Tentar encontrar uma tag parcial
        for tag in mock_data:
            if tag in normalized_tag or normalized_tag in tag:
                tracks = mock_data[tag]
                logger.info(f"Usando dados mockados para tag similar: '{tag}'")
                break
        else:
            # Se não encontrar, usar rock como padrão
            tracks = mock_data["rock"]
            logger.info(f"Tag '{tag_name}' não encontrada, usando 'rock' como padrão")
    
    # Limitar o número de músicas
    return tracks[:limit]

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
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    from cli.main import smart_mp3_search, is_duplicate_download, connectToSlskd
    
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
            # Chamar a função de busca e download
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
