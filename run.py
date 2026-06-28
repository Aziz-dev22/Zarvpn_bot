# FILE: run.py

import asyncio
from bot.bot import start_bot
from web.app import start_web
from core.database import init_db


async def main():
    await init_db()

    await asyncio.gather(
        start_bot(),
        start_web()
    )


if __name__ == "__main__":
    asyncio.run(main())
