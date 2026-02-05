from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import jdatetime
from datetime import datetime

def format_config_message(cfg: dict) -> tuple[str, InlineKeyboardMarkup]:
    now = datetime.now()
    shamsi = jdatetime.datetime.fromgregorian(datetime=now)
    text = f"""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔷 MRH-NETcore Config Bot ┃
┃ ⚡️ کانال: @mrhnetcore ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
📂 کانفیگ {cfg['type']}
📍 لوکیشن: {cfg['location_flag']} {cfg['location']}
📶 پینگ: {cfg['ping']}ms {cfg['quality_emoji']}
#{cfg['type']} #VPN #MRH_NETcore #{cfg['location']}
🕒 {shamsi.strftime('%H:%M - %Y/%m/%d')}
{cfg['full_link']}
⚡️ بررسی: ✅ تا این لحظه فعال
🔗 بفرست برای بقیه: @mrhnetcore
🔒 سطح امنیتی: عمومی
✅ مناسب: وبگردی، شبکه‌های اجتماعی
❌ نامناسب: تراکنش مالی، ترید"""

    keyboard = [[InlineKeyboardButton("📱 دریافت QR Code", callback_data=f"qr_{cfg['unique_id']}")]]
    return text, InlineKeyboardMarkup(keyboard)
