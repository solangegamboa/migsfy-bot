#!/usr/bin/env python3

"""
Teste da nova funcionalidade de seleção de álbuns no bot do Telegram
"""

import os
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_album_search_candidates():
    """Testa a busca de candidatos de álbum"""
    try:
        # Importa funções necessárias do módulo correto
        import sys
        import importlib.util
        
        # Carrega o módulo slskd-mp3-search.py
        spec = importlib.util.spec_from_file_location("slskd_mp3_search", "slskd-mp3-search.py")
        slskd_module = importlib.util.module_from_spec(spec)
        sys.modules["slskd_mp3_search"] = slskd_module
        spec.loader.exec_module(slskd_module)
        
        # Importa funções necessárias
        connectToSlskd = slskd_module.connectToSlskd
        is_duplicate_download = slskd_module.is_duplicate_download
        extract_artist_and_album = slskd_module.extract_artist_and_album
        create_album_search_variations = slskd_module.create_album_search_variations
        wait_for_search_completion = slskd_module.wait_for_search_completion
        find_album_candidates = slskd_module.find_album_candidates
        
        # Conecta ao slskd
        slskd = connectToSlskd()
        if not slskd:
            print("❌ Não foi possível conectar ao slskd")
            return False
        
        print("✅ Conectado ao slskd")
        
        # Teste com um álbum conhecido
        test_query = "Pink Floyd - The Dark Side of the Moon"
        print(f"\n🧪 Testando busca por: {test_query}")
        
        # Verifica duplicatas
        if is_duplicate_download(test_query):
            print(f"⏭️ Álbum já baixado anteriormente")
            return True
        
        # Extrai artista e álbum
        artist, album = extract_artist_and_album(test_query)
        print(f"🎤 Artista: '{artist}' | 💿 Álbum: '{album}'")
        
        # Cria variações de busca
        variations = create_album_search_variations(test_query)
        print(f"📝 {len(variations)} variações criadas")
        
        all_candidates = []
        
        # Testa apenas a primeira variação para economizar tempo
        for i, search_term in enumerate(variations[:2], 1):
            print(f"\n📍 Tentativa {i}: '{search_term}'")
            
            try:
                search_result = slskd.searches.search_text(search_term)
                search_id = search_result.get('id')
                print(f"🔍 ID da busca: {search_id}")
                
                # Aguarda resultados (tempo reduzido para teste)
                search_responses = wait_for_search_completion(slskd, search_id, max_wait=15)
                
                if not search_responses:
                    print("❌ Nenhuma resposta")
                    continue
                
                # Conta arquivos
                total_files = sum(len(response.get('files', [])) for response in search_responses)
                print(f"📊 Total de arquivos: {total_files}")
                
                if total_files > 0:
                    # Busca candidatos de álbum
                    album_candidates = find_album_candidates(search_responses, test_query)
                    
                    if album_candidates:
                        print(f"💿 Encontrados {len(album_candidates)} candidatos")
                        all_candidates.extend(album_candidates)
                        
                        # Mostra detalhes dos candidatos
                        for j, candidate in enumerate(album_candidates, 1):
                            print(f"\n   📀 Candidato {j}:")
                            print(f"      👤 Usuário: {candidate['username']}")
                            print(f"      📁 Diretório: {candidate['directory']}")
                            print(f"      🎵 Faixas: {candidate['track_count']}")
                            print(f"      🎧 Bitrate médio: {candidate['avg_bitrate']:.0f} kbps")
                            print(f"      💾 Tamanho: {candidate['total_size'] / 1024 / 1024:.1f} MB")
                        
                        if len(all_candidates) >= 3:
                            break
            
            except Exception as e:
                print(f"❌ Erro na busca: {e}")
        
        # Processa candidatos finais
        if all_candidates:
            # Remove duplicatas
            unique_candidates = {}
            for candidate in all_candidates:
                key = f"{candidate['username']}:{candidate['directory']}"
                if key not in unique_candidates or candidate['track_count'] > unique_candidates[key]['track_count']:
                    unique_candidates[key] = candidate
            
            final_candidates = list(unique_candidates.values())
            final_candidates.sort(key=lambda x: (x['track_count'], x['avg_bitrate']), reverse=True)
            
            print(f"\n🏆 CANDIDATOS FINAIS ({len(final_candidates)}):")
            for i, candidate in enumerate(final_candidates[:5], 1):
                try:
                    from album_name_extractor import get_album_name
                    album_name = get_album_name(candidate)
                except ImportError:
                    album_name = extract_album_name_from_metadata(candidate)
                
                print(f"\n{i}. {album_name}")
                print(f"   👤 {candidate['username']}")
                print(f"   🎵 {candidate['track_count']} faixas")
                print(f"   🎧 {candidate['avg_bitrate']:.0f} kbps")
                print(f"   💾 {candidate['total_size'] / 1024 / 1024:.1f} MB")
            
            print(f"\n✅ Teste concluído com sucesso! Encontrados {len(final_candidates)} candidatos únicos.")
            return True
        else:
            print("\n❌ Nenhum candidato encontrado")
            return False
    
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def extract_album_name_from_path(directory_path: str) -> str:
    """Extrai nome do álbum do caminho do diretório"""
    if not directory_path:
        return "Álbum Desconhecido"
    
    # Pega o último diretório do caminho
    album_name = os.path.basename(directory_path)
    
    # Se estiver vazio, pega o penúltimo
    if not album_name:
        parts = directory_path.rstrip('/\\').split('/')
        if len(parts) > 1:
            album_name = parts[-2]
    
    # Limita o tamanho
    if len(album_name) > 50:
        album_name = album_name[:47] + "..."
    
    return album_name or "Álbum Desconhecido"

def extract_album_name_from_metadata(candidate: dict) -> str:
    """Extrai nome do álbum usando análise inteligente do diretório e arquivos"""
    import re
    
    try:
        # Pega alguns arquivos do álbum para análise
        files = candidate.get('files', [])
        if not files:
            return extract_album_name_from_path(candidate['directory'])
        
        # Tenta extrair nome do álbum dos metadados/estrutura
        album_names = []
        
        # Verifica até 3 arquivos para encontrar o nome do álbum
        for file_info in files[:3]:
            filename = file_info.get('filename', '')
            if not filename.lower().endswith('.mp3'):
                continue
            
            try:
                # Extrai possível nome do álbum do caminho
                directory = candidate['directory']
                
                if directory:
                    # Procura por padrões comuns de organização
                    # Ex: /Music/Artist/Album/, /Artist - Album/, etc.
                    parts = directory.replace('\\', '/').split('/')
                    
                    for part in reversed(parts):
                        if part and not part.lower() in ['music', 'mp3', 'flac', 'audio']:
                            # Remove anos e outros padrões comuns
                            clean_part = re.sub(r'\b(19|20)\d{2}\b', '', part).strip()
                            clean_part = re.sub(r'[\[\]()]', '', clean_part).strip()
                            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
                            
                            if len(clean_part) > 3:  # Nome mínimo válido
                                album_names.append(clean_part)
                                break
                
                # Se não encontrou no diretório, tenta extrair do nome do arquivo
                if not album_names:
                    basename = os.path.basename(filename)
                    # Remove extensão e número da faixa
                    clean_name = re.sub(r'\.(mp3|flac|wav)$', '', basename, flags=re.IGNORECASE)
                    clean_name = re.sub(r'^\d+[\s\-\.]*', '', clean_name)  # Remove número da faixa
                    
                    # Procura por padrões como "Artist - Album - Track"
                    if ' - ' in clean_name:
                        parts = clean_name.split(' - ')
                        if len(parts) >= 3:  # Artist - Album - Track
                            album_names.append(parts[1].strip())
                        elif len(parts) == 2:  # Artist - Track ou Album - Track
                            # Verifica se o primeiro parte parece ser um álbum
                            first_part = parts[0].strip()
                            if len(first_part) > 10:  # Provavelmente um álbum
                                album_names.append(first_part)
                
                break  # Para no primeiro arquivo processado com sucesso
                
            except Exception as e:
                continue
        
        # Escolhe o nome mais comum ou o primeiro válido
        if album_names:
            # Remove duplicatas mantendo ordem
            unique_names = []
            for name in album_names:
                if name not in unique_names:
                    unique_names.append(name)
            
            # Pega o primeiro nome válido
            best_name = unique_names[0]
            
            # Limita o tamanho
            if len(best_name) > 50:
                best_name = best_name[:47] + "..."
            
            return best_name
        
        # Fallback para nome do diretório
        return extract_album_name_from_path(candidate['directory'])
        
    except Exception as e:
        print(f"Erro ao extrair nome do álbum dos metadados: {e}")
        return extract_album_name_from_path(candidate['directory'])

def test_telegram_bot_integration():
    """Testa a integração com o bot do Telegram"""
    try:
        from telegram_bot import TelegramMusicBot
        
        print("\n🤖 Testando integração com bot do Telegram...")
        
        # Verifica se as variáveis necessárias estão configuradas
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN não configurado")
            return False
        
        print("✅ Token do bot configurado")
        
        # Tenta criar instância do bot (sem iniciar)
        try:
            bot = TelegramMusicBot()
            print("✅ Bot criado com sucesso")
            
            # Verifica se os métodos necessários existem
            required_methods = [
                '_search_album_candidates',
                '_show_album_candidates', 
                '_handle_album_selection',
                '_start_album_download',
                '_execute_album_download',
                '_download_album_tracks',
                '_extract_album_name_from_path'
            ]
            
            for method_name in required_methods:
                if hasattr(bot, method_name):
                    print(f"✅ Método {method_name} encontrado")
                else:
                    print(f"❌ Método {method_name} não encontrado")
                    return False
            
            print("✅ Todos os métodos necessários estão presentes")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar bot: {e}")
            return False
    
    except ImportError as e:
        print(f"❌ Erro ao importar bot: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🧪 TESTE DA FUNCIONALIDADE DE SELEÇÃO DE ÁLBUNS")
    print("=" * 50)
    
    # Teste 1: Busca de candidatos
    print("\n1️⃣ Testando busca de candidatos de álbum...")
    test1_success = test_album_search_candidates()
    
    # Teste 2: Integração com bot
    print("\n2️⃣ Testando integração com bot do Telegram...")
    test2_success = test_telegram_bot_integration()
    
    # Resultado final
    print("\n" + "=" * 50)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   Busca de candidatos: {'✅ PASSOU' if test1_success else '❌ FALHOU'}")
    print(f"   Integração com bot: {'✅ PASSOU' if test2_success else '❌ FALHOU'}")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 Para testar no Telegram:")
        print("   1. Execute: python3 telegram_bot.py")
        print("   2. Use o comando: /album Pink Floyd - The Dark Side of the Moon")
        print("   3. Selecione um álbum da lista que aparecer")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("   Verifique os erros acima e corrija antes de usar")

if __name__ == "__main__":
    main()
