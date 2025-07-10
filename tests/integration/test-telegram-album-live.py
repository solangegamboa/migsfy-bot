#!/usr/bin/env python3

"""
Teste ao vivo da funcionalidade de seleção de álbuns no Telegram
Este script inicia o bot e fornece instruções para teste manual
"""

import os
import sys
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def check_prerequisites():
    """Verifica se todos os pré-requisitos estão atendidos"""
    print("🔍 Verificando pré-requisitos...")
    
    # Verifica token do bot
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN não configurado no .env")
        return False
    print("✅ Token do Telegram configurado")
    
    # Verifica configuração do slskd
    slskd_host = os.getenv('SLSKD_HOST')
    slskd_key = os.getenv('SLSKD_API_KEY')
    if not slskd_host or not slskd_key:
        print("❌ Configuração do slskd incompleta no .env")
        return False
    print("✅ Configuração do slskd OK")
    
    # Verifica se o arquivo do bot existe
    if not os.path.exists('telegram_bot.py'):
        print("❌ Arquivo telegram_bot.py não encontrado")
        return False
    print("✅ Bot do Telegram encontrado")
    
    return True

def show_test_instructions():
    """Mostra instruções para teste manual"""
    print("\n" + "="*60)
    print("🧪 INSTRUÇÕES PARA TESTE DA SELEÇÃO DE ÁLBUNS")
    print("="*60)
    
    print("\n📱 COMANDOS PARA TESTAR NO TELEGRAM:")
    print("   /album Pink Floyd - The Dark Side of the Moon")
    print("   /album Beatles - Abbey Road")
    print("   /album Radiohead - OK Computer")
    print("   /album Led Zeppelin - IV")
    print("   /album Queen - A Night at the Opera")
    
    print("\n🎯 O QUE ESPERAR:")
    print("   1. Bot mostra 'Buscando álbum...' com botão de cancelar")
    print("   2. Bot lista os 5 melhores álbuns encontrados")
    print("   3. Cada álbum mostra: nome, usuário, faixas, bitrate, tamanho")
    print("   4. Botões clicáveis para cada álbum")
    print("   5. Ao clicar, inicia download com progresso")
    print("   6. Relatório final com estatísticas")
    
    print("\n🧪 CENÁRIOS DE TESTE:")
    print("   ✅ Teste normal: Buscar álbum e selecionar um")
    print("   ✅ Teste de cancelamento: Cancelar durante busca")
    print("   ✅ Teste de cancelamento: Cancelar durante download")
    print("   ✅ Teste sem resultados: Buscar álbum inexistente")
    print("   ✅ Teste de múltiplos usuários: Vários comandos simultâneos")
    
    print("\n🔍 VERIFICAÇÕES:")
    print("   • Interface mostra informações corretas?")
    print("   • Botões funcionam corretamente?")
    print("   • Cancelamento funciona em todas as etapas?")
    print("   • Downloads são iniciados no slskd?")
    print("   • Relatórios finais são precisos?")
    
    print("\n💡 DICAS:")
    print("   • Use /tasks para ver tarefas ativas")
    print("   • Use /status para verificar conexões")
    print("   • Monitore logs do bot para debug")
    print("   • Verifique interface web do slskd para downloads")

def main():
    """Função principal"""
    print("🎵 TESTE AO VIVO - SELEÇÃO DE ÁLBUNS NO TELEGRAM")
    print("="*50)
    
    # Verifica pré-requisitos
    if not check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Corrija os problemas acima.")
        sys.exit(1)
    
    # Mostra instruções
    show_test_instructions()
    
    # Pergunta se quer iniciar o bot
    print("\n" + "="*60)
    response = input("🚀 Deseja iniciar o bot agora? (s/n): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        print("\n🤖 Iniciando bot do Telegram...")
        print("💡 Pressione Ctrl+C para parar o bot")
        print("📱 Abra o Telegram e teste os comandos listados acima")
        
        # Pequena pausa para o usuário ler
        time.sleep(2)
        
        try:
            # Importa e executa o bot
            from telegram_bot import main as bot_main
            bot_main()
        except KeyboardInterrupt:
            print("\n🛑 Bot interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro ao executar bot: {e}")
    else:
        print("\n💡 Para iniciar o bot manualmente:")
        print("   python3 telegram_bot.py")
        print("\n📖 Consulte TELEGRAM-ALBUM-EXAMPLE.md para exemplos visuais")

if __name__ == "__main__":
    main()
