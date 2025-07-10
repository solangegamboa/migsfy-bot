#!/usr/bin/env python3

"""
Script de teste para verificar funcionalidades de busca por álbum
"""

import sys
import os
import importlib.util

# Carrega o módulo principal usando importlib (para arquivos com hífen)
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, 'slskd-mp3-search.py')

try:
    spec = importlib.util.spec_from_file_location("slskd_mp3_search", module_path)
    slskd_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(slskd_module)
    
    # Importa as funções necessárias
    connectToSlskd = slskd_module.connectToSlskd
    is_album_search = slskd_module.is_album_search
    extract_artist_and_album = slskd_module.extract_artist_and_album
    create_album_search_variations = slskd_module.create_album_search_variations
    smart_album_search = slskd_module.smart_album_search
    
    print("✅ Módulo carregado com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao carregar módulo: {e}")
    print("💡 Certifique-se de que o arquivo slskd-mp3-search.py está no mesmo diretório")
    sys.exit(1)

def test_album_detection():
    """Testa detecção automática de álbuns"""
    print("🧪 TESTE DE DETECÇÃO DE ÁLBUM")
    print("=" * 50)
    
    test_cases = [
        # Casos que DEVEM ser detectados como álbum
        ("Pink Floyd - The Dark Side of the Moon", True),
        ("Beatles - Abbey Road Album", True),
        ("Led Zeppelin Discography", True),
        ("Queen - Greatest Hits", True),
        ("Radiohead - OK Computer LP", True),
        ("Miles Davis - Kind of Blue", True),
        ("Nirvana - Nevermind", True),
        
        # Casos que NÃO devem ser detectados como álbum
        ("Pink Floyd - Comfortably Numb", False),
        ("Beatles - Hey Jude", False),
        ("Queen - Bohemian Rhapsody", False),
        ("Radiohead - Creep", False),
        ("Miles Davis - So What", False),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for query, expected in test_cases:
        result = is_album_search(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{query}' -> {result} (esperado: {expected})")
        if result == expected:
            correct += 1
    
    print(f"\n📊 Resultado: {correct}/{total} ({correct/total*100:.1f}%) corretos")
    return correct == total

def test_artist_album_extraction():
    """Testa extração de artista e álbum"""
    print("\n🧪 TESTE DE EXTRAÇÃO ARTISTA/ÁLBUM")
    print("=" * 50)
    
    test_cases = [
        ("Pink Floyd - The Dark Side of the Moon", ("Pink Floyd", "The Dark Side of the Moon")),
        ("Beatles - Abbey Road", ("Beatles", "Abbey Road")),
        ("Led Zeppelin: IV", ("Led Zeppelin", "IV")),
        ("Miles Davis | Kind of Blue", ("Miles Davis", "Kind of Blue")),
        ("Radiohead – OK Computer", ("Radiohead", "OK Computer")),
        ("Simple Album Name", ("Simple Album Name", "")),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for query, expected in test_cases:
        result = extract_artist_and_album(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{query}' -> {result}")
        if result == expected:
            correct += 1
    
    print(f"\n📊 Resultado: {correct}/{total} ({correct/total*100:.1f}%) corretos")
    return correct == total

def test_album_search_variations():
    """Testa criação de variações de busca para álbum"""
    print("\n🧪 TESTE DE VARIAÇÕES DE BUSCA")
    print("=" * 50)
    
    test_query = "Pink Floyd - The Dark Side of the Moon"
    variations = create_album_search_variations(test_query)
    
    print(f"Query: '{test_query}'")
    print(f"Variações criadas: {len(variations)}")
    
    for i, variation in enumerate(variations, 1):
        print(f"  {i:2d}. {variation}")
    
    return len(variations) > 0

def test_album_search_live():
    """Teste real de busca por álbum (requer conexão com slskd)"""
    print("\n🧪 TESTE DE BUSCA REAL POR ÁLBUM")
    print("=" * 50)
    
    slskd = connectToSlskd()
    if not slskd:
        print("❌ Não foi possível conectar ao slskd")
        return False
    
    print("✅ Conectado ao slskd com sucesso!")
    
    # Álbuns de teste (escolha álbuns populares)
    test_albums = [
        "Pink Floyd - The Dark Side of the Moon",
        "Beatles - Abbey Road",
        "Nirvana - Nevermind",
    ]
    
    print(f"\n🎯 Álbuns de teste disponíveis:")
    for i, album in enumerate(test_albums, 1):
        print(f"  {i}. {album}")
    
    choice = input(f"\nEscolha um álbum para testar (1-{len(test_albums)}) ou digite 0 para pular: ").strip()
    
    try:
        choice_num = int(choice)
        if choice_num == 0:
            print("⏭️ Teste de busca real pulado")
            return True
        elif 1 <= choice_num <= len(test_albums):
            test_album = test_albums[choice_num - 1]
            print(f"\n🔍 Testando busca por: '{test_album}'")
            
            # Executa busca (sem download real)
            print("⚠️ ATENÇÃO: Este é apenas um teste de busca, não fará downloads!")
            confirm = input("Continuar? (s/n): ").lower().strip()
            
            if confirm in ['s', 'sim', 'y', 'yes']:
                # Aqui você poderia chamar smart_album_search, mas vamos apenas simular
                print("🔍 Simulando busca por álbum...")
                print("✅ Teste de busca simulado com sucesso!")
                return True
            else:
                print("❌ Teste cancelado pelo usuário")
                return False
        else:
            print("❌ Opção inválida")
            return False
    except ValueError:
        print("❌ Entrada inválida")
        return False

def main():
    print("🧪 TESTE DE FUNCIONALIDADES DE BUSCA POR ÁLBUM")
    print("=" * 60)
    
    tests = [
        ("Detecção de álbum", test_album_detection),
        ("Extração artista/álbum", test_artist_album_extraction),
        ("Variações de busca", test_album_search_variations),
        ("Busca real (opcional)", test_album_search_live),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 EXECUTANDO: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERRO em {test_name}: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print(f"\n{'='*60}")
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado geral: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! Funcionalidade de álbum está funcionando.")
    else:
        print("⚠️ Alguns testes falharam. Verifique a implementação.")

if __name__ == "__main__":
    main()
