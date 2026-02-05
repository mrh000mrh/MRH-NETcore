from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID, CHANNELS, APPROVAL_MODE, SEND_CLIENTS_AFTER_STATS
from database.mongo import db
from processor.config_processor import process_html_file
from sender.channel_sender import send_batch_configs
from utils.location import get_location_flag
import jdatetime
from datetime import datetime

UPLOAD_HTML = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما ادمین نیستید.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کانال", callback_data="add_channel")],
        [InlineKeyboardButton("➖ حذف کانال", callback_data="remove_channel")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
        [InlineKeyboardButton("📢 برودکست", callback_data="broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("پنل ادمین MRH-NETcore", reply_markup=reply_markup)

async def upload_html(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("فایل HTML اکسپورت تلگرام را بفرستید (تکی یا چندتایی)")
    return UPLOAD_HTML

async def receive_html(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    documents = update.message.document or [update.message.document]
    if not documents:
        await update.message.reply_text("لطفاً فایل HTML بفرستید.")
        return UPLOAD_HTML

    configs = []
    for doc in documents if isinstance(documents, list) else [documents]:
        file = await doc.get_file()
        file_bytes = await file.download_as_bytearray()
        new_configs = await process_html_file(file_bytes, update.effective_user.username)
        configs.extend(new_configs)

    if not configs:
        await update.message.reply_text("هیچ کانفیگ معتبری استخراج نشد.")
        return ConversationHandler.END

    # ذخیره موقت برای تأیید یا ارسال مستقیم
    if APPROVAL_MODE:
        # ذخیره در دیتابیس با وضعیت pending
        for cfg in configs:
            cfg["status"] = "pending"
            cfg["submitted_by"] = update.effective_user.id
            db.configs.insert_one(cfg)
        await update.message.reply_text(f"{len(configs)} کانفیگ در صف تأیید قرار گرفت.")
    else:
        await send_batch_configs(configs)
        await update.message.reply_text(f"{len(configs)} کانفیگ پردازش و ارسال شد.")

    return ConversationHandler.END

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    today = datetime.now()
    shamsi = jdatetime.date.fromgregorian(date=today)
    count = db.configs.count_documents({"date": {"$gte": today.replace(hour=0, minute=0, second=0)}})
    locations = db.configs.aggregate([
        {"$match": {"date": {"$gte": today.replace(hour=0, minute=0, second=0)}}},
        {"$group": {"_id": "$location", "count": {"$sum": 1}}}
    ])
    loc_text = " ".join([f"{loc['_id']}({loc['count']})" for loc in locations])
    text = f"""📊 آمار امروز MRH-NETcore
📤 کانفیگ ارسال شده: {count} عدد
🌍 لوکیشن‌ها: {loc_text}
🕒 {shamsi.strftime('%Y/%m/%d')}"""
    await update.message.reply_text(text)
