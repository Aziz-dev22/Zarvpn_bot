# database/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    balance = Column(Float, default=0.0)       # موجودی کیف پول به تومان
    role = Column(String(50), default="user")  # user, admin
    is_banned = Column(Boolean, default=False)
    referred_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InboundPanel(Base):
    """ذخیره اطلاعات اتصال به پنل‌های سنایی و مرزبان"""
    __tablename__ = 'panels'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    panel_type = Column(String(50), nullable=False)
    api_url = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

class Package(Base):
    """پکیج‌های تعریف شده برای فروش"""
    __tablename__ = 'packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    volume_gb = Column(Integer, nullable=False)
    expiry_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class Ticket(Base):
    """جدول ثبت تیکت‌ها و پیام‌های پشتیبانی کاربران"""
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)          # تلگرام آی‌دی کابر
    message_text = Column(Text, nullable=False)        # متن پیام کاربر
    photo_id = Column(String(255), nullable=True)      # فایل آی‌دی تصویر فیش یا اسکرین‌شات
    status = Column(String(50), default="open")       # open, answered, closed
    created_at = Column(DateTime, default=datetime.utcnow)

class Gateway(Base):
    """تنظیمات درگاه‌های صرافی ایرانی و ریالی"""
    __tablename__ = 'gateways'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    merchant_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
