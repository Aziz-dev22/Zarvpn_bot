import os
from dotenv import load_dotenv

load_dotenv()

# تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# دیتابیس تحت وب
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./zarvpn_web.db")

# اطلاعات وب پنل
WEB_PORT = int(os.getenv("WEB_PORT", 8080))
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "zarvpn_admin")

