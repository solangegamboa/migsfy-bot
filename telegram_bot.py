#!/usr/bin/env python3

import os
import sys
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
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramMusicBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = self._get_allowed_users()
        self.slskd = None
        self.spotify_client = None
        self.spotify_user_client = None
        
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
    
    def _is_authorized(self, user_id: int) -> bool:
        """Verifica se usuário está autorizado"""
        if not self.allowed_users:
            return True  # Se não há lista, permite todos
        return user_id in self.allowed_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Você não tem permissão para usar este bot.")
            return
        
        welcome_text = """
🎵 **SLSKD Music Bot**

Bem-vindo! Este bot permite buscar e baixar músicas usando slskd e Spotify.

**Comandos disponíveis:**
/help - Mostra esta ajuda
/search <termo> - Busca uma música
/spotify <url> - Baixa playlist do Spotify
/history - Mostra histórico de downloads
/status - Status dos serviços

**Exemplos:**
`/search Radiohead - Creep`
`/spotify https://open.spotify.com/playlist/...`

💡 Use apenas os comandos acima para interagir com o bot.
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        if not self._is_authorized(update.effective_user.id):
            return
        
        help_text = """
🎵 **Comandos do Bot**

**Busca de Música:**
`/search <termo>` - Busca específica
Exemplo: `/search Linkin Park - In the End`

**Spotify:**
`/spotify <url>` - Baixa playlist
`/spotify <url> limit=10` - Limita downloads
`/spotify <url> remove=yes` - Remove da playlist

**Histórico:**
`/history` - Ver downloads
`/clear_history` - Limpar histórico

**Sistema:**
`/status` - Status dos serviços
`/help` - Esta ajuda

**Exemplos completos:**
`/search Radiohead - Creep`
`/spotify https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
`/spotify https://spotify.com/playlist/ID limit=5 remove=yes`
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        if not self._is_authorized(update.effective_user.id):
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
        if not self._is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /search <termo de busca>")
            return
        
        search_term = ' '.join(context.args)
        await self._handle_music_search(update, search_term)
    
    async def spotify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /spotify"""
        if not self._is_authorized(update.effective_user.id):
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
        if not self._is_authorized(update.effective_user.id):
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
        if not self._is_authorized(update.effective_user.id):
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
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula botões inline"""
        query = update.callback_query
        await query.answer()
        
        if not self._is_authorized(query.from_user.id):
            return
        
        if query.data == "clear_history_yes":
            try:
                clear_download_history()
                await query.edit_message_text("🗑️ Histórico limpo com sucesso!")
            except Exception as e:
                await query.edit_message_text(f"❌ Erro ao limpar histórico: {e}")
        
        elif query.data == "clear_history_no":
            await query.edit_message_text("❌ Operação cancelada")
    
    async def _handle_music_search(self, update: Update, search_term: str):
        """Manipula busca de música"""
        if not self.slskd:
            await update.message.reply_text("❌ SLSKD não está conectado")
            return
        
        # Mensagem de progresso
        progress_msg = await update.message.reply_text(f"🔍 Buscando: {search_term}")
        
        try:
            # Executa busca
            success = smart_mp3_search(self.slskd, search_term)
            
            if success:
                await progress_msg.edit_text(f"✅ Busca iniciada: {search_term}\n💡 Download em andamento no slskd")
            else:
                await progress_msg.edit_text(f"❌ Nenhum resultado encontrado para: {search_term}")
                
        except Exception as e:
            await progress_msg.edit_text(f"❌ Erro na busca: {e}")
    
    async def _handle_playlist_download(self, update: Update, playlist_url: str, options: dict):
        """Manipula download de playlist"""
        if not self.spotify_client:
            await update.message.reply_text("❌ Spotify não está configurado")
            return
        
        if not self.slskd:
            await update.message.reply_text("❌ SLSKD não está conectado")
            return
        
        # Mensagem de progresso
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
            
            info_text = f"🎵 **{playlist_name}**\n"
            info_text += f"📊 {len(tracks)} faixas"
            if max_tracks and total_tracks > max_tracks:
                info_text += f" (de {total_tracks} total)"
            if remove_from_playlist:
                info_text += f"\n🗑️ Faixas encontradas serão removidas da playlist"
            info_text += f"\n\n⏳ Iniciando downloads..."
            
            await progress_msg.edit_text(info_text, parse_mode='Markdown')
            
            # Inicia downloads em background
            asyncio.create_task(self._download_playlist_background(
                progress_msg, tracks, playlist_name, playlist_id, 
                remove_from_playlist, max_tracks
            ))
            
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
                
                # Tenta download
                try:
                    success = smart_mp3_search(self.slskd, search_term)
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
                
                # Pausa entre downloads
                await asyncio.sleep(2)
            
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
        application.add_handler(CommandHandler("spotify", self.spotify_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("clear_history", self.clear_history_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # NÃO adiciona handler para mensagens de texto - elas serão ignoradas
        
        # Inicia o bot
        logger.info("✅ Bot iniciado! Pressione Ctrl+C para parar.")
        logger.info("🔇 Mensagens que não sejam comandos serão ignoradas")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


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
