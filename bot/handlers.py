"""
هندلرهای دستورات تلگرام
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع - فقط ادمین"""
    user_id = str(update.effective_user.id)
    
    # TODO: چک کردن ادمین
    
    await update.message.reply_text(
        "🔷 <b>MRH-NETcore Admin Panel</b>\n\n"
        "دستورات:\n"
        "/upload - آپلود فایل HTML\n"
        "/stats - آمار\n"
        "/settings - تنظیمات\n"
        "/channels - مدیریت کانال‌ها",
        parse_mode='HTML'
    )

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور آپلود"""
    await update.message.reply_text(
        "📁 لطفاً فایل HTML اکسپورت شده را ارسال کنید:\n"
        "راهنما: Telegram Desktop → کانال → سه نقطه → Export chat history → HTML"
    )
