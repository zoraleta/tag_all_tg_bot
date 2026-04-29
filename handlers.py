import re

from telethon import TelegramClient, events

from members import MembersCache
from mentions import build_mention_batches

ALL_PATTERN = re.compile(r"(?<!\w)@all(?!\w)", re.IGNORECASE)


def register_handlers(client: TelegramClient) -> None:
    cache = MembersCache(client)

    @client.on(events.ChatAction)
    async def on_chat_action(event):
        if event.user_joined or event.user_added or event.user_left or event.user_kicked:
            cache.invalidate(event.chat_id)

    @client.on(events.NewMessage(incoming=True))
    async def on_message(event):
        if not event.is_group:
            return
        text = event.message.message
        if not text or not ALL_PATTERN.search(text):
            return
        members = await cache.get(event.chat_id)
        batches = build_mention_batches(members, exclude_user_id=event.sender_id)
        if not batches:
            await event.reply("Пока некого тегать — никто, кроме тебя, не в чате.")
            return
        for batch in batches:
            await event.reply(batch, parse_mode="html")
