# FILE: bot/bot.py

import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.config import BOT_TOKEN, API_ID, API_HASH, ADMIN_ID
from core.database import get_setting, set_setting

app = Client(
    "zarvpn_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)


# ---------- START ----------
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    user = message.from_user

    await message.reply_text(
        f"""
🤖 سلام {user.first_name}

به سیستم حرفه‌ای فروش VPN خوش آمدید.

📌 از منو استفاده کنید.
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍 خرید سرویس", callback_data="buy")],
            [InlineKeyboardButton("💰 کیف پول", callback_data="wallet")],
            [InlineKeyboardButton("👥 زیرمجموعه", callback_data="ref")]
        ])
    )


# ---------- CALLBACK ----------
@app.on_callback_query()
async def callback(client, call):
    data = call.data

    if data == "buy":
        await call.message.edit_text("🛍 بخش خرید در حال توسعه است...")

    elif data == "wallet":
        await call.message.edit_text("💰 کیف پول شما فعلاً خالی است.")

    elif data == "ref":
        bot_username = (await client.get_me()).username
        link = f"https://t.me/{bot_username}?start={call.from_user.id}"

        await call.message.edit_text(
            f"👥 لینک دعوت شما:\n{link}"
        )


# ---------- RUN ----------
async def start_bot():
    print("BOT STARTED ✅")
    await app.start()
    await idle()
