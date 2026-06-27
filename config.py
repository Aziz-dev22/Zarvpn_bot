import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# آدرس و مشخصات پنل مرزبان کاربر
PANEL_URL = os.getenv("PANEL_URL", "http://YOUR_PANEL_IP:8000")
PANEL_USERNAME = os.getenv("PANEL_USERNAME", "admin")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "password")
