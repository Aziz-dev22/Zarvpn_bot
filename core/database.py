import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # جدول کاربران (با ثبت وضعیت تست رایگان)
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            balance INTEGER DEFAULT 0, 
            role TEXT DEFAULT "user", 
            referred_by INTEGER DEFAULT 0,
            used_test INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول پلن‌ها (تجاری و تست)
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            size_gb INTEGER, 
            days INTEGER, 
            price INTEGER, 
            panel_type TEXT
        )''')
        
        # جدول سفارشات و کانکشن‌ها
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            plan_name TEXT, 
            sub_link TEXT, 
            v2ray_username TEXT, 
            panel_type TEXT, 
            buy_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # جدول تنظیمات سرورها (پشتیبانی همزمان از چندین پنل)
        await db.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            panel_type TEXT PRIMARY KEY, url TEXT, username TEXT, password TEXT
        )''')
        
        # جدول تنظیمات عمومی سیستم
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')
        
        # مقادیر پیش‌فرض
        defaults = [
            ('card_number', 'ثبت نشده'),
            ('crypto_wallet', 'ثبت نشده'),
            ('swapwallet_merchant', ''),
            ('channel_id', '@your_channel'),
            ('backup_channel', '@your_backup_channel'), # کانال پشتیبان‌گیری
            ('test_status', 'on'), # وضعیت اکانت تست
            ('miniapp_url', '') # آدرس مینی‌اپ در صورت فعال‌سازی
        ]
        for key, val in defaults:
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
            
        await db.commit()
