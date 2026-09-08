insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'apple-slices', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--apple-slices.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Apple Slices No Bag', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'bacon-egg-cheese-bagel', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--bacon-egg-cheese-bagel.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Bacon Egg Cheese Bagel', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'bacon-egg-cheese-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--bacon-egg-cheese-biscuit.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Bacon Egg Cheese Biscuit', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'bacon-egg-cheese-mcgriddles', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--bacon-egg-cheese-mcgriddles.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'EVM HB Bacon Egg Cheese Mc Griddle', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'baked-hot-apple-pie', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--baked-hot-apple-pie.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Baked Apple Pie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'big-breakfast', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--big-breakfast.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Big Breakfast', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'big-breakfast-w-hotcakes', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--big-breakfast-w-hotcakes.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Big Breakfast Hot Cakes', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'big-mac', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--big-mac.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Big Mac', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'cheeseburger', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--cheeseburger.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Cheeseburger Alt Protein', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'chocolate-chip-cookie', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--chocolate-chip-cookie.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Chocolate Chip Cookie Upright', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'diet-coke-extra-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--diet-coke-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Diet Coke', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'diet-coke-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--diet-coke-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Diet Coke', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'diet-coke-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--diet-coke-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Diet Coke', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'diet-coke-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--diet-coke-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Diet Coke', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'double-cheeseburger', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--double-cheeseburger.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Double Cheeseburgerv 2', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'double-quarter-pounder-w-cheese', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--double-quarter-pounder-w-cheese.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Double Quarter Pounderwith Cheese', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'dr-pepper-extra-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--dr-pepper-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Dr Pepper', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'dr-pepper-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--dr-pepper-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Dr Pepper', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'dr-pepper-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--dr-pepper-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Dr Pepper', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'dr-pepper-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--dr-pepper-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Dr Pepper', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'egg-mcmuffin', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--egg-mcmuffin.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Egg Mc Muffin Protein', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hamburger', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hamburger.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Hamburger', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hash-browns', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hash-browns.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Hash Browns Upright', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hot-caramel-sundae', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hot-caramel-sundae.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Caramel Sundae', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hot-fudge-sundae', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hot-fudge-sundae.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Hot Fudge Sundae', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hotcakes', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hotcakes.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', '3 Hot Cakes', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'hotcakes-sausage', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--hotcakes-sausage.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', '3 Hot Cakes Sausage', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-americano-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-americano-medium.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Americano HL', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-americano-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-americano-medium.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Americano HL', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-caramel-frappe-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-caramel-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Caramel Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-caramel-frappe-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-caramel-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Caramel Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-chocolate-shake-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-chocolate-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Chocolate Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-chocolate-shake-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-chocolate-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Chocolate Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-chocolate-shake-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-chocolate-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Chocolate Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-coffee-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-coffee-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Coffee HL', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-coffee-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-coffee-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Coffee HL', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-coffee-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-coffee-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Coffee HL', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-frappe-caramel-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-caramel-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Caramel Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mango-pineapple-smoothie-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mango-pineapple-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mango Pineapple Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mango-pineapple-smoothie-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mango-pineapple-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mango Pineapple Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mango-pineapple-smoothie-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mango-pineapple-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mango Pineapple Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mocha-frappe-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mocha-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mocha Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mocha-frappe-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mocha-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mocha Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-mocha-frappe-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-mocha-frappe-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Mocha Frappe', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-banana-smoothie-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-banana-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Banana Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-banana-smoothie-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-banana-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Banana Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-banana-smoothie-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-banana-smoothie-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Banana Smoothie', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-shake-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-shake-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-strawberry-shake-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-strawberry-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Strawberry Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-vanilla-shake-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-vanilla-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Vanilla Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-vanilla-shake-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-vanilla-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Vanilla Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mccafe-vanilla-shake-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mccafe-vanilla-shake-large.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Vanilla Shake', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mcchicken', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mcchicken.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Mc Chicken', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'mcdouble', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--mcdouble.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Mc Double Protein', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'quarter-pounder-w-cheese', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--quarter-pounder-w-cheese.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Quarter Pounderwith Cheese', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-biscuit', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-biscuit.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Biscuit', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-biscuit-w-egg', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-biscuit-w-egg.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Egg Biscuit', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-burrito', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-burrito.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Burrito Protein', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-egg-cheese-mcgriddles', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-egg-cheese-mcgriddles.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Egg Cheese Mc Griddle', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-mcgriddles', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-mcgriddles.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Mc Griddle', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-mcmuffin', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-mcmuffin.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Mc Muffin', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sausage-mcmuffin-w-egg', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sausage-mcmuffin-w-egg.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sausage Egg Mc Muffin', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sprite-extra-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sprite-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Sprite', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sprite-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sprite-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Sprite', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sprite-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sprite-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Sprite', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sprite-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sprite-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Medium Sprite', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sweet-tea-extra-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sweet-tea-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sweet Tea', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sweet-tea-large', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sweet-tea-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sweet Tea', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sweet-tea-medium', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sweet-tea-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sweet Tea', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'sweet-tea-small', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--sweet-tea-extra-small.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Sweet Tea', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;

insert into item_photos (chain_id, ext_key, url, license, creator, title, source_page)
select c.id, 'vanilla-cone', 'https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos/mcdonalds--vanilla-cone.png', '© McDonald''s Corporation. Used with permission. Source: mcdonalds.com', 'McDonald''s', 'Large Vanilla Cone', 'https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html'
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set url = excluded.url, license = excluded.license, creator = excluded.creator, title = excluded.title, source_page = excluded.source_page;
