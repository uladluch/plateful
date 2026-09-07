-- Storage: публичный бакет для паков. Клиент читает по прямой ссылке
-- /storage/v1/object/public/packs/…, пишет только конвейер service-ролью.
insert into storage.buckets (id, name, public)
values ('packs', 'packs', true)
on conflict (id) do nothing;

create policy packs_public_read on storage.objects
  for select using (bucket_id = 'packs');

-- search_events принимает anon-вставки, поэтому ограничиваем размер строк:
-- RLS не умеет rate limit, но хотя бы не даст залить мегабайты в одну строку.
alter table search_events
  add constraint search_events_query_len
    check (char_length(query) between 1 and 200),
  add constraint search_events_chain_slug_len
    check (chain_slug is null or char_length(chain_slug) <= 64),
  add constraint search_events_app_version_len
    check (app_version is null or char_length(app_version) <= 32);

-- Индекс назывался trgm, но триграммным не был (btree по lower(name)).
-- Серверного поиска нет — приложение ищет в памяти по паку. Убираем.
drop index if exists items_name_trgm_current;
