import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# اگر فایل .env نبود، اسکریپت setup را اجرا کن
if not env_path.exists():
    # اضافه کردن مسیر ریشه به sys.path برای ایمپورت setup
    sys.path.append(str(BASE_DIR))
    from setup import run_setup
    run_setup()

# حالا فایل .env را لود کن
load_dotenv(env_path)

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    
    ADMIN_IDS: list[int] = [
        int(admin_id.strip()) 
        for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
        if admin_id.strip()
    ]
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///database/zarvpn.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

settings = Config()

