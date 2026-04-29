import asyncio
import logging

import uvloop
from telethon import TelegramClient

from config import API_HASH, API_ID, BOT_TOKEN
from handlers import register_handlers


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    client = TelegramClient("tag_all_bot", API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    register_handlers(client, bot_username=me.username)
    try:
        await client.run_until_disconnected()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
