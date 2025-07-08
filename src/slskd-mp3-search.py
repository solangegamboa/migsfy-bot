#!/usr/bin/env python

import slskd_api
import time
import re
import sys
import os
from difflib import SequenceMatcher

try:
    import music_tag
    MUSIC_TAG_AVAILABLE = True
    print("✅ music_tag disponível para melhorar nomes de arquivos")
except ImportError:
    MUSIC_TAG_AVAILABLE = False
    print("⚠️ music_tag não encontrado - usando nomes originais")
    print("💡 Instale com: pip install music-tag")


def connectToSlskd():
    try:
        slskd = slskd_api.SlskdClient(host='192.168.15.100', api_key='ffa07bf8-3a02-4fbc-8be3-5618f58f1d5e', url_base='http://192.168.15.100:5030')
        app_state = slskd.application.state()
        print("✅ Conectado com sucesso ao slskd!")
        return slskd
    except Exception as e:
        print(f"❌ Falha ao conectar: {e}")
        return None


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
    
    return unique_variations[:8]  # Mantém 8 variações eficientes


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


def download_mp3(slskd, username, filename, file_size=0):
    """Inicia download do MP3 com verificação de usuário online"""
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
        return True
        
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        
        # Tenta sintaxe alternativa apenas se usuário estiver online
        if user_online:
            try:
                # Tenta com parâmetros nomeados
                slskd.transfers.enqueue(username=username, files=[file_dict])
                print(f"✅ Download enfileirado (sintaxe alternativa)!")
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
    success = download_mp3(slskd, best_user, filename, file_size)
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
        success = download_mp3(slskd, alt_user, alt_filename, alt_size)
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
            search_responses = wait_for_search_completion(slskd, search_id, max_wait=25)
            
            if not search_responses:
                print("❌ Nenhuma resposta")
                continue
            
            # Conta total de arquivos encontrados
            total_files = sum(len(response.get('files', [])) for response in search_responses)
            
            print(f"📊 Total de arquivos encontrados: {total_files}")
            
            # Se encontrou mais de 50 arquivos, processa e para
            if total_files > 50:
                print(f"🎯 Encontrados {total_files} arquivos (>50) - processando resultados...")
                
                best_file, best_user, best_score = find_best_mp3(search_responses, query)
                
                if best_file and best_score > 15:
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
                
                if best_file and best_score > 15:
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
    print()
    
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
        # Buscas de teste
        test_queries = [
            "In the end Linkin Park",
        ]
        
        print("🧪 Modo teste - buscando MP3s...")
        
        for query in test_queries:
            print(f"\n{'='*50}")
            success = smart_mp3_search(slskd, query)
            
            if success:
                print(f"✅ Teste bem-sucedido com '{query}'")
                break
            else:
                print(f"❌ Teste falhou com '{query}'")
            
            time.sleep(2)
        
        show_downloads(slskd)


if __name__ == "__main__":
    main()
