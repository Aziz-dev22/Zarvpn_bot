import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # ساخت جدول کاربران با فیلدهای کامل
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, 
            role TEXT DEFAULT "user", referred_by INTEGER DEFAULT 0, used_test INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        # جدول پلن‌ها
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size_gb INTEGER, days INTEGER, price INTEGER, panel_type TEXT)''')
        # جدول سفارشات و لینک‌های ساب مشتریان
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_name TEXT, sub_link TEXT, v2ray_username TEXT, panel_type TEXT, buy_date TEXT DEFAULT CURRENT_TIMESTAMP)''')
        # جدول تنظیمات اتصال واقعی به سرورها
        await db.execute('''CREATE TABLE IF NOT EXISTS server_settings (panel_type TEXT PRIMARY KEY, url TEXT, username TEXT, password TEXT)''')
        # جدول تنظیمات عمومی ربات و پسورد ادمین وب
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        
        # مقادیر پیش‌فرض امنیتی و عمومی
        defaults = [
            ('card_number', 'ثبت نشده'), ('card_status', 'on'),
            ('crypto_details', 'تتر TRC20:\nثبت نشده'), ('crypto_status', 'on'),
            ('swapwallet_merchant', ''), ('swapwallet_api', ''), ('swapwallet_endpoint', 'https://swapwallet.ir/api'), ('swapwallet_status', 'off'),
            ('channel_id', '@your_channel'), ('sub_status', 'off'), ('test_status', 'on'),
            ('web_admin_user', 'admin'), ('web_admin_pass', 'secure_zar_pass_2026')  # رمز عبور اولیه و پسورد دار شدن پنل
        ]
        for key, val in defaults:
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        await db.commit()
