#!/usr/bin/env python3
"""
MRH-NETcore Config Bot
ربات اهدای کانفیگ VPN
"""

import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import Config

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """نقطه ورود اصلی"""
    logger.info("Starting MRH-NETcore Bot...")
    
    # ساخت اپلیکیشن
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # اضافه کردن هندلرها (بعداً کامل می‌شود)
    application.add_handler(CommandHandler("start", start_command))
    
    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def start_command(update, context):
    """دستور شروع"""
    await update.message.reply_text("🚀 ربات MRH-NETcore در حال راه‌اندازی است...")

if __name__ == "__main__":
    main()
