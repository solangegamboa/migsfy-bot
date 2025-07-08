#!/usr/bin/env python

import slskd_api
import time
import re
import sys
import os
import json
import hashlib
from datetime import datetime
from difflib import SequenceMatcher
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
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
    print("✅ spotipy disponível para integração com Spotify")
except ImportError:
    SPOTIPY_AVAILABLE = False
    print("⚠️ spotipy não encontrado - funcionalidades do Spotify desabilitadas")
    print("💡 Instale com: pip install spotipy")


def connectToSlskd():
    try:
        # Usa variáveis de ambiente
        host = os.getenv('SLSKD_HOST', '192.168.15.100')
        api_key = os.getenv('SLSKD_API_KEY')
        url_base = os.getenv('SLSKD_URL_BASE', f'http://{host}:5030')
        
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
    return os.path.join(os.path.dirname(__file__), 'download_history.json')


def load_download_history():
    """Carrega o histórico de downloads do arquivo JSON"""
    history_file = get_download_history_file()
    
    if not os.path.exists(history_file):
        return {}
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar histórico: {e}")
        return {}


def save_download_history(history):
    """Salva o histórico de downloads no arquivo JSON"""
    history_file = get_download_history_file()
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")


def normalize_search_term(search_term):
    """Normaliza termo de busca para comparação"""
    # Remove caracteres especiais e converte para minúsculas
    normalized = re.sub(r'[^\w\s]', '', search_term.lower())
    # Remove espaços extras
    normalized = ' '.join(normalized.split())
    return normalized


def generate_search_hash(search_term):
    """Gera hash único para o termo de busca normalizado"""
    normalized = normalize_search_term(search_term)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:12]


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
        'original_search': search_term,
        'normalized_search': normalize_search_term(search_term),
        'filename': filename,
        'username': username,
        'file_size': file_size,
        'date': datetime.now().isoformat(),
        'hash': search_hash
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
        history.values(), 
        key=lambda x: x.get('date', ''), 
        reverse=True
    )
    
    print(f"📝 Histórico de downloads (últimos {min(limit, len(sorted_entries))}):")
    print("=" * 60)
    
    for i, entry in enumerate(sorted_entries[:limit], 1):
        date_str = entry.get('date', 'N/A')
        if date_str != 'N/A':
            try:
                date_obj = datetime.fromisoformat(date_str)
                date_str = date_obj.strftime('%d/%m/%Y %H:%M')
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
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Credenciais do Spotify não encontradas no .env")
        print("💡 Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET")
        print("💡 Obtenha em: https://developer.spotify.com/dashboard/")
        return None
    
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Testa a conexão
        sp.search(q='test', type='track', limit=1)
        print("✅ Cliente Spotify configurado com sucesso!")
        return sp
        
    except Exception as e:
        print(f"❌ Erro ao configurar cliente Spotify: {e}")
        return None


def extract_playlist_id(playlist_url):
    """Extrai ID da playlist de uma URL do Spotify"""
    # Padrões de URL do Spotify
    patterns = [
        r'spotify:playlist:([a-zA-Z0-9]+)',
        r'open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
        r'spotify\.com/playlist/([a-zA-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            return match.group(1)
    
    # Se não encontrou padrão, assume que já é um ID
    if re.match(r'^[a-zA-Z0-9]+$', playlist_url):
        return playlist_url
    
    return None


def get_playlist_tracks(sp, playlist_id):
    """Obtém todas as faixas de uma playlist do Spotify"""
    try:
        print(f"🎵 Buscando faixas da playlist...")
        
        # Obtém informações da playlist
        playlist_info = sp.playlist(playlist_id, fields='name,description,owner,tracks')
        playlist_name = playlist_info['name']
        owner_name = playlist_info['owner']['display_name']
        
        print(f"📋 Playlist: '{playlist_name}' por {owner_name}")
        
        tracks = []
        results = sp.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('type') == 'track':
                    # Extrai informações da faixa
                    track_name = track['name']
                    artists = [artist['name'] for artist in track['artists']]
                    artist_str = ', '.join(artists)
                    
                    # Formato: "Artista - Música"
                    search_term = f"{artist_str} - {track_name}"
                    
                    track_info = {
                        'search_term': search_term,
                        'track_name': track_name,
                        'artists': artists,
                        'artist_str': artist_str,
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'popularity': track['popularity'],
                        'spotify_url': track['external_urls']['spotify']
                    }
                    
                    tracks.append(track_info)
            
            # Próxima página
            results = sp.next(results) if results['next'] else None
        
        print(f"✅ Encontradas {len(tracks)} faixas na playlist")
        return tracks, playlist_name
        
    except Exception as e:
        print(f"❌ Erro ao obter faixas da playlist: {e}")
        return [], ""


def download_playlist_tracks(slskd, tracks, playlist_name, max_tracks=None, skip_duplicates=True):
    """Baixa todas as faixas de uma playlist"""
    if not tracks:
        print("❌ Nenhuma faixa para baixar")
        return
    
    total_tracks = len(tracks)
    if max_tracks:
        tracks = tracks[:max_tracks]
        print(f"🎯 Limitando a {max_tracks} faixas (de {total_tracks} total)")
    
    print(f"\n🎵 Iniciando download de {len(tracks)} faixas da playlist '{playlist_name}'")
    print("=" * 70)
    
    successful_downloads = 0
    skipped_duplicates = 0
    failed_downloads = 0
    
    for i, track in enumerate(tracks, 1):
        search_term = track['search_term']
        
        print(f"\n📍 [{i}/{len(tracks)}] {search_term}")
        print(f"   💿 Álbum: {track['album']}")
        print(f"   ⏱️ Duração: {track['duration_ms'] // 1000 // 60}:{(track['duration_ms'] // 1000) % 60:02d}")
        
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
        print(f"💡 Monitore o progresso no slskd web interface")


def show_playlist_preview(tracks, limit=10):
    """Mostra preview das faixas da playlist"""
    if not tracks:
        print("❌ Nenhuma faixa para mostrar")
        return
    
    print(f"\n🎵 Preview da playlist ({min(limit, len(tracks))} de {len(tracks)} faixas):")
    print("=" * 60)
    
    for i, track in enumerate(tracks[:limit], 1):
        duration_min = track['duration_ms'] // 1000 // 60
        duration_sec = (track['duration_ms'] // 1000) % 60
        
        print(f"{i:2d}. 🎵 {track['search_term']}")
        print(f"     💿 {track['album']} | ⏱️ {duration_min}:{duration_sec:02d}")
    
    if len(tracks) > limit:
        print(f"     ... e mais {len(tracks) - limit} faixas")


# ==================== FIM DO SISTEMA SPOTIFY ====================


def extract_artist_and_song(search_text):
    """Extrai artista e música do texto de busca"""
    separators = [' - ', ' – ', ' — ', ': ', ' | ', ' by ']
    
    for sep in separators:
        if sep in search_text:
            parts = search_text.split(sep, 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                song = parts[1].strip()
                return artist, song
    
    return search_text.strip(), ""


def create_search_variations(search_text):
    """Cria variações de busca priorizando música sem artista primeiro"""
    artist, song = extract_artist_and_song(search_text)
    
    variations = []
    
    if artist and song:
        # PRIORIDADE 1: Busca apenas pela música (mais resultados)
        variations.extend([
            f"{song} *.mp3",                    # Só a música
            f"{song} *.mp3 -flac -wav",         # Só a música, excluindo lossless
            f'"{song}" *.mp3',                  # Música exata
            f"*{song[:4]}* *.mp3",              # Wildcard no início da música
        ])
        
        # PRIORIDADE 2: Busca com artista (mais específico)
        variations.extend([
            f"{artist} {song} *.mp3",           # Artista + música
            f"{song} {artist} *.mp3",           # Música + artista
            f"{artist} {song} -flac -wav",      # Com exclusões
            f'"{artist}" "{song}" *.mp3',       # Termos exatos
        ])
    else:
        # Para buscas simples, também prioriza busca ampla
        variations.extend([
            f"{search_text} *.mp3",             # Busca básica
            f"{search_text} *.mp3 -flac -wav",  # Com exclusões
            f'"{search_text}" *.mp3',           # Termo exato
            f"*{search_text[:4]}* *.mp3",       # Wildcard no início
        ])
    
    # Remove duplicatas e limita
    seen = set()
    unique_variations = []
    for var in variations:
        if var and var not in seen and len(var.strip()) > 0:
            seen.add(var)
            unique_variations.append(var)
    
    # Usa configuração do ambiente ou padrão
    max_variations = int(os.getenv('MAX_SEARCH_VARIATIONS', 8))
    return unique_variations[:max_variations]


def calculate_similarity(search_text, filename):
    """Calcula similaridade entre busca e nome do arquivo"""
    search_normalized = re.sub(r'[^\w\s]', '', search_text.lower())
    filename_normalized = re.sub(r'[^\w\s]', '', filename.lower())
    similarity = SequenceMatcher(None, search_normalized, filename_normalized).ratio()
    return similarity


def score_mp3_file(file_info, search_text):
    """Pontua arquivo MP3 baseado em critérios de qualidade"""
    filename = file_info.get('filename', '')
    size = file_info.get('size', 0)
    bitrate = file_info.get('bitRate', 0)
    
    # FILTRO OBRIGATÓRIO: Apenas MP3
    if not filename.lower().endswith('.mp3'):
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
    bad_words = ['sample', 'preview', 'demo', 'test', 'snippet']
    if any(word in filename_lower for word in bad_words):
        penalty = -30
    
    total_score = similarity_score + quality_bonus + size_bonus + penalty
    return max(0, total_score)


def find_best_mp3(search_responses, search_text):
    """Encontra o melhor arquivo MP3"""
    best_file = None
    best_score = 0
    best_user = None
    
    total_files = 0
    mp3_files = 0
    
    for response in search_responses:
        username = response.get('username', '')
        files = response.get('files', [])
        
        for file_info in files:
            total_files += 1
            filename = file_info.get('filename', '')
            
            if not filename.lower().endswith('.mp3'):
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
        status = user_info.get('status', '').lower()
        is_online = status in ['online', 'away'] or user_info.get('isOnline', False)
        
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
        
        if browse_result and 'directories' in browse_result:
            print(f"✅ Usuário {username} respondeu ao browse - está ativo")
            return True
        else:
            print(f"❌ Usuário {username} não respondeu ao browse")
            return False
            
    except Exception as e:
        print(f"⚠️ Browse falhou para {username}: {e}")
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
        file_dict = {
            'filename': filename,
            'size': file_size
        }
        
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
            
            print(f"📊 Respostas: {current_count} (+{current_count - last_response_count})")
            
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
        username = response.get('username', '')
        if username == original_user:
            continue
            
        files = response.get('files', [])
        for file_info in files:
            filename = file_info.get('filename', '')
            
            # Verifica se é o mesmo arquivo (nome similar)
            if (filename.lower().endswith('.mp3') and 
                os.path.basename(filename).lower() == os.path.basename(target_filename).lower()):
                
                alternatives.append({
                    'username': username,
                    'file_info': file_info,
                    'similarity': calculate_similarity(target_filename, filename)
                })
    
    # Ordena por similaridade
    alternatives.sort(key=lambda x: x['similarity'], reverse=True)
    return alternatives[:3]  # Retorna até 3 alternativas


def smart_download_with_fallback(slskd, search_responses, best_file, best_user, search_query):
    """Tenta download inteligente com fallback para usuários alternativos"""
    filename = best_file.get('filename')
    file_size = best_file.get('size', 0)
    
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
        alt_user = alt['username']
        alt_file = alt['file_info']
        alt_filename = alt_file.get('filename')
        alt_size = alt_file.get('size', 0)
        similarity = alt['similarity']
        
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
    """Melhora o nome do arquivo usando tags de metadados"""
    if not MUSIC_TAG_AVAILABLE or not os.path.exists(file_path):
        return file_path
    
    try:
        # Lê as tags do arquivo
        audio_file = music_tag.load_file(file_path)
        
        # Extrai informações das tags
        artist = str(audio_file.get('artist', '')).strip()
        title = str(audio_file.get('title', '')).strip()
        album = str(audio_file.get('album', '')).strip()
        year = str(audio_file.get('year', '')).strip()
        track = str(audio_file.get('tracknumber', '')).strip()
        
        # Remove caracteres inválidos para nomes de arquivo
        def clean_filename(text):
            if not text:
                return ""
            # Remove caracteres problemáticos
            cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
            # Remove espaços extras
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
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
            search_id = search_result.get('id')
            
            # Aguarda a busca finalizar completamente
            search_responses = wait_for_search_completion(slskd, search_id, max_wait=int(os.getenv('SEARCH_WAIT_TIME', 25)))
            
            if not search_responses:
                print("❌ Nenhuma resposta")
                continue
            
            # Conta total de arquivos encontrados
            total_files = sum(len(response.get('files', [])) for response in search_responses)
            
            print(f"📊 Total de arquivos encontrados: {total_files}")
            
            # Score mínimo configurável
            min_score = int(os.getenv('MIN_MP3_SCORE', 15))
            
            # Se encontrou mais de 50 arquivos, processa e para
            if total_files > 50:
                print(f"🎯 Encontrados {total_files} arquivos (>50) - processando resultados...")
                
                best_file, best_user, best_score = find_best_mp3(search_responses, query)
                
                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                    
                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                    if success:
                        print(f"✅ Sucesso com '{search_term}' ({total_files} arquivos)!")
                        return True
                    else:
                        print(f"❌ Falha no download após tentar todas as alternativas")
                        return False
                else:
                    print(f"❌ Nenhum MP3 adequado (melhor score: {best_score:.1f})")
                    return False
            
            # Se encontrou poucos arquivos, continua com próxima variação
            else:
                best_file, best_user, best_score = find_best_mp3(search_responses, query)
                
                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                    
                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True
                    else:
                        print(f"❌ Falha no download - continuando...")
                else:
                    print(f"❌ Nenhum MP3 adequado (score: {best_score:.1f}) - continuando...")
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
        
        # Pausa maior entre buscas para evitar sobrecarga
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
            search_id = search_result.get('id')
            
            # Aguarda a busca finalizar completamente
            search_responses = wait_for_search_completion(slskd, search_id, max_wait=int(os.getenv('SEARCH_WAIT_TIME', 25)))
            
            if not search_responses:
                print("❌ Nenhuma resposta")
                continue
            
            # Conta total de arquivos encontrados
            total_files = sum(len(response.get('files', [])) for response in search_responses)
            
            print(f"📊 Total de arquivos encontrados: {total_files}")
            
            # Score mínimo configurável
            min_score = int(os.getenv('MIN_MP3_SCORE', 15))
            
            # Se encontrou mais de 50 arquivos, processa e para
            if total_files > 50:
                print(f"🎯 Encontrados {total_files} arquivos (>50) - processando resultados...")
                
                best_file, best_user, best_score = find_best_mp3(search_responses, query)
                
                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                    
                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                    if success:
                        print(f"✅ Sucesso com '{search_term}' ({total_files} arquivos)!")
                        return True
                    else:
                        print(f"❌ Falha no download após tentar todas as alternativas")
                        return False
                else:
                    print(f"❌ Nenhum MP3 adequado (melhor score: {best_score:.1f})")
                    return False
            
            # Se encontrou poucos arquivos, continua com próxima variação
            else:
                best_file, best_user, best_score = find_best_mp3(search_responses, query)
                
                if best_file and best_score > min_score:
                    print(f"\n🎵 Melhor MP3 (score: {best_score:.1f}):")
                    print(f"   👤 Usuário: {best_user}")
                    print(f"   📄 Arquivo: {best_file.get('filename')}")
                    print(f"   💾 Tamanho: {best_file.get('size', 0) / 1024 / 1024:.2f} MB")
                    print(f"   🎧 Bitrate: {best_file.get('bitRate', 0)} kbps")
                    
                    # Usa download inteligente com fallback
                    success = smart_download_with_fallback(slskd, search_responses, best_file, best_user, query)
                    if success:
                        print(f"✅ Sucesso com '{search_term}'!")
                        return True
                    else:
                        print(f"❌ Falha no download - continuando...")
                else:
                    print(f"❌ Nenhum MP3 adequado (score: {best_score:.1f}) - continuando...")
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
        
        # Pausa maior entre buscas para evitar sobrecarga
        if i < len(variations):
            print("⏸️ Pausa entre buscas...")
            time.sleep(3)
    
    return False


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
            state = download.get('state', '').lower()
            filename = download.get('filename', '')
            username = download.get('username', '')
            
            if state in ['completed', 'complete', 'finished']:
                completed_downloads.append({
                    'filename': os.path.basename(filename),
                    'username': username,
                    'state': state
                })
            else:
                active_downloads.append({
                    'filename': os.path.basename(filename),
                    'username': username,
                    'state': state
                })
        
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
                print(f"   {i}. {download['filename']} - {download['state']} (de {download['username']})")
        
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
                filename = download.get('filename', 'N/A')
                state = download.get('state', 'N/A')
                username = download.get('username', 'N/A')
                
                if state.lower() in ['completed', 'complete', 'finished']:
                    completed_count += 1
                    print(f"   {i}. ✅ {os.path.basename(filename)}")
                else:
                    print(f"   {i}. ⏳ {os.path.basename(filename)}")
                print(f"      👤 De: {username} | Estado: {state}")
            
            if completed_count > 0:
                print(f"\n💡 {completed_count} downloads completados podem ser removidos")
                print(f"   Use a função manual_cleanup_downloads() para limpar")
        else:
            print("   Nenhum download ativo")
    except Exception as e:
        print(f"❌ Erro ao listar downloads: {e}")


def main():
    print("🎵 SLSKD MP3 Search & Download Tool")
    print("💡 Uso: python3 slskd-mp3-search.py [\"artista - música\"]")
    print("💡 Comandos especiais:")
    print("   --history          : Mostra histórico de downloads")
    print("   --clear-history    : Limpa todo o histórico")
    print("   --remove \"busca\"   : Remove entrada específica do histórico")
    print("   --force \"busca\"    : Força download mesmo se já baixado")
    print("🎵 Comandos Spotify:")
    print("   --playlist URL     : Baixa todas as músicas de uma playlist")
    print("   --preview URL      : Mostra preview da playlist (sem baixar)")
    print("   --playlist URL --limit N : Limita download a N músicas")
    print("   --playlist URL --no-skip : Baixa mesmo duplicatas")
    print("   --playlist URL --auto    : Baixa sem confirmação")
    print("   --playlist URL --auto --limit N --no-skip : Combina opções")
    print()
    
    # Verifica comandos especiais
    if len(sys.argv) > 1:
        first_arg = sys.argv[1].lower()
        
        # Comando para mostrar histórico
        if first_arg == '--history':
            show_download_history()
            return
        
        # Comando para limpar histórico
        elif first_arg == '--clear-history':
            clear_download_history()
            return
        
        # Comando para remover entrada específica
        elif first_arg == '--remove' and len(sys.argv) > 2:
            search_term = ' '.join(sys.argv[2:])
            remove_from_history(search_term)
            return
        
        # Comando para preview de playlist
        elif first_arg == '--preview' and len(sys.argv) > 2:
            playlist_url = sys.argv[2]
            
            sp = setup_spotify_client()
            if not sp:
                return
            
            playlist_id = extract_playlist_id(playlist_url)
            if not playlist_id:
                print("❌ URL de playlist inválida")
                print("💡 Use: https://open.spotify.com/playlist/ID ou spotify:playlist:ID")
                return
            
            tracks, playlist_name = get_playlist_tracks(sp, playlist_id)
            if tracks:
                show_playlist_preview(tracks, limit=20)
            return
        
        # Comando para baixar playlist
        elif first_arg == '--playlist' and len(sys.argv) > 2:
            playlist_url = sys.argv[2]
            
            # Processa argumentos adicionais
            max_tracks = None
            skip_duplicates = True
            auto_confirm = False
            
            for i, arg in enumerate(sys.argv[3:], 3):
                if arg == '--limit' and i + 1 < len(sys.argv):
                    try:
                        max_tracks = int(sys.argv[i + 1])
                    except ValueError:
                        print("❌ Valor inválido para --limit")
                        return
                elif arg == '--no-skip':
                    skip_duplicates = False
                elif arg == '--auto' or arg == '--yes' or arg == '-y':
                    auto_confirm = True
            
            # Configura Spotify
            sp = setup_spotify_client()
            if not sp:
                return
            
            # Configura slskd
            slskd = connectToSlskd()
            if not slskd:
                return
            
            # Extrai ID da playlist
            playlist_id = extract_playlist_id(playlist_url)
            if not playlist_id:
                print("❌ URL de playlist inválida")
                print("💡 Use: https://open.spotify.com/playlist/ID ou spotify:playlist:ID")
                return
            
            # Obtém faixas da playlist
            tracks, playlist_name = get_playlist_tracks(sp, playlist_id)
            if not tracks:
                return
            
            # Mostra preview antes de baixar
            show_playlist_preview(tracks, limit=10)
            
            # Confirmação do usuário (se não for automático)
            if not auto_confirm:
                print(f"\n🤔 Deseja baixar {len(tracks)} faixas da playlist '{playlist_name}'?")
                if max_tracks:
                    print(f"   (limitado a {max_tracks} faixas)")
                if not skip_duplicates:
                    print(f"   (incluindo duplicatas)")
                
                confirm = input("Digite 'sim' para continuar: ").lower().strip()
                if confirm not in ['sim', 's', 'yes', 'y']:
                    print("❌ Download cancelado pelo usuário")
                    return
            else:
                print(f"\n🚀 Iniciando download automático de {len(tracks)} faixas da playlist '{playlist_name}'")
                if max_tracks:
                    print(f"   (limitado a {max_tracks} faixas)")
                if not skip_duplicates:
                    print(f"   (incluindo duplicatas)")
            
            # Inicia downloads
            download_playlist_tracks(slskd, tracks, playlist_name, max_tracks, skip_duplicates)
            return
        
        # Comando para forçar download
        elif first_arg == '--force' and len(sys.argv) > 2:
            custom_query = ' '.join(sys.argv[2:])
            print(f"🎯 Forçando busca por: '{custom_query}' (ignorando histórico)")
            
            slskd = connectToSlskd()
            if not slskd:
                return
            
            # Busca sem verificar histórico
            success = smart_mp3_search_force(slskd, custom_query)
            
            if success:
                show_downloads(slskd)
                print(f"\n✅ Busca forçada concluída com sucesso!")
                print(f"💡 Para limpar downloads completados manualmente, use manual_cleanup_downloads()")
            else:
                print(f"\n❌ Nenhum MP3 adequado encontrado")
            return
    
    slskd = connectToSlskd()
    if not slskd:
        return
    
    if len(sys.argv) > 1:
        # Busca personalizada
        custom_query = ' '.join(sys.argv[1:])
        print(f"🎯 Iniciando busca por: '{custom_query}'")
        
        success = smart_mp3_search(slskd, custom_query)
        
        if success:
            show_downloads(slskd)
            print(f"\n✅ Busca concluída com sucesso!")
            print(f"💡 Para limpar downloads completados manualmente, use manual_cleanup_downloads()")
        else:
            print(f"\n❌ Nenhum MP3 adequado encontrado")
    else:
        # Sem parâmetros - apenas mostra ajuda
        print("💡 Nenhum parâmetro fornecido.")
        print("💡 Use um dos comandos acima ou forneça um termo de busca.")
        print("💡 Exemplo: python3 slskd-mp3-search.py \"Artista - Música\"")


if __name__ == "__main__":
    main()
