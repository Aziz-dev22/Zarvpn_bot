import shutil
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from core import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# تابع پشتیبان‌گیری زنده از دیتابیس تحت وب
def backup_database():
    try:
        backup_dir = "./backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        db_path = "./zarvpn_web.db" # مسیر پیش‌فرض دیتابیس
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{backup_dir}/backup_{timestamp}.db"
            shutil.copyfile(db_path, backup_path)
            return f"✅ پشتیبان‌گیری با موفقیت انجام شد: {backup_path}"
        return "❌ فایل دیتابیس اصلی پیدا نشد!"
    except Exception as e:
        return f"❌ خطای پشتیبان‌گیری: {e}"

# تابع بازیابی دیتابیس
def restore_database(backup_filename):
    try:
        backup_path = f"./backups/{backup_filename}"
        db_path = "./zarvpn_web.db"
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, db_path)
            return "✅ دیتابیس با موفقیت به نسخه پشتیبان بازیابی شد. لطفا ربات را ریستارت کنید."
        return "❌ فایل پشتیبان مورد نظر یافت نشد!"
    except Exception as e:
        return f"❌ خطای بازیابی: {e}"

