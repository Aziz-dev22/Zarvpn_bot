import os
from dotenv import load_dotenv

load_dotenv()

# ۱. تنظیمات ربات تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# ۲. تنظیمات اتصال به پنل‌های مرزبان و سنایی (Sanaei)
PANEL_URL = os.getenv("PANEL_URL", "http://YOUR_PANEL_IP:8000")
PANEL_USERNAME = os.getenv("PANEL_USERNAME", "admin")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "password")

# ۳. تنظیمات دیتابیس تحت وب
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./zarvpn_web.db")

# ۴. اطلاعات وب پنل مدیریت
WEB_PORT = int(os.getenv("WEB_PORT", 8080))
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "zarvpn_admin")
