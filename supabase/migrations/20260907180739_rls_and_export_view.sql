-- RLS везде. Политик нет = anon не видит ничего.
-- Конвейер ходит service-ролью, она RLS обходит.
alter table chains        enable row level security;
alter table items         enable row level security;
alter table overrides     enable row level security;
alter table crawls        enable row level security;
alter table releases      enable row level security;
alter table search_events enable row level security;

-- Единственное, что можно из клиента: писать телеметрию поиска.
-- Читать её нельзя — только вставлять.
create policy search_events_insert_anon on search_events
  for insert to anon with check (true);

-- Экспортное представление: текущие позиции с наложенными ручными правками.
create view items_export
with (security_invoker = true) as
select
  c.name as chain,
  jsonb_strip_nulls(
    jsonb_build_object(
      'chain',    c.name,
      'name',     i.name,
      'category', i.category,
      'serving',  i.serving_text,
      'kcal',     i.kcal,
      'protein',  i.protein,
      'carbs',    i.carbs,
      'fat',      i.fat,
      'kcalMin',  i.kcal_min,
      'kcalMax',  i.kcal_max,
      'source',   i.source,
      'observed', i.observed_at,
      'stale',    nullif(i.stale, false)
    ) || coalesce(o.patch, '{}'::jsonb)
  ) as item
from items i
join chains c on c.id = i.chain_id
left join overrides o on o.chain_id = i.chain_id and o.ext_key = i.ext_key
where i.valid_to is null;

comment on view items_export is 'Источник для сборки пака. Правки из overrides накладываются поверх данных кроула.';
