-- Hardee's, Carl's Jr и Krystal подключались прямым update в базу, а не
-- миграцией: свежая база из миграций не знала бы, откуда у них снимки.
-- Повторять безопасно — значения те же, что уже лежат.
update chains set photo_source_kind = 'olo', photo_source_url = 'https://www.hardees.com/menu',
  photo_rights = '© Hardee''s Restaurants LLC. Used with permission. Source: hardees.com' where slug = 'hardee-s';
update chains set photo_source_kind = 'olo', photo_source_url = 'https://www.carlsjr.com/menu',
  photo_rights = '© Carl Karcher Enterprises, Inc. Used with permission. Source: carlsjr.com' where slug = 'carl-s-jr';
update chains set photo_source_kind = 'olo', photo_source_url = 'https://www.krystal.com/menu',
  photo_rights = '© The Krystal Company. Used with permission. Source: krystal.com' where slug = 'krystal';
