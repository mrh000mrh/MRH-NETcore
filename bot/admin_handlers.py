from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database.mongo import db
from sender.channel_sender import send_single_config
from utils.qr_generator import generate_qr_code

async def handle_config_donation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    if "vless://" not in text and "vmess://" not in text and "trojan://" not in text:
        return  # فقط کانفیگ‌ها را پردازش کن

    config = {
        "full_link": text.strip(),
        "remark": f"MRH-NETcore | @{user.username}" if user.username else "MRH-NETcore",
        "submitted_by": user.id,
        "status": "pending" if APPROVAL_MODE else "approved",
        "date": datetime.utcnow()
    }
    # استخراج نوع و ... ساده (کامل‌تر در processor)
    if "vless://" in text:
        config["type"] = "VLESS"
    # ... بقیه پروتکل‌ها

    db.configs.insert_one(config)
    if not APPROVAL_MODE:
        await send_single_config(config)
    else:
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{config['_id']}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{config['_id']}")
            ]
        ]
        await context.bot.send_message(
            ADMIN_ID,
            f"کانفیگ جدید از @{user.username}:\n{text[:100]}...",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    await update.message.reply_text("کانفیگ شما دریافت شد و در حال بررسی است.")

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("شما ادمین نیستید.")
        return

    action, config_id = query.data.split("_", 1)
    config = db.configs.find_one({"_id": config_id})
    if not config:
        await query.answer("کانفیگ یافت نشد.")
        return

    if action == "approve":
        config["status"] = "approved"
        db.configs.update_one({"_id": config_id}, {"$set": config})
        await send_single_config(config)
        await query.edit_message_text("کانفیگ تأیید و ارسال شد.")
    else:
        db.configs.delete_one({"_id": config_id})
        await query.edit_message_text("کانفیگ رد شد.")
    await query.answer()
