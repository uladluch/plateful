-- WordPress-сети одной выкладкой на строку (adapters/wordpress_menus.LAYOUTS)
-- и Dickey's — JSON прямо в странице меню.
alter table chains drop constraint chains_photo_source_kind_check;
alter table chains add constraint chains_photo_source_kind_check
  check (photo_source_kind in ('olo', 'sanity-rbi', 'sanity-products', 'wordpress-cards', 'contentful-gotofoods', 'collected', 'mcdonalds-snapshot', 'panera-aem', 'starbucks-scene7', 'jerseymikes-api', 'quiznos-site', 'subway-newsroom', 'chickfila-wordpress', 'tacobell-nextjs', 'culvers-nextjs', 'einstein-wordpress', 'dickeys-json'));

update chains set photo_source_kind = 'wordpress-cards', photo_source_url = 'https://www.rubytuesday.com/menu',
  photo_rights = '© Ruby Tuesday, Inc. Used with permission. Source: rubytuesday.com' where slug = 'ruby-tuesday';
update chains set photo_source_kind = 'wordpress-cards', photo_source_url = 'https://www.roundtablepizza.com/menu',
  photo_rights = '© Round Table Pizza, Inc. Used with permission. Source: roundtablepizza.com' where slug = 'round-table-pizza';
update chains set photo_source_kind = 'wordpress-cards', photo_source_url = 'https://www.sbarro.com/menu',
  photo_rights = '© Sbarro LLC. Used with permission. Source: sbarro.com' where slug = 'sbarro';
update chains set photo_source_kind = 'wordpress-cards', photo_source_url = 'https://www.fiveguys.com/menu/',
  photo_rights = '© Five Guys Holdings, Inc. Used with permission. Source: fiveguys.com' where slug = 'five-guys';
update chains set photo_source_kind = 'dickeys-json', photo_source_url = 'https://www.dickeys.com/menu',
  photo_rights = '© Dickey''s Barbecue Restaurants, Inc. Used with permission. Source: dickeys.com' where slug = 'dickey-s-barbeque-pit';
