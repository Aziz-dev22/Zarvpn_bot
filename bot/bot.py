# FILE: bot/bot.py

from pyrogram import Client, filters
from pyrogram.types import Message
from core.config import BOT_TOKEN, API_ID, API_HASH
from core.database import get_setting

app = Client(
    "zarvpn_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user = message.from_user

    await message.reply_text(
        f"""
🤖 خوش آمدید {user.first_name}

به سیستم فروش VPN خوش آمدید.

📌 از منوی زیر استفاده کنید.
"""
    )


async def start_bot():
    print("Bot is running...")
    await app.start()
    await idle()
