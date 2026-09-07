-- Plateful: каталог меню ресторанных сетей.
-- Клиент НИКОГДА не читает эти таблицы напрямую: он качает пак из Storage.
-- Единственная запись из клиента — search_events.

create table chains (
  id          bigint generated always as identity primary key,
  slug        text not null unique,
  name        text not null,
  source_kind text not null default 'seed'
              check (source_kind in ('seed','json_in_html','next_data','json_api','pdf','manual')),
  source_url  text,
  crawl_every interval not null default '7 days',
  status      text not null default 'active'
              check (status in ('active','paused','held')),
  item_count  integer not null default 0,
  last_crawl_at timestamptz,
  created_at  timestamptz not null default now()
);

comment on table chains is 'Сети. crawl_every: ключевые 7 дней, хвост 30 дней.';

-- Позиции меню. Версионируются: valid_to is null = текущая версия.
-- Кроул не перезаписывает строку, а закрывает старую и вставляет новую.
create table items (
  id          bigint generated always as identity primary key,
  chain_id    bigint not null references chains(id) on delete cascade,
  ext_key     text not null,              -- стабильный ключ позиции внутри сети
  name        text not null,
  category    text,
  serving_text text,

  kcal        numeric(7,1),
  protein     numeric(6,1),
  carbs       numeric(6,1),
  fat         numeric(6,1),
  sat_fat     numeric(6,1),
  sodium      numeric(8,1),
  sugar       numeric(6,1),
  fiber       numeric(6,1),

  kcal_min    numeric(7,1),               -- для комбо-диапазонов «730-1010»
  kcal_max    numeric(7,1),

  source      text not null,              -- 'menustat-2018' | 'chick-fil-a.com' | ...
  source_url  text,
  observed_at date,                       -- когда цифра была актуальна у источника
  confidence  numeric(3,2) not null default 1.00,
  stale       boolean not null default false,

  valid_from  timestamptz not null default now(),
  valid_to    timestamptz                 -- null = текущая версия
);

-- Одна текущая версия на позицию
create unique index items_current_uniq on items (chain_id, ext_key) where valid_to is null;
create index items_chain_current on items (chain_id) where valid_to is null;
create index items_name_trgm_current on items (lower(name)) where valid_to is null;

comment on column items.ext_key is 'Стабильный ключ. Overrides цепляются к нему, а не к items.id, чтобы переживать кроулы.';

-- Ручные правки. Живут ОТДЕЛЬНО от items и накладываются при экспорте,
-- поэтому следующий кроул их не затирает.
create table overrides (
  chain_id   bigint not null references chains(id) on delete cascade,
  ext_key    text not null,
  patch      jsonb not null,              -- {"kcal": 580, "fat": 34}
  reason     text not null,
  author     text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (chain_id, ext_key)
);

create table crawls (
  id          bigint generated always as identity primary key,
  chain_id    bigint not null references chains(id) on delete cascade,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  found       integer not null default 0,
  changed     integer not null default 0,
  dropped     integer not null default 0,
  status      text not null default 'running'
              check (status in ('running','ok','held','failed')),
  notes       text
);

create index crawls_chain_recent on crawls (chain_id, started_at desc);

comment on table crawls is 'status=held: дифф не прошёл проверку (>30% изменилось или >20% пропало) — релиз не собирать.';

create table releases (
  version    integer primary key,
  pack_url   text not null,
  sha256     text not null,
  item_count integer not null,
  created_at timestamptz not null default now(),
  notes      text
);

-- Анонимная телеметрия поиска: что искали и нашлось ли.
-- Топ matched=false — приоритет следующего адаптера.
create table search_events (
  id         bigint generated always as identity primary key,
  query      text not null,
  chain_slug text,
  matched    boolean not null,
  app_version text,
  created_at timestamptz not null default now()
);

create index search_events_unmatched on search_events (created_at desc) where not matched;
