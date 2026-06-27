import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # جدول کاربران، نقش‌ها و کیف پول تومانی
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            balance INTEGER DEFAULT 0, 
            role TEXT DEFAULT "user", 
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول پلن‌ها (مدیریت مولتی‌پنل مرزبان و XUI)
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            size_gb INTEGER, 
            days INTEGER, 
            price INTEGER, 
            panel_type TEXT
        )''')
        
        # جدول سفارشات و لایسنس‌های صادر شده
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            plan_name TEXT, 
            sub_link TEXT, 
            v2ray_username TEXT, 
            panel_type TEXT, 
            buy_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # جدول اطلاعات اتصال به پنل‌های مرزبان و سنایی
        await db.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            panel_type TEXT PRIMARY KEY, 
            url TEXT, 
            username TEXT, 
            password TEXT
        )''')
        
        # جدول تنظیمات صرافی ایرانی Swap Wallet
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, 
            value TEXT
        )''')
        
        # ثبت رکوردهای اولیه صرافی برای جلوگیری از خطای خالی بودن دیتابیس
        async with db.execute("SELECT COUNT(*) FROM settings WHERE key='swapwallet_api'") as cursor:
            if (await cursor.fetchone())[0] == 0:
                await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('swapwallet_api', '')")
                await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('swapwallet_merchant', '')")
                await db.commit()
