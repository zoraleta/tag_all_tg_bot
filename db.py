import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)


async def close_pool() -> None:
    if _pool is not None:
        await _pool.close()


async def upsert_chat(chat_id: int, chat_type: str, title: str | None) -> None:
    await _pool.execute(
        """
        insert into chats (chat_id, chat_type, title)
        values ($1, $2, $3)
        on conflict (chat_id) do update
        set chat_type = excluded.chat_type,
            title     = excluded.title
        """,
        chat_id, chat_type, title,
    )


async def delete_chat(chat_id: int) -> None:
    await _pool.execute("delete from chats where chat_id = $1", chat_id)


async def upsert_member(
    chat_id: int,
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    is_bot: bool,
) -> None:
    await _pool.execute(
        """
        insert into chat_members (chat_id, user_id, username, first_name, last_name, is_bot)
        values ($1, $2, $3, $4, $5, $6)
        on conflict (chat_id, user_id) do update
        set username   = excluded.username,
            first_name = excluded.first_name,
            last_name  = excluded.last_name,
            is_bot     = excluded.is_bot,
            last_seen  = now(),
            left_at    = null
        """,
        chat_id, user_id, username, first_name, last_name, is_bot,
    )


async def mark_member_left(chat_id: int, user_id: int) -> None:
    await _pool.execute(
        """
        update chat_members
        set left_at = now()
        where chat_id = $1 and user_id = $2
        """,
        chat_id, user_id,
    )


async def get_active_members(chat_id: int) -> list[asyncpg.Record]:
    return await _pool.fetch(
        """
        select user_id, username, first_name, last_name
        from chat_members
        where chat_id = $1
          and left_at is null
          and is_bot = false
        """,
        chat_id,
    )
