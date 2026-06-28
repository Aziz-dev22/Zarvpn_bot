import aiosqlite

DB_NAME = "zarvpn_web.db"

async def init_commercial_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            balance INTEGER DEFAULT 0, 
            role TEXT DEFAULT "user", 
            referred_by INTEGER DEFAULT 0,
            used_test INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            size_gb INTEGER, 
            days INTEGER, 
            price INTEGER, 
            panel_type TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            plan_name TEXT, 
            sub_link TEXT, 
            v2ray_username TEXT, 
            panel_type TEXT, 
            buy_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        await db.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            panel_type TEXT PRIMARY KEY, url TEXT, username TEXT, password TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')
        
        defaults = [
            ('card_number', 'ثبت نشده'),
            ('crypto_wallet', 'ثبت نشده'),
            ('swapwallet_merchant', ''),
            ('channel_id', '@your_channel'),
            ('backup_channel', '@your_backup_channel'), 
            ('test_status', 'on'),
            ('miniapp_url', 'https://yourminiappurl.com')
        ]
        for key, val in defaults:
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        await db.commit()
