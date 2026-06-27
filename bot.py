import telebot
from telebot import types
import sqlite3
import requests
import time
import config

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

# ==========================================
# 💾 بخش اول: ساخت و مدیریت دیتابیس (کیف پول)
# ==========================================
def init_db():
    conn = sqlite3.connect("zarvpn.db")
    cursor = conn.cursor()
    # جدول کاربران و موجودی کیف پول
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, username TEXT)''')
    # جدول پلن‌های فروش
    cursor.execute('''CREATE TABLE IF NOT EXISTS plans 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size INTEGER, days INTEGER, price INTEGER)''')
    conn.commit()
    
    # افزودن چند پلن پیش‌فرض در صورت خالی بودن دیتابیس
    cursor.execute("SELECT COUNT(*) FROM plans")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("👑 پلن برنزی (یک‌ماهه ۱۰ گیگ)", 10, 30, 50000))
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("💎 پلن نقره‌ای (یک‌ماهه ۳۰ گیگ)", 30, 30, 100000))
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("🔥 پلن طلایی (سه‌ماهه ۱۰۰ گیگ)", 100, 90, 250000))
        conn.commit()
    conn.close()

init_db()

# ==========================================
# 🌐 بخش دوم: اتصال واقعی به API پنل مرزبان
# ==========================================
def get_marzban_token():
    try:
        login_url = f"{config.PANEL_URL}/api/admin/token"
        data = {
            "username": config.PANEL_USERNAME,
            "password": config.PANEL_PASSWORD
        }
        response = requests.post(login_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def create_vpn_account(username, days, size_gb):
    token = get_marzban_token()
    if not token:
        return "❌ خطا در اتصال به پنل ادمین (توکن دریافت نشد)"
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # محاسبه زمان انقضا به فرمت Epoch
    expire_time = int(time.time()) + (days * 86400)
