-- Общий Sanity: проект и набор данных — в photo_source_url, а не в коде.
-- Список видов — из adapters/photo_sources.KINDS (sql_check()).
alter table chains drop constraint chains_photo_source_kind_check;
alter table chains add constraint chains_photo_source_kind_check
  check (photo_source_kind in ('olo', 'sanity-rbi', 'sanity-products', 'contentful-gotofoods', 'collected', 'mcdonalds-snapshot', 'panera-aem', 'starbucks-scene7', 'jerseymikes-api', 'quiznos-site', 'subway-newsroom', 'chickfila-wordpress', 'tacobell-nextjs', 'culvers-nextjs', 'einstein-wordpress'));

update chains set photo_source_kind = 'sanity-products',
  photo_source_url = 'https://9tlw6prn.apicdn.sanity.io/v2021-10-21/data/query/production',
  photo_rights = '© Krispy Kreme Doughnut Corporation. Used with permission. Source: krispykreme.com'
  where slug = 'krispy-kreme';
update chains set photo_source_kind = 'olo',
  photo_source_url = 'https://www.papamurphys.com/menu',
  photo_rights = '© Papa Murphy''s International LLC. Used with permission. Source: papamurphys.com'
  where slug = 'papa-murphy-s';
