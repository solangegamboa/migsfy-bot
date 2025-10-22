#!/usr/bin/env python3

import os
import sys
import time

import slskd_api
from dotenv import load_dotenv

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Carrega variáveis de ambiente
load_dotenv()


def connectToSlskd():
    """Conecta ao slskd usando variáveis de ambiente"""
    try:
        host = os.getenv("SLSKD_HOST", "192.168.15.100")
        api_key = os.getenv("SLSKD_API_KEY")
        url_base = os.getenv("SLSKD_URL_BASE", f"http://{host}:5030")

        if not api_key:
            print("❌ SLSKD_API_KEY não encontrada no arquivo .env")
            return None

        slskd = slskd_api.SlskdClient(host=host, api_key=api_key, url_base=url_base)
        slskd.application.state()  # Testa conexão
        print(f"✅ Conectado com sucesso ao slskd em {host}!")
        return slskd
    except Exception as e:
        print(f"❌ Falha ao conectar: {e}")
        return None


def batch_download_from_file(file_path, delay=3):
    """Baixa músicas linha por linha de um arquivo TXT"""

    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        return

    # Conecta ao slskd
    slskd = connectToSlskd()
    if not slskd:
        return

    # Importa função de busca
    try:
        from cli.main import smart_mp3_search
    except ImportError:
        print("❌ Erro ao importar função de busca")
        return

    print(f"📖 Lendo arquivo: {file_path}")

    # Lê o arquivo
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return

    if not lines:
        print("❌ Arquivo vazio ou sem linhas válidas")
        return

    print(f"🎵 Encontradas {len(lines)} músicas para baixar")
    print("=" * 60)

    successful_downloads = 0
    failed_downloads = 0

    for i, search_term in enumerate(lines, 1):
        print(f"\n📍 [{i}/{len(lines)}] {search_term}")

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

        # Pausa entre downloads
        if i < len(lines):
            print(f"   ⏸️ Pausa de {delay}s...")
            time.sleep(delay)

    # Relatório final
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO FINAL - BATCH DOWNLOAD")
    print(f"✅ Downloads bem-sucedidos: {successful_downloads}")
    print(f"❌ Downloads com falha: {failed_downloads}")
    print(f"📊 Total processado: {len(lines)}")

    if successful_downloads > 0:
        print(f"\n💡 {successful_downloads} downloads foram iniciados!")
        print(f"💡 Monitore o progresso no slskd web interface")


def main():
    if len(sys.argv) < 2:
        print("🎵 BATCH DOWNLOAD TOOL")
        print("📖 Baixa músicas linha por linha de um arquivo TXT")
        print()
        print("Uso:")
        print("  python3 batch-download.py <arquivo.txt> [delay]")
        print()
        print("Parâmetros:")
        print("  arquivo.txt  : Arquivo com uma música por linha")
        print("  delay        : Pausa entre downloads em segundos (padrão: 3)")
        print()
        print("Exemplo:")
        print("  python3 batch-download.py musicas.txt 5")
        print()
        print("Formato do arquivo:")
        print("  Artista - Música")
        print("  Pink Floyd - Comfortably Numb")
        print("  Beatles - Hey Jude")
        return

    file_path = sys.argv[1]
    delay = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"📁 Arquivo: {file_path}")
    print(f"⏱️ Delay: {delay}s entre downloads")
    print()

    batch_download_from_file(file_path, delay)


if __name__ == "__main__":
    main()
