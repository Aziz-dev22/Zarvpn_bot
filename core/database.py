import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # جدول کاربران و سفارشات
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, used_test INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_name TEXT, sub_link TEXT, v2ray_username TEXT, panel_type TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS server_settings (panel_type TEXT PRIMARY KEY, url TEXT, username TEXT, password TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        
        # تنظیمات و سوییچ‌های جدید سیستم (بند ۳ و ۵)
        defaults = [
            ('card_number', 'ثبت نشده'), ('card_status', 'on'),
            ('crypto_wallet', 'ثبت نشده'), ('crypto_status', 'on'),
            ('swapwallet_merchant', ''), ('swapwallet_status', 'on'),
            ('nobitex_token', ''), ('nobitex_status', 'off'), # صرافی دوم فعال/غیرفعال
            ('channel_id', '@your_channel'), ('backup_channel', '@your_backup_channel'),
            ('test_status', 'on'), ('miniapp_url', 'http://127.0.0.1:8000')
        ]
        for key, val in defaults:
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        await db.commit()
