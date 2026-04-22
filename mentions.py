from html import escape
from typing import Iterable

MAX_MENTIONS_PER_MESSAGE = 50
MAX_MESSAGE_LENGTH = 4000


def _format_mention(user_id: int, username: str | None, first_name: str | None) -> str:
    if username:
        return f"@{username}"
    name = escape(first_name) if first_name else "user"
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def build_mention_batches(
    members: Iterable[tuple[int, str | None, str | None]],
    exclude_user_id: int | None = None,
) -> list[str]:
    mentions = [
        _format_mention(uid, username, first_name)
        for uid, username, first_name in members
        if uid != exclude_user_id
    ]
    if not mentions:
        return []

    batches: list[str] = []
    current: list[str] = []
    current_len = 0
    for m in mentions:
        added_len = len(m) + (1 if current else 0)
        too_many = len(current) >= MAX_MENTIONS_PER_MESSAGE
        too_long = current_len + added_len > MAX_MESSAGE_LENGTH
        if current and (too_many or too_long):
            batches.append(" ".join(current))
            current = []
            current_len = 0
            added_len = len(m)
        current.append(m)
        current_len += added_len
    if current:
        batches.append(" ".join(current))
    return batches
