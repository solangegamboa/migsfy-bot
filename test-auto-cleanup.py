#!/usr/bin/env python3

"""
Script de teste para verificar funcionalidades de limpeza automática
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from slskd_mp3_search import (
    connectToSlskd, 
    auto_cleanup_completed_downloads,
    manual_cleanup_downloads,
    monitor_and_cleanup_downloads
)

def test_connection():
    """Testa conexão com slskd"""
    print("🔗 Testando conexão com slskd...")
    slskd = connectToSlskd()
    if slskd:
        print("✅ Conexão estabelecida com sucesso!")
        return slskd
    else:
        print("❌ Falha na conexão!")
        return None

def test_auto_cleanup(slskd):
    """Testa limpeza automática"""
    print("\n🧹 Testando limpeza automática...")
    
    # Teste silencioso
    print("📝 Teste silencioso:")
    removed = auto_cleanup_completed_downloads(slskd, silent=True)
    print(f"   Removidos: {removed} downloads")
    
    # Teste com feedback
    print("📝 Teste com feedback:")
    removed = auto_cleanup_completed_downloads(slskd, silent=False)
    print(f"   Total removidos: {removed} downloads")

def test_manual_cleanup(slskd):
    """Testa limpeza manual"""
    print("\n🛠️ Testando limpeza manual...")
    removed = manual_cleanup_downloads(slskd)
    print(f"✅ Limpeza manual concluída: {removed} downloads removidos")

def test_monitor_cleanup(slskd):
    """Testa monitoramento (versão curta para teste)"""
    print("\n👀 Testando monitoramento (30 segundos)...")
    try:
        monitor_and_cleanup_downloads(slskd, max_wait=30, check_interval=5)
        print("✅ Teste de monitoramento concluído!")
    except KeyboardInterrupt:
        print("⚠️ Teste interrompido pelo usuário")

def show_current_downloads(slskd):
    """Mostra downloads atuais"""
    print("\n📊 Downloads atuais:")
    try:
        downloads = slskd.transfers.get_all_downloads()
        if downloads:
            for i, download in enumerate(downloads, 1):
                filename = os.path.basename(download.get('filename', 'N/A'))
                state = download.get('state', 'N/A')
                username = download.get('username', 'N/A')
                print(f"   {i}. {filename} - {state} (de {username})")
        else:
            print("   Nenhum download ativo")
    except Exception as e:
        print(f"   ❌ Erro ao listar downloads: {e}")

def main():
    print("🧪 TESTE DE FUNCIONALIDADES DE LIMPEZA AUTOMÁTICA")
    print("=" * 60)
    
    # Testa conexão
    slskd = test_connection()
    if not slskd:
        return
    
    # Mostra downloads atuais
    show_current_downloads(slskd)
    
    # Menu de testes
    while True:
        print("\n" + "=" * 60)
        print("🧪 MENU DE TESTES:")
        print("1. Limpeza automática")
        print("2. Limpeza manual")
        print("3. Monitoramento (30s)")
        print("4. Mostrar downloads atuais")
        print("5. Sair")
        
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == '1':
            test_auto_cleanup(slskd)
        elif choice == '2':
            test_manual_cleanup(slskd)
        elif choice == '3':
            test_monitor_cleanup(slskd)
        elif choice == '4':
            show_current_downloads(slskd)
        elif choice == '5':
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()
