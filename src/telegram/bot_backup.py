#!/usr/bin/env python3

import os
import sys
import re
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
    print("✅ python-telegram-bot disponível")
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("❌ python-telegram-bot não encontrado")
    print("💡 Instale com: pip install python-telegram-bot")
    sys.exit(1)

# Importa funções do script principal
try:
    from slskd_mp3_search import (
        connectToSlskd, 
        smart_mp3_search,
        smart_album_search,
        setup_spotify_client, 
        setup_spotify_user_client,
        extract_playlist_id, 
        get_playlist_tracks_with_uris,
        download_playlist_tracks_with_removal,
        download_playlist_tracks,
        show_download_history,
        clear_download_history
    )
except ImportError:
    # Se não conseguir importar como módulo, importa como script
    import sys
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("slskd_mp3_search", "slskd-mp3-search.py")
    slskd_module = importlib.util.module_from_spec(spec)
    sys.modules["slskd_mp3_search"] = slskd_module
    spec.loader.exec_module(slskd_module)
    
    # Importa as funções necessárias
    connectToSlskd = slskd_module.connectToSlskd
    smart_mp3_search = slskd_module.smart_mp3_search
    smart_album_search = slskd_module.smart_album_search
    setup_spotify_client = slskd_module.setup_spotify_client
    setup_spotify_user_client = slskd_module.setup_spotify_user_client
    extract_playlist_id = slskd_module.extract_playlist_id
    get_playlist_tracks_with_uris = slskd_module.get_playlist_tracks_with_uris
    download_playlist_tracks_with_removal = slskd_module.download_playlist_tracks_with_removal
    download_playlist_tracks = slskd_module.download_playlist_tracks
    show_download_history = slskd_module.show_download_history
    clear_download_history = slskd_module.clear_download_history

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Reduz logs verbosos do httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

class TelegramMusicBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = self._get_allowed_users()
        self.allowed_groups = self._get_allowed_groups()
        self.allowed_threads = self._get_allowed_threads()
        self.slskd = None
        self.spotify_client = None
        self.spotify_user_client = None
        
        # Sistema de controle de tarefas ativas
        self.active_tasks = {}  # {task_id: {'task': asyncio.Task, 'type': str, 'user_id': int, 'chat_id': int}}
        self.task_counter = 0
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN não encontrado no .env")
        
        # Conecta aos serviços
        self._connect_services()
    
    def _get_allowed_users(self):
        """Obtém lista de usuários autorizados"""
        users_str = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        if users_str:
            return [int(user_id.strip()) for user_id in users_str.split(',') if user_id.strip()]
        return []
    
    def _get_allowed_groups(self):
        """Obtém lista de grupos autorizados"""
        groups_str = os.getenv('TELEGRAM_ALLOWED_GROUPS', '')
        if groups_str:
            return [int(group_id.strip()) for group_id in groups_str.split(',') if group_id.strip()]
        return []
    
    def _get_allowed_threads(self):
        """Obtém dicionário de threads permitidas por grupo"""
        threads_str = os.getenv('TELEGRAM_ALLOWED_THREADS', '')
        threads_dict = {}
        
        if threads_str:
            # Formato: group_id:thread_id,group_id:thread_id
            for thread_config in threads_str.split(','):
                if ':' in thread_config:
                    try:
                        group_id, thread_id = thread_config.strip().split(':', 1)
                        group_id = int(group_id)
                        thread_id = int(thread_id)
                        
                        if group_id not in threads_dict:
                            threads_dict[group_id] = []
                        threads_dict[group_id].append(thread_id)
                    except ValueError:
                        logger.warning(f"Formato inválido para thread: {thread_config}")
        
        return threads_dict
    
    def _connect_services(self):
        """Conecta aos serviços externos"""
        try:
            self.slskd = connectToSlskd()
            if self.slskd:
                logger.info("✅ Conectado ao slskd")
            else:
                logger.error("❌ Falha ao conectar ao slskd")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao slskd: {e}")
        
        try:
            self.spotify_client = setup_spotify_client()
            if self.spotify_client:
                logger.info("✅ Cliente Spotify configurado")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Spotify: {e}")
    
    def _create_task_id(self) -> str:
        """Cria um ID único para a tarefa"""
        self.task_counter += 1
        return f"task_{self.task_counter}"
    
    def _register_task(self, task: asyncio.Task, task_type: str, user_id: int, chat_id: int) -> str:
        """Registra uma tarefa ativa"""
        task_id = self._create_task_id()
        self.active_tasks[task_id] = {
            'task': task,
            'type': task_type,
            'user_id': user_id,
            'chat_id': chat_id,
            'created_at': datetime.now()
        }
        logger.info(f"Tarefa registrada: {task_id} ({task_type}) para usuário {user_id}")
        return task_id
    
    def _unregister_task(self, task_id: str):
        """Remove uma tarefa do registro"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            logger.info(f"Tarefa removida: {task_id}")
    
    def _cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa específica"""
        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            task = task_info['task']
            
            if not task.done():
                task.cancel()
                logger.info(f"Tarefa cancelada: {task_id} ({task_info['type']})")
                self._unregister_task(task_id)
                return True
            else:
                self._unregister_task(task_id)
                return False
        return False
    
    def _get_user_tasks(self, user_id: int, chat_id: int) -> list:
        """Obtém tarefas ativas de um usuário em um chat específico"""
        user_tasks = []
        for task_id, task_info in self.active_tasks.items():
            if task_info['user_id'] == user_id and task_info['chat_id'] == chat_id:
                if not task_info['task'].done():
                    user_tasks.append((task_id, task_info))
                else:
                    # Remove tarefas concluídas automaticamente
                    self._unregister_task(task_id)
        return user_tasks
    
    def _create_cancel_keyboard(self, task_id: str) -> InlineKeyboardMarkup:
        """Cria teclado inline com botão de cancelar"""
        keyboard = [
            [InlineKeyboardButton("🛑 Cancelar Busca", callback_data=f"cancel_{task_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _is_authorized(self, update: Update) -> bool:
        """Verifica se usuário/grupo/thread está autorizado"""
        user_id = update.effective_user.id
        chat = update.effective_chat
        
        # Log para debug
        logger.info(f"Verificando autorização - User: {user_id}, Chat: {chat.id}, Type: {chat.type}")
        
        # Se é chat privado, verifica usuários permitidos
        if chat.type == 'private':
            if not self.allowed_users:
                return True  # Se não há lista, permite todos em privado
            return user_id in self.allowed_users
        
        # Se é grupo/supergrupo
        elif chat.type in ['group', 'supergroup']:
            # Verifica se o grupo está na lista de grupos permitidos
            if self.allowed_groups and chat.id not in self.allowed_groups:
                logger.info(f"Grupo {chat.id} não está na lista de grupos permitidos")
                return False
            
            # Se há configuração de threads específicas para este grupo
            if chat.id in self.allowed_threads:
                message_thread_id = getattr(update.message, 'message_thread_id', None)
                
                # Log para debug
                logger.info(f"Thread ID da mensagem: {message_thread_id}")
                logger.info(f"Threads permitidas para grupo {chat.id}: {self.allowed_threads[chat.id]}")
                
                # Se a mensagem não tem thread_id (mensagem no grupo principal)
                if message_thread_id is None:
                    logger.info("Mensagem no grupo principal - negando acesso")
                    return False
                
                # Verifica se a thread está permitida
                if message_thread_id not in self.allowed_threads[chat.id]:
                    logger.info(f"Thread {message_thread_id} não está permitida")
                    return False
                
                logger.info(f"Thread {message_thread_id} está permitida")
                return True
            
            # Se não há configuração específica de threads, permite o grupo todo
            elif self.allowed_groups and chat.id in self.allowed_groups:
                return True
            
            # Se não há configuração de grupos, nega acesso
            logger.info("Grupo não configurado - negando acesso")
            return False
        
        # Outros tipos de chat não são suportados
        logger.info(f"Tipo de chat não suportado: {chat.type}")
        return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Você não tem permissão para usar este bot neste local.")
            return
        
        welcome_text = """
🎵 **SLSKD Music Bot**

Bem-vindo! Este bot permite buscar e baixar músicas usando slskd e Spotify.

**Comandos disponíveis:**
/help - Mostra ajuda completa
/search <termo> - Busca uma música
/album <artista - álbum> - Busca álbum completo
/spotify <url> - Baixa playlist do Spotify
/tasks - Ver e cancelar tarefas ativas
/history - Mostra histórico de downloads
/status - Status dos serviços

**Exemplos:**
`/search Radiohead - Creep`
`/album Pink Floyd - The Dark Side of the Moon`
`/spotify https://open.spotify.com/playlist/...`

🛑 **Novo:** Todas as buscas agora podem ser canceladas! Use os botões que aparecem ou `/tasks` para gerenciar.

💡 Use `/help` para ver todos os comandos e opções disponíveis.
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        if not self._is_authorized(update):
            return
        
        help_text = """
🎵 **Comandos do Bot**

**Busca de Música:**
`/search <termo>` - Busca específica
Exemplo: `/search Linkin Park - In the End`

**Busca de Álbum:**
`/album <artista - álbum>` - Busca álbum completo
🆕 **Novo:** Mostra os 5 melhores álbuns encontrados para você escolher!
Exemplo: `/album Pink Floyd - The Dark Side of the Moon`

**Spotify:**
`/spotify <url>` - Baixa playlist
`/spotify <url> limit=10` - Limita downloads
`/spotify <url> remove=yes` - Remove da playlist

**Histórico:**
`/history` - Ver downloads
`/clear_history` - Limpar histórico

**Controle de Tarefas:**
`/tasks` - Ver tarefas ativas e cancelar

**Sistema:**
`/status` - Status dos serviços
`/info` - Informações do chat atual
`/help` - Esta ajuda

**Exemplos completos:**
`/search Radiohead - Creep`
`/album Beatles - Abbey Road`
`/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
`/spotify https://spotify.com/playlist/ID limit=5 remove=yes`

💡 **Cancelamento:** Todas as buscas e downloads mostram um botão 🛑 para cancelar. Use `/tasks` para ver todas as tarefas ativas.

🆕 **Seleção de Álbuns:** Ao buscar álbuns, você verá uma lista com os melhores matches encontrados, incluindo número de faixas, qualidade e tamanho. Clique no botão do álbum desejado para iniciar o download!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        if not self._is_authorized(update):
            return
        
        status_text = "🔍 **Status dos Serviços**\n\n"
        
        # Status slskd
        if self.slskd:
            status_text += "✅ SLSKD: Conectado\n"
        else:
            status_text += "❌ SLSKD: Desconectado\n"
        
        # Status Spotify
        if self.spotify_client:
            status_text += "✅ Spotify: Configurado\n"
        else:
            status_text += "❌ Spotify: Não configurado\n"
        
        # Informações do sistema
        status_text += f"\n📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /search"""
        if not self._is_authorized(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /search <termo de busca>")
            return
        
        search_term = ' '.join(context.args)
        await self._handle_music_search(update, search_term)
    
    async def album_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /album"""
        if not self._is_authorized(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /album <artista - álbum>\n\nExemplos:\n• `/album Pink Floyd - The Dark Side of the Moon`\n• `/album Beatles - Abbey Road`\n• `/album Nirvana - Nevermind`", parse_mode='Markdown')
            return
        
        album_query = ' '.join(context.args)
        await self._handle_album_search(update, album_query)
    
    async def spotify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /spotify"""
        if not self._is_authorized(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /spotify <url> [opções]\n\nExemplo: `/spotify https://open.spotify.com/playlist/ID`", parse_mode='Markdown')
            return
        
        playlist_url = context.args[0]
        
        # Processa opções
        options = {}
        for arg in context.args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                options[key.lower()] = value.lower()
        
        await self._handle_playlist_download(update, playlist_url, options)
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /history"""
        if not self._is_authorized(update):
            return
        
        try:
            # Captura saída do histórico
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                show_download_history()
            
            history_output = f.getvalue()
            
            if history_output.strip():
                # Limita o tamanho da mensagem
                if len(history_output) > 4000:
                    history_output = history_output[:4000] + "\n... (truncado)"
                
                await update.message.reply_text(f"```\n{history_output}\n```", parse_mode='Markdown')
            else:
                await update.message.reply_text("📝 Histórico vazio")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao obter histórico: {e}")
    
    async def clear_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /clear_history"""
        if not self._is_authorized(update):
            return
        
        # Botões de confirmação
        keyboard = [
            [
                InlineKeyboardButton("✅ Sim, limpar", callback_data="clear_history_yes"),
                InlineKeyboardButton("❌ Cancelar", callback_data="clear_history_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🗑️ Tem certeza que deseja limpar todo o histórico?",
            reply_markup=reply_markup
        )
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /info - mostra informações do chat atual"""
        chat = update.effective_chat
        user = update.effective_user
        message = update.message
        
        info_text = "📋 **Informações do Chat**\n\n"
        info_text += f"👤 **Usuário:**\n"
        info_text += f"• ID: `{user.id}`\n"
        info_text += f"• Nome: {user.first_name}"
        if user.last_name:
            info_text += f" {user.last_name}"
        if user.username:
            info_text += f" (@{user.username})"
        info_text += "\n\n"
        
        info_text += f"💬 **Chat:**\n"
        info_text += f"• ID: `{chat.id}`\n"
        info_text += f"• Tipo: {chat.type}\n"
        if chat.title:
            info_text += f"• Título: {chat.title}\n"
        
        # Informações de thread (se aplicável)
        thread_id = getattr(message, 'message_thread_id', None)
        if thread_id:
            info_text += f"• Thread ID: `{thread_id}`\n"
            info_text += f"• Configuração para .env: `{chat.id}:{thread_id}`\n"
        else:
            info_text += f"• Thread: Mensagem no grupo principal\n"
        
        info_text += "\n🔧 **Para configurar acesso:**\n"
        
        if chat.type == 'private':
            info_text += f"Adicione ao .env:\n`TELEGRAM_ALLOWED_USERS={user.id}`"
        elif chat.type in ['group', 'supergroup']:
            info_text += f"Para permitir todo o grupo:\n`TELEGRAM_ALLOWED_GROUPS={chat.id}`\n\n"
            if thread_id:
                info_text += f"Para permitir apenas esta thread:\n"
                info_text += f"`TELEGRAM_ALLOWED_GROUPS={chat.id}`\n"
                info_text += f"`TELEGRAM_ALLOWED_THREADS={chat.id}:{thread_id}`"
            else:
                info_text += f"Para permitir apenas uma thread específica:\n"
                info_text += f"`TELEGRAM_ALLOWED_GROUPS={chat.id}`\n"
                info_text += f"`TELEGRAM_ALLOWED_THREADS={chat.id}:THREAD_ID`\n"
                info_text += f"(substitua THREAD_ID pelo ID da thread desejada)"
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /tasks - mostra tarefas ativas do usuário"""
        if not self._is_authorized(update):
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        user_tasks = self._get_user_tasks(user_id, chat_id)
        
        if not user_tasks:
            await update.message.reply_text("📝 Nenhuma tarefa ativa no momento")
            return
        
        tasks_text = "🔄 **Tarefas Ativas:**\n\n"
        keyboard = []
        
        for task_id, task_info in user_tasks:
            task_type = task_info['type']
            created_at = task_info['created_at'].strftime('%H:%M:%S')
            
            tasks_text += f"• **{task_type}** (ID: `{task_id}`)\n"
            tasks_text += f"  Iniciada às {created_at}\n\n"
            
            # Adiciona botão de cancelar para cada tarefa
            keyboard.append([
                InlineKeyboardButton(f"🛑 Cancelar {task_type}", callback_data=f"cancel_{task_id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(tasks_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula botões inline"""
        query = update.callback_query
        await query.answer()
        
        if not self._is_authorized(update):
            return
        
        if query.data == "clear_history_yes":
            try:
                clear_download_history()
                await query.edit_message_text("🗑️ Histórico limpo com sucesso!")
            except Exception as e:
                await query.edit_message_text(f"❌ Erro ao limpar histórico: {e}")
        
        elif query.data == "clear_history_no":
            await query.edit_message_text("❌ Operação cancelada")
        
        elif query.data == "album_cancel":
            await query.edit_message_text("❌ Seleção de álbum cancelada")
        
        elif query.data.startswith("album_"):
            # Processa seleção de álbum
            await self._handle_album_selection(query)
        
        elif query.data.startswith("cancel_"):
            # Extrai o task_id do callback data
            task_id = query.data[7:]  # Remove "cancel_" prefix
            
            # Verifica se a tarefa pertence ao usuário
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                
                # Verifica se o usuário tem permissão para cancelar esta tarefa
                if task_info['user_id'] == user_id and task_info['chat_id'] == chat_id:
                    if self._cancel_task(task_id):
                        await query.edit_message_text(f"🛑 Tarefa cancelada: {task_info['type']}")
                    else:
                        await query.edit_message_text("❌ Tarefa já foi concluída ou não pôde ser cancelada")
                else:
                    await query.edit_message_text("❌ Você não tem permissão para cancelar esta tarefa")
            else:
                await query.edit_message_text("❌ Tarefa não encontrada ou já foi concluída")
    
    async def _handle_album_selection(self, query):
        """Manipula seleção de álbum pelo usuário"""
        try:
            # Parse do callback data: album_{index}_{query_hash}
            parts = query.data.split('_')
            if len(parts) != 3:
                await query.edit_message_text("❌ Dados inválidos")
                return
            
            album_index = int(parts[1])
            query_hash = int(parts[2])
            
            # Recupera candidatos do cache
            if not hasattr(self, '_album_candidates_cache') or query_hash not in self._album_candidates_cache:
                await query.edit_message_text("❌ Dados expirados. Faça uma nova busca.")
                return
            
            cache_data = self._album_candidates_cache[query_hash]
            candidates = cache_data['candidates']
            original_query = cache_data['original_query']
            
            if album_index >= len(candidates):
                await query.edit_message_text("❌ Álbum inválido")
                return
            
            selected_album = candidates[album_index]
            
            # Inicia download do álbum selecionado
            await self._start_album_download(query, selected_album, original_query)
            
            # Remove do cache após uso
            del self._album_candidates_cache[query_hash]
            
        except (ValueError, IndexError) as e:
            await query.edit_message_text(f"❌ Erro ao processar seleção: {e}")
        except Exception as e:
            await query.edit_message_text(f"❌ Erro inesperado: {e}")
    
    async def _start_album_download(self, query, album_info: dict, original_query: str):
        """Inicia o download do álbum selecionado"""
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        album_name = self._extract_album_name_from_metadata(album_info)
        clean_album_name = self._escape_markdown(album_name)
        clean_username = self._escape_markdown(album_info['username'])
        
        # Cria tarefa para o download
        task = asyncio.create_task(self._execute_album_download(album_info, original_query))
        task_id = self._register_task(task, f"Download de Álbum", user_id, chat_id)
        
        # Atualiza mensagem com informações do download (sem formatação markdown)
        cancel_keyboard = self._create_cancel_keyboard(task_id)
        
        download_text = f"💿 Baixando Álbum Selecionado\n\n"
        download_text += f"📀 {clean_album_name}\n"
        download_text += f"👤 Usuário: {clean_username}\n"
        download_text += f"🎵 Faixas: {album_info['track_count']}\n"
        download_text += f"🎧 Bitrate médio: {album_info['avg_bitrate']:.0f} kbps\n"
        download_text += f"💾 Tamanho: {album_info['total_size'] / 1024 / 1024:.1f} MB\n\n"
        download_text += f"⏳ Iniciando downloads...\n"
        download_text += f"💡 Use o botão abaixo para cancelar se necessário"
        
        try:
            await query.edit_message_text(download_text, reply_markup=cancel_keyboard)
        except Exception as e:
            logger.error(f"Erro ao atualizar mensagem de download: {e}")
            # Fallback simples
            await query.edit_message_text(f"💿 Baixando: {clean_album_name}", reply_markup=cancel_keyboard)
        
        try:
            # Aguarda conclusão do download
            result = await task
            
            if result['success']:
                final_text = f"✅ Álbum baixado com sucesso!\n\n"
                final_text += f"📀 {clean_album_name}\n"
                final_text += f"✅ Downloads iniciados: {result['successful']}\n"
                final_text += f"❌ Falhas: {result['failed']}\n\n"
                final_text += f"💡 Monitore o progresso na interface web do slskd"
                
                await query.edit_message_text(final_text)
            else:
                error_msg = f"❌ Falha no download do álbum: {result.get('error', 'Erro desconhecido')}"
                await query.edit_message_text(error_msg)
                
        except asyncio.CancelledError:
            cancel_msg = f"🛑 Download do álbum cancelado: {clean_album_name}"
            await query.edit_message_text(cancel_msg)
        except Exception as e:
            error_msg = f"❌ Erro durante download: {str(e)}"
            await query.edit_message_text(error_msg)
        finally:
            self._unregister_task(task_id)
    
    async def _execute_album_download(self, album_info: dict, search_term: str) -> dict:
        """Executa o download do álbum de forma assíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_album_tracks, album_info, search_term)
    
    def _download_album_tracks(self, album_info: dict, search_term: str) -> dict:
        """Baixa todas as faixas de um álbum"""
        from slskd_mp3_search import download_mp3
        import time
        import os
        
        username = album_info['username']
        files = album_info['files']
        
        print(f"\n📥 Iniciando download de {len(files)} faixas do álbum...")
        
        successful_downloads = 0
        failed_downloads = 0
        
        try:
            for i, file_info in enumerate(files, 1):
                filename = file_info.get('filename', '')
                file_size = file_info.get('size', 0)
                
                print(f"\n📍 [{i}/{len(files)}] {os.path.basename(filename)}")
                print(f"   💾 Tamanho: {file_size / 1024 / 1024:.2f} MB")
                print(f"   🎧 Bitrate: {file_info.get('bitRate', 0)} kbps")
                
                # Tenta fazer o download
                success = download_mp3(self.slskd, username, filename, file_size, f"{search_term} - {os.path.basename(filename)}")
                
                if success:
                    successful_downloads += 1
                    print(f"   ✅ Download iniciado com sucesso")
                else:
                    failed_downloads += 1
                    print(f"   ❌ Falha no download")
                
                # Pausa entre downloads
                if i < len(files):
                    time.sleep(1)
            
            return {
                'success': True,
                'successful': successful_downloads,
                'failed': failed_downloads
            }
            
        except Exception as e:
            print(f"❌ Erro durante download do álbum: {e}")
            return {
                'success': False,
                'error': str(e),
                'successful': successful_downloads,
                'failed': failed_downloads
            }
    
    async def _handle_music_search(self, update: Update, search_term: str):
        """Manipula busca de música"""
        if not self.slskd:
            await update.message.reply_text("❌ SLSKD não está conectado")
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Cria tarefa para a busca
        task = asyncio.create_task(self._execute_music_search(search_term))
        task_id = self._register_task(task, "Busca de Música", user_id, chat_id)
        
        # Mensagem de progresso com botão de cancelar
        cancel_keyboard = self._create_cancel_keyboard(task_id)
        progress_msg = await update.message.reply_text(
            f"🔍 Buscando: {search_term}\n💡 Use o botão abaixo para cancelar se necessário",
            reply_markup=cancel_keyboard
        )
        
        try:
            # Aguarda resultado da busca
            success = await task
            
            if success:
                await progress_msg.edit_text(f"✅ Busca concluída: {search_term}\n💡 Download em andamento no slskd")
            else:
                await progress_msg.edit_text(f"❌ Nenhum resultado encontrado para: {search_term}")
                
        except asyncio.CancelledError:
            await progress_msg.edit_text(f"🛑 Busca cancelada: {search_term}")
        except Exception as e:
            await progress_msg.edit_text(f"❌ Erro na busca: {e}")
        finally:
            # Remove tarefa do registro
            self._unregister_task(task_id)
    
    async def _execute_music_search(self, search_term: str) -> bool:
        """Executa a busca de música de forma assíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, smart_mp3_search, self.slskd, search_term)
    
    async def _handle_album_search(self, update: Update, album_query: str):
        """Manipula busca de álbum com seleção de candidatos"""
        if not self.slskd:
            await update.message.reply_text("❌ SLSKD não está conectado")
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Cria tarefa para a busca de álbum
        task = asyncio.create_task(self._execute_album_search_candidates(album_query))
        task_id = self._register_task(task, "Busca de Álbum", user_id, chat_id)
        
        # Mensagem de progresso com botão de cancelar
        cancel_keyboard = self._create_cancel_keyboard(task_id)
        progress_msg = await update.message.reply_text(
            f"💿 Buscando álbum: {album_query}\n💡 Use o botão abaixo para cancelar se necessário",
            reply_markup=cancel_keyboard
        )
        
        try:
            # Aguarda resultado da busca
            album_candidates = await task
            
            if album_candidates:
                # Mostra os 5 melhores candidatos com botões
                await self._show_album_candidates(progress_msg, album_candidates, album_query)
            else:
                await progress_msg.edit_text(f"❌ Nenhum álbum encontrado para: {album_query}\n💡 Tente:\n• Verificar a grafia\n• Usar formato 'Artista - Álbum'\n• Buscar por música individual com /search")
                
        except asyncio.CancelledError:
            await progress_msg.edit_text(f"🛑 Busca de álbum cancelada: {album_query}")
        except Exception as e:
            await progress_msg.edit_text(f"❌ Erro na busca de álbum: {e}")
        finally:
            # Remove tarefa do registro
            self._unregister_task(task_id)
    
    async def _execute_album_search_candidates(self, album_query: str) -> list:
        """Executa a busca de álbum e retorna candidatos sem fazer download"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_album_candidates, album_query)
    
    def _search_album_candidates(self, album_query: str) -> list:
        """Busca candidatos de álbum sem fazer download automático"""
        from slskd_mp3_search import (
            is_duplicate_download, extract_artist_and_album, 
            create_album_search_variations, wait_for_search_completion,
            find_album_candidates
        )
        import os
        
        print(f"💿 Busca inteligente por ÁLBUM: '{album_query}'")
        
        # Verifica se já foi baixado anteriormente
        if is_duplicate_download(album_query):
            print(f"⏭️ Pulando busca - álbum já baixado anteriormente")
            return []
        
        artist, album = extract_artist_and_album(album_query)
        if artist and album:
            print(f"🎤 Artista: '{artist}' | 💿 Álbum: '{album}'")
        
        variations = create_album_search_variations(album_query)
        print(f"📝 {len(variations)} variações criadas para álbum")
        
        all_candidates = []
        
        for i, search_term in enumerate(variations, 1):
            print(f"\n📍 Tentativa {i}/{len(variations)}: '{search_term}'")
            
            try:
                print(f"🔍 Buscando álbum: '{search_term}'")
                
                search_result = self.slskd.searches.search_text(search_term)
                search_id = search_result.get('id')
                
                # Aguarda a busca finalizar
                search_responses = wait_for_search_completion(self.slskd, search_id, max_wait=int(os.getenv('SEARCH_WAIT_TIME', 25)))
                
                if not search_responses:
                    print("❌ Nenhuma resposta")
                    continue
                
                # Conta total de arquivos encontrados
                total_files = sum(len(response.get('files', [])) for response in search_responses)
                print(f"📊 Total de arquivos encontrados: {total_files}")
                
                if total_files > 0:
                    # Para álbuns, procura por múltiplos arquivos do mesmo usuário/diretório
                    album_candidates = find_album_candidates(search_responses, album_query)
                    
                    if album_candidates:
                        print(f"💿 Encontrados {len(album_candidates)} candidatos a álbum")
                        all_candidates.extend(album_candidates)
                        
                        # Se encontrou bons candidatos, para a busca
                        if len(all_candidates) >= 5:
                            break
            
            except Exception as e:
                print(f"❌ Erro na busca: {e}")
        
        # Remove duplicatas e ordena por qualidade
        unique_candidates = {}
        for candidate in all_candidates:
            key = f"{candidate['username']}:{candidate['directory']}"
            if key not in unique_candidates or candidate['track_count'] > unique_candidates[key]['track_count']:
                unique_candidates[key] = candidate
        
        final_candidates = list(unique_candidates.values())
        final_candidates.sort(key=lambda x: (x['track_count'], x['avg_bitrate']), reverse=True)
        
        # Retorna os 5 melhores
        return final_candidates[:5]
    
    def _escape_markdown(self, text: str) -> str:
        """Escapa caracteres especiais do Markdown para evitar erros de parsing"""
        if not text:
            return ""
        
        # Remove ou substitui caracteres problemáticos
        # Em vez de escapar, vamos limpar o texto
        cleaned_text = text
        
        # Remove caracteres que podem causar problemas
        problematic_chars = ['*', '_', '[', ']', '`', '\\']
        for char in problematic_chars:
            cleaned_text = cleaned_text.replace(char, '')
        
        # Substitui outros caracteres problemáticos
        cleaned_text = cleaned_text.replace('(', '\\(')
        cleaned_text = cleaned_text.replace(')', '\\)')
        
        return cleaned_text
    
    def _safe_format_text(self, text: str, use_markdown: bool = True) -> str:
        """Formata texto de forma segura para o Telegram"""
        if not use_markdown:
            return text
        
        # Remove formatação markdown existente e aplica escape
        clean_text = text.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
        return clean_text
    
    async def _show_album_candidates(self, message, candidates: list, original_query: str):
        """Mostra candidatos de álbum com botões para seleção"""
        if not candidates:
            await message.edit_text("❌ Nenhum álbum encontrado")
            return
        
        # Texto com informações dos álbuns (sem formatação markdown para evitar erros)
        text = f"💿 Álbuns encontrados para: {original_query}\n\n"
        text += "📋 Selecione um álbum para baixar:\n\n"
        
        # Botões para cada álbum
        keyboard = []
        
        for i, candidate in enumerate(candidates, 1):
            # Informações do álbum no texto usando metadados
            album_name = self._extract_album_name_from_metadata(candidate)
            username = candidate['username']
            
            # Limpa caracteres problemáticos
            clean_album_name = self._escape_markdown(album_name)
            clean_username = self._escape_markdown(username)
            
            text += f"{i}. {clean_album_name}\n"
            text += f"   👤 {clean_username}\n"
            text += f"   🎵 {candidate['track_count']} faixas\n"
            text += f"   🎧 {candidate['avg_bitrate']:.0f} kbps\n"
            text += f"   💾 {candidate['total_size'] / 1024 / 1024:.1f} MB\n\n"
            
            # Botão para este álbum (também limpa o texto do botão)
            button_album_name = album_name.replace('[', '').replace(']', '').replace('*', '').replace('_', '')
            button_text = f"💿 {i}. {button_album_name} ({candidate['track_count']} faixas)"
            
            # Limita tamanho do botão
            if len(button_text) > 64:  # Limite do Telegram
                short_name = button_album_name[:35] + "..."
                button_text = f"💿 {i}. {short_name} ({candidate['track_count']} faixas)"
            
            # Dados do callback incluem índice e query original
            callback_data = f"album_{i-1}_{hash(original_query) % 10000}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Botão de cancelar
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="album_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Armazena candidatos temporariamente para uso nos callbacks
        query_hash = hash(original_query) % 10000
        if not hasattr(self, '_album_candidates_cache'):
            self._album_candidates_cache = {}
        self._album_candidates_cache[query_hash] = {
            'candidates': candidates,
            'original_query': original_query,
            'timestamp': datetime.now()
        }
        
        # Envia mensagem sem formatação markdown para evitar erros
        try:
            await message.edit_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Erro ao exibir candidatos: {e}")
            # Fallback ainda mais simples
            simple_text = f"💿 Encontrados {len(candidates)} álbuns para: {original_query}\n\nUse os botões abaixo para selecionar:"
            try:
                await message.edit_text(simple_text, reply_markup=reply_markup)
            except Exception as e2:
                logger.error(f"Erro mesmo com texto simples: {e2}")
                await message.edit_text("❌ Erro ao exibir resultados. Tente novamente.")
    
    def _extract_album_name_from_path(self, directory_path: str) -> str:
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
    
    def _extract_album_name_from_metadata(self, candidate: dict) -> str:
        """Extrai nome do álbum usando o módulo especializado"""
        try:
            from album_name_extractor import get_album_name
            return get_album_name(candidate)
        except ImportError:
            # Fallback para método básico se módulo não disponível
            return self._extract_album_name_from_path(candidate['directory'])
    
    async def _handle_playlist_download(self, update: Update, playlist_url: str, options: dict):
        """Manipula download de playlist"""
        if not self.spotify_client:
            await update.message.reply_text("❌ Spotify não está configurado")
            return
        
        if not self.slskd:
            await update.message.reply_text("❌ SLSKD não está conectado")
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Mensagem de progresso inicial
        progress_msg = await update.message.reply_text(f"🎵 Processando playlist...")
        
        try:
            # Extrai ID da playlist
            playlist_id = extract_playlist_id(playlist_url)
            if not playlist_id:
                await progress_msg.edit_text("❌ URL de playlist inválida")
                return
            
            # Processa opções
            max_tracks = None
            remove_from_playlist = False
            
            if 'limit' in options:
                try:
                    max_tracks = int(options['limit'])
                except ValueError:
                    pass
            
            if options.get('remove') in ['yes', 'true', '1']:
                remove_from_playlist = True
                # Configura cliente com autenticação de usuário
                if not self.spotify_user_client:
                    self.spotify_user_client = setup_spotify_user_client()
                
                if not self.spotify_user_client:
                    await progress_msg.edit_text("❌ Não foi possível autenticar para modificar playlist")
                    return
            
            # Obtém faixas da playlist
            if remove_from_playlist:
                tracks, playlist_name = get_playlist_tracks_with_uris(self.spotify_client, playlist_id)
            else:
                from slskd_mp3_search import get_playlist_tracks
                tracks, playlist_name = get_playlist_tracks(self.spotify_client, playlist_id)
            
            if not tracks:
                await progress_msg.edit_text("❌ Nenhuma faixa encontrada na playlist")
                return
            
            # Atualiza mensagem com informações da playlist
            total_tracks = len(tracks)
            if max_tracks:
                tracks = tracks[:max_tracks]
            
            # Cria tarefa para o download da playlist
            task = asyncio.create_task(self._download_playlist_background(
                progress_msg, tracks, playlist_name, playlist_id, 
                remove_from_playlist, max_tracks
            ))
            task_id = self._register_task(task, "Download de Playlist", user_id, chat_id)
            
            # Atualiza mensagem com botão de cancelar
            cancel_keyboard = self._create_cancel_keyboard(task_id)
            info_text = f"🎵 **{playlist_name}**\n"
            info_text += f"📊 {len(tracks)} faixas"
            if max_tracks and total_tracks > max_tracks:
                info_text += f" (de {total_tracks} total)"
            if remove_from_playlist:
                info_text += f"\n🗑️ Faixas encontradas serão removidas da playlist"
            info_text += f"\n\n⏳ Iniciando downloads...\n💡 Use o botão abaixo para cancelar se necessário"
            
            await progress_msg.edit_text(info_text, parse_mode='Markdown', reply_markup=cancel_keyboard)
            
            # Aguarda conclusão da tarefa
            try:
                await task
            except asyncio.CancelledError:
                await progress_msg.edit_text(f"🛑 Download de playlist cancelado: {playlist_name}", parse_mode='Markdown')
            finally:
                self._unregister_task(task_id)
            
        except Exception as e:
            await progress_msg.edit_text(f"❌ Erro ao processar playlist: {e}")
    
    async def _download_playlist_background(self, progress_msg, tracks, playlist_name, 
                                         playlist_id, remove_from_playlist, max_tracks):
        """Executa download da playlist em background"""
        try:
            successful_downloads = 0
            skipped_duplicates = 0
            failed_downloads = 0
            removed_from_playlist_count = 0
            
            for i, track in enumerate(tracks, 1):
                # Verifica se a tarefa foi cancelada
                if asyncio.current_task().cancelled():
                    raise asyncio.CancelledError()
                
                search_term = track['search_term']
                
                # Atualiza progresso
                progress_text = f"🎵 **{playlist_name}**\n"
                progress_text += f"📍 [{i}/{len(tracks)}] {search_term[:50]}...\n"
                progress_text += f"✅ Sucessos: {successful_downloads} | "
                progress_text += f"⏭️ Puladas: {skipped_duplicates} | "
                progress_text += f"❌ Falhas: {failed_downloads}"
                
                if remove_from_playlist:
                    progress_text += f" | 🗑️ Removidas: {removed_from_playlist_count}"
                
                try:
                    await progress_msg.edit_text(progress_text, parse_mode='Markdown')
                except:
                    pass  # Ignora erros de edição (rate limit)
                
                # Verifica duplicatas
                from slskd_mp3_search import is_duplicate_download
                if is_duplicate_download(search_term):
                    skipped_duplicates += 1
                    
                    # Remove da playlist se já foi baixada
                    if remove_from_playlist and self.spotify_user_client:
                        from slskd_mp3_search import remove_track_from_playlist
                        if remove_track_from_playlist(self.spotify_user_client, playlist_id, track['uri']):
                            removed_from_playlist_count += 1
                    continue
                
                # Tenta download de forma assíncrona
                try:
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(None, smart_mp3_search, self.slskd, search_term)
                    
                    if success:
                        successful_downloads += 1
                        
                        # Remove da playlist se bem-sucedido
                        if remove_from_playlist and self.spotify_user_client:
                            from slskd_mp3_search import remove_track_from_playlist
                            if remove_track_from_playlist(self.spotify_user_client, playlist_id, track['uri']):
                                removed_from_playlist_count += 1
                    else:
                        failed_downloads += 1
                        
                except Exception:
                    failed_downloads += 1
                
                # Pausa entre downloads (cancelável)
                try:
                    await asyncio.sleep(2)
                except asyncio.CancelledError:
                    raise
            
            # Relatório final
            final_text = f"🎵 **{playlist_name}** - Concluído!\n\n"
            final_text += f"📊 **Relatório Final:**\n"
            final_text += f"✅ Downloads iniciados: {successful_downloads}\n"
            final_text += f"⏭️ Duplicatas puladas: {skipped_duplicates}\n"
            final_text += f"❌ Falhas: {failed_downloads}\n"
            
            if remove_from_playlist:
                final_text += f"🗑️ Removidas da playlist: {removed_from_playlist_count}\n"
            
            final_text += f"\n💡 Monitore o progresso no slskd web interface"
            
            await progress_msg.edit_text(final_text, parse_mode='Markdown')
            
        except asyncio.CancelledError:
            # Tarefa foi cancelada
            raise
        except Exception as e:
            error_text = f"❌ Erro durante download da playlist: {e}"
            try:
                await progress_msg.edit_text(error_text)
            except:
                pass
            
            # Relatório final
            final_text = f"🎵 **{playlist_name}** - Concluído!\n\n"
            final_text += f"📊 **Relatório Final:**\n"
            final_text += f"✅ Downloads iniciados: {successful_downloads}\n"
            final_text += f"⏭️ Duplicatas puladas: {skipped_duplicates}\n"
            final_text += f"❌ Falhas: {failed_downloads}\n"
            
            if remove_from_playlist:
                final_text += f"🗑️ Removidas da playlist: {removed_from_playlist_count}\n"
            
            final_text += f"\n💡 Monitore o progresso no slskd web interface"
            
            await progress_msg.edit_text(final_text, parse_mode='Markdown')
            
        except Exception as e:
            error_text = f"❌ Erro durante download da playlist: {e}"
            try:
                await progress_msg.edit_text(error_text)
            except:
                pass
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula erros do bot"""
        logger.error(f"Erro no bot: {context.error}")
        
        # Se há um update, tenta responder ao usuário
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Ocorreu um erro interno. Tente novamente em alguns segundos."
                )
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de erro: {e}")
    
    def run(self):
        """Inicia o bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot não está disponível")
            return
        
        logger.info("🤖 Iniciando Telegram Bot...")
        
        # Cria aplicação
        application = Application.builder().token(self.bot_token).build()
        
        # Adiciona handlers de comandos específicos
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("search", self.search_command))
        application.add_handler(CommandHandler("album", self.album_command))
        application.add_handler(CommandHandler("spotify", self.spotify_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("clear_history", self.clear_history_command))
        application.add_handler(CommandHandler("tasks", self.tasks_command))
        application.add_handler(CommandHandler("info", self.info_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Adiciona handler de erro
        application.add_error_handler(self.error_handler)
        
        # NÃO adiciona handler para mensagens de texto - elas serão ignoradas
        
        # Inicia o bot com configurações robustas
        logger.info("✅ Bot iniciado! Pressione Ctrl+C para parar.")
        logger.info("🔇 Mensagens que não sejam comandos serão ignoradas")
        
        try:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=1.0,
                timeout=10
            )
        except Exception as e:
            logger.error(f"Erro durante polling: {e}")
            raise


def main():
    """Função principal"""
    try:
        bot = TelegramMusicBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
