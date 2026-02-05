"""
تنظیمات ربات
"""

import os

class Config:
    """کلاس تنظیمات"""
    
    # توکن ربات تلگرام (از @BotFather)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # آیدی عددی ادمین (از @userinfobot)
    ADMIN_ID = os.environ.get("ADMIN_ID", "")
    
    # کانال‌های مقصد (با کاما جدا شوند)
    CHANNELS = os.environ.get("CHANNELS", "")
    
    # ارسال کلاینت‌ها (true/false)
    SEND_CLIENTS = os.environ.get("SEND_CLIENTS", "true").lower() == "true"
    
    # حالت تأییدیه (true/false)
    APPROVAL_MODE = os.environ.get("APPROVAL_MODE", "false").lower() == "true"
    
    # تعداد هر batch
    BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))
    
    # فاصله بین batchها (ثانیه)
    BATCH_INTERVAL = int(os.environ.get("BATCH_INTERVAL", "120"))
    
    # MongoDB
    MONGODB_URI = os.environ.get("MONGODB_URI", "")
    
    # ipinfo (اختیاری)
    IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN", "")
    
    @classmethod
    def validate(cls):
        """بررسی تنظیمات ضروری"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required!")
        if not cls.ADMIN_ID:
            raise ValueError("ADMIN_ID is required!")
