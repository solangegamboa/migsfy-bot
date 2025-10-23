#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("❌ python-telegram-bot não encontrado")
    print("💡 Instale com: pip install python-telegram-bot")
    sys.exit(1)

# Adiciona src ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from cli.main import process_spotify_playlist
except ImportError:
    print("❌ Não foi possível importar process_spotify_playlist")
    sys.exit(1)

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SpotifyTelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = self._get_allowed_users()
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN não encontrado no .env")
    
    def _get_allowed_users(self):
        users_str = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        if users_str:
            return [int(user_id.strip()) for user_id in users_str.split(',') if user_id.strip()]
        return []
    
    def _is_authorized(self, update: Update) -> bool:
        if not self.allowed_users:
            return True
        return update.effective_user.id in self.allowed_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Não autorizado")
            return
        
        await update.message.reply_text(
            "🎵 **Spotify to TXT Bot**\n\n"
            "Comandos:\n"
            "/spotify <url> - Converte playlist para TXT\n\n"
            "Exemplo:\n"
            "`/spotify https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd`",
            parse_mode='Markdown'
        )
    
    async def spotify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Não autorizado")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ **Uso incorreto**\n\n"
                "Use: `/spotify <url_da_playlist>`\n\n"
                "Exemplo:\n"
                "`/spotify https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd`",
                parse_mode='Markdown'
            )
            return
        
        playlist_url = context.args[0]
        
        # Mensagem de progresso
        progress_msg = await update.message.reply_text(
            "🎵 **Processando playlist...**\n\n"
            "⏳ Convertendo para arquivo TXT\n"
            "_Aguarde..._",
            parse_mode='Markdown'
        )
        
        try:
            # Executa em thread separada
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, process_spotify_playlist, playlist_url)
            
            if success:
                await progress_msg.edit_text(
                    "✅ **Playlist processada com sucesso!**\n\n"
                    "📁 Arquivo TXT criado em `/app/data/playlists/`\n"
                    "🔄 O sistema processará automaticamente em segundo plano\n\n"
                    "💡 As músicas serão buscadas e baixadas individualmente",
                    parse_mode='Markdown'
                )
            else:
                await progress_msg.edit_text(
                    "❌ **Falha ao processar playlist**\n\n"
                    "Verifique se a URL está correta e a playlist é pública",
                    parse_mode='Markdown'
                )
        
        except Exception as e:
            await progress_msg.edit_text(
                f"❌ **Erro:** `{str(e)}`",
                parse_mode='Markdown'
            )
    
    def run(self):
        logger.info("🤖 Iniciando Spotify Telegram Bot...")
        
        application = Application.builder().token(self.bot_token).build()
        
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("spotify", self.spotify_command))
        
        logger.info("✅ Bot iniciado!")
        application.run_polling()

if __name__ == "__main__":
    try:
        bot = SpotifyTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        sys.exit(1)
