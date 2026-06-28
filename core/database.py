import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from core.config import settings

# ایجاد دایرکتوری دیتابیس در صورتی که وجود نداشته باشد
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# راه‌اندازی موتور دیتابیس
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ۱. جدول کاربران
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    wallet_balance = Column(Float, default=0.0)  # موجودی کیف پول به تومان
    referred_by = Column(BigInteger, nullable=True)  # آیدی کسی که معرف بوده
    is_ban = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ۲. جدول پنل‌ها و سرورها (Sanaei / Marzban)
class ServerPanel(Base):
    __tablename__ = "server_panels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # نام مستعار سرور
    panel_type = Column(String, nullable=False)  # sanaei یا marzban
    url = Column(String, nullable=False)  # آدرس پنل مثل http://1.2.3.4:2053
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

# ۳. جدول سرویس‌های فروشی (پکیج‌ها)
class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # مثلا: ۱ ماهه ۲۰ گیگ
    price = Column(Float, nullable=False)  # قیمت به تومان
    volume_gb = Column(Integer, nullable=False)  # حجم به گیگابایت
    days = Column(Integer, nullable=False)  # تعداد روز اعتبار
    is_active = Column(Boolean, default=True)

# ۴. جدول اشتراک‌های خریداری شده توسط کاربران
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    panel_id = Column(Integer, ForeignKey("server_panels.id"), nullable=False)
    email_in_panel = Column(String, nullable=False, unique=True)  # نام کاربری ساخته شده در X-UI
    uuid = Column(String, nullable=True)  # یو‌یودی کانکشن
    sub_url = Column(Text, nullable=True)  # لینک اشتراک کاربر
    created_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=True)

# ۵. جدول تراکنش‌های مالی (خرید یا شارژ حساب)
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)
    gateway = Column(String, nullable=False)  # Zarinpal, Cryptomus, Wallet
    status = Column(String, default="pending")  # pending, success, failed
    authority = Column(String, nullable=True)  # کد پیگیری درگاه
    created_at = Column(DateTime, default=datetime.utcnow)

# ۶. جدول سیستم تیکت و پشتیبانی
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="open")  # open, answered, closed
    created_at = Column(DateTime, default=datetime.utcnow)

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    sender_id = Column(BigInteger, nullable=False)  # آیدی کاربر یا ادمین
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# تابع ایجاد جدول‌ها و دریافت Session دیتابیس
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

