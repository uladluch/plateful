-- Фотографии конкретных блюд. Поверх снимков по архетипу.
-- Отдельная таблица, а не колонка в items: снимок не меняется от кроула
-- к кроулу и не должен переписываться вместе с цифрами.
create table item_photos (
  chain_id    bigint not null references chains(id) on delete cascade,
  ext_key     text not null,
  url         text not null,
  license     text not null,
  license_url text,
  creator     text,
  title       text,
  source_page text,
  created_at  timestamptz not null default now(),
  primary key (chain_id, ext_key)
);

alter table item_photos enable row level security;

insert into storage.buckets (id, name, public)
values ('photos', 'photos', true) on conflict (id) do nothing;

create policy photos_public_read on storage.objects
  for select using (bucket_id = 'photos');
-- Вью items_export пересоздаётся с полем photo. Полное определение —
-- в миграции menu_taxonomy: только там оно записано целиком.
