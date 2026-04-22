import re

from aiogram import Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated, Message

from db import (
    delete_chat,
    get_active_members,
    mark_member_left,
    upsert_chat,
    upsert_member,
)
from mentions import build_mention_batches

router = Router()

ALL_PATTERN = re.compile(r"(?<!\w)@all(?!\w)", re.IGNORECASE)

GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}
LEFT_STATUSES = {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}


@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated) -> None:
    chat = event.chat
    if chat.type not in GROUP_TYPES:
        return
    new_status = event.new_chat_member.status
    if new_status in LEFT_STATUSES:
        await delete_chat(chat.id)
    else:
        await upsert_chat(chat.id, chat.type, chat.title)


@router.chat_member()
async def on_chat_member(event: ChatMemberUpdated) -> None:
    chat = event.chat
    if chat.type not in GROUP_TYPES:
        return
    user = event.new_chat_member.user
    new_status = event.new_chat_member.status
    if new_status in LEFT_STATUSES:
        await mark_member_left(chat.id, user.id)
    else:
        await upsert_chat(chat.id, chat.type, chat.title)
        await upsert_member(
            chat.id, user.id, user.username, user.first_name, user.last_name, user.is_bot
        )


@router.message()
async def on_message(message: Message) -> None:
    if message.chat.type not in GROUP_TYPES:
        return
    user = message.from_user
    if user is None:
        return

    if not user.is_bot:
        await upsert_chat(message.chat.id, message.chat.type, message.chat.title)
        await upsert_member(
            message.chat.id, user.id, user.username, user.first_name, user.last_name, False
        )

    text = message.text or message.caption
    if text and ALL_PATTERN.search(text):
        await _tag_all(message)


async def _tag_all(message: Message) -> None:
    members = await get_active_members(message.chat.id)
    triple = [(r["user_id"], r["username"], r["first_name"]) for r in members]
    batches = build_mention_batches(triple, exclude_user_id=message.from_user.id)
    if not batches:
        await message.reply("Пока некого тегать — никто, кроме тебя, не отмечался в чате.")
        return
    for batch in batches:
        await message.reply(batch, parse_mode="HTML")
