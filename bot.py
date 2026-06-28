# پاک کردن فایل به‌هم‌ریخته قبلی
rm -f ~/Zarvpn_bot/bot.py

# بازنویسی کاملاً هوشمند با پایتون برای جلوگیری از گلیچ کیبورد گوشی
uv run python -c '
import os
code = """import asyncio
import sys
import jwt
import datetime
import sqlite3
import uvicorn
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.config import settings
from core.database import init_db
from core.logger import logger
from web_panel import app

dp = Dispatcher()
DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    user_id = message.from_user.id
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (user_id, message.from_user.username or "User"))
        conn.commit()
        conn.close()
    except:
        pass

    b1 = InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")
    b2 = InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")
    keyboard = [[b1], [b2]]

    if str(user_id) in str(settings.ADMIN_IDS):
        token = jwt.encode({"admin_id": user_id, "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15)}, settings.SECRET_KEY, algorithm="HS256")
        web_url = f"http://178.105.165.200:8050/login/token?token={token}"
        b_admin = InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)
        keyboard.append([b_admin])

    await message.answer("🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\\nلطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

async def main():
    init_db()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    config = uvicorn.Config(app, host=settings.WEB_HOST, port=settings.WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), dp.start_polling(bot))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
"""
with open(os.path.expanduser("~/Zarvpn_bot/bot.py"), "w") as f:
    f.write(code)
'

# آزاد کردن پورت و پروسه‌های قبلی
pkill -f bot.py
sudo fuser -k 8050/tcp 2>/dev/null

# اجرای نهایی نسخه بدون گلیچ
cd ~/Zarvpn_bot && uv run python bot.py
