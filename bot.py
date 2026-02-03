import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from ping3 import ping
import re
import asyncio
import os
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
#                 تنظیمات اصلی (امن – از env)
# ────────────────────────────────────────────────

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_NAME = "MRH-NETcore"
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", None)
MAX_DAILY_CONFIGS = 100
CHECK_INTERVAL_MINUTES = 60

# Rate limit ساده (۵ درخواست در ۱۰ ثانیه)
RATE_LIMIT = 5
RATE_WINDOW = 10  # ثانیه

# ────────────────────────────────────────────────
#                 دیتابیس
# ────────────────────────────────────────────────

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config TEXT NOT NULL,
        location TEXT,
        protocol TEXT,
        quality TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
""")
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (ADMIN_ID,))

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        type TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        user_id INTEGER,
        timestamp TIMESTAMP
    )
""")

conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# منابع اولیه استخراج (مخفی از کاربر)
INITIAL_SOURCES = [
    "https://t.me/s/persianvpnhub",
    "https://www.vpngate.net/en/",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/configs.txt",
    "https://github.com/mahdibland/V2RayAggregator/raw/master/configs",
]

for url in INITIAL_SOURCES:
    cursor.execute("INSERT OR IGNORE INTO sources (url, type) VALUES (?, ?)", (url, "config"))
conn.commit()

# ────────────────────────────────────────────────
#                 استخراج اتوماتیک
# ────────────────────────────────────────────────

async def extract_configs(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT url FROM sources")
    urls = [row[0] for row in cursor.fetchall()]

    new_configs = []
    max_daily = int(get_setting("max_daily_configs") or MAX_DAILY_CONFIGS)

    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            if "t.me/s" in url:
                soup = BeautifulSoup(r.text, "html.parser")
                texts = soup.find_all("div", class_="tgme_widget_message_text")
                for t in texts:
                    links = re.findall(r"(vmess|vless|trojan)://[^\s<>\"]+", str(t))
                    for link in links:
                        new_configs.append(link)
            elif "vpngate.net" in url:
                soup = BeautifulSoup(r.text, "html.parser")
                rows = soup.select("table#vg_hosts_table tr")[1:max_daily//len(urls)]
                for row in rows:
                    a = row.find("a", href=re.compile(r"\.ovpn$"))
                    if a:
                        ovpn = requests.get("https://www.vpngate.net" + a["href"], timeout=10).text
                        new_configs.append(ovpn)
            elif "raw.githubusercontent.com" in url:
                new_configs.extend(re.findall(r"(vmess|vless|trojan)://[^\n]+", r.text))
        except Exception as e:
            logger.error(f"خطا در منبع {url}: {e}")

    added = 0
    for config in new_configs[:max_daily]:
        quality = check_quality(config)
        if quality in ("High", "Medium"):
            modified = apply_remark(config)
            cursor.execute(
                "INSERT OR IGNORE INTO configs (config, quality) VALUES (?, ?)",
                (modified, quality)
            )
            added += cursor.rowcount

    conn.commit()
    logger.info(f"{added} کانفیگ اضافه شد")

def check_quality(config):
    host = re.search(r"(?:add|remote|host)\s*[= ]\s*([^\s#]+)", config, re.IGNORECASE)
    if not host:
        return "Low"
    latency = ping(host.group(1), timeout=3)
    if latency is None:
        return "Low"
    if latency < 150:
        return "High"
    return "Medium" if latency < 300 else "Low"

def apply_remark(config):
    remark = f"MRH-NETcore - {BOT_NAME}"
    if "ps=" in config:
        return re.sub(r"ps=[^&]*", f"ps={remark}", config)
    elif "# " in config:
        return re.sub(r"# .*$", f"# {remark}", config, flags=re.MULTILINE)
    return config + f" # {remark}"

# ────────────────────────────────────────────────
#                 منوی اصلی
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("دریافت کانفیگ", callback_data="get_config")],
        [InlineKeyboardButton("دریافت پروکسی", callback_data="get_proxy")],
        [InlineKeyboardButton("اهدای کانفیگ", callback_data="donate_config")],
        [InlineKeyboardButton("دانلود کلاینت", callback_data="download_client")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "سلام! به ربات @mrhnetcorebot خوش آمدی\n\n"
        "پروژه MRH-NETcore – دسترسی به اینترنت آزاد\n"
        "کانفیگ‌های به‌روز VPN و پروکسی MTProto برای دور زدن فیلترینگ شدید"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

# ────────────────────────────────────────────────
#                 زیرمنو دریافت کانفیگ
# ────────────────────────────────────────────────

async def get_config_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("کانفیگ اختصاصی", callback_data="config_dedicated")],
        [InlineKeyboardButton("لوکیشن دلخواه", callback_data="config_location")],
        [InlineKeyboardButton("گروهی (حداکثر ۱۰)", callback_data="config_group")],
        [InlineKeyboardButton("اهدای کانفیگ", callback_data="donate_config")],
    ]
    await query.edit_message_text("دریافت کانفیگ:", reply_markup=InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────
#                 پنل ادمین (دسته‌بندی شده)
# ────────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("دسترسی ندارید.")
        return

    keyboard = [
        [InlineKeyboardButton("تنظیمات عمومی", callback_data="admin_general")],
        [InlineKeyboardButton("ویژگی‌ها", callback_data="admin_features")],
        [InlineKeyboardButton("محتوا و منابع", callback_data="admin_content")],
        [InlineKeyboardButton("آمار و لاگ", callback_data="admin_stats")],
        [InlineKeyboardButton("کاربران و ادمین‌ها", callback_data="admin_users")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("پنل مدیریت:", reply_markup=reply_markup)

# ادامه پنل ادمین در کد کامل‌تر
