import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # جدول کاربران و مدیریت کیف پول و نقش‌ها
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            role TEXT DEFAULT "user",
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # جدول پلن‌های فروش (حجم، زمان، قیمت، نوع پنل)
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            size_gb INTEGER,
            days INTEGER,
            price INTEGER,
            panel_type TEXT
        )''')
        
        # جدول سفارشات و کانکشن‌های فروخته شده برای مدیریت و تمدید کاربری
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_name TEXT,
            sub_link TEXT,
            v2ray_username TEXT,
            panel_type TEXT,
            buy_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # وارد کردن پلن‌های پیش‌فرض تجاری در صورت خالی بودن دیتابیس
        async with db.execute("SELECT COUNT(*) FROM plans") as cursor:
            if (await cursor.fetchone())[0] == 0:
                default_plans = [
                    ("🚀 پلن اقتصادی ثنایی (۱۵ گیگ - ۳۰ روز)", 15, 30, 45000, "xui"),
                    ("🔥 پلن حرفه‌ای ثنایی (۵۰ گیگ - ۳۰ روز)", 50, 30, 95000, "xui"),
                    ("💎 پلن ویژه مرزبان (۱۰۰ گیگ - ۳۰ روز)", 100, 30, 160000, "marzban")
                ]
                await db.executemany(
                    "INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)",
                    default_plans
                )
        await db.commit()
