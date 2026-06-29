import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", 8000))
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database/zarvpn.db")
