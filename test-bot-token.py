#!/usr/bin/env python3
"""
Script para testar se o token do bot Telegram está válido
"""

import os
import asyncio
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

async def test_bot_token():
    """Testa se o token do bot está válido"""
    
    try:
        from telegram import Bot
    except ImportError:
        print("❌ python-telegram-bot não encontrado")
        return False
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")
        return False
    
    print(f"🔍 Testando token: {bot_token[:10]}...")
    
    try:
        bot = Bot(token=bot_token)
        
        # Testa chamada básica
        me = await bot.get_me()
        
        print(f"✅ Bot válido!")
        print(f"📛 Nome: {me.first_name}")
        print(f"🆔 Username: @{me.username}")
        print(f"🔢 ID: {me.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar bot: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot_token())
    exit(0 if result else 1)
