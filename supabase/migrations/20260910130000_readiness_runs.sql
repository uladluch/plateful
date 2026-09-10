-- История готовности: один срез в неделю мало что говорит, важна
-- динамика — кто выпал, кто добавился. Пишет readiness.py --record,
-- читает refresh_chain.py --publish auto: пак не публикуется, если
-- готовых сетей стало меньше, чем в прошлый раз.
create table readiness_runs (
  id       bigint generated always as identity primary key,
  ran_at   timestamptz not null default now(),
  ready    integer not null,
  chains   jsonb not null
);

comment on table readiness_runs is 'Срез readiness.py: ready — сколько сетей прошли порог, chains — по каждой сети доли снимков и свежести.';
