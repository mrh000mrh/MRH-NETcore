import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, ADMIN_ID
from bot.handlers import start, upload_html, stats, settings, broadcast, add_channel, remove_channel
from bot.admin_handlers import handle_config_donation, handle_approval
from bot.handlers import handle_qr_callback
from scheduler.jobs import setup_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    application = Application.builder().token(BOT_TOKEN).concurrent_updates(8).build()

    # Admin commands (فقط ADMIN_ID)
    admin_filter = filters.User(user_id=ADMIN_ID)

    application.add_handler(CommandHandler("start", start, filters=admin_filter))
    application.add_handler(CommandHandler("upload", upload_html, filters=admin_filter))
    application.add_handler(CommandHandler("stats", stats, filters=admin_filter))
    application.add_handler(CommandHandler("settings", settings, filters=admin_filter))
    application.add_handler(CommandHandler("broadcast", broadcast, filters=admin_filter))
    application.add_handler(CommandHandler("addchannel", add_channel, filters=admin_filter))
    application.add_handler(CommandHandler("removechannel", remove_channel, filters=admin_filter))

    # Donation from users
    application.add_handler(MessageHandler(filters.TEXT | filters.Document.HTML | filters.PHOTO, handle_config_donation))

    # Approval buttons
    application.add_handler(CallbackQueryHandler(handle_approval, pattern="^(approve|reject)_"))

    # QR Code button
    application.add_handler(CallbackQueryHandler(handle_qr_callback, pattern="^qr_"))

    # Scheduler for daily stats & batch sending
    await setup_scheduler(application)

    logger.info("MRH-NETcore Bot started")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )
    await asyncio.Event().wait()  # نگه داشتن تا infinity

if __name__ == "__main__":
    asyncio.run(main())
