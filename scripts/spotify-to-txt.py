#!/usr/bin/env python3

import importlib.util
import os
import sys

from dotenv import load_dotenv

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Carrega variáveis de ambiente
load_dotenv()


def spotify_artist_to_txt(artist_url, output_file=None):
    """Converte todas as músicas de um artista do Spotify para arquivo TXT"""

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
    except ImportError:
        print("❌ spotipy não encontrado")
        print("💡 Instale com: pip install spotipy")
        return False

    # Configura cliente Spotify
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Credenciais do Spotify não encontradas no .env")
        print("💡 Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET")
        return False

    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Extrai ID do artista
        artist_id = artist_url.split("/")[-1].split("?")[0]

        # Obtém informações do artista
        artist_info = sp.artist(artist_id)
        artist_name = artist_info["name"]

        print(f"🎤 Artista: '{artist_name}'")

        # Obtém todos os álbuns do artista
        albums = []
        results = sp.artist_albums(artist_id, album_type='album,single', limit=50)
        
        while results:
            albums.extend(results['items'])
            results = sp.next(results) if results['next'] else None

        print(f"💿 Encontrados {len(albums)} álbuns/singles")

        # Obtém todas as tracks de todos os álbuns
        tracks = []
        for album in albums:
            album_tracks = sp.album_tracks(album['id'])
            
            for track in album_tracks['items']:
                artists = [artist["name"] for artist in track["artists"]]
                artist_str = ", ".join(artists)

                tracks.append({
                    "artist": artist_str,
                    "album": album["name"],
                    "title": track["name"],
                })

        if not tracks:
            print("❌ Nenhuma música encontrada para o artista")
            return False

        print(f"🎵 Encontradas {len(tracks)} músicas")

        # Determina diretório correto (Docker ou local)
        data_dir = "/app/data" if os.path.exists("/app/data") else "data"
        playlists_dir = os.path.join(data_dir, "playlists")
        
        # Cria diretório se não existir
        os.makedirs(playlists_dir, exist_ok=True)

        # Define nome do arquivo de saída
        if not output_file:
            import re
            safe_name = re.sub(r"[^\w\s-]", "", artist_name)
            safe_name = re.sub(r"\s+", "_", safe_name.strip())[:50]
            output_file = os.path.join(playlists_dir, f"spotify_artist_{safe_name}_{artist_id}.txt")
        else:
            output_file = os.path.join(playlists_dir, output_file)

        # Escreve arquivo TXT
        with open(output_file, "w", encoding="utf-8") as f:
            for track in tracks:
                line = f"{track['artist']} - {track['album']} - {track['title']}\n"
                f.write(line)

        print(f"✅ Arquivo criado: {output_file}")
        print(f"📊 {len(tracks)} músicas exportadas")
        return True

    except Exception as e:
        print(f"❌ Erro ao processar artista: {e}")
        return False


def spotify_to_txt(playlist_url, output_file=None):
    """Converte playlist do Spotify para arquivo TXT"""

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
    except ImportError:
        print("❌ spotipy não encontrado")
        print("💡 Instale com: pip install spotipy")
        return False

    # Configura cliente Spotify
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Credenciais do Spotify não encontradas no .env")
        print("💡 Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET")
        return False

    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Extrai ID da playlist
        playlist_id = playlist_url.split("/")[-1].split("?")[0]

        # Obtém informações da playlist
        playlist_info = sp.playlist(playlist_id)
        playlist_name = playlist_info["name"]

        print(f"📋 Playlist: '{playlist_name}'")

        # Obtém todas as tracks
        tracks = []
        results = sp.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and track.get("type") == "track":
                    artists = [artist["name"] for artist in track["artists"]]
                    artist_str = ", ".join(artists)

                    tracks.append(
                        {
                            "artist": artist_str,
                            "album": track["album"]["name"],
                            "title": track["name"],
                        }
                    )

            results = sp.next(results) if results["next"] else None

        if not tracks:
            print("❌ Nenhuma música encontrada na playlist")
            return False

        print(f"🎵 Encontradas {len(tracks)} músicas")

        # Determina diretório correto (Docker ou local)
        data_dir = "/app/data" if os.path.exists("/app/data") else "data"
        playlists_dir = os.path.join(data_dir, "playlists")
        
        print(f"📁 Diretório de dados: {data_dir}")
        print(f"📁 Diretório de playlists: {playlists_dir}")
        print(f"📁 Diretório atual: {os.getcwd()}")
        
        # Cria diretório se não existir
        try:
            os.makedirs(playlists_dir, exist_ok=True)
            print(f"✅ Diretório criado/verificado: {playlists_dir}")
            
            # Testa permissões de escrita
            test_file = os.path.join(playlists_dir, ".test_write")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ Permissões de escrita OK")
            
        except Exception as e:
            print(f"❌ Erro ao criar diretório ou testar permissões: {e}")
            return False

        # Define nome do arquivo de saída
        if not output_file:
            import re

            # Remove caracteres problemáticos e limita tamanho
            safe_name = re.sub(r"[^\w\s-]", "", playlist_name)
            safe_name = re.sub(r"\s+", "_", safe_name.strip())[:50]
            output_file = os.path.join(playlists_dir, f"spotify_{safe_name}_{playlist_id}.txt")
        else:
            output_file = os.path.join(playlists_dir, output_file)

        # Escreve arquivo TXT
        with open(output_file, "w", encoding="utf-8") as f:
            for track in tracks:
                line = f"{track['artist']} - {track['album']} - {track['title']}\n"
                f.write(line)

        # Verifica se arquivo está vazio e deleta se necessário
        if os.path.getsize(output_file) == 0:
            os.remove(output_file)
            print(f"❌ Arquivo vazio removido: {output_file}")
            return False

        print(f"✅ Arquivo criado: {output_file}")
        print(f"📊 {len(tracks)} músicas exportadas")
        print(f"📁 Arquivo existe? {os.path.exists(output_file)}")
        if os.path.exists(output_file):
            print(f"💾 Tamanho do arquivo: {os.path.getsize(output_file)} bytes")
        return True

    except Exception as e:
        print(f"❌ Erro ao processar playlist: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("🎵 SPOTIFY TO TXT CONVERTER")
        print("📖 Converte playlist ou artista do Spotify para arquivo TXT")
        print()
        print("Uso:")
        print("  python3 spotify-to-txt.py <url> [output_file]")
        print()
        print("Parâmetros:")
        print("  url         : URL da playlist ou artista do Spotify")
        print("  output_file : Nome do arquivo de saída (opcional)")
        print()
        print("Exemplos:")
        print("  # Playlist")
        print("  python3 spotify-to-txt.py https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd")
        print()
        print("  # Artista (todas as músicas)")
        print("  python3 spotify-to-txt.py https://open.spotify.com/artist/0epOFNiUfyON9EYx7Tpr6V")
        print()
        print("Formato de saída:")
        print("  Artista - Album - Titulo")
        return

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔗 URL: {url}")
    if output_file:
        print(f"📁 Arquivo de saída: {output_file}")
    print()

    # Detecta se é playlist ou artista
    if "/artist/" in url:
        print("🎤 Detectado: URL de artista")
        spotify_artist_to_txt(url, output_file)
    elif "/playlist/" in url:
        print("📋 Detectado: URL de playlist")
        spotify_to_txt(url, output_file)
    else:
        print("❌ URL não reconhecida. Use URL de playlist ou artista do Spotify.")
        return


if __name__ == "__main__":
    main()
