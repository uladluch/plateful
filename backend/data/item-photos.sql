insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'whopper-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/burger-king--whopper-sandwich.jpg', 'CC0', 'http://creativecommons.org/publicdomain/zero/1.0/deed.en', 'Tokfo', 'Whopper.jpg', 'https://commons.wikimedia.org/wiki/File:Whopper.jpg'
from chains c where c.name = 'Burger King'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;
