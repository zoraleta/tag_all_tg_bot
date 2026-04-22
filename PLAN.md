# План: Telegram-бот «@all»

## Что делаем
Бот, которого можно добавить в любой групповой чат. Когда кто-то пишет `@all` как отдельное слово в сообщении — бот отвечает сообщением, упоминающим всех известных ему участников этого чата.

## Стек
- **Python 3.11+**
- **aiogram 3.x** — основной фреймворк бота (async)
- **asyncpg** — прямое асинхронное подключение к Postgres (Supabase предоставляет connection string)
- **python-dotenv** — загрузка `.env`
- **Supabase** — хостинг Postgres. Через MCP в разработке создаём схему и смотрим данные; сам бот в рантайме ходит в Postgres напрямую через `asyncpg`.

## Ключевое ограничение Telegram
Bot API не отдаёт список всех участников чата. Поэтому бот строит свою базу участников по ходу работы из событий:
- `my_chat_member` — когда бота добавили/удалили из чата;
- `chat_member` — когда участник вступил/вышел (требует включения `chat_member` в `allowed_updates`);
- `message` — любое сообщение от участника (отсюда мы узнаём тех, кто был в чате до появления бота).

Это значит: **бот знает только тех, кто хоть раз что-то написал или вошёл после его добавления**. Молчаливых старожилов он не увидит. Это фундаментальное ограничение платформы, обойти нельзя.

## Требования к настройке бота (вне кода)
- В BotFather **выключить privacy mode** (`/setprivacy` → Disable) — иначе бот не видит обычные сообщения в группах.
- Включить получение `chat_member` апдейтов (делается в коде через `allowed_updates`).

## Схема БД (Supabase / Postgres)
```sql
create table chats (
  chat_id     bigint primary key,
  chat_type   text not null,
  title       text,
  added_at    timestamptz not null default now()
);

create table chat_members (
  chat_id     bigint not null references chats(chat_id) on delete cascade,
  user_id     bigint not null,
  username    text,
  first_name  text,
  last_name   text,
  is_bot      boolean not null default false,
  last_seen   timestamptz not null default now(),
  left_at     timestamptz,
  primary key (chat_id, user_id)
);

create index on chat_members (chat_id) where left_at is null;
```
- `left_at` помечает вышедших — не удаляем, чтобы можно было восстановить историю; для тегания берём `where left_at is null`.
- Ботов (`is_bot = true`) в упоминания не включаем.

## Логика триггера `@all`
- Ловим в тексте сообщения регуляркой: `(?:^|[\s])@all(?=[\s.,!?;:]|$)` — совпадает только если `@all` стоит как отдельное слово, не как часть `@allison` и т.п.
- Регистронезависимо (`@ALL`, `@All` тоже срабатывают).
- Команды/ограничений по правам **нет** (в MVP любой участник может позвать всех).

## Формирование ответного сообщения
- Для пользователей с `@username` — пишем `@username`.
- Для пользователей без `@username` — `text_mention`-ссылка `<a href="tg://user?id=123">Имя</a>` (parse_mode=HTML).
- Автора триггера из списка **исключаем** — смысла пинговать самого себя нет.
- Ботов исключаем.
- Режем на батчи по ~50 упоминаний на сообщение (и следим, чтобы не превысить 4096 символов). Отправляем последовательно с небольшим ответом-заголовком у первого.
- Первое сообщение — реплай на исходное с `@all`.

## Структура проекта
```
tag_all_tg_bot/
├── .env.example
├── .env                   # gitignored (уже в .gitignore Python-шаблон)
├── requirements.txt
├── PLAN.md                # этот файл
├── bot.py                 # точка входа: Dispatcher, polling
├── config.py              # загрузка env: BOT_TOKEN, DATABASE_URL
├── db.py                  # asyncpg pool, функции upsert/select
├── handlers.py            # все хендлеры: my_chat_member, chat_member, message
├── mentions.py            # построение батчей упоминаний
└── migrations/
    └── 001_init.sql       # схема БД (выше)
```

## Этапы реализации
1. **Подготовка Supabase**: через MCP создать проект/таблицы по `001_init.sql`; получить connection string.
2. **`.env.example` + `requirements.txt`**: задать `BOT_TOKEN`, `DATABASE_URL`.
3. **`config.py`**: чтение env, валидация.
4. **`db.py`**: pool-подключение, функции `upsert_chat`, `upsert_member`, `mark_member_left`, `get_active_members(chat_id)`.
5. **`handlers.py`**:
   - `my_chat_member` → upsert/delete чата;
   - `chat_member` → upsert/пометка left;
   - `message` → upsert автора + проверка на `@all` → сборка и отправка тегов.
6. **`mentions.py`**: функция, которая из списка участников собирает список готовых строк-батчей в HTML.
7. **`bot.py`**: Dispatcher, `allowed_updates=["message","my_chat_member","chat_member"]`, polling.
8. **Локальный прогон**: добавить бота в тестовый чат, проверить сценарии:
   - Бота добавили → чат появился в БД.
   - Юзер написал сообщение → юзер появился в БД.
   - Юзер написал `@all` → пришли теги всех активных.
   - Юзер вышел → `left_at` проставлен, в теги не попадает.
   - Слова `@allison`, `email@all.com` **не** триггерят.

## Чего в MVP НЕ делаем (возможные фичи на потом)
- Ограничение «звать всех могут только админы».
- Команда `/all` как альтернатива.
- Антиспам-кулдаун на `@all`.
- Опт-аут пользователей («не пинговать меня»).
- Локализация.
