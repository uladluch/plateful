-- readiness_runs ушла в прод без RLS.
--
-- Таблица в схеме public, а у anon и authenticated на неё были полные права —
-- их по умолчанию раздаёт схема. Вместе это значило: по адресу проекта и
-- публичному ключу историю готовности можно было прочитать, переписать и
-- стереть. Советник Supabase поймал это как rls_disabled_in_public 2026-09-13.
--
-- Модель та же, что у остальных таблиц конвейера: RLS включён, политик нет.
-- Пишет readiness.py --record, читает refresh_chain.py --publish auto — оба
-- через CLI от имени postgres, у которого bypassrls, так что конвейер этого
-- не заметит. Клиенту таблица не нужна вовсе.
alter table public.readiness_runs enable row level security;

-- Права снимаем тоже, чтобы защита не держалась на одном RLS: TRUNCATE,
-- например, RLS не подчиняется совсем.
revoke all on table public.readiness_runs from anon, authenticated;

-- Идентификатор берётся из последовательности, и права на неё раздаются
-- так же. Имя спрашиваем у базы, а не пишем по памяти.
do $$
declare
  seq text := pg_get_serial_sequence('public.readiness_runs', 'id');
begin
  if seq is not null then
    execute format('revoke all on sequence %s from anon, authenticated', seq);
  end if;
end
$$;
