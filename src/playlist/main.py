#!/usr/bin/env python3
"""
Playlist Processor - Script Principal

Processa playlists automaticamente via SLSKD com controle de duplicatas,
rate limiting e cache inteligente.

Uso:
    python main.py                    # Processamento normal
    python main.py --verbose         # Com logs detalhados  
    python main.py --status          # Apenas estatísticas
    python main.py --help            # Ajuda
"""

import sys
import argparse
import os
from pathlib import Path

# Adicionar diretório src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from playlist.playlist_processor import PlaylistProcessor

def setup_environment():
    """Configura ambiente e carrega .env"""
    # Carregar .env do diretório raiz do projeto
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Configurações carregadas de: {env_path}")
    else:
        print(f"⚠️ Arquivo .env não encontrado em: {env_path}")

def show_status():
    """Mostra apenas estatísticas sem processar"""
    try:
        processor = PlaylistProcessor()
        
        print("📊 STATUS DO SISTEMA")
        print("="*40)
        
        # Estatísticas do banco
        db_stats = processor.db_manager.get_stats()
        print(f"💾 Registros no banco:")
        for status, count in db_stats.items():
            if status != 'cache_entries':
                print(f"   {status}: {count}")
        
        print(f"🗄️ Cache entries: {db_stats.get('cache_entries', 0)}")
        
        # Estatísticas de conexão
        conn_stats = processor.slskd_client.get_connection_stats()
        print(f"🌐 Conexão SLSKD:")
        print(f"   Host: {conn_stats['host']}:{conn_stats['port']}")
        print(f"   Falhas consecutivas: {conn_stats['consecutive_failures']}")
        print(f"   Sobrecarregado: {'Sim' if conn_stats['is_overloaded'] else 'Não'}")
        
        # Arquivos pendentes
        playlist_path = processor.playlist_path
        if os.path.exists(playlist_path):
            import glob
            txt_files = glob.glob(os.path.join(playlist_path, "*.txt"))
            total_lines = 0
            
            for file_path in txt_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                        total_lines += len(lines)
                except Exception:
                    pass
            
            print(f"📁 Arquivos pendentes: {len(txt_files)}")
            print(f"📝 Linhas pendentes: {total_lines}")
        else:
            print(f"❌ Diretório de playlists não encontrado: {playlist_path}")
        
        print("="*40)
        
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        sys.exit(1)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Playlist Processor - Processamento automático de playlists via SLSKD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                    # Processamento normal
  python main.py --verbose         # Com logs detalhados
  python main.py --status          # Apenas estatísticas
  
Configuração:
  Configure as variáveis no arquivo .env na raiz do projeto.
  
Mais informações:
  Consulte a documentação em docs/playlist/
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Ativa logs detalhados'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Mostra apenas estatísticas do sistema'
    )
    
    args = parser.parse_args()
    
    # Configurar ambiente
    setup_environment()
    
    # Verificar se é apenas status
    if args.status:
        show_status()
        return
    
    # Configurar verbosidade
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
        print("🔍 Modo verbose ativado")
    
    try:
        # Executar processamento
        processor = PlaylistProcessor()
        processor.process_all_playlists()
        
    except KeyboardInterrupt:
        print("\n⏹️ Processamento interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
