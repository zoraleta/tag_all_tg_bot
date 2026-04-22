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

create index chat_members_active_idx on chat_members (chat_id) where left_at is null;
