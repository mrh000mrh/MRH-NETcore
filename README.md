# MRH-NETcore Config Bot

ربات پردازش و انتشار کانفیگ VPN از فایل HTML تلگرام

## ویژگی‌های اصلی
- پارس HTML اکسپورت تلگرام
- استخراج VLESS/VMess/Trojan/SS/MTProto
- لوکیشن هیبرید (ipinfo + متن)
- چک تکراری با MongoDB
- ارسال batch + تأیید ادمین (اختیاری)
- دکمه QR Code زیر هر کانفیگ
- آمار روزانه ۲۳:۵۹
- اهدای کانفیگ توسط کاربران

## Deploy
- Render → Background Worker (Docker)
- Secret File: secrets.env با BOT_TOKEN, ADMIN_ID, MONGODB_URI, ...
