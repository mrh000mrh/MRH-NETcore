from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from config import SEND_CLIENTS_AFTER_STATS
import jdatetime

async def daily_stats(application: Application):
    # مشابه stats در handlers اما خودکار
    pass  # پیاده‌سازی آمار روزانه + ارسال کلاینت‌ها اگر روشن باشد

def setup_scheduler(application: Application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_stats,
        CronTrigger(hour=23, minute=59),
        args=(application,)
    )
    scheduler.start()
