#!/usr/bin/env python3

import importlib.util
import os
import sys

from dotenv import load_dotenv

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Carrega variáveis de ambiente
load_dotenv()


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

        # Cria diretório data/playlists se não existir
        os.makedirs("data/playlists", exist_ok=True)

        # Define nome do arquivo de saída na pasta data/playlists/
        if not output_file:
            import re

            # Remove caracteres problemáticos e limita tamanho
            safe_name = re.sub(r"[^\w\s-]", "", playlist_name)
            safe_name = re.sub(r"\s+", "_", safe_name.strip())[:50]
            output_file = f"data/playlists/spotify_{safe_name}_{playlist_id}.txt"
        else:
            output_file = f"data/playlists/{output_file}"

        # Escreve arquivo TXT
        with open(output_file, "w", encoding="utf-8") as f:
            for track in tracks:
                line = f"{track['artist']} - {track['album']} - {track['title']}\n"
                f.write(line)

        print(f"✅ Arquivo criado: {output_file}")
        print(f"📊 {len(tracks)} músicas exportadas")
        return True

    except Exception as e:
        print(f"❌ Erro ao processar playlist: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("🎵 SPOTIFY TO TXT CONVERTER")
        print("📖 Converte playlist do Spotify para arquivo TXT")
        print()
        print("Uso:")
        print("  python3 spotify-to-txt.py <playlist_url> [output_file]")
        print()
        print("Parâmetros:")
        print("  playlist_url : URL da playlist do Spotify")
        print("  output_file  : Nome do arquivo de saída (opcional)")
        print()
        print("Exemplo:")
        print(
            "  python3 spotify-to-txt.py https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd"
        )
        print(
            "  python3 spotify-to-txt.py https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd minha_playlist.txt"
        )
        print()
        print("Formato de saída:")
        print("  Artista - Album - Titulo")
        return

    playlist_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔗 Playlist URL: {playlist_url}")
    if output_file:
        print(f"📁 Arquivo de saída: {output_file}")
    print()

    spotify_to_txt(playlist_url, output_file)


if __name__ == "__main__":
    main()
