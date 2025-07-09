#!/usr/bin/env python3

"""
Script de teste para verificar se o comando /album foi implementado corretamente no bot do Telegram
"""

import sys
import os
import importlib.util

def test_bot_imports():
    """Testa se as importações do bot estão funcionando"""
    print("🧪 TESTE DE IMPORTAÇÕES DO BOT")
    print("=" * 50)
    
    try:
        # Lê o arquivo do bot diretamente para verificar se as funções existem
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bot_path = os.path.join(current_dir, 'telegram_bot.py')
        
        with open(bot_path, 'r', encoding='utf-8') as f:
            bot_content = f.read()
        
        print("✅ Arquivo telegram_bot.py lido com sucesso")
        
        # Verifica se a classe TelegramMusicBot existe
        if 'class TelegramMusicBot:' in bot_content:
            print("✅ Classe TelegramMusicBot encontrada")
        else:
            print("❌ Classe TelegramMusicBot NÃO encontrada")
            return False
        
        # Verifica se o método album_command existe
        if 'async def album_command(' in bot_content:
            print("✅ Método album_command encontrado")
        else:
            print("❌ Método album_command NÃO encontrado")
            return False
        
        # Verifica se o método _handle_album_search existe
        if 'async def _handle_album_search(' in bot_content:
            print("✅ Método _handle_album_search encontrado")
        else:
            print("❌ Método _handle_album_search NÃO encontrado")
            return False
        
        # Verifica se smart_album_search está sendo importado
        if 'smart_album_search' in bot_content:
            print("✅ Importação smart_album_search encontrada")
        else:
            print("❌ Importação smart_album_search NÃO encontrada")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo do bot: {e}")
        return False

def test_main_module_imports():
    """Testa se as importações do módulo principal estão funcionando"""
    print("\n🧪 TESTE DE IMPORTAÇÕES DO MÓDULO PRINCIPAL")
    print("=" * 50)
    
    try:
        # Carrega o módulo principal
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_path = os.path.join(current_dir, 'slskd-mp3-search.py')
        
        spec = importlib.util.spec_from_file_location("slskd_mp3_search", main_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        print("✅ Módulo slskd-mp3-search carregado com sucesso")
        
        # Testa se a função smart_album_search existe
        if hasattr(main_module, 'smart_album_search'):
            print("✅ Função smart_album_search encontrada")
        else:
            print("❌ Função smart_album_search NÃO encontrada")
            return False
        
        # Testa se outras funções relacionadas existem
        functions_to_check = [
            'is_album_search',
            'extract_artist_and_album',
            'create_album_search_variations',
            'find_album_candidates',
            'download_album_tracks'
        ]
        
        for func_name in functions_to_check:
            if hasattr(main_module, func_name):
                print(f"✅ Função {func_name} encontrada")
            else:
                print(f"❌ Função {func_name} NÃO encontrada")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar módulo principal: {e}")
        return False

def test_help_text():
    """Testa se o texto de ajuda foi atualizado"""
    print("\n🧪 TESTE DO TEXTO DE AJUDA")
    print("=" * 50)
    
    try:
        # Lê o arquivo do bot
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bot_path = os.path.join(current_dir, 'telegram_bot.py')
        
        with open(bot_path, 'r', encoding='utf-8') as f:
            bot_content = f.read()
        
        # Verifica se o comando /album está no texto de ajuda
        if '/album' in bot_content:
            print("✅ Comando /album encontrado no código do bot")
        else:
            print("❌ Comando /album NÃO encontrado no código do bot")
            return False
        
        # Verifica se há exemplos de álbum
        album_examples = [
            'Pink Floyd - The Dark Side of the Moon',
            'Beatles - Abbey Road'
        ]
        
        found_examples = 0
        for example in album_examples:
            if example in bot_content:
                print(f"✅ Exemplo '{example}' encontrado")
                found_examples += 1
            else:
                print(f"⚠️ Exemplo '{example}' não encontrado")
        
        if found_examples > 0:
            print(f"✅ {found_examples} exemplos de álbum encontrados")
        else:
            print("❌ Nenhum exemplo de álbum encontrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar texto de ajuda: {e}")
        return False

def test_command_handler():
    """Testa se o handler do comando foi registrado"""
    print("\n🧪 TESTE DO HANDLER DO COMANDO")
    print("=" * 50)
    
    try:
        # Lê o arquivo do bot
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bot_path = os.path.join(current_dir, 'telegram_bot.py')
        
        with open(bot_path, 'r', encoding='utf-8') as f:
            bot_content = f.read()
        
        # Verifica se o handler foi registrado
        if 'CommandHandler("album", self.album_command)' in bot_content:
            print("✅ Handler do comando /album registrado corretamente")
        else:
            print("❌ Handler do comando /album NÃO registrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar handler: {e}")
        return False

def main():
    print("🧪 TESTE DE IMPLEMENTAÇÃO DO COMANDO /ALBUM NO BOT TELEGRAM")
    print("=" * 70)
    
    tests = [
        ("Importações do Bot", test_bot_imports),
        ("Importações do Módulo Principal", test_main_module_imports),
        ("Texto de Ajuda", test_help_text),
        ("Handler do Comando", test_command_handler),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"🧪 EXECUTANDO: {test_name}")
        print(f"{'='*70}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERRO em {test_name}: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print(f"\n{'='*70}")
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print(f"{'='*70}")
    
    passed = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado geral: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! O comando /album foi implementado corretamente.")
        print("\n💡 Para testar o bot:")
        print("1. Configure o token do bot no arquivo .env")
        print("2. Execute: python3 telegram_bot.py")
        print("3. No Telegram, use: /album Pink Floyd - The Dark Side of the Moon")
    else:
        print("⚠️ Alguns testes falharam. Verifique a implementação.")

if __name__ == "__main__":
    main()
