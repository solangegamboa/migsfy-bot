#!/usr/bin/env python

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher

import slskd_api
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

try:
    import music_tag

    MUSIC_TAG_AVAILABLE = True
    print("✅ music_tag disponível para melhorar nomes de arquivos")
except ImportError:
    MUSIC_TAG_AVAILABLE = False
    print("⚠️ music_tag não encontrado - usando nomes originais")
    print("💡 Instale com: pip install music-tag")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

    SPOTIPY_AVAILABLE = True
    print("✅ spotipy disponível para integração com Spotify")
except ImportError:
    SPOTIPY_AVAILABLE = False
    print("⚠️ spotipy não encontrado - funcionalidades do Spotify desabilitadas")
    print("💡 Instale com: pip install spotipy")


def connectToSlskd():
    try:
        # Usa variáveis de ambiente
        host = os.getenv("SLSKD_HOST", "192.168.15.100")
        api_key = os.getenv("SLSKD_API_KEY")
        url_base = os.getenv("SLSKD_URL_BASE", f"http://{host}:5030")

        if not api_key:
            print("❌ SLSKD_API_KEY não encontrada no arquivo .env")
            return None

        slskd = slskd_api.SlskdClient(host=host, api_key=api_key, url_base=url_base)
        app_state = slskd.application.state()
        print(f"✅ Conectado com sucesso ao slskd em {host}!")
        return slskd
    except Exception as e:
        print(f"❌ Falha ao conectar: {e}")
        print("💡 Verifique as configurações no arquivo .env")
        return None


# ==================== SISTEMA DE HISTÓRICO DE DOWNLOADS ====================


def get_download_history_file():
    """Retorna o caminho do arquivo de histórico"""
    # Verifica se está rodando em Docker (variável de ambiente ou diretório /app/data)
    if os.path.exists("/app/data"):
        return "/app/data/download_history.json"
    else:
        return os.path.join(os.path.dirname(__file__), "download_history.json")


def load_download_history():
    """Carrega o histórico de downloads do arquivo JSON"""
    history_file = get_download_history_file()

    if not os.path.exists(history_file):
        return {}

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar histórico: {e}")
        return {}


def save_download_history(history):
    """Salva o histórico de downloads no arquivo JSON"""
    history_file = get_download_history_file()

    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")


def normalize_search_term(search_term):
    """Normaliza termo de busca para comparação"""
    # Remove caracteres especiais e converte para minúsculas
    normalized = re.sub(r"[^\w\s]", "", search_term.lower())
    # Remove espaços extras
    normalized = " ".join(normalized.split())
    return normalized


def generate_search_hash(search_term):
    """Gera hash único para o termo de busca normalizado"""
    normalized = normalize_search_term(search_term)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()[:12]


def is_duplicate_download(search_term):
    """Verifica se já foi feito download desta música"""
    history = load_download_history()
    search_hash = generate_search_hash(search_term)

    if search_hash in history:
        entry = history[search_hash]
        print(f"🔄 Música já baixada anteriormente:")
        print(f"   📅 Data: {entry['date']}")
        print(f"   🎵 Busca: {entry['original_search']}")
        print(f"   📄 Arquivo: {entry.get('filename', 'N/A')}")
        print(f"   👤 Usuário: {entry.get('username', 'N/A')}")
        return True

    return False


def add_to_download_history(search_term, filename, username, file_size=0):
    """Adiciona download ao histórico"""
    history = load_download_history()
    search_hash = generate_search_hash(search_term)

    entry = {
        "original_search": search_term,
        "normalized_search": normalize_search_term(search_term),
        "filename": filename,
        "username": username,
        "file_size": file_size,
        "date": datetime.now().isoformat(),
        "hash": search_hash,
    }

    history[search_hash] = entry
    save_download_history(history)

    print(f"📝 Adicionado ao histórico: {search_term}")


def show_download_history(limit=10):
    """Mostra histórico de downloads recentes"""
    history = load_download_history()

    if not history:
        print("📝 Histórico de downloads vazio")
        return

    # Ordena por data (mais recente primeiro)
    sorted_entries = sorted(
        history.values(), key=lambda x: x.get("date", ""), reverse=True
    )

    print(f"📝 Histórico de downloads (últimos {min(limit, len(sorted_entries))}):")
    print("=" * 60)

    for i, entry in enumerate(sorted_entries[:limit], 1):
        date_str = entry.get("date", "N/A")
        if date_str != "N/A":
            try:
                date_obj = datetime.fromisoformat(date_str)
                date_str = date_obj.strftime("%d/%m/%Y %H:%M")
            except:
                pass

        print(f"{i:2d}. 🎵 {entry['original_search']}")
        print(f"     📅 {date_str}")
        print(f"     📄 {os.path.basename(entry.get('filename', 'N/A'))}")
        print(f"     👤 {entry.get('username', 'N/A')}")
        print()


def clear_download_history():
    """Limpa todo o histórico de downloads"""
    history_file = get_download_history_file()

    try:
        if os.path.exists(history_file):
            os.remove(history_file)
            print("🗑️ Histórico de downloads limpo com sucesso!")
        else:
            print("📝 Histórico já estava vazio")
    except Exception as e:
        print(f"❌ Erro ao limpar histórico: {e}")


def remove_from_history(search_term):
    """Remove entrada específica do histórico"""
    history = load_download_history()
    search_hash = generate_search_hash(search_term)

    if search_hash in history:
        removed_entry = history.pop(search_hash)
        save_download_history(history)
        print(f"🗑️ Removido do histórico: {removed_entry['original_search']}")
        return True
    else:
        print(f"❌ Entrada não encontrada no histórico: {search_term}")
        return False


# ==================== FIM DO SISTEMA DE HISTÓRICO ====================


# ==================== SISTEMA DE INTEGRAÇÃO COM SPOTIFY ====================


def setup_spotify_client():
    """Configura cliente Spotify usando credenciais do .env"""
    if not SPOTIPY_AVAILABLE:
        print("❌ Spotipy não está disponível")
        return None

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Credenciais do Spotify não encontradas no .env")
        print("💡 Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET")
        print("💡 Obtenha em: https://developer.spotify.com/dashboard/")
        return None

    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Testa a conexão
        sp.search(q="test", type="track", limit=1)
        print("✅ Cliente Spotify configurado com sucesso!")
        return sp

    except Exception as e:
        print(f"❌ Erro ao configurar cliente Spotify: {e}")
        return None


def setup_spotify_user_client():
    """Configura cliente Spotify com autenticação de usuário (para modificar playlists)"""
    if not SPOTIPY_AVAILABLE:
        print("❌ Spotipy não está disponível")
        return None

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        print("❌ Credenciais do Spotify não encontradas no .env")
        print("💡 Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET")
        print("💡 Obtenha em: https://developer.spotify.com/dashboard/")
        return None

    try:
        # Scopes necessários para modificar playlists
        scope = "playlist-modify-public playlist-modify-private"

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache",
        )

        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Testa a conexão obtendo perfil do usuário
        user_profile = sp.current_user()
        print(f"✅ Cliente Spotify autenticado como: {user_profile['display_name']}")
        return sp

    except Exception as e:
        print(f"❌ Erro ao configurar autenticação Spotify: {e}")
        print("💡 Certifique-se de que o redirect_uri está configurado no app Spotify")
        return None


def extract_playlist_id(playlist_url):
    """Extrai ID da playlist de uma URL do Spotify"""
    # Padrões de URL do Spotify
    patterns = [
        r"spotify:playlist:([a-zA-Z0-9]+)",
        r"open\.spotify\.com/playlist/([a-zA-Z0-9]+)",
        r"spotify\.com/playlist/([a-zA-Z0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            return match.group(1)

    # Se não encontrou padrão, assume que já é um ID
    if re.match(r"^[a-zA-Z0-9]+$", playlist_url):
        return playlist_url

    return None


def get_playlist_tracks(sp, playlist_id):
    """Obtém todas as faixas de uma playlist do Spotify"""
    try:
        print(f"🎵 Buscando faixas da playlist...")

        # Obtém informações da playlist
        playlist_info = sp.playlist(playlist_id, fields="name,description,owner,tracks")
        playlist_name = playlist_info["name"]
        owner_name = playlist_info["owner"]["display_name"]

        print(f"📋 Playlist: '{playlist_name}' por {owner_name}")

        tracks = []
        results = sp.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and track.get("type") == "track":
                    # Extrai informações da faixa
                    track_name = track["name"]
                    artists = [artist["name"] for artist in track["artists"]]
                    artist_str = ", ".join(artists)

                    # Formato: "Artista - Música"
                    search_term = f"{artist_str} - {track_name}"

                    track_info = {
                        "search_term": search_term,
                        "track_name": track_name,
                        "artists": artists,
                        "artist_str": artist_str,
                        "album": track["album"]["name"],
                        "duration_ms": track["duration_ms"],
                        "popularity": track["popularity"],
                        "spotify_url": track["external_urls"]["spotify"],
                    }

                    tracks.append(track_info)

            # Próxima página
            results = sp.next(results) if results["next"] else None

        print(f"✅ Encontradas {len(tracks)} faixas na playlist")
        return tracks, playlist_name

    except Exception as e:
        print(f"❌ Erro ao obter faixas da playlist: {e}")
        return [], ""


def remove_track_from_playlist(sp_user, playlist_id, track_uri):
    """Remove uma faixa específica da playlist do Spotify"""
    try:
        # Remove a faixa da playlist
        sp_user.playlist_remove_all_occurrences_of_items(playlist_id, [track_uri])
        return True
    except Exception as e:
        print(f"❌ Erro ao remover faixa da playlist: {e}")
        return False


def get_playlist_tracks_with_uris(sp, playlist_id):
    """Obtém todas as faixas de uma playlist com URIs para remoção"""
    try:
        print(f"🎵 Buscando faixas da playlist...")

        # Obtém informações da playlist
        playlist_info = sp.playlist(playlist_id, fields="name,description,owner,tracks")
        playlist_name = playlist_info["name"]
        owner_name = playlist_info["owner"]["display_name"]

        print(f"📋 Playlist: '{playlist_name}' por {owner_name}")

        tracks = []
        results = sp.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and track.get("type") == "track":
                    # Extrai informações da faixa
                    track_name = track["name"]
                    artists = [artist["name"] for artist in track["artists"]]
                    artist_str = ", ".join(artists)

                    # Formato: "Artista - Música"
                    search_term = f"{artist_str} - {track_name}"

                    track_info = {
                        "search_term": search_term,
                        "track_name": track_name,
                        "artists": artists,
                        "artist_str": artist_str,
                        "album": track["album"]["name"],
                        "duration_ms": track["duration_ms"],
                        "popularity": track["popularity"],
                        "spotify_url": track["external_urls"]["spotify"],
                        "uri": track["uri"],  # URI necessário para remoção
                    }

                    tracks.append(track_info)

            # Próxima página
            results = sp.next(results) if results["next"] else None

        print(f"✅ Encontradas {len(tracks)} faixas na playlist")
        return tracks, playlist_name

    except Exception as e:
        print(f"❌ Erro ao obter faixas da playlist: {e}")
        return [], ""


def download_playlist_tracks(
    slskd,
    tracks,
    playlist_name,
    max_tracks=None,
    skip_duplicates=True,
    auto_cleanup=True,
):
    """Baixa todas as faixas de uma playlist"""
    if not tracks:
        print("❌ Nenhuma faixa para baixar")
        return

    total_tracks = len(tracks)
    if max_tracks:
        tracks = tracks[:max_tracks]
        print(f"🎯 Limitando a {max_tracks} faixas (de {total_tracks} total)")

    print(
        f"\n🎵 Iniciando download de {len(tracks)} faixas da playlist '{playlist_name}'"
    )
    print("=" * 70)

    successful_downloads = 0
    skipped_duplicates = 0
    failed_downloads = 0

    for i, track in enumerate(tracks, 1):
        search_term = track["search_term"]

        print(f"\n📍 [{i}/{len(tracks)}] {search_term}")
        print(f"   💿 Álbum: {track['album']}")
        print(
            f"   ⏱️ Duração: {track['duration_ms'] // 1000 // 60}:{(track['duration_ms'] // 1000) % 60:02d}"
        )

        # Verifica duplicatas se habilitado
        if skip_duplicates and is_duplicate_download(search_term):
            print(f"   ⏭️ Pulando - já baixada anteriormente")
            skipped_duplicates += 1
            continue

        # Tenta fazer o download
        try:
            success = smart_mp3_search(slskd, search_term)
            if success:
                successful_downloads += 1
                print(f"   ✅ Download iniciado com sucesso")
            else:
                failed_downloads += 1
                print(f"   ❌ Falha no download")

        except Exception as e:
            failed_downloads += 1
            print(f"   ❌ Erro: {e}")

        # Pausa entre downloads para evitar sobrecarga
        if i < len(tracks):
            print(f"   ⏸️ Pausa de 2s...")
            time.sleep(2)

    # Relatório final
    print(f"\n{'='*70}")
    print(f"📊 RELATÓRIO FINAL - Playlist: '{playlist_name}'")
    print(f"✅ Downloads bem-sucedidos: {successful_downloads}")
    print(f"⏭️ Duplicatas puladas: {skipped_duplicates}")
    print(f"❌ Falhas: {failed_downloads}")
    print(f"📊 Total processado: {len(tracks)}")

    if successful_downloads > 0:
        print(f"\n💡 {successful_downloads} downloads foram iniciados!")

        if auto_cleanup:
            print(f"🧹 Iniciando limpeza automática de downloads completados...")
            # Aguarda um pouco para os downloads começarem
            time.sleep(5)
            # Monitora e limpa downloads por 10 minutos
            monitor_and_cleanup_downloads(slskd, max_wait=600, check_interval=15)
        else:
            print(f"💡 Monitore o progresso no slskd web interface")
            print(
                f"💡 Use manual_cleanup_downloads() para limpar downloads completados"
            )


def show_playlist_preview(tracks, limit=10):
    """Mostra preview das faixas da playlist"""
    if not tracks:
        print("❌ Nenhuma faixa para mostrar")
        return

    print(
        f"\n🎵 Preview da playlist ({min(limit, len(tracks))} de {len(tracks)} faixas):"
    )
    print("=" * 60)

    for i, track in enumerate(tracks[:limit], 1):
        duration_min = track["duration_ms"] // 1000 // 60
        duration_sec = (track["duration_ms"] // 1000) % 60

        print(f"{i:2d}. 🎵 {track['search_term']}")
        print(f"     💿 {track['album']} | ⏱️ {duration_min}:{duration_sec:02d}")

    if len(tracks) > limit:
        print(f"     ... e mais {len(tracks) - limit} faixas")


def download_playlist_tracks_with_removal(
    slskd,
    sp_user,
    playlist_id,
    tracks,
    playlist_name,
    max_tracks=None,
    skip_duplicates=True,
    auto_cleanup=True,
):
    """Baixa faixas de uma playlist e remove as encontradas da playlist do Spotify"""
    if not tracks:
        print("❌ Nenhuma faixa para baixar")
        return

    total_tracks = len(tracks)
    if max_tracks:
        tracks = tracks[:max_tracks]
        print(f"🎯 Limitando a {max_tracks} faixas (de {total_tracks} total)")

    print(
        f"\n🎵 Iniciando download de {len(tracks)} faixas da playlist '{playlist_name}'"
    )
    print("🗑️ Faixas encontradas serão removidas da playlist automaticamente")
    print("=" * 70)

    successful_downloads = 0
    skipped_duplicates = 0
    failed_downloads = 0
    removed_from_playlist = 0

    for i, track in enumerate(tracks, 1):
        search_term = track["search_term"]
        track_uri = track["uri"]

        print(f"\n📍 [{i}/{len(tracks)}] {search_term}")
        print(f"   💿 Álbum: {track['album']}")
        print(
            f"   ⏱️ Duração: {track['duration_ms'] // 1000 // 60}:{(track['duration_ms'] // 1000) % 60:02d}"
        )

        # Verifica duplicatas se habilitado
        if skip_duplicates and is_duplicate_download(search_term):
            print(f"   ⏭️ Pulando - já baixada anteriormente")
            skipped_duplicates += 1

            # Remove da playlist mesmo se já foi baixada antes
            if sp_user and remove_track_from_playlist(sp_user, playlist_id, track_uri):
                print(f"   🗑️ Removida da playlist (já baixada anteriormente)")
                removed_from_playlist += 1

            continue

        # Tenta fazer o download
        try:
            success = smart_mp3_search(slskd, search_term)
            if success:
                successful_downloads += 1
                print(f"   ✅ Download iniciado com sucesso")

                # Remove da playlist se download foi bem-sucedido
                if sp_user and remove_track_from_playlist(
                    sp_user, playlist_id, track_uri
                ):
                    print(f"   🗑️ Removida da playlist do Spotify")
                    removed_from_playlist += 1
                else:
                    print(f"   ⚠️ Falha ao remover da playlist")

            else:
                failed_downloads += 1
                print(f"   ❌ Falha no download - mantendo na playlist")

        except Exception as e:
            failed_downloads += 1
            print(f"   ❌ Erro: {e}")

        # Pausa entre downloads para evitar sobrecarga
        if i < len(tracks):
            print(f"   ⏸️ Pausa de 2s...")
            time.sleep(2)

    # Relatório final
    print(f"\n{'='*70}")
    print(f"📊 RELATÓRIO FINAL - Playlist: '{playlist_name}'")
    print(f"✅ Downloads bem-sucedidos: {successful_downloads}")
    print(f"⏭️ Duplicatas puladas: {skipped_duplicates}")
    print(f"❌ Falhas: {failed_downloads}")
    print(f"🗑️ Removidas da playlist: {removed_from_playlist}")
    print(f"📊 Total processado: {len(tracks)}")

    if successful_downloads > 0:
        print(f"\n💡 {successful_downloads} downloads foram iniciados!")

        if auto_cleanup:
            print(f"🧹 Iniciando limpeza automática de downloads completados...")
            # Aguarda um pouco para os downloads começarem
            time.sleep(5)
            # Monitora e limpa downloads por 10 minutos
            monitor_and_cleanup_downloads(slskd, max_wait=600, check_interval=15)
        else:
            print(f"💡 Monitore o progresso no slskd web interface")
            print(
                f"💡 Use manual_cleanup_downloads() para limpar downloads completados"
            )

    if removed_from_playlist > 0:
        print(
            f"🎵 {removed_from_playlist} faixas foram removidas da playlist do Spotify"
        )


def process_spotify_playlist(playlist_url):
    """Processa playlist do Spotify usando spotify-to-txt.py e aguarda processamento"""
    import subprocess
    import time
    import glob
    
    print(f"🎵 Processando playlist do Spotify: {playlist_url}")
    
    # Determina o diretório do script
    script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
    script_path = os.path.join(script_dir, "spotify-to-txt.py")
    
    # Determina diretório correto (Docker ou local)
    data_dir = "/app/data" if os.path.exists("/app/data") else "data"
    playlists_dir = os.path.join(data_dir, "playlists")
    print(f"📁 Diretório de dados: {data_dir}")
    print(f"📁 Diretório de playlists: {playlists_dir}")
    
    # Cria diretório se não existir
    os.makedirs(playlists_dir, exist_ok=True)
    
    try:
        # Executa o script spotify-to-txt.py
        print("🔄 Convertendo playlist para arquivo TXT...")
        
        # Determina diretório raiz do projeto
        project_root = os.path.join(os.path.dirname(__file__), "..", "..")
        project_root = os.path.abspath(project_root)
        
        print(f"📁 Executando script em: {project_root}")
        print(f"📝 Script: {script_path}")
        
        result = subprocess.run(
            ["python3", script_path, playlist_url],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode != 0:
            print(f"❌ Erro ao converter playlist: {result.stderr}")
            return False
            
        print(result.stdout)
        
        # Procura por novos arquivos de playlist
        playlist_files = glob.glob(os.path.join(playlists_dir, "spotify_*.txt"))
        print(f"🔍 Procurando arquivos em: {playlists_dir}")
        print(f"📁 Arquivos encontrados: {len(playlist_files)}")
        
        if playlist_files:
            newest_file = max(playlist_files, key=os.path.getctime)
            print(f"✅ Playlist adicionada à fila: {os.path.basename(newest_file)}")
            print("🔄 Status: Aguardando processamento automático")
            print("📋 O sistema processará a playlist em segundo plano")
            print("⏱️ Tempo estimado: 2-5 minutos por música")
            print("📊 Use o histórico para acompanhar o progresso")
            return True
        else:
            print("❌ Arquivo de playlist não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar playlist: {e}")
        return False


# ==================== FIM DO SISTEMA SPOTIFY ====================


def extract_artist_and_song(search_text):
    """Extrai artista e música do texto de busca"""
    separators = [" - ", " – ", " — ", ": ", " | ", " by "]

    for sep in separators:
        if sep in search_text:
            parts = search_text.split(sep, 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                song = parts[1].strip()
                return artist, song

    return search_text.strip(), ""


def extract_artist_and_album(search_text):
    """Extrai artista e álbum do texto de busca"""
    separators = [" - ", " – ", " — ", ": ", " | "]

    for sep in separators:
        if sep in search_text:
            parts = search_text.split(sep, 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                album = parts[1].strip()
                return artist, album

    return search_text.strip(), ""


def is_album_search(search_text):
    """Detecta se a busca é por álbum baseado em palavras-chave"""
    album_keywords = [
        "album",
        "álbum",
        "lp",
        "ep",
        "discography",
        "discografia",
        "complete",
        "completo",
        "collection",
        "coleção",
        "anthology",
        "antologia",
        "greatest hits",
        "best of",
        "compilation",
        "compilação",
    ]

    search_lower = search_text.lower()

    # Verifica se contém palavras-chave de álbum
    for keyword in album_keywords:
        if keyword in search_lower:
            return True

    # Verifica se tem formato "Artista - Algo" e o "Algo" parece ser álbum
    artist, potential_album = extract_artist_and_album(search_text)
    if artist and potential_album:
        # Lista de palavras que indicam que é uma música, não álbum
        song_indicators = [
            "feat",
            "ft",
            "featuring",
            "remix",
            "version",
            "live",
            "acoustic",
            "radio edit",
            "extended",
            "instrumental",
            "cover",
            "demo",
            "unplugged",
            "remaster",
            "single",
            "edit",
        ]

        potential_album_lower = potential_album.lower()

        # Se tem indicadores de música, não é álbum
        has_song_indicators = any(
            indicator in potential_album_lower for indicator in song_indicators
        )
        if has_song_indicators:
            return False

        # Lista de músicas famosas conhecidas (para evitar falsos positivos)
        famous_songs = [
            "comfortably numb",
            "hey jude",
            "bohemian rhapsody",
            "creep",
            "so what",
            "stairway to heaven",
            "imagine",
            "like a rolling stone",
            "satisfaction",
            "yesterday",
            "purple haze",
            "good vibrations",
            "respect",
            "what's going on",
            "smells like teen spirit",
            "billie jean",
            "hotel california",
            "sweet child o' mine",
        ]

        # Se é uma música famosa conhecida, definitivamente não é álbum
        if potential_album_lower in famous_songs:
            return False

        # Lista de álbuns famosos conhecidos (para melhorar detecção)
        famous_albums = [
            "the dark side of the moon",
            "abbey road",
            "nevermind",
            "ok computer",
            "kind of blue",
            "pet sounds",
            "sgt pepper",
            "the wall",
            "thriller",
            "back in black",
            "rumours",
            "led zeppelin iv",
            "the joshua tree",
            "born to run",
            "purple rain",
            "blonde on blonde",
            "revolver",
            "what's going on",
            "exile on main st",
            "london calling",
        ]

        # Se é um álbum famoso conhecido, definitivamente é álbum
        if potential_album_lower in famous_albums:
            return True

        # Heurísticas para detectar álbuns:
        # 1. Se tem 3-4 palavras e não tem indicadores de música, provavelmente é álbum
        word_count = len(potential_album.split())
        if 3 <= word_count <= 4 and not has_song_indicators:
            return True

        # 2. Se tem 2 palavras, só considera álbum se não for música conhecida
        if word_count == 2 and not has_song_indicators:
            return True

        # 3. Se tem apenas 1 palavra, só considera se for álbum conhecido
        if word_count == 1:
            single_word_albums = [
                "nevermind",
                "thriller",
                "rumours",
                "revolver",
                "blonde",
                "purple",
                "born",
                "exile",
                "london",
                "iv",
                "blue",
            ]
            if potential_album_lower in single_word_albums:
                return True

    return False


def create_album_search_variations(search_text):
    """Cria variações de busca específicas para álbuns"""
    artist, album = extract_artist_and_album(search_text)

    variations = []

    if artist and album:
        # PRIORIDADE 1: Busca por diretório/pasta do álbum
        variations.extend(
            [
                f"{artist} {album}",  # Busca básica
                f'"{artist}" "{album}"',  # Termos exatos
                f"{artist} - {album}",  # Com separador
                f"{album} {artist}",  # Ordem invertida
            ]
        )

        # PRIORIDADE 2: Busca por arquivos do álbum
        variations.extend(
            [
                f"{artist} {album} *.flac",  # Arquivos MP3 do álbum
                f"{artist} {album} -single -remix",  # Excluindo singles e remixes
                f"{artist} {album} *.flac",  # Arquivos FLAC
                f'"{album}" "{artist}" *.flac',  # Ordem invertida com MP3
            ]
        )

        # PRIORIDADE 3: Variações com wildcards
        variations.extend(
            [
                f"{artist[:4]}* {album[:4]}*",  # Wildcards truncados
                f"*{artist}* *{album}*",  # Wildcards completos
                f"{artist} *{album}*",  # Wildcard só no álbum
                f"*{artist}* {album}",  # Wildcard só no artista
            ]
        )
    else:
        # Para buscas simples de álbum
        variations.extend(
            [
                f"{search_text}",  # Busca original
                f'"{search_text}"',  # Termo exato
                f"{search_text} *.flac",  # Com MP3
                f"{search_text} album",  # Com palavra álbum
                f"*{search_text}*",  # Com wildcards
            ]
        )

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_variations = []
    for var in variations:
        if var not in seen:
            seen.add(var)
            unique_variations.append(var)

    return unique_variations


def create_audiobook_search_variations(search_text):
    """Cria variações de busca específicas para audiobooks"""
    variations = []
    
    # Busca direta com formatos de audiobook (sem palavra 'audiobook')
    variations.extend([
        f"{search_text} m4b",
        f"{search_text} m4a",
        f"{search_text} mp3",
        f"{search_text} *.m4b",
        f"{search_text} *.m4a",
        f'"{search_text}" m4b',
        f'"{search_text}" m4a',
    ])
    
    # Se contém autor e título
    if " - " in search_text:
        author, title = search_text.split(" - ", 1)
        variations.extend([
            f"{title} {author} m4b",
            f"{title} {author} m4a",
            f"{author} {title} m4b",
            f"{author} {title} m4a",
        ])
    
    # Wildcards para busca mais ampla
    variations.extend([
        f"*{search_text}* m4b",
        f"*{search_text}* m4a",
    ])
    
    # Remove duplicatas
    seen = set()
    unique_variations = []
    for var in variations:
        if var and var not in seen:
            seen.add(var)
            unique_variations.append(var)
    
    return unique_variations[:8]

def create_search_variations(search_text):
    """Cria variações de busca priorizando música sem artista primeiro"""
    artist, song = extract_artist_and_song(search_text)

    variations = []

    if artist and song:
        # PRIORIDADE 1: Busca apenas pela música (mais resultados)
        variations.extend(
            [
                f"{song} *.flac",  # Só a música
                f"{song} *.flac -mp3 -wav",  # Só a música, excluindo lossless
                f'"{song}" *.flac',  # Música exata
                f"*{song[:4]}* *.flac",  # Wildcard no início da música
            ]
        )

        # PRIORIDADE 2: Busca com artista (mais específico)
        variations.extend(
            [
                f"{artist} {song} *.flac",  # Artista + música
                f"{song} {artist} *.flac",  # Música + artista
                f"{artist} {song} -mp3 -wav",  # Com exclusões
                f'"{artist}" "{song}" *.flac',  # Termos exatos
            ]
        )
    else:
        # Para buscas simples, também prioriza busca ampla
        variations.extend(
            [
                f"{search_text} *.flac",  # Busca básica
                f"{search_text} *.flac -mp3 -wav",  # Com exclusões
                f'"{search_text}" *.flac',  # Termo exato
                f"*{search_text[:4]}* *.flac",  # Wildcard no início
            ]
        )

    # Remove duplicatas e limita
    seen = set()
    unique_variations = []
    for var in variations:
        if var and var not in seen and len(var.strip()) > 0:
            seen.add(var)
            unique_variations.append(var)

    # Usa configuração do ambiente ou padrão
    max_variations = int(os.getenv("MAX_SEARCH_VARIATIONS", 8))
    return unique_variations[:max_variations]


def calculate_similarity(search_text, filename):
    """Calcula similaridade entre busca e nome do arquivo"""
    search_normalized = re.sub(r"[^\w\s]", "", search_text.lower())
    filename_normalized = re.sub(r"[^\w\s]", "", filename.lower())
    similarity = SequenceMatcher(None, search_normalized, filename_normalized).ratio()
    return similarity


def score_audiobook_file(file_info, search_text):
    """Pontua arquivo de audiobook baseado em critérios de qualidade"""
    filename = file_info.get("filename", "")
    size = file_info.get("size", 0)
    
    # FILTRO OBRIGATÓRIO: Apenas formatos de audiobook
    audiobook_extensions = [".m4b", ".m4a", ".mp3", ".aac", ".flac"]
    if not any(filename.lower().endswith(ext) for ext in audiobook_extensions):
        return 0
    
    # Pontução base por similaridade
    similarity_score = calculate_similarity(search_text, filename) * 100
    
    # Bônus por formato preferido
    format_bonus = 0
    if filename.lower().endswith(".m4b"):
        format_bonus = 40  # M4B é o melhor formato para audiobooks
    elif filename.lower().endswith(".m4a"):
        format_bonus = 30
    elif filename.lower().endswith(".mp3"):
        format_bonus = 20
    elif filename.lower().endswith(".aac"):
        format_bonus = 15
    elif filename.lower().endswith(".flac"):
        format_bonus = 10
    
    # Bônus por tamanho (audiobooks são grandes)
    size_bonus = 0
    if size > 100 * 1024 * 1024:  # > 100MB
        size_bonus = 30
    elif size > 50 * 1024 * 1024:  # > 50MB
        size_bonus = 20
    elif size > 20 * 1024 * 1024:  # > 20MB
        size_bonus = 10
    
    # Bônus por palavras-chave de audiobook
    filename_lower = filename.lower()
    audiobook_keywords = ["audiobook", "unabridged", "narrated", "read by"]
    keyword_bonus = sum(15 for keyword in audiobook_keywords if keyword in filename_lower)
    
    # Penalidades
    penalty = 0
    bad_words = ["sample", "preview", "demo", "excerpt", "chapter 1"]
    if any(word in filename_lower for word in bad_words):
        penalty = -30
    
    total_score = similarity_score + format_bonus + size_bonus + keyword_bonus + penalty
    return max(0, total_score)

def score_mp3_file(file_info, search_text):
    """Pontua arquivo MP3 baseado em critérios de qualidade"""
    filename = file_info.get("filename", "")
    size = file_info.get("size", 0)
    bitrate = file_info.get("bitRate", 0)

    # FILTRO OBRIGATÓRIO: Apenas MP3
    if not filename.lower().endswith(".flac"):
        return 0

    # Pontuação base por similaridade
    similarity_score = calculate_similarity(search_text, filename) * 100

    # Bônus por qualidade de áudio
    quality_bonus = 0
    if bitrate >= 320:
        quality_bonus = 30
    elif bitrate >= 256:
        quality_bonus = 25
    elif bitrate >= 192:
        quality_bonus = 20
    elif bitrate >= 128:
        quality_bonus = 15
    elif bitrate > 0:
        quality_bonus = 10

    # Bônus por tamanho adequado
    size_bonus = 0
    if 2000000 <= size <= 15000000:  # 2-15MB
        size_bonus = 15
    elif 1000000 <= size <= 20000000:  # 1-20MB
        size_bonus = 10
    elif size >= 500000:  # Pelo menos 500KB
        size_bonus = 5

    # Penalidades
    penalty = 0
    filename_lower = filename.lower()
    bad_words = ["sample", "preview", "demo", "test", "snippet"]
    if any(word in filename_lower for word in bad_words):
        penalty = -30

    total_score = similarity_score + quality_bonus + size_bonus + penalty
    return max(0, total_score)


def find_best_audiobook(search_responses, search_text):
    """Encontra o melhor arquivo de audiobook"""
    best_file = None
    best_score = 0
    best_user = None

    total_files = 0
    audiobook_files = 0

    for response in search_responses:
        username = response.get("username", "")
        files = response.get("files", [])

        for file_info in files:
            total_files += 1
            filename = file_info.get("filename", "")

            audiobook_extensions = [".m4b", ".m4a", ".mp3", ".aac", ".flac"]
            if not any(filename.lower().endswith(ext) for ext in audiobook_extensions):
                continue

            audiobook_files += 1
            score = score_audiobook_file(file_info, search_text)

            if score > best_score:
                best_score = score
                best_file = file_info
                best_user = username

    print(f"📊 Arquivos analisados: {total_files} | Audiobooks: {audiobook_files}")

    return best_file, best_user, best_score

def find_best_mp3(search_responses, search_text):
    """Encontra o melhor arquivo MP3"""
    best_file = None
    best_score = 0
    best_user = None

    total_files = 0
    mp3_files = 0

    for response in search_responses:
        username = response.get("username", "")
        files = response.get("files", [])

        for file_info in files:
            total_files += 1
            filename = file_info.get("filename", "")

            if not filename.lower().endswith(".flac"):
                continue

            mp3_files += 1
            score = score_mp3_file(file_info, search_text)

            if score > best_score:
                best_score = score
                best_file = file_info
                best_user = username

    print(f"📊 Arquivos analisados: {total_files} | MP3s: {mp3_files}")

    return best_file, best_user, best_score


def check_user_online(slskd, username):
    """Verifica se o usuário está online/conectado"""
    try:
        # Tenta obter informações do usuário
        user_info = slskd.users.get(username)

        # Verifica status de conexão
        status = user_info.get("status", "").lower()
        is_online = status in ["online", "away"] or user_info.get("isOnline", False)

        if is_online:
            print(f"✅ Usuário {username} está online")
            return True
        else:
            print(f"❌ Usuário {username} está offline (status: {status})")
            return False

    except Exception as e:
        print(f"⚠️ Erro ao verificar usuário {username}: {e}")
        # Se não conseguir verificar, assume que pode tentar
        print(f"🤔 Tentando download mesmo assim...")
        return True


def get_user_browse_info(slskd, username):
    """Obtém informações de browse do usuário para verificar conectividade"""
    try:
        # Tenta fazer browse do usuário (mais confiável que status)
        browse_result = slskd.users.browse(username)

        if browse_result and "directories" in browse_result:
            print(f"✅ Usuário {username} respondeu ao browse - está ativo")
            return True
        else:
            print(f"❌ Usuário {username} não respondeu ao browse")
            return False

    except Exception as e:
        print(f"⚠️ Browse falhou para {username}: {e}")
        return False


def download_audiobook(slskd, username, filename, file_size=0, search_term=None, custom_dir=None):
    """Inicia download do audiobook com diretório personalizado"""
    try:
        print(f"🔍 Verificando conectividade do usuário {username}...")

        # Primeira verificação: status do usuário
        user_online = check_user_online(slskd, username)

        if not user_online:
            print(f"⚠️ Usuário parece offline, tentando browse para confirmar...")
            browse_ok = get_user_browse_info(slskd, username)
            if not browse_ok:
                print(f"❌ Usuário {username} não está respondendo - pulando download")
                return False

        print(f"📥 Iniciando download de audiobook: {os.path.basename(filename)}")
        
        # Configura diretório personalizado se fornecido
        file_dict = {"filename": filename, "size": file_size}
        
        # Se diretório personalizado foi especificado, tenta configurar
        if custom_dir:
            try:
                # Verifica se slskd suporta diretório personalizado
                print(f"📁 Tentando salvar em: {custom_dir}")
                # Nota: slskd pode não suportar diretório personalizado por arquivo
                # Neste caso, o arquivo será baixado no diretório padrão
            except:
                print(f"⚠️ Diretório personalizado não suportado, usando padrão")

        slskd.transfers.enqueue(username, [file_dict])
        print(f"✅ Download de audiobook enfileirado com sucesso!")
        
        if custom_dir:
            print(f"📝 Nota: Mova manualmente para {custom_dir} após o download")

        # Adiciona ao histórico
        if search_term:
            add_to_download_history(search_term, filename, username, file_size)

        return True

    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return False

def download_mp3(slskd, username, filename, file_size=0, search_term=None):
    """Inicia download do MP3 com verificação de usuário online e histórico"""
    try:
        print(f"🔍 Verificando conectividade do usuário {username}...")

        # Primeira verificação: status do usuário
        user_online = check_user_online(slskd, username)

        if not user_online:
            print(f"⚠️ Usuário parece offline, tentando browse para confirmar...")
            # Segunda verificação: browse do usuário
            browse_ok = get_user_browse_info(slskd, username)

            if not browse_ok:
                print(f"❌ Usuário {username} não está respondendo - pulando download")
                return False

        print(f"📥 Iniciando download de: {os.path.basename(filename)}")

        # Formato correto da API slskd: lista de dicionários com filename e size
        file_dict = {"filename": filename, "size": file_size}

        slskd.transfers.enqueue(username, [file_dict])
        print(f"✅ Download enfileirado com sucesso!")

        # Adiciona ao histórico se o download foi bem-sucedido
        if search_term:
            add_to_download_history(search_term, filename, username, file_size)

        return True

    except Exception as e:
        print(f"❌ Erro no download: {e}")

        # Tenta sintaxe alternativa apenas se usuário estiver online
        if user_online:
            try:
                # Tenta com parâmetros nomeados
                slskd.transfers.enqueue(username=username, files=[file_dict])
                print(f"✅ Download enfileirado (sintaxe alternativa)!")

                # Adiciona ao histórico se o download foi bem-sucedido
                if search_term:
                    add_to_download_history(search_term, filename, username, file_size)

                return True
            except Exception as e2:
                print(f"❌ Erro na sintaxe alternativa: {e2}")

        return False


def wait_for_search_completion(slskd, search_id, max_wait=30, check_interval=2):
    """Aguarda a busca finalizar completamente"""
    print(f"⏳ Aguardando finalização da busca (máx {max_wait}s)...")

    start_time = time.time()
    last_response_count = 0
    stable_count = 0

    while time.time() - start_time < max_wait:
        try:
            search_responses = slskd.searches.search_responses(search_id)
            current_count = len(search_responses)

            print(
                f"📊 Respostas: {current_count} (+{current_count - last_response_count})"
            )

            # Se o número de respostas não mudou, incrementa contador de estabilidade
            if current_count == last_response_count:
                stable_count += 1
            else:
                stable_count = 0
                last_response_count = current_count

            # Se ficou estável por 3 verificações consecutivas, considera finalizada
            if stable_count >= 3 and current_count > 0:
                print(f"✅ Busca estabilizada com {current_count} respostas")
                return search_responses

            time.sleep(check_interval)

        except Exception as e:
            print(f"⚠️ Erro ao verificar busca: {e}")
            time.sleep(check_interval)

    # Timeout - retorna o que conseguiu coletar
    final_responses = slskd.searches.search_responses(search_id)
    print(f"⏰ Timeout - coletadas {len(final_responses)} respostas")
    return final_responses


def find_alternative_users(search_responses, target_filename, original_user):
    """Encontra usuários alternativos que têm o mesmo arquivo"""
    alternatives = []

    for response in search_responses:
        username = response.get("username", "")
        if username == original_user:
            continue

        files = response.get("files", [])
        for file_info in files:
            filename = file_info.get("filename", "")

            # Verifica se é o mesmo arquivo (nome similar)
            if (
                filename.lower().endswith(".flac")
                and os.path.basename(filename).lower()
                == os.path.basename(target_filename).lower()
            ):

                alternatives.append(
                    {
                        "username": username,
                        "file_info": file_info,
                        "similarity": calculate_similarity(target_filename, filename),
                    }
                )

    # Ordena por similaridade
    alternatives.sort(key=lambda x: x["similarity"], reverse=True)
    return alternatives[:3]  # Retorna até 3 alternativas


def smart_download_with_fallback(
    slskd, search_responses, best_file, best_user, search_query
):
    """Tenta download inteligente com fallback para usuários alternativos"""
    filename = best_file.get("filename")
    file_size = best_file.get("size", 0)

    print(f"\n🎯 Tentando download inteligente...")
    print(f"   📄 Arquivo: {os.path.basename(filename)}")
    print(f"   👤 Usuário principal: {best_user}")

    # Tenta download com usuário principal
    success = download_mp3(slskd, best_user, filename, file_size, search_query)
    if success:
        return True

    # Se falhou, busca usuários alternativos
    print(f"\n🔄 Buscando usuários alternativos...")
    alternatives = find_alternative_users(search_responses, filename, best_user)

    if not alternatives:
        print(f"❌ Nenhum usuário alternativo encontrado")
        return False

    print(f"📋 Encontrados {len(alternatives)} usuários alternativos:")

    for i, alt in enumerate(alternatives, 1):
        alt_user = alt["username"]
        alt_file = alt["file_info"]
        alt_filename = alt_file.get("filename")
        alt_size = alt_file.get("size", 0)
        similarity = alt["similarity"]

        print(f"\n📍 Alternativa {i}: {alt_user}")
        print(f"   📄 Arquivo: {os.path.basename(alt_filename)}")
        print(f"   💾 Tamanho: {alt_size / 1024 / 1024:.2f} MB")
        print(f"   🎧 Bitrate: {alt_file.get('bitRate', 0)} kbps")
        print(f"   🎯 Similaridade: {similarity:.1f}%")

        # Tenta download com usuário alternativo
        success = download_mp3(slskd, alt_user, alt_filename, alt_size, search_query)
        if success:
            print(f"✅ Sucesso com usuário alternativo: {alt_user}")
            return True
        else:
            print(f"❌ Falhou com {alt_user}, tentando próximo...")

    print(f"❌ Todos os usuários alternativos falharam")
    return False


def improve_filename_with_tags(file_path):
    """Melhora o nome do arquivo usando tags de metadados"""
    if not MUSIC_TAG_AVAILABLE or not os.path.exists(file_path):
        return file_path

    try:
        # Lê as tags do arquivo
        audio_file = music_tag.load_file(file_path)

        # Extrai informações das tags
        artist = str(audio_file.get("artist", "")).strip()
        title = str(audio_file.get("title", "")).strip()
        album = str(audio_file.get("album", "")).strip()
        year = str(audio_file.get("year", "")).strip()
        track = str(audio_file.get("tracknumber", "")).strip()

        # Remove caracteres inválidos para nomes de arquivo
        def clean_filename(text):
            if not text:
                return ""
            # Remove caracteres problemáticos
            cleaned = re.sub(r'[<>:"/\\|?*]', "", text)
            # Remove espaços extras
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return cleaned

        # Constrói novo nome baseado nas tags disponíveis
        new_name_parts = []

        if artist and title:
            # Formato: Artista - Título
            new_name_parts.append(f"{clean_filename(artist)} - {clean_filename(title)}")
        elif title:
            # Apenas título
            new_name_parts.append(clean_filename(title))
        elif artist:
            # Apenas artista
            new_name_parts.append(clean_filename(artist))

        # Adiciona informações extras se disponíveis
        extras = []
        if album and album.lower() not in (artist.lower() if artist else ""):
            extras.append(f"[{clean_filename(album)}]")
        if year and len(year) == 4:
            extras.append(f"({year})")
        if track and track.isdigit():
            extras.append(f"#{track.zfill(2)}")

        if extras:
            new_name_parts.extend(extras)

        # Se não conseguiu extrair informações úteis, mantém nome original
        if not new_name_parts:
            print(f"⚠️ Sem tags úteis encontradas - mantendo nome original")
            return file_path

        # Constrói o novo nome
        base_dir = os.path.dirname(file_path)
        file_ext = os.path.splitext(file_path)[1]
        new_filename = " ".join(new_name_parts) + file_ext
        new_path = os.path.join(base_dir, new_filename)

        # Evita sobrescrever arquivos existentes
        counter = 1
        while os.path.exists(new_path) and new_path != file_path:
            name_without_ext = " ".join(new_name_parts)
            new_filename = f"{name_without_ext} ({counter}){file_ext}"
            new_path = os.path.join(base_dir, new_filename)
            counter += 1

        # Renomeia o arquivo se necessário
        if new_path != file_path:
            os.rename(file_path, new_path)
            print(f"📝 Arquivo renomeado:")
            print(f"   De: {os.path.basename(file_path)}")
            print(f"   Para: {os.path.basename(new_path)}")
            return new_path
        else:
            print(f"✅ Nome do arquivo já está adequado")
            return file_path

    except Exception as e:
        print(f"⚠️ Erro ao processar tags: {e}")
        return file_path


def cleanup_search(slskd, search_id):
    """Remove busca finalizada para liberar recursos"""
    try:
        slskd.searches.delete(search_id)
        print(f"🧹 Busca {search_id} removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover busca: {e}")


def smart_mp3_search(slskd, query):
    """Busca inteligente por MP3 com múltiplas variações"""

    # Detecta automaticamente se é busca por álbum
    if is_album_search(query):
        print(f"💿 Detectada busca por ÁLBUM: '{query}'")
        return smart_album_search(slskd, query)

    print(f"🎯 Busca inteligente por MP3: '{query}'")

    # Verifica se já foi baixado anteriormente
    if is_duplicate_download(query):
        print(f"⏭️ Pulando download - música já baixada anteriormente")
        return False

    artist, song = extract_artist_and_song(query)
    if artist and song:
        print(f"🎤 Artista: '{artist}' | 🎵 Música: '{song}'")

    variations = create_search_variations(query)
    print(f"📝 {len(variations)} variações criadas")

    for i, search_term in enumerate(variations, 1):
        print(f"\n📍 Tentativa {i}/{len(variations)}: '{search_term}'")

        # Executa a busca e verifica quantos arquivos encontrou
        try:
            print(f"🔍 Buscando: '{search_term}'")

            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get("id")

            # Aguarda a busca finalizar completamente
            search_responses = wait_for_search_completion(
                slskd, search_id, max_wait=int(os.getenv("SEARCH_WAIT_TIME", 25))
            )

            if not search_responses:
                print("❌ Nenhuma resposta")
                continue

            # Conta total de arquivos encontrados
            total_files = sum(
                len(response.get("files", [])) for response in search_responses
            )

            print(f"📊 Total de arquivos encontrados: {total_files}")

            # Score mínimo configurável
            min_score = int(os.getenv("MIN_MP3_SCORE", 15))

            # Se encontrou mais de 50 arquivos, processa e para
            if total_files > 50:
                print(
                    f"🎯 Encontrados {total_files} arquivos (>50) - processando resultados..."
                )

                best_file, best_user, best_score = find_best_mp3(
                    search_responses, query
                )

                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(
                        f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB"
                    )
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")

                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(
                        slskd, search_responses, best_file, best_user, query
                    )
                    if success:
                        print(
                            f"✅ Sucesso com '{search_term}' ({total_files} arquivos)!"
                        )
                        return True
                    else:
                        print(f"❌ Falha no download após tentar todas as alternativas")
                        return False
                else:
                    print(f"❌ Nenhum MP3 adequado (melhor score: {best_score:.1f})")
                    return False

            # Se encontrou poucos arquivos, continua com próxima variação
            else:
                best_file, best_user, best_score = find_best_mp3(
                    search_responses, query
                )

                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(
                        f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB"
                    )
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")

                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(
                        slskd, search_responses, best_file, best_user, query
                    )
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True
                    else:
                        print(f"❌ Falha no download - continuando...")
                else:
                    print(
                        f"❌ Nenhum MP3 adequado (score: {best_score:.1f}) - continuando..."
                    )

        except Exception as e:
            print(f"❌ Erro na busca: {e}")

        # Pausa maior entre buscas para evitar sobrecarga
        if i < len(variations):
            print("⏸️ Pausa entre buscas...")
            time.sleep(3)

    return False


def smart_album_search(slskd, query):
    """Busca inteligente por álbum com múltiplas variações"""
    print(f"💿 Busca inteligente por ÁLBUM: '{query}'")

    # Verifica se já foi baixado anteriormente
    if is_duplicate_download(query):
        print(f"⏭️ Pulando download - álbum já baixado anteriormente")
        return False

    artist, album = extract_artist_and_album(query)
    if artist and album:
        print(f"🎤 Artista: '{artist}' | 💿 Álbum: '{album}'")

    variations = create_album_search_variations(query)
    print(f"📝 {len(variations)} variações criadas para álbum")

    best_results = []

    for i, search_term in enumerate(variations, 1):
        print(f"\n📍 Tentativa {i}/{len(variations)}: '{search_term}'")

        try:
            print(f"🔍 Buscando álbum: '{search_term}'")

            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get("id")

            # Aguarda a busca finalizar
            search_responses = wait_for_search_completion(
                slskd, search_id, max_wait=int(os.getenv("SEARCH_WAIT_TIME", 25))
            )

            if not search_responses:
                print("❌ Nenhuma resposta")
                continue

            # Conta total de arquivos encontrados
            total_files = sum(
                len(response.get("files", [])) for response in search_responses
            )
            print(f"📊 Total de arquivos encontrados: {total_files}")

            if total_files > 0:
                # Para álbuns, procura por múltiplos arquivos do mesmo usuário/diretório
                album_candidates = find_album_candidates(search_responses, query)

                if album_candidates:
                    print(f"💿 Encontrados {len(album_candidates)} candidatos a álbum")

                    # Ordena por número de faixas e qualidade
                    album_candidates.sort(
                        key=lambda x: (x["track_count"], x["avg_bitrate"]), reverse=True
                    )

                    best_album = album_candidates[0]
                    print(f"\n🎵 Melhor álbum encontrado:")
                    print(f"   👤 Usuário: {best_album['username']}")
                    print(f"   📁 Diretório: {best_album['directory']}")
                    print(f"   🎵 Faixas: {best_album['track_count']}")
                    print(f"   🎧 Bitrate médio: {best_album['avg_bitrate']:.0f} kbps")
                    print(
                        f"   💾 Tamanho total: {best_album['total_size'] / 1024 / 1024:.1f} MB"
                    )

                    # Pergunta se quer baixar o álbum completo
                    print(
                        f"\n🤔 Deseja baixar o álbum completo ({best_album['track_count']} faixas)?"
                    )
                    confirm = input("Digite 'sim' para continuar: ").lower().strip()

                    if confirm in ["sim", "s", "yes", "y"]:
                        return download_album_tracks(slskd, best_album, query)
                    else:
                        print("❌ Download cancelado pelo usuário")
                        return False

                # Se não encontrou álbum completo, tenta download individual
                best_file, best_user, best_score = find_best_mp3(
                    search_responses, query
                )

                if best_file and best_score > 10:  # Score mais baixo para álbuns
                    print(
                        f"\n🎵 Arquivo individual encontrado (score: {best_score:.1f}):"
                    )
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")

                    success = smart_download_with_fallback(
                        slskd, search_responses, best_file, best_user, query
                    )
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True

        except Exception as e:
            print(f"❌ Erro na busca: {e}")

        # Pausa entre buscas
        if i < len(variations):
            print("⏸️ Pausa entre buscas...")
            time.sleep(3)

    return False


def find_album_candidates(search_responses, query):
    """Encontra candidatos a álbum completo nos resultados de busca"""
    candidates = {}

    for response in search_responses:
        username = response.get("username", "")
        files = response.get("files", [])

        if not files:
            continue

        # Agrupa arquivos por diretório
        directories = {}
        for file_info in files:
            filename = file_info.get("filename", "")
            if not filename.lower().endswith(".flac"):
                continue

            # Extrai diretório do arquivo
            directory = os.path.dirname(filename)
            if directory not in directories:
                directories[directory] = []
            directories[directory].append(file_info)

        # Analisa cada diretório
        for directory, dir_files in directories.items():
            if len(dir_files) < 3:  # Mínimo 3 faixas para ser considerado álbum
                continue

            # Calcula estatísticas do diretório
            total_size = sum(f.get("size", 0) for f in dir_files)
            bitrates = [
                f.get("bitRate", 0) for f in dir_files if f.get("bitRate", 0) > 0
            ]
            avg_bitrate = sum(bitrates) / len(bitrates) if bitrates else 0

            # Cria chave única para o candidato
            candidate_key = f"{username}:{directory}"

            if candidate_key not in candidates:
                candidates[candidate_key] = {
                    "username": username,
                    "directory": directory,
                    "track_count": len(dir_files),
                    "total_size": total_size,
                    "avg_bitrate": avg_bitrate,
                    "files": dir_files,
                }

    # Filtra candidatos com pelo menos 5 faixas ou mais de 50MB
    good_candidates = []
    for candidate in candidates.values():
        if (
            candidate["track_count"] >= 5 or candidate["total_size"] > 50 * 1024 * 1024
        ):  # 50MB
            good_candidates.append(candidate)

    return good_candidates


def download_album_tracks(slskd, album_info, search_term):
    """Baixa todas as faixas de um álbum"""
    username = album_info["username"]
    files = album_info["files"]

    print(f"\n📥 Iniciando download de {len(files)} faixas do álbum...")

    successful_downloads = 0
    failed_downloads = 0

    for i, file_info in enumerate(files, 1):
        filename = file_info.get("filename", "")
        file_size = file_info.get("size", 0)

        print(f"\n📍 [{i}/{len(files)}] {os.path.basename(filename)}")
        print(f"   💾 Tamanho: {file_size / 1024 / 1024:.2f} MB")
        print(f"   🎧 Bitrate: {file_info.get('bitRate', 0)} kbps")

        # Tenta fazer o download
        success = download_mp3(
            slskd,
            username,
            filename,
            file_size,
            f"{search_term} - {os.path.basename(filename)}",
        )

        if success:
            successful_downloads += 1
            print(f"   ✅ Download iniciado com sucesso")
        else:
            failed_downloads += 1
            print(f"   ❌ Falha no download")

        # Pausa entre downloads
        if i < len(files):
            time.sleep(1)

    # Relatório final
    print(f"\n{'='*50}")
    print(f"📊 RELATÓRIO FINAL - Álbum")
    print(f"✅ Downloads bem-sucedidos: {successful_downloads}")
    print(f"❌ Falhas: {failed_downloads}")
    print(f"📊 Total de faixas: {len(files)}")

    # Adiciona ao histórico se pelo menos metade foi baixada com sucesso
    if successful_downloads >= len(files) // 2:
        add_to_download_history(
            search_term,
            f"Álbum: {album_info['directory']}",
            username,
            album_info["total_size"],
        )
        return True

    return False


def list_audiobook_options(slskd, query, limit=10):
    """Lista opções de audiobooks para seleção no Telegram"""
    print(f"📚 Listando opções de audiobook: '{query}'")
    
    variations = create_audiobook_search_variations(query)
    print(f"📝 Variações criadas: {variations}")
    all_options = []
    
    # Executa todas as buscas e acumula resultados
    for i, search_term in enumerate(variations, 1):
        try:
            print(f"🔍 Busca {i}/{len(variations)}: '{search_term}'")
            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get("id")
            
            search_responses = wait_for_search_completion(
                slskd, search_id, max_wait=15
            )
            
            if search_responses:
                total_files = sum(len(response.get("files", [])) for response in search_responses)
                print(f"📊 Arquivos encontrados: {total_files}")
                
                # Coleta todos os audiobooks encontrados
                found_in_this_search = 0
                for response in search_responses:
                    username = response.get("username", "")
                    files = response.get("files", [])
                    
                    for file_info in files:
                        filename = file_info.get("filename", "")
                        audiobook_extensions = [".m4b", ".m4a", ".mp3", ".aac", ".flac"]
                        
                        if any(filename.lower().endswith(ext) for ext in audiobook_extensions):
                            score = score_audiobook_file(file_info, query)
                            
                            if score > 10:  # Score mínimo reduzido
                                all_options.append({
                                    'filename': filename,
                                    'username': username,
                                    'size': file_info.get('size', 0),
                                    'score': score,
                                    'file_info': file_info
                                })
                                found_in_this_search += 1
                
                print(f"✅ Audiobooks válidos nesta busca: {found_in_this_search}")
            else:
                print(f"❌ Nenhuma resposta para '{search_term}'")
        
        except Exception as e:
            print(f"⚠️ Erro na busca '{search_term}': {e}")
            continue  # Continua para próxima busca mesmo com erro
    
    print(f"📋 Total de opções coletadas de todas as buscas: {len(all_options)}")
    
    # Remove duplicatas e ordena por score
    unique_options = {}
    for option in all_options:
        key = f"{option['username']}:{os.path.basename(option['filename'])}"
        if key not in unique_options or option['score'] > unique_options[key]['score']:
            unique_options[key] = option
    
    # Ordena por score e limita a 10 melhores
    sorted_options = sorted(unique_options.values(), key=lambda x: x['score'], reverse=True)
    final_options = sorted_options[:10]  # Sempre limita a 10
    
    print(f"✅ Opções únicas após filtro: {len(sorted_options)}")
    print(f"📋 Apresentando os {len(final_options)} melhores audiobooks encontrados")
    
    # Mostra os resultados finais
    if final_options:
        print(f"\n📚 Top {len(final_options)} audiobooks encontrados:")
        for i, option in enumerate(final_options, 1):
            filename = os.path.basename(option['filename'])
            size_mb = option['size'] / 1024 / 1024
            print(f"{i:2d}. {filename} ({size_mb:.1f}MB) - Score: {option['score']:.1f} - {option['username']}")
    
    return final_options

def download_audiobook_by_selection(slskd, option, query, custom_dir=None):
    """Baixa audiobook selecionado da lista"""
    return download_audiobook(
        slskd, option['username'], option['filename'], 
        option['size'], query, custom_dir
    )

def smart_audiobook_search(slskd, query, custom_dir=None):
    """Busca inteligente por audiobooks"""
    print(f"📚 Busca inteligente por AUDIOBOOK: '{query}'")
    
    if custom_dir:
        print(f"📁 Diretório personalizado: {custom_dir}")
    
    # Verifica duplicatas
    if is_duplicate_download(query):
        print(f"⏭️ Pulando download - audiobook já baixado anteriormente")
        return False
    
    variations = create_audiobook_search_variations(query)
    print(f"📝 {len(variations)} variações criadas para audiobook")
    
    for i, search_term in enumerate(variations, 1):
        print(f"\n📍 Tentativa {i}/{len(variations)}: '{search_term}'")
        
        try:
            print(f"🔍 Buscando audiobook: '{search_term}'")
            
            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get("id")
            
            search_responses = wait_for_search_completion(
                slskd, search_id, max_wait=int(os.getenv("SEARCH_WAIT_TIME", 30))
            )
            
            if not search_responses:
                print("❌ Nenhuma resposta")
                continue
            
            total_files = sum(len(response.get("files", [])) for response in search_responses)
            print(f"📊 Total de arquivos encontrados: {total_files}")
            
            if total_files > 0:
                best_file, best_user, best_score = find_best_audiobook(search_responses, query)
                
                min_score = int(os.getenv("MIN_AUDIOBOOK_SCORE", 20))
                
                if best_file and best_score > min_score:
                    print(f"\n📚 Melhor audiobook (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                    
                    # Download com diretório personalizado
                    success = download_audiobook(
                        slskd, best_user, best_file.get('filename'), 
                        best_file.get('size', 0), query, custom_dir
                    )
                    
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True
                    else:
                        print(f"❌ Falha no download - continuando...")
                else:
                    print(f"❌ Nenhum audiobook adequado (score: {best_score:.1f}) - continuando...")
        
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
        
        if i < len(variations):
            print("⏸️ Pausa entre buscas...")
            time.sleep(3)
    
    return False

def smart_mp3_search_force(slskd, query):
    """Busca inteligente por MP3 ignorando histórico (para comando --force)"""
    print(f"🎯 Busca inteligente por MP3 (FORÇADA): '{query}'")

    artist, song = extract_artist_and_song(query)
    if artist and song:
        print(f"🎤 Artista: '{artist}' | 🎵 Música: '{song}'")

    variations = create_search_variations(query)
    print(f"📝 {len(variations)} variações criadas")

    for i, search_term in enumerate(variations, 1):
        print(f"\n📍 Tentativa {i}/{len(variations)}: '{search_term}'")

        # Executa a busca e verifica quantos arquivos encontrou
        try:
            print(f"🔍 Buscando: '{search_term}'")

            search_result = slskd.searches.search_text(search_term)
            search_id = search_result.get("id")

            # Aguarda a busca finalizar completamente
            search_responses = wait_for_search_completion(
                slskd, search_id, max_wait=int(os.getenv("SEARCH_WAIT_TIME", 25))
            )

            if not search_responses:
                print("❌ Nenhuma resposta")
                continue

            # Conta total de arquivos encontrados
            total_files = sum(
                len(response.get("files", [])) for response in search_responses
            )

            print(f"📊 Total de arquivos encontrados: {total_files}")

            # Score mínimo configurável
            min_score = int(os.getenv("MIN_MP3_SCORE", 15))

            # Se encontrou mais de 50 arquivos, processa e para
            if total_files > 50:
                print(
                    f"🎯 Encontrados {total_files} arquivos (>50) - processando resultados..."
                )

                best_file, best_user, best_score = find_best_mp3(
                    search_responses, query
                )

                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(
                        f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB"
                    )
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")

                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(
                        slskd, search_responses, best_file, best_user, query
                    )
                    if success:
                        print(
                            f"✅ Sucesso com '{search_term}' ({total_files} arquivos)!"
                        )
                        return True
                    else:
                        print(f"❌ Falha no download após tentar todas as alternativas")
                        return False
                else:
                    print(f"❌ Nenhum MP3 adequado (melhor score: {best_score:.1f})")
                    return False

            # Se encontrou poucos arquivos, continua com próxima variação
            else:
                best_file, best_user, best_score = find_best_mp3(
                    search_responses, query
                )

                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(
                        f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB"
                    )
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")

                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(
                        slskd, search_responses, best_file, best_user, query
                    )
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True
                    else:
                        print(f"❌ Falha no download - continuando...")
                else:
                    print(
                        f"❌ Nenhum MP3 adequado (score: {best_score:.1f}) - continuando..."
                    )

        except Exception as e:
            print(f"❌ Erro na busca: {e}")

        # Pausa maior entre buscas para evitar sobrecarga
        if i < len(variations):
            print("⏸️ Pausa entre buscas...")
            time.sleep(3)

    return False


def auto_cleanup_completed_downloads(slskd, silent=False):
    """Remove automaticamente downloads completados da fila"""
    try:
        downloads = slskd.transfers.get_all_downloads()
        if not downloads:
            return 0

        completed_downloads = []
        for download in downloads:
            state = download.get("state", "").lower()
            if state in ["completed", "complete", "finished"]:
                completed_downloads.append(
                    {
                        "filename": os.path.basename(download.get("filename", "")),
                        "username": download.get("username", ""),
                        "state": state,
                    }
                )

        if completed_downloads:
            if not silent:
                print(
                    f"🧹 Removendo {len(completed_downloads)} downloads completados da fila..."
                )
                for download in completed_downloads:
                    print(f"   ✅ {download['filename']} (de {download['username']})")

            # Remove downloads completados
            try:
                slskd.transfers.remove_completed_downloads()
                if not silent:
                    print(f"🎉 {len(completed_downloads)} downloads removidos da fila!")
                return len(completed_downloads)
            except Exception as e:
                if not silent:
                    print(f"⚠️ Erro ao remover downloads: {e}")
                return 0
        else:
            if not silent:
                print("ℹ️ Nenhum download completado para remover")
            return 0

    except Exception as e:
        if not silent:
            print(f"❌ Erro na limpeza automática: {e}")
        return 0


def monitor_and_cleanup_downloads(
    slskd, search_term=None, max_wait=300, check_interval=10
):
    """Monitora downloads e remove automaticamente os completados"""
    try:
        print(f"👀 Monitorando downloads por até {max_wait//60} minutos...")
        print(f"🧹 Limpeza automática a cada {check_interval} segundos")

        start_time = time.time()
        last_cleanup_time = start_time

        while time.time() - start_time < max_wait:
            # Verifica se é hora de fazer limpeza
            current_time = time.time()
            if current_time - last_cleanup_time >= check_interval:
                removed_count = auto_cleanup_completed_downloads(slskd, silent=True)
                if removed_count > 0:
                    print(f"🧹 {removed_count} downloads completados removidos da fila")
                last_cleanup_time = current_time

            # Verifica se ainda há downloads ativos
            downloads = slskd.transfers.get_all_downloads()
            if not downloads:
                print("✅ Todos os downloads foram processados!")
                break

            # Mostra status dos downloads ativos
            active_count = 0
            completed_count = 0
            for download in downloads:
                state = download.get("state", "").lower()
                if state in ["completed", "complete", "finished"]:
                    completed_count += 1
                else:
                    active_count += 1

            if active_count > 0:
                print(
                    f"⏳ {active_count} downloads ativos, {completed_count} completados"
                )

            time.sleep(check_interval)

        # Limpeza final
        final_cleanup = auto_cleanup_completed_downloads(slskd)
        if final_cleanup > 0:
            print(f"🧹 Limpeza final: {final_cleanup} downloads removidos")

        print("✅ Monitoramento concluído!")

    except KeyboardInterrupt:
        print("\n⚠️ Monitoramento interrompido pelo usuário")
        # Faz limpeza final mesmo se interrompido
        auto_cleanup_completed_downloads(slskd)
    except Exception as e:
        print(f"❌ Erro no monitoramento: {e}")


def manual_cleanup_downloads(slskd):
    """Função para limpeza manual imediata dos downloads completados"""
    try:
        print("🧹 LIMPEZA MANUAL DE DOWNLOADS COMPLETADOS")
        print("=" * 50)

        # Mostra status atual
        downloads = slskd.transfers.get_all_downloads()
        print(f"📊 Downloads na fila: {len(downloads)}")

        completed_downloads = []
        active_downloads = []

        for download in downloads:
            state = download.get("state", "").lower()
            filename = download.get("filename", "")
            username = download.get("username", "")

            if state in ["completed", "complete", "finished"]:
                completed_downloads.append(
                    {
                        "filename": os.path.basename(filename),
                        "username": username,
                        "state": state,
                    }
                )
            else:
                active_downloads.append(
                    {
                        "filename": os.path.basename(filename),
                        "username": username,
                        "state": state,
                    }
                )

        print(f"✅ Downloads completados: {len(completed_downloads)}")
        print(f"⏳ Downloads ativos: {len(active_downloads)}")

        if completed_downloads:
            print(f"\n📋 DOWNLOADS COMPLETADOS PARA REMOVER:")
            for i, download in enumerate(completed_downloads, 1):
                print(f"   {i}. {download['filename']} (de {download['username']})")

            # Remove downloads completados
            removed_count = slskd.transfers.remove_completed_downloads()
            print(f"\n🎉 {len(completed_downloads)} downloads completados removidos!")
        else:
            print(f"\nℹ️ Nenhum download completado para remover")

        if active_downloads:
            print(f"\n⏳ DOWNLOADS AINDA ATIVOS:")
            for i, download in enumerate(active_downloads, 1):
                print(
                    f"   {i}. {download['filename']} - {download['state']} (de {download['username']})"
                )

        return len(completed_downloads)

    except Exception as e:
        print(f"❌ Erro na limpeza manual: {e}")
        return 0


def show_downloads(slskd):
    """Mostra downloads ativos com opção de limpeza"""
    try:
        print(f"\n{'='*50}")
        print("📥 Downloads ativos:")

        downloads = slskd.transfers.get_all_downloads()
        if downloads:
            completed_count = 0
            for i, download in enumerate(downloads, 1):
                filename = download.get("filename", "N/A")
                state = download.get("state", "N/A")
                username = download.get("username", "N/A")

                if state.lower() in ["completed", "complete", "finished"]:
                    completed_count += 1
                    print(f"   {i}. ✅ {os.path.basename(filename)}")
                else:
                    print(f"   {i}. ⏳ {os.path.basename(filename)}")
                print(f"      👤 De: {username} | Estado: {state}")

            if completed_count > 0:
                print(
                    f"\n💡 {completed_count} downloads completados podem ser removidos"
                )
                print(f"   Use a função manual_cleanup_downloads() para limpar")
        else:
            print("   Nenhum download ativo")
    except Exception as e:
        print(f"❌ Erro ao listar downloads: {e}")


def main():
    print("🎵 SLSKD MP3 Search & Download Tool")
    print('💡 Uso: python3 slskd-mp3-search.py ["artista - música"]')
    print("💡 Comandos especiais:")
    print("   --history          : Mostra histórico de downloads")
    print("   --clear-history    : Limpa todo o histórico")
    print('   --remove "busca"   : Remove entrada específica do histórico')
    print('   --force "busca"    : Força download mesmo se já baixado')
    print("💿 Busca por álbum:")
    print('   --album "Artista - Álbum" : Busca álbum completo')
    print('   "Artista - Nome Album"     : Detecção automática de álbum')
    print("📚 Busca por audiobook:")
    print('   --audiobook "Autor - Título" : Busca audiobook')
    print('   --audiobook "Stephen King IT" --dir ./audiobooks : Salva em diretório específico')
    print('   --audiobook-list "busca" : Lista opções para seleção no Telegram')
    print("🎵 Comandos Spotify:")
    print("   --playlist URL     : Converte playlist para TXT e agenda processamento")
    print("   --preview URL      : Mostra preview da playlist (sem baixar)")
    print()
    print("🏷️ Comandos Last.fm:")
    print('   --lastfm-tag "tag" : Baixa músicas populares de uma tag')
    print('   --lastfm-tag "rock" --limit 25 : Limita a 25 músicas')
    print('   --lastfm-tag "jazz" --output-dir ./jazz : Salva em diretório específico')
    print('   --lastfm-tag "pop" --no-skip-existing : Inclui duplicatas')
    print()
    print("🧹 Limpeza de downloads:")
    print("   --cleanup          : Remove downloads completados da fila")
    print("   --monitor          : Monitora e limpa downloads automaticamente")
    print()
    print("🎧 Upgrade para FLAC:")
    print("   --flac-upgrade     : Busca versões FLAC das músicas do histórico")
    print()

    # Verifica comandos especiais
    if len(sys.argv) > 1:
        first_arg = sys.argv[1].lower()

        # Comando para mostrar histórico
        if first_arg == "--history":
            show_download_history()
            return

        # Comando para limpar histórico
        elif first_arg == "--clear-history":
            clear_download_history()
            return

        # Comando para limpeza manual de downloads
        elif first_arg == "--cleanup":
            slskd = connectToSlskd()
            if slskd:
                manual_cleanup_downloads(slskd)
            return

        # Comando para monitoramento de downloads
        elif first_arg == "--monitor":
            slskd = connectToSlskd()
            if slskd:
                print("🎯 Iniciando monitoramento de downloads...")
                monitor_and_cleanup_downloads(
                    slskd, max_wait=1800, check_interval=30
                )  # 30 min
            return
        
        # Comando para upgrade FLAC
        elif first_arg == "--flac-upgrade":
            # Importa e executa o upgrade FLAC
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from scripts.flac_upgrade_module import upgrade_to_flac
                upgrade_to_flac()
            except ImportError:
                print("❌ Script de upgrade FLAC não encontrado")
                print("💡 Execute: python3 /app/scripts/flac-upgrade.py")
            return

        # Comando para remover entrada específica
        elif first_arg == "--remove" and len(sys.argv) > 2:
            search_term = " ".join(sys.argv[2:])
            remove_from_history(search_term)
            return

        # Comando para busca de álbum
        elif first_arg == "--album" and len(sys.argv) > 2:
            album_query = " ".join(sys.argv[2:])
            print(f"💿 Forçando busca por álbum: '{album_query}'")

            slskd = connectToSlskd()
            if not slskd:
                return

            # Verifica se deve desabilitar limpeza automática
            auto_cleanup = "--no-auto-cleanup" not in sys.argv

            success = smart_album_search(slskd, album_query)

            if success:
                show_downloads(slskd)
                print(f"\n✅ Busca de álbum concluída com sucesso!")

                if auto_cleanup:
                    print(
                        f"🧹 Iniciando limpeza automática de downloads completados..."
                    )
                    time.sleep(5)  # Aguarda downloads começarem
                    monitor_and_cleanup_downloads(
                        slskd, max_wait=600, check_interval=15
                    )  # 10 min
                else:
                    print(
                        f"💡 Para limpar downloads completados manualmente, use --cleanup"
                    )
            else:
                print(f"\n❌ Nenhum álbum adequado encontrado")
            return
        
        # Comando para listar opções de audiobook
        elif first_arg == "--audiobook-list" and len(sys.argv) > 2:
            audiobook_query = " ".join(sys.argv[2:])
            print(f"📚 Listando opções de audiobook: '{audiobook_query}'")

            slskd = connectToSlskd()
            if not slskd:
                return

            options = list_audiobook_options(slskd, audiobook_query, limit=10)
            
            if options:
                print(f"\n📚 {len(options)} audiobooks encontrados:")
                print("=" * 60)
                
                for i, option in enumerate(options, 1):
                    filename = os.path.basename(option['filename'])
                    size_mb = option['size'] / 1024 / 1024
                    score = option['score']
                    username = option['username']
                    
                    # Detecta formato
                    ext = os.path.splitext(filename)[1].lower()
                    format_emoji = {
                        '.m4b': '📚',
                        '.m4a': '🎧', 
                        '.mp3': '🎵',
                        '.aac': '🔊',
                        '.flac': '🎼'
                    }.get(ext, '📄')
                    
                    print(f"{i:2d}. {format_emoji} {filename}")
                    print(f"     👤 {username} | 💾 {size_mb:.1f}MB | ⭐ {score:.0f}")
                    print()
                
                print("💡 Para usar no Telegram: /audiobook_select <número>")
                
                # Salva opções em arquivo temporário para o Telegram
                import json
                temp_file = "/app/data/audiobook_options.json" if os.path.exists("/app/data") else "audiobook_options.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'query': audiobook_query,
                        'options': options
                    }, f, indent=2, ensure_ascii=False)
                print(f"💾 Opções salvas para seleção no Telegram")
            else:
                print(f"\n❌ Nenhum audiobook encontrado para '{audiobook_query}'")
            return
        
        # Comando para busca de audiobook
        elif first_arg == "--audiobook" and len(sys.argv) > 2:
            # Processa argumentos do audiobook
            audiobook_args = sys.argv[2:]
            custom_dir = None
            audiobook_query = ""
            
            # Procura por --dir
            if "--dir" in audiobook_args:
                dir_index = audiobook_args.index("--dir")
                if dir_index + 1 < len(audiobook_args):
                    custom_dir = audiobook_args[dir_index + 1]
                    # Remove --dir e o diretório dos argumentos
                    audiobook_args = audiobook_args[:dir_index] + audiobook_args[dir_index + 2:]
            
            audiobook_query = " ".join(audiobook_args)
            
            if not audiobook_query:
                print("❌ Nenhuma busca de audiobook fornecida")
                return
            
            print(f"📚 Buscando audiobook: '{audiobook_query}'")
            if custom_dir:
                print(f"📁 Diretório personalizado: {custom_dir}")

            slskd = connectToSlskd()
            if not slskd:
                return

            success = smart_audiobook_search(slskd, audiobook_query, custom_dir)

            if success:
                show_downloads(slskd)
                print(f"\n✅ Busca de audiobook concluída com sucesso!")
                if custom_dir:
                    print(f"📝 Lembre-se de mover o arquivo para {custom_dir} após o download")
            else:
                print(f"\n❌ Nenhum audiobook adequado encontrado")
            return

        # Comando para preview de playlist
        elif first_arg == "--preview" and len(sys.argv) > 2:
            playlist_url = sys.argv[2]

            sp = setup_spotify_client()
            if not sp:
                return

            playlist_id = extract_playlist_id(playlist_url)
            if not playlist_id:
                print("❌ URL de playlist inválida")
                print(
                    "💡 Use: https://open.spotify.com/playlist/ID ou spotify:playlist:ID"
                )
                return

            tracks, playlist_name = get_playlist_tracks(sp, playlist_id)
            if tracks:
                show_playlist_preview(tracks, limit=20)
            return

        # Comando para baixar playlist
        elif first_arg == "--playlist" and len(sys.argv) > 2:
            playlist_url = sys.argv[2]
            
            print("🎵 PROCESSAMENTO DE PLAYLIST SPOTIFY")
            print("=" * 50)
            
            if process_spotify_playlist(playlist_url):
                print("\n✅ Playlist adicionada à fila de processamento!")
                print("\n🔄 COMO FUNCIONA:")
                print("1. Sua playlist foi convertida para arquivo TXT")
                print("2. O sistema processará automaticamente em segundo plano")
                print("3. Cada música será buscada e baixada individualmente")
                print("4. Músicas já baixadas serão puladas automaticamente")
                print("\n⏱️ TEMPO ESTIMADO:")
                print("- 2-5 minutos por música (dependendo da disponibilidade)")
                print("- O processamento continua mesmo se você fechar o terminal")
                print("\n📊 ACOMPANHAR PROGRESSO:")
                print("- Use: python3 src/cli/main.py --history")
                print("- Verifique a interface web do slskd")
                print("- Monitore os logs do sistema")
            else:
                print("\n❌ Falha ao processar playlist")
                print("💡 Verifique se a URL está correta e tente novamente")
            return

        # Comando para forçar download
        elif first_arg == "--force" and len(sys.argv) > 2:
            custom_query = " ".join(sys.argv[2:])
            print(f"🎯 Forçando busca por: '{custom_query}' (ignorando histórico)")

            slskd = connectToSlskd()
            if not slskd:
                return

            # Verifica se deve desabilitar limpeza automática
            auto_cleanup = "--no-auto-cleanup" not in sys.argv

            # Busca sem verificar histórico
            success = smart_mp3_search_force(slskd, custom_query)

            if success:
                show_downloads(slskd)
                print(f"\n✅ Busca forçada concluída com sucesso!")

                if auto_cleanup:
                    print(
                        f"🧹 Iniciando limpeza automática de downloads completados..."
                    )
                    time.sleep(5)  # Aguarda download começar
                    monitor_and_cleanup_downloads(
                        slskd, max_wait=300, check_interval=10
                    )  # 5 min
                else:
                    print(
                        f"💡 Para limpar downloads completados manualmente, use --cleanup"
                    )
            else:
                print(f"\n❌ Nenhum MP3 adequado encontrado")
            return

        # Comando para download por tag do Last.fm
        elif first_arg == "--lastfm-tag" and len(sys.argv) > 2:
            # Importar função do Last.fm
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from core.lastfm.tag_downloader import download_tracks_by_tag

            tag_name = sys.argv[2]

            # Processar argumentos opcionais
            limit = 25  # padrão
            output_dir = None
            skip_existing = True

            # Verificar argumentos adicionais
            for i, arg in enumerate(sys.argv[3:], 3):
                if arg == "--limit" and i + 1 < len(sys.argv):
                    try:
                        limit = int(sys.argv[i + 1])
                    except ValueError:
                        print("⚠️ Valor inválido para --limit, usando padrão (25)")
                elif arg == "--output-dir" and i + 1 < len(sys.argv):
                    output_dir = sys.argv[i + 1]
                elif arg == "--no-skip-existing":
                    skip_existing = False

            print(f"🏷️ Baixando músicas populares da tag '{tag_name}' (limite: {limit})")
            if output_dir:
                print(f"📁 Diretório de saída: {output_dir}")
            if not skip_existing:
                print("🔄 Incluindo músicas já baixadas anteriormente")

            try:
                result = download_tracks_by_tag(
                    tag_name=tag_name,
                    limit=limit,
                    output_dir=output_dir,
                    skip_existing=skip_existing,
                )

                if result is None:
                    print(f"\n❌ Falha na autenticação ou configuração do Last.fm")
                    print(f"💡 Verifique suas credenciais no arquivo .env:")
                    print(f"   - LASTFM_API_KEY")
                    print(f"   - LASTFM_API_SECRET")
                    print(
                        f"💡 Obtenha suas credenciais em: https://www.last.fm/api/account/create"
                    )
                    return

                total, successful, failed, skipped = result

                print(f"\n📊 RELATÓRIO FINAL - Tag: '{tag_name}'")
                print(f"✅ Downloads bem-sucedidos: {successful}")
                print(f"❌ Downloads com falha: {failed}")
                print(f"⏭️ Músicas puladas: {skipped}")
                print(f"📊 Total processado: {total}")

            except Exception as e:
                print(f"❌ Erro ao processar tag '{tag_name}': {e}")
            return

    slskd = connectToSlskd()
    if not slskd:
        return

    if len(sys.argv) > 1:
        # Verifica se deve desabilitar limpeza automática
        auto_cleanup = "--no-auto-cleanup" not in sys.argv

        # Busca personalizada
        custom_query = " ".join(
            [arg for arg in sys.argv[1:] if arg != "--no-auto-cleanup"]
        )
        print(f"🎯 Iniciando busca por: '{custom_query}'")

        success = smart_mp3_search(slskd, custom_query)

        if success:
            show_downloads(slskd)
            print(f"\n✅ Busca concluída com sucesso!")

            if auto_cleanup:
                print(f"🧹 Iniciando limpeza automática de downloads completados...")
                time.sleep(5)  # Aguarda download começar
                monitor_and_cleanup_downloads(
                    slskd, max_wait=300, check_interval=10
                )  # 5 min
            else:
                print(
                    f"💡 Para limpar downloads completados manualmente, use --cleanup"
                )
        else:
            print(f"\n❌ Nenhum MP3 adequado encontrado")
    else:
        # Sem parâmetros - apenas mostra ajuda
        print("💡 Nenhum parâmetro fornecido.")
        print("💡 Use um dos comandos acima ou forneça um termo de busca.")
        print('💡 Exemplo: python3 slskd-mp3-search.py "Artista - Música"')
        print("💡 Para desabilitar limpeza automática: adicione --no-auto-cleanup")


if __name__ == "__main__":
    main()
