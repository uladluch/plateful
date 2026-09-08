-- Пометки позиции: детская порция, на компанию, не во всех точках, сезонное.
--
-- Источник держит их нулём и единицей у каждой из 25 836 строк, то есть про
-- каждое блюдо известно точно, а не «может быть». В каталоге пометка есть
-- у 3 591 позиции.
--
-- Массивом, а не пятью булевыми колонками: словарь открытый — адаптеры сетей
-- принесут своё, и добавление термина не должно быть миграцией таблицы. Но
-- и не свободный текст: check держит словарь закрытым для записи, потому что
-- термин, которого клиент не знает, для человека ничего не значит.
--
-- `Combo_Meal` из источника не берём: 166 позиций, и слово «Combo» у
-- большинства и так стоит в названии.

alter table items
  add column flags text[] not null default '{}';

alter table items
  add constraint items_flags_known
  check (flags <@ array['kids','shareable','regional','seasonal']::text[]);

comment on column items.flags is
  'Пометки позиции. Словарь закрыт check-констрейнтом: клиент должен знать термин, иначе он для него ничего не значит. seasonal — «было сезонным на момент снятия», а не «действует до».';

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
      'sugar',       i.sugar,
      'satFat',      i.sat_fat,
      'transFat',    i.trans_fat,
      'cholesterol', i.cholesterol,
      'sodium',      i.sodium,
      'fiber',       i.fiber,
      'flags',    nullif(to_jsonb(i.flags), '[]'::jsonb),
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
