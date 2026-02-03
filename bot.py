import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from ping3 import ping
import re
import asyncio
import os  # برای env vars (امنیت توکن)
import random  # برای CAPTCHA ساده

# ────────────────────────────────────────────────
#                 تنظیمات اصلی (امن – از env vars)
# ────────────────────────────────────────────────

TOKEN = os.getenv("BOT_TOKEN")  
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # ID ادمین اولیه
BOT_NAME = "MRH-NETcore"
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", None)
CHECK_INTERVAL_MINUTES = 60
MAX_DAILY_CONFIGS = 100

# ────────────────────────────────────────────────
#                 دیتابیس
# ────────────────────────────────────────────────

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# جدول کانفیگ‌ها
cursor.execute('CREATE TABLE IF NOT EXISTS configs (id INTEGER PRIMARY KEY, config TEXT, location TEXT, protocol TEXT, quality TEXT)')

# جدول تنظیمات
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')

defaults = {
    "max_daily_configs": str(MAX_DAILY_CONFIGS),
    "enable_donation": "false",  # پیش‌فرض خاموش
    # ... بقیه defaults از قبل
}
for k, v in defaults.items():
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

# جدول ادمین‌ها
cursor.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))

# جدول کانال/گروه‌ها
cursor.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, chat_id TEXT)')

# جدول منابع استخراج
cursor.execute('CREATE TABLE IF NOT EXISTS sources (id INTEGER PRIMARY KEY, url TEXT)')

# منابع اولیه (مخفی از کاربر)
initial_sources = [
    "https://t.me/s/persianvpnhub",
    "https://www.vpngate.net/en/",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/configs.txt",
    "https://github.com/mahdibland/V2RayAggregator/raw/master/configs",
]
for url in initial_sources:
    cursor.execute('INSERT OR IGNORE INTO sources (url) VALUES (?)', (url,))

conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
#                 استخراج اتوماتیک
# ────────────────────────────────────────────────

async def extract_configs(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT url FROM sources')
    urls = [row[0] for row in cursor.fetchall()]

    configs = []
    max_daily = int(get_setting("max_daily_configs"))

    for url in urls:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser') if 'html' in r.headers.get('Content-Type', '') else None
        # استخراج (مثال – برای انواع منابع)
        for link in soup.find_all('a', href=re.compile(r'\.ovpn$|vmess://|vless://')) if soup else []:
            config = requests.get(link['href']).text
            configs.append(config)
        # برای raw GitHub
        if 'raw.githubusercontent.com' in url:
            configs.append(r.text)

    # چک و ذخیره
    for config in configs[:max_daily]:
        quality = check_quality(config)
        if quality != 'Invalid':
            modified = modify_remark(config)
            cursor.execute('INSERT INTO configs (config, quality) VALUES (?, ?)', (modified, quality))
    conn.commit()

# چک کیفیت
def check_quality(config):
    ip = re.search(r'remote (\S+)', config)
    if ip:
        latency = ping(ip.group(1))
        return 'High' if latency < 200 else 'Low'
    return 'Invalid'

# تغییر ریمارک
def modify_remark(config):
    return re.sub(r'remark = .*', f'remark = {BOT_NAME}', config)

# ────────────────────────────────────────────────
#                 منو اصلی
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("دریافت کانفیگ", callback_data='get_config')],
        [InlineKeyboardButton("دریافت پروکسی", callback_data='get_proxy')],
        [InlineKeyboardButton("اهدای کانفیگ", callback_data='donate_config')],
        [InlineKeyboardButton("دانلود کلاینت", callback_data='download_client')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('سلام! به ربات خوش آمدی.', reply_markup=reply_markup)

# ────────────────────────────────────────────────
#                 اجرا
# ────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == '__main__':
    main()
