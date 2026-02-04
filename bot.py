import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ping3 import ping
import re
import asyncio
import os
from datetime import datetime

# ────────────────────────────────────────────────
#                 تنظیمات اصلی (امن – از env vars)
# ────────────────────────────────────────────────

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_NAME = "MRH-NETcore"
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", None)
MAX_DAILY_CONFIGS = 100
CHECK_INTERVAL_MINUTES = 30

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

cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("max_daily_configs", str(MAX_DAILY_CONFIGS)))
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# منابع استخراج (مخفی از کاربر)
SOURCES = [
    "https://t.me/s/persianvpnhub",
    "https://www.vpngate.net/en/",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/configs.txt",
    "https://github.com/mahdibland/V2RayAggregator/raw/master/configs",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/configs",
]

# ────────────────────────────────────────────────
#                 استخراج اتوماتیک
# ────────────────────────────────────────────────

async def extract_configs(context: ContextTypes.DEFAULT_TYPE):
    new_configs = []
    max_daily = int(get_setting("max_daily_configs") or str(MAX_DAILY_CONFIGS))

    for url in SOURCES:
        try:
            r = requests.get(url, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser") if "html" in r.headers.get("Content-Type", "") else None

            if "t.me/s" in url:
                texts = soup.find_all("div", class_="tgme_widget_message_text")
                for t in texts:
                    links = re.findall(r"(vmess|vless|trojan)://[^\s<>\"]+", str(t))
                    for link in links:
                        new_configs.append(link)

            elif "vpngate.net" in url:
                rows = soup.select("table#vg_hosts_table tr")[1:max_daily//len(SOURCES)]
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
                "INSERT OR IGNORE INTO configs (config, location, protocol, quality) VALUES (?, ?, ?, ?)",
                (modified, "IR/Global", "Unknown", quality)
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

def get_setting(key: str) -> str:
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else "false"

# ────────────────────────────────────────────────
#                 منوی اصلی (ReplyKeyboard - دکمه‌های پایین کوچک و خوانا)
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("دریافت کانفیگ"), KeyboardButton("دریافت پروکسی")],
        [KeyboardButton("اهدای کانفیگ"), KeyboardButton("دانلود کلاینت")],
    ], resize_keyboard=True, one_time_keyboard=False)
    text = "سلام! به ربات @mrhnetcorebot خوش آمدی\nپروژه MRH-NETcore – دسترسی به اینترنت آزاد"
    await update.message.reply_text(text, reply_markup=keyboard)

# ────────────────────────────────────────────────
#                 هندلر پیام‌ها (دکمه‌های پایین + بازگشت)
# ────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "دریافت کانفیگ":
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("کانفیگ اختصاصی"), KeyboardButton("لوکیشن دلخواه")],
            [KeyboardButton("گروهی (حداکثر ۱۰)"), KeyboardButton("اهدای کانفیگ")],
            [KeyboardButton("بازگشت به منوی اصلی")],
        ], resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text("گزینه دریافت کانفیگ:", reply_markup=keyboard)

    elif text == "کانفیگ اختصاصی":
        cursor.execute("SELECT config FROM configs WHERE quality = 'High' ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        msg = row[0] if row else "کانفیگ موجود نیست. کمی صبر کنید تا استخراج جدید انجام شود."
        await update.message.reply_text(msg)

    elif text == "اهدای کانفیگ":
        await update.message.reply_text(
            "ممنون که می‌خوای کمک کنی!\n"
            "کانفیگ (متن یا لینک) رو همین‌جا بفرست. ما چک می‌کنیم و اگر خوب بود، با ریمارک MRH-NETcore به دیگران هم می‌رسونیم."
        )

    elif text == "دانلود کلاینت":
        await update.message.reply_text(
            "لینک دانلود کلاینت‌های امن:\n"
            "اندروید: Psiphon https://psiphon.ca/psiphon3-android.apk\n"
            "ویندوز: Psiphon https://psiphon.ca/psiphon3.exe\n"
            "Tor Browser https://www.torproject.org/download/"
        )

    elif text == "بازگشت به منوی اصلی":
        await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(extract_configs, interval=CHECK_INTERVAL_MINUTES * 60, first=0)  # بلافاصله + هر ۶۰ دقیقه
    app.run_polling()

if __name__ == '__main__':
    main()
