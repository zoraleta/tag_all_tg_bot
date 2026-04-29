import asyncio
import time

from telethon import TelegramClient
from telethon.tl.types import User

Member = tuple[int, str | None, str | None]


class MembersCache:
    def __init__(self, client: TelegramClient, min_interval_seconds: float = 2.5) -> None:
        self._client = client
        self._cache: dict[int, list[Member]] = {}
        self._chat_locks: dict[int, asyncio.Lock] = {}
        self._rate_lock = asyncio.Lock()
        self._last_call_at = 0.0
        self._min_interval = min_interval_seconds

    def invalidate(self, chat_id: int) -> None:
        self._cache.pop(chat_id, None)

    async def get(self, chat_id: int) -> list[Member]:
        cached = self._cache.get(chat_id)
        if cached is not None:
            return cached
        lock = self._chat_locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            cached = self._cache.get(chat_id)
            if cached is not None:
                return cached
            members = await self._fetch(chat_id)
            self._cache[chat_id] = members
            return members

    async def _fetch(self, chat_id: int) -> list[Member]:
        await self._throttle()
        result: list[Member] = []
        async for p in self._client.iter_participants(chat_id):
            if not isinstance(p, User) or p.bot or p.deleted:
                continue
            result.append((p.id, p.username, p.first_name))
        return result

    async def _throttle(self) -> None:
        async with self._rate_lock:
            wait = self._min_interval - (time.monotonic() - self._last_call_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_at = time.monotonic()
