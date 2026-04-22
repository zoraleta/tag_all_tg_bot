import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from db import close_pool, init_pool
from handlers import router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    await init_pool()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "my_chat_member", "chat_member"],
        )
    finally:
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
