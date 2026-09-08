insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'big-mac', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--big-mac.jpg', 'CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0', 'Anemonemma, 3df', 'Big Mac.png', 'https://commons.wikimedia.org/wiki/File:Big_Mac.png'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'quarter-pounder-w-cheese', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--quarter-pounder-w-cheese.jpg', 'CC0', 'http://creativecommons.org/publicdomain/zero/1.0/deed.en', 'Evan-Amos', 'McDonald''s Quarter Pounder with Cheese, United States.jpg', 'https://commons.wikimedia.org/wiki/File:McDonald%27s_Quarter_Pounder_with_Cheese,_United_States.jpg'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'mcchicken', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mcchicken.jpg', 'Public domain', null, 'Evan-Amos', 'McD-McChicken (infobox).png', 'https://commons.wikimedia.org/wiki/File:McD-McChicken_(infobox).png'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'egg-mcmuffin', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--egg-mcmuffin.jpg', 'CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0', 'Famartin', '2020-03-30 07 57 37 An Egg McMuffin from McDonald''s in the Franklin Farm section of Oak Hill, Fairfax County, Virginia.jpg', 'https://commons.wikimedia.org/wiki/File:2020-03-30_07_57_37_An_Egg_McMuffin_from_McDonald%27s_in_the_Franklin_Farm_section_of_Oak_Hill,_Fairfax_County,_Virginia.jpg'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, license_url, creator, title, source_page)
select c.id, 'double-cheeseburger', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--double-cheeseburger.jpg', 'CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0', 'Famartin', '2020-10-11 22 12 40 A McDonald''s Double Cheeseburger in the Franklin Farm section of Oak Hill, Fairfax County, Virginia.jpg', 'https://commons.wikimedia.org/wiki/File:2020-10-11_22_12_40_A_McDonald%27s_Double_Cheeseburger_in_the_Franklin_Farm_section_of_Oak_Hill,_Fairfax_County,_Virginia.jpg'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, license_url = excluded.license_url, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;
