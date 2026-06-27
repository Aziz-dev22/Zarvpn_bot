import os
from dotenv import load_dotenv

# لود کردن فایل تنظیمات محیطی .env
load_dotenv()

# خواندن اطلاعات از متغیرهای محیطی سرور
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# بررسی حیاتی بودن اطلاعات
if not TELEGRAM_TOKEN or not ADMIN_ID:
    raise ValueError("خطا: متغیرهای TELEGRAM_TOKEN و ADMIN_ID تنظیم نشده‌اند!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("خطا: ADMIN_ID باید یک عدد چندرقمی باشد!")

# تنظیمات پیش‌فرض پنل مرزبان یا X-UI
PANEL_URL = os.getenv("PANEL_URL", "https://your-panel.com:8000")
PANEL_USERNAME = os.getenv("PANEL_USERNAME", "admin")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "password")
