-- Экспортёру нужны ключ позиции и стабильный порядок для постраничной выборки,
-- иначе пак нельзя собрать детерминированно. create or replace не умеет
-- вставлять колонки в начало, поэтому пересоздаём.
drop view if exists items_export;

create view items_export
with (security_invoker = true) as
select
  i.id      as item_id,
  i.ext_key as ext_key,
  c.name    as chain,
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
