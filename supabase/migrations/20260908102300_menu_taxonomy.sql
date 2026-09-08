-- Раздел меню и вариант блюда — рядом с позицией, а не только в паке.
--
-- Правила считает конвейер (plateful_data/taxonomy.py и variants.py): они
-- общие для всех 96 сетей, и разбирать рестораны по очереди не нужно.
-- Результат материализуется сюда, чтобы его видел SQL: «сколько у сети
-- завтраков», «все размеры этого блюда», выборки для будущего поиска по
-- заведениям рядом. Пак и база тогда говорят одно и то же.
--
-- Значения производные: их перезаписывает sync_taxonomy.py после каждого
-- изменения правил. Руками не править — правка переживёт ровно до
-- следующего прогона.

alter table items
  add column section       text,
  add column variant_group text,
  add column variant_label text,
  add column variant_order smallint,
  add column variant_kind  text check (variant_kind in ('size','option'));

comment on column items.section is
  'Раздел меню: категория источника, а поверх неё выделенный завтрак.';
comment on column items.variant_group is
  'Ключ группы вариантов внутри сети. Позиции с одним ключом — одно блюдо.';

-- Собрать все варианты блюда — самый частый запрос к этим колонкам.
create index items_variant_group_idx on items (chain_id, variant_group)
  where variant_group is not null;
create index items_section_idx on items (chain_id, section);

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
      'kcalMin',  i.kcal_min,
      'kcalMax',  i.kcal_max,
      'source',   i.source,
      'observed', i.observed_at,
      'stale',    nullif(i.stale, false),
      -- Снимок конкретного блюда. Лицензия обязательна: она условие, на
      -- котором сеть разрешила использование.
      'photo',    case when p.url is null then null else jsonb_strip_nulls(
                    jsonb_build_object(
                      'url',        p.url,
                      'license',    p.license,
                      'licenseUrl', p.license_url,
                      'creator',    p.creator,
                      'title',      p.title,
                      'page',       p.source_page)) end,
      -- Позиции больше нет в меню сети. Приходит только когда это правда:
      -- «есть в меню» для каждой из 25 тысяч позиций возить незачем.
      'offMenu',  case when m.on_menu is false then true else null end
    ) || coalesce(o.patch, '{}'::jsonb)
  ) as item
from items i
join chains c on c.id = i.chain_id
left join overrides o on o.chain_id = i.chain_id and o.ext_key = i.ext_key
left join item_photos p on p.chain_id = i.chain_id and p.ext_key = i.ext_key
left join menu_presence m on m.chain_id = i.chain_id and m.ext_key = i.ext_key
where i.valid_to is null;

comment on view items_export is 'Источник для сборки пака: цифры, правки из overrides, снимки блюд и присутствие в меню.';
