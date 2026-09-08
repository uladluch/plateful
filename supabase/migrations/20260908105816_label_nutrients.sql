-- Сахар, насыщенные жиры, натрий и клетчатка доезжают до пака.
--
-- Колонки в items были с самого начала, но load_seed.py их не заполнял, а
-- вью не отдавала — данные лежали в источнике и терялись на первом же шаге.
-- Сахар нужен тем, кто его считает; остальное идёт тем же раскрытием и
-- ничего не стоит: 21 CFR 101.11 обязывает сети публиковать всю этикетку,
-- поэтому покрытие 98-100%.

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
      'section',  i.section,
      'serving',  i.serving_text,
      'kcal',     i.kcal,
      'protein',  i.protein,
      'carbs',    i.carbs,
      'fat',      i.fat,
      -- Остальная этикетка. Источник обязан раскрывать её наравне с
      -- калориями (21 CFR 101.11), поэтому она есть почти везде.
      'sugar',    i.sugar,
      'satFat',   i.sat_fat,
      'sodium',   i.sodium,
      'fiber',    i.fiber,
      'kcalMin',  i.kcal_min,
      'kcalMax',  i.kcal_max,
      'source',   i.source,
      'observed', i.observed_at,
      'stale',    nullif(i.stale, false),
      'photo',    case when p.url is null then null else jsonb_strip_nulls(
                    jsonb_build_object(
                      'url',        p.url,
                      'license',    p.license,
                      'licenseUrl', p.license_url,
                      'creator',    p.creator,
                      'title',      p.title,
                      'page',       p.source_page)) end,
      'offMenu',  case when m.on_menu is false then true else null end
    ) || coalesce(o.patch, '{}'::jsonb)
  ) as item
from items i
join chains c on c.id = i.chain_id
left join overrides o on o.chain_id = i.chain_id and o.ext_key = i.ext_key
left join item_photos p on p.chain_id = i.chain_id and p.ext_key = i.ext_key
left join menu_presence m on m.chain_id = i.chain_id and m.ext_key = i.ext_key
where i.valid_to is null;

comment on view items_export is 'Источник для сборки пака: этикетка целиком, правки из overrides, снимки блюд и присутствие в меню.';
