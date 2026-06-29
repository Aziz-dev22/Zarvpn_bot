# core/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import Config
from database.models import Base

# ایجاد موتور دیتابیس به صورت غیرهمزمان
engine = create_async_engine(Config.DATABASE_URL, echo=False, future=True)

# کلاس ساخت سشن‌های دیتابیس
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """ایجاد جداول دیتابیس در صورت عدم وجود"""
    # اطمینان از وجود پوشه دیتابیس
    db_dir = os.path.dirname(Config.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    async with engine.begin() as conn:
        # ساخت تمام جداول تعریف شده در models.py
        await conn.run_sync(Base.metadata.create_all)
    print(" [✓] Database tables initialized successfully.")

async def get_db():
    """یک Generator برای استفاده از سشن دیتابیس در بخش‌های مختلف"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
