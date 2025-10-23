import os
import time
from typing import Dict, List, Optional

from slskd_api import SlskdClient

from .cache_manager import CacheManager
from .rate_limiter import RateLimiter


class SlskdApiClient:
    def __init__(self, db_manager):
        # Configuração da API usando .env existente
        self.host = os.getenv("SLSKD_HOST", "localhost")
        self.port = int(os.getenv("SLSKD_PORT", 5030))
        self.api_key = os.getenv("SLSKD_API_KEY", "")
        self.base_url = os.getenv("SLSKD_URL_BASE", f"http://{self.host}:{self.port}")

        # Inicializar componentes
        self.api = SlskdClient(host=self.base_url, api_key=self.api_key)
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager(db_manager)

        # Configurações
        self.max_retries = int(os.getenv("MAX_RETRY_ATTEMPTS", 3))
        self.server_overload_threshold = 5  # Falhas consecutivas
        self.consecutive_failures = 0

    def search_tracks_cached(self, query: str) -> List[Dict]:
        """Busca com cache e rate limiting"""

        def _search_function(q):
            return self._search_tracks_raw(q)

        return self.cache_manager.search_with_cache(query, _search_function)

    def _search_tracks_raw(self, query: str) -> List[Dict]:
        """Busca raw sem cache"""
        self.rate_limiter.wait_if_needed()

        for attempt in range(1, self.max_retries + 1):
            try:
                # Executar busca
                search_response = self.api.searches.search_text(query)
                print(f"🔍 Busca iniciada: {search_response}")
                
                # Aguardar conclusão da busca
                search_id = search_response.get('id')
                if not search_id:
                    raise Exception("ID da busca não retornado")
                
                results = self._wait_for_search_completion(search_id)
                
                # Sucesso - resetar contadores
                self.rate_limiter.record_request()
                self.consecutive_failures = 0

                return self._process_search_results(results)

            except Exception as e:
                self.consecutive_failures += 1
                self.rate_limiter.record_failure()

                if "rate limit" in str(e).lower():
                    self.rate_limiter.handle_rate_limit_error()
                    continue

                if attempt < self.max_retries:
                    self.rate_limiter.apply_backoff(attempt)
                    continue

                # Última tentativa falhou
                if self.consecutive_failures >= self.server_overload_threshold:
                    print("Servidor possivelmente sobrecarregado. Pausando...")
                    time.sleep(600)  # 10 minutos

                raise e

        return []

    def get_user_status(self, username: str) -> Optional[Dict]:
        """Obtém status do usuário (online/offline)"""
        try:
            return self.api.users.status(username)
        except Exception as e:
            print(f"Erro ao obter status do usuário {username}: {e}")
            return None

    def is_user_online(self, username: str) -> bool:
        """Verifica se usuário está online"""
        status = self.get_user_status(username)
        if status:
            presence = status.get('presence', '').lower()
            return presence == 'online'
        return False

    def _wait_for_search_completion(self, search_id: str, timeout: int = None) -> List[Dict]:
        """Aguarda conclusão da busca e retorna os resultados"""
        if timeout is None:
            timeout = int(os.getenv('SEARCH_COMPLETION_TIMEOUT', 120))
            
        start_time = time.time()
        check_interval = 10  # Intervalo fixo de 10 segundos
        
        print(f"🔍 Aguardando conclusão da busca {search_id} (timeout: {timeout}s, intervalo: {check_interval}s)")
        
        while time.time() - start_time < timeout:
            try:
                # Verificar status de todas as buscas
                all_searches = self.api.searches.get_all()
                search_status = None
                
                # Encontrar nossa busca pelo ID
                for search in all_searches:
                    if search.get('id') == search_id:
                        search_status = search
                        break
                
                if not search_status:
                    print(f"⚠️ Busca {search_id} não encontrada na lista")
                    time.sleep(check_interval)
                    continue
                
                state = search_status.get('state', 'Unknown')
                file_count = search_status.get('fileCount', 0)
                is_complete = search_status.get('isComplete', False)
                elapsed = int(time.time() - start_time)
                
                print(f"🔍 [{elapsed}s] Estado: {state} | Complete: {is_complete} | Arquivos: {file_count}")
                
                # Aguardar especificamente por isComplete = True
                if is_complete is True:
                    print(f"✅ Busca marcada como completa após {elapsed}s")
                    
                    if file_count > 0:
                        # Obter respostas usando o ID da busca
                        try:
                            responses = self.api.searches.search_responses(search_id)
                            print(f"🔍 Busca concluída com {len(responses)} respostas e {file_count} arquivos")
                            return responses
                        except Exception as e:
                            print(f"⚠️ Erro ao obter respostas da busca: {e}")
                            # Continuar tentando por mais algumas iterações
                            time.sleep(check_interval)
                            continue
                    else:
                        print("🔍 Busca concluída mas sem resultados (fileCount = 0)")
                        return []
                
                # Aguardar antes da próxima verificação
                time.sleep(check_interval)
                
            except Exception as e:
                elapsed = int(time.time() - start_time)
                print(f"❌ [{elapsed}s] Erro ao verificar status da busca: {e}")
                time.sleep(check_interval)
        
        elapsed = int(time.time() - start_time)
        raise Exception(f"Timeout ({elapsed}s) aguardando conclusão da busca {search_id}")

    def _process_search_results(self, raw_results) -> List[Dict]:
        """Processa resultados da API para formato padrão"""
        processed = []

        if not raw_results:
            print("🔍 DEBUG: Nenhum resultado bruto recebido")
            return processed

        print(f"🔍 DEBUG: Processando {len(raw_results)} usuários")
        print(
            f"🔍 DEBUG: Tipo do primeiro resultado: {type(raw_results[0]) if raw_results else 'N/A'}"
        )

        # Debug: mostrar estrutura do primeiro resultado
        if raw_results and len(raw_results) > 0:
            first_result = raw_results[0]
            print(
                f"🔍 DEBUG: Chaves do primeiro resultado: {list(first_result.keys()) if isinstance(first_result, dict) else 'Não é dict'}"
            )
            if isinstance(first_result, dict) and "files" in first_result:
                files = first_result.get("files", [])
                print(f"🔍 DEBUG: Primeiro usuário tem {len(files)} arquivos")
                if files:
                    print(
                        f"🔍 DEBUG: Chaves do primeiro arquivo: {list(files[0].keys()) if isinstance(files[0], dict) else 'Não é dict'}"
                    )

        # Processar estrutura da API slskd - cada resultado tem username e files
        for i, user_result in enumerate(raw_results):
            if isinstance(user_result, dict):
                username = user_result.get("username", "")
                files = user_result.get("files", [])

                if "files" not in user_result:
                    print(
                        f"🔍 DEBUG: PROBLEMA - Usuário {username} não tem chave 'files'"
                    )
                    print(f"🔍 DEBUG: Chaves disponíveis: {list(user_result.keys())}")
                    continue

                # Processar cada arquivo do usuário
                for j, file_info in enumerate(files):
                    if isinstance(file_info, dict):
                        filename = file_info.get("filename", "")
                        processed.append(
                            {
                                "username": username,
                                "filename": filename,
                                "size": file_info.get("size", 0),
                                "bitDepth": file_info.get("bitDepth", 0),
                                "sampleRate": file_info.get("sampleRate", 0),
                                "bitRate": file_info.get("bitRate", 0),
                                "length": file_info.get("length", 0),
                                "extension": file_info.get("extension", ""),
                                "isLocked": file_info.get("isLocked", False),
                            }
                        )
                    else:
                        print(
                            f"🔍 DEBUG: Arquivo {j+1} do usuário {username} não é dict: {type(file_info)}"
                        )
            else:
                print(f"🔍 DEBUG: Resultado {i+1} não é dict: {type(user_result)}")

        return processed

    def get_download_queue(self) -> List[Dict]:
        """Obtém fila de downloads"""
        try:
            return self.api.transfers.get_all_downloads()
        except Exception as e:
            print(f"Erro ao obter fila de downloads: {e}")
            return []

    def add_download(self, username: str, filename: str, file_size: int = 0) -> Optional[str]:
        """Adiciona download à fila"""
        try:
            # Validar parâmetros
            if not username or not username.strip():
                print(f"❌ Username vazio ou inválido: '{username}'")
                return None
                
            if not filename or not filename.strip():
                print(f"❌ Filename vazio ou inválido: '{filename}'")
                return None
            
            # Limpar parâmetros
            clean_username = username.strip()
            clean_filename = filename.strip()
            
            # Formato correto baseado no curl que funciona
            file_dict = {
                "filename": clean_filename,
                "size": file_size
            }
            
            result = self.api.transfers.enqueue(clean_username, [file_dict])
            
            # Se enqueue retorna True, precisamos encontrar o download na fila
            if result:
                # Gerar um ID único baseado no username e filename para monitoramento
                download_id = f"{clean_username}:{clean_filename}"
                return download_id
            else:
                return None
        except Exception as e:
            error_msg = str(e)
            print(f"Erro ao adicionar download: {e}")
            
            # Verificar se é erro de download já em progresso
            if "already in progress" in error_msg.lower():
                print(f"🔄 Download já existe, removendo da fila...")
                # Encontrar e remover o download existente
                queue = self.get_download_queue()
                for user_data in queue:
                    if user_data.get('username') == clean_username:
                        directories = user_data.get('directories', [])
                        for directory in directories:
                            files = directory.get('files', [])
                            for file_info in files:
                                if file_info.get('filename') == clean_filename:
                                    existing_id = file_info.get('id')
                                    if existing_id:
                                        print(f"🗑️ Removendo download existente: {existing_id}")
                                        self.remove_download(existing_id)
                                        return None
            
            # Tentar obter mais detalhes do erro
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Status Code: {e.response.status_code}")
                try:
                    error_text = e.response.text
                    print(f"  Response Body: {error_text}")
                except:
                    print(f"  Response Body: Não foi possível ler")
            
            return None

    def remove_download(self, download_id: str) -> bool:
        """Remove download da fila"""
        try:
            # Se o download_id é nosso formato customizado, encontrar o ID real primeiro
            if ":" in download_id:
                username, filename = download_id.split(":", 1)
                queue = self.get_download_queue()
                
                # Procurar o download na fila para obter o ID real
                for user_data in queue:
                    if user_data.get('username') == username:
                        directories = user_data.get('directories', [])
                        for directory in directories:
                            files = directory.get('files', [])
                            for file_info in files:
                                if file_info.get('filename') == filename:
                                    real_id = file_info.get('id')
                                    if real_id:
                                        self.api.transfers.cancel_download(username=username, id=real_id, remove=True)
                                        return True
                return False
            else:
                # ID real (UUID) - precisamos encontrar o username
                queue = self.get_download_queue()
                for user_data in queue:
                    username = user_data.get('username')
                    directories = user_data.get('directories', [])
                    for directory in directories:
                        files = directory.get('files', [])
                        for file_info in files:
                            if file_info.get('id') == download_id:
                                self.api.transfers.cancel_download(username=username, id=download_id, remove=True)
                                return True
                return False
        except Exception as e:
            print(f"Erro ao remover download: {e}")
            return False

    def get_download_status(self, download_id: str) -> Optional[Dict]:
        """Obtém status de download específico"""
        try:
            # Se o download_id é nosso formato customizado, procurar na fila
            if ":" in download_id:
                username, filename = download_id.split(":", 1)
                queue = self.get_download_queue()
                
                # Procurar o download na fila
                for user_data in queue:
                    if user_data.get('username') == username:
                        directories = user_data.get('directories', [])
                        for directory in directories:
                            files = directory.get('files', [])
                            for file_info in files:
                                if file_info.get('filename') == filename:
                                    return file_info
                return None
            else:
                # Para IDs reais (UUID), procurar na fila por ID
                queue = self.get_download_queue()
                for user_data in queue:
                    directories = user_data.get('directories', [])
                    for directory in directories:
                        files = directory.get('files', [])
                        for file_info in files:
                            if file_info.get('id') == download_id:
                                return file_info
                return None
        except Exception as e:
            print(f"Erro ao obter status: {e}")
            return None

    def is_server_overloaded(self) -> bool:
        """Detecta se servidor está sobrecarregado"""
        return self.consecutive_failures >= self.server_overload_threshold

    def get_connection_stats(self) -> Dict:
        """Estatísticas de conexão"""
        return {
            "host": self.host,
            "port": self.port,
            "consecutive_failures": self.consecutive_failures,
            "is_overloaded": self.is_server_overloaded(),
            "cache_stats": self.cache_manager.get_cache_stats(),
        }
