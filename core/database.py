import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # جدول کاربران، نقش‌ها و کیف پول
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, role TEXT DEFAULT "user", created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول پلن‌ها (مدیریت مولتی‌پنل مرزبان و XUI)
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size_gb INTEGER, days INTEGER, price INTEGER, panel_type TEXT
        )''')
        
        # جدول سفارشات و لایسنس‌ها
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_name TEXT, sub_link TEXT, v2ray_username TEXT, panel_type TEXT, buy_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # جدول تراکنش‌های مالی و API صرافی (برای شارژ خودکار)
        await db.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, tx_id TEXT UNIQUE, status TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول تنظیمات پیشرفته سیستم (توکن صرافی، قیمت ارز و وضعیت بکاپ)
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')
        
        # ثبت پلن‌های اولیه تجاری
        async with db.execute("SELECT COUNT(*) FROM plans") as cursor:
            if (await cursor.fetchone())[0] == 0:
                await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", ("🚀 پلن سنایی اقتصادی", 15, 30, 45000, "xui"))
                await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", ("💎 پلن مرزبان VIP", 50, 30, 120000, "marzban"))
                await db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("nowpayments_api", "YOUR_API_KEY"))
                await db.commit()
