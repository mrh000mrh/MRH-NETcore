import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from ping3 import ping
import re
import asyncio
import os  # برای خواندن توکن از محیط (امنیت)

# تنظیمات اصلی - توکن و ID ادمین رو از محیط می‌خونه (در Render تنظیم می‌شه)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # ID خودت رو در Render بگذار
BOT_NAME = "MRH-NETcore"
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", None)  # اختیاری

# دیتابیس محلی
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS configs (id INTEGER PRIMARY KEY, config TEXT, location TEXT, protocol TEXT, quality TEXT)')
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استخراج اتوماتیک کانفیگ (هر ساعت یکبار)
async def extract_configs(context: ContextTypes.DEFAULT_TYPE):
    urls = [
        "https://t.me/s/persianvpnhub",
        "https://www.vpngate.net/en/",
        # می‌تونی بعداً از پنل ادمین اضافه کنی
    ]
    configs = []
    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            # استخراج ساده (برای مثال)
            for text in soup.find_all(string=re.compile(r'(vmess|vless|trojan)://')):
                configs.append(text.strip())
        except Exception as e:
            logger.error(e)
    
    # ذخیره و اعمال ریمارک
    for config in configs:
        quality = check_quality(config)
        modified = modify_remark(config)
        cursor.execute('INSERT OR IGNORE INTO configs (config, quality) VALUES (?, ?)', (modified, quality))
    conn.commit()
    logger.info(f"{len(configs)} کانفیگ استخراج شد")

def check_quality(config):
    ip = re.search(r'remote (\S+)', config)
    if ip:
        latency = ping(ip.group(1))
        return 'High' if latency and latency < 200 else 'Low'
    return 'Invalid'

def modify_remark(config):
    return re.sub(r'remark = .*', f'remark = {BOT_NAME}', config)

# منوی اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("دریافت کانفیگ", callback_data='get_config')],
        [InlineKeyboardButton("دریافت پروکسی", callback_data='get_proxy')],
        [InlineKeyboardButton("اهدای کانفیگ", callback_data='donate_config')],
        [InlineKeyboardButton("دانلود کلاینت", callback_data='download_client')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('سلام! به ربات خوش آمدی.', reply_markup=reply_markup)

# هندلر دکمه‌ها (ساده برای شروع)
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == 'get_config':
        await query.message.reply_text("در حال بارگذاری کانفیگ...")
    elif data == 'donate_config':
        await query.message.reply_text("کانفیگت رو بفرست تا چک کنیم!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.job_queue.run_repeating(extract_configs, interval=3600, first=10)
    app.run_polling()

if __name__ == '__main__':
    main()
