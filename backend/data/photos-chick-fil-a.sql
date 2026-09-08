insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'bacon-egg-cheese-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--bacon-egg-cheese-biscuit.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Bacon, Egg & Cheese Biscuit Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/bacon-egg-cheese-biscuit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'bacon-egg-cheese-muffin', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--bacon-egg-cheese-muffin.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Bacon, Egg & Cheese Muffin Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/bacon-egg-cheese-muffin'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-n-minis', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-n-minis.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A Chick-n-Minis® Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/chick-fil-a-chick-n-minis'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-chicken-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-chicken-biscuit.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A® Chicken Biscuit Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/chick-fil-a-chicken-biscuit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'egg-white-grill', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--egg-white-grill.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Egg White Grill Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/egg-white-grill'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hash-brown-scramble-bowl', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--hash-brown-scramble-bowl.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Hash Brown Scramble Bowl Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/hash-brown-scramble-bowl'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hash-brown-scramble-burrito', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--hash-brown-scramble-burrito.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Hash Brown Scramble Burrito Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/hash-brown-scramble-burrito'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hash-browns', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--hash-browns.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Hash Browns Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/hash-browns'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-egg-cheese-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--sausage-egg-cheese-biscuit.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Sausage, Egg & Cheese Biscuit Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/sausage-egg-cheese-biscuit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-chicken-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-chicken-biscuit.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Spicy Chicken Biscuit Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/breakfast/spicy-chicken-biscuit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hot-coffee', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--hot-coffee.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Hot Coffee', 'https://www.chick-fil-a.com/menu/coffee/coffee'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'avocado-lime-ranch-dressing', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--avocado-lime-ranch-dressing.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Avocado Lime Ranch Dressing', 'https://www.chick-fil-a.com/menu/dressings/avocado-lime-ranch-dressing'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'creamy-salsa-dressing', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--creamy-salsa-dressing.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Creamy Salsa Dressing', 'https://www.chick-fil-a.com/menu/dressings/creamy-salsa-dressing'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-chicken-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-chicken-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A® Chicken Sandwich', 'https://www.chick-fil-a.com/menu/entrees/chick-fil-a-chicken-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-deluxe-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-deluxe-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A® Deluxe Sandwich', 'https://www.chick-fil-a.com/menu/entrees/chick-fil-a-deluxe-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'grilled-chicken-club-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--grilled-chicken-club-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A® Grilled Chicken Club Sandwich', 'https://www.chick-fil-a.com/menu/entrees/chick-fil-a-grilled-chicken-club-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-nuggets', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-nuggets.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chick-fil-A Nuggets', 'https://www.chick-fil-a.com/menu/entrees/chick-fil-a-nuggets'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'grilled-chicken-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--grilled-chicken-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Grilled Chicken Sandwich', 'https://www.chick-fil-a.com/menu/entrees/grilled-chicken-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chick-fil-a-chicken-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chick-fil-a-chicken-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Spicy Chicken Sandwich', 'https://www.chick-fil-a.com/menu/entrees/spicy-chicken-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'spicy-deluxe-sandwich', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--spicy-deluxe-sandwich.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Spicy Deluxe Sandwich', 'https://www.chick-fil-a.com/menu/entrees/spicy-deluxe-sandwich'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'cobb-salad', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--cobb-salad.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Cobb Salad Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/salads/cobb-salad'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'spicy-southwest-salad', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--spicy-southwest-salad.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Spicy Southwest Salad Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/salads/spicy-southwest-salad'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chicken-noodle-soup', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chicken-noodle-soup.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chicken Noodle Soup Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/sides/chicken-noodle-soup'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'side-salad', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--side-salad.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Side Salad Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/sides/side-salad'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chocolate-chunk-cookie', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/chick-fil-a--chocolate-chunk-cookie.png', '© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com', 'Chick-Fil-A', 'Chocolate Chunk Cookie Nutrition and Ingredients', 'https://www.chick-fil-a.com/menu/treats/chocolate-chunk-cookie'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;
