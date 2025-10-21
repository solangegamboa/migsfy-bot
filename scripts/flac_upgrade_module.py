#!/usr/bin/env python3

import os
import sys
import json
import time
import slskd_api
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def get_download_history_file():
    """Retorna o caminho do arquivo de histórico"""
    if os.path.exists('/app/data'):
        return '/app/data/download_history.json'
    else:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'download_history.json'),
            os.path.join(os.path.dirname(__file__), '..', 'src', 'cli', 'download_history.json'),
            os.path.join(os.path.dirname(__file__), '..', 'download_history.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return possible_paths[0]

def load_download_history():
    """Carrega o histórico de downloads do arquivo JSON"""
    history_file = get_download_history_file()
    
    if not os.path.exists(history_file):
        print(f"❌ Arquivo de histórico não encontrado: {history_file}")
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
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")

def connectToSlskd():
    """Conecta ao slskd usando variáveis de ambiente"""
    try:
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
        return None

def search_flac_version(slskd, search_term):
    """Busca versão FLAC de uma música"""
    print(f"🔍 Buscando versão FLAC: {search_term}")
    
    flac_variations = [
        f"{search_term} *.flac",
        f"{search_term} flac",
        f'"{search_term}" *.flac',
        f"{search_term} lossless"
    ]
    
    for i, search_query in enumerate(flac_variations, 1):
        print(f"  📍 Tentativa {i}: {search_query}")
        
        try:
            search_result = slskd.searches.search_text(search_query)
            search_id = search_result.get('id')
            
            time.sleep(10)
            search_responses = slskd.searches.search_responses(search_id)
            
            if not search_responses:
                continue
            
            best_flac = find_best_flac(search_responses, search_term)
            
            if best_flac:
                return best_flac
                
        except Exception as e:
            print(f"    ❌ Erro na busca: {e}")
            continue
    
    return None

def find_best_flac(search_responses, search_term):
    """Encontra o melhor arquivo FLAC nos resultados"""
    flac_files = []
    
    for response in search_responses:
        username = response.get('username', '')
        files = response.get('files', [])
        
        for file_info in files:
            filename = file_info.get('filename', '')
            
            if not filename.lower().endswith('.flac'):
                continue
            
            size = file_info.get('size', 0)
            bitrate = file_info.get('bitRate', 0)
            
            score = 0
            if size > 20000000:
                score += 30
            elif size > 10000000:
                score += 20
            elif size > 5000000:
                score += 10
            
            if bitrate >= 1000:
                score += 20
            
            flac_files.append({
                'file_info': file_info,
                'username': username,
                'score': score,
                'size': size,
                'bitrate': bitrate
            })
    
    if not flac_files:
        return None
    
    flac_files.sort(key=lambda x: x['score'], reverse=True)
    best = flac_files[0]
    
    print(f"  🎵 Melhor FLAC encontrado:")
    print(f"    👤 Usuário: {best['username']}")
    print(f"    📄 Arquivo: {os.path.basename(best['file_info']['filename'])}")
    print(f"    💾 Tamanho: {best['size'] / 1024 / 1024:.1f} MB")
    print(f"    🎧 Bitrate: {best['bitrate']} kbps")
    
    return best

def download_flac(slskd, flac_info, search_term):
    """Inicia download do arquivo FLAC"""
    try:
        username = flac_info['username']
        file_info = flac_info['file_info']
        filename = file_info['filename']
        file_size = file_info['size']
        
        print(f"  📥 Iniciando download FLAC...")
        
        file_dict = {
            'filename': filename,
            'size': file_size
        }
        
        slskd.transfers.enqueue(username, [file_dict])
        print(f"  ✅ Download FLAC enfileirado!")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no download FLAC: {e}")
        return False

def upgrade_to_flac():
    """Função principal para upgrade das músicas para FLAC"""
    print("🎵 FLAC UPGRADE TOOL")
    print("📖 Lendo histórico de downloads...")
    
    history = load_download_history()
    
    if not history:
        print("❌ Nenhum histórico encontrado")
        return
    
    print(f"📊 Encontradas {len(history)} músicas no histórico")
    
    slskd = connectToSlskd()
    if not slskd:
        return
    
    successful_upgrades = 0
    failed_upgrades = 0
    
    for i, (hash_key, entry) in enumerate(history.items(), 1):
        search_term = entry.get('original_search', '')
        
        print(f"\n📍 [{i}/{len(history)}] {search_term}")
        
        if 'flac_upgraded' in entry and entry['flac_upgraded']:
            print("  ⏭️ Já tem versão FLAC - pulando")
            continue
        
        flac_info = search_flac_version(slskd, search_term)
        
        if flac_info:
            success = download_flac(slskd, flac_info, search_term)
            
            if success:
                entry['flac_upgraded'] = True
                entry['flac_filename'] = flac_info['file_info']['filename']
                entry['flac_username'] = flac_info['username']
                entry['flac_size'] = flac_info['file_info']['size']
                
                successful_upgrades += 1
                print("  ✅ Upgrade para FLAC bem-sucedido!")
            else:
                failed_upgrades += 1
                print("  ❌ Falha no upgrade para FLAC")
        else:
            failed_upgrades += 1
            print("  ❌ Versão FLAC não encontrada")
        
        if i < len(history):
            print("  ⏸️ Pausa de 3s...")
            time.sleep(3)
    
    save_download_history(history)
    
    print(f"\n{'='*50}")
    print(f"📊 RELATÓRIO FINAL - FLAC UPGRADE")
    print(f"✅ Upgrades bem-sucedidos: {successful_upgrades}")
    print(f"❌ Upgrades com falha: {failed_upgrades}")
    print(f"📊 Total processado: {len(history)}")
    
    if successful_upgrades > 0:
        print(f"\n💡 {successful_upgrades} downloads FLAC foram iniciados!")
        print(f"💡 Monitore o progresso no slskd web interface")