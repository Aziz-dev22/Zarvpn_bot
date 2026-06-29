# core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Settings
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    
    # Web Panel Settings
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", 8000))
    WEB_ADMIN_USERNAME = os.getenv("WEB_ADMIN_USERNAME", "admin")
    WEB_ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD")
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database/zarvpn.db")
