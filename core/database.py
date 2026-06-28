import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جدول سرورها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )""")
    
    # جدول پکیج‌ها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        size_gb INTEGER NOT NULL,
        days INTEGER NOT NULL,
        price INTEGER NOT NULL
    )""")
    
    # جدول کاربران ربات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        referred_by INTEGER
    )""")
    
    # جدول سفارشات و اشتراک‌ها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        email TEXT,
        uuid TEXT,
        sub_url TEXT,
        package_name TEXT,
        price INTEGER,
        status TEXT DEFAULT 'active'
    )""")
    
    conn.commit()
    conn.close()
