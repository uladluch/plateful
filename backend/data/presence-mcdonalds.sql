insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '1-low-fat-milk-jug', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '10-chicken-mcnuggets', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '20-chicken-mcnuggets', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '4-chicken-mcnuggets', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '40-chicken-mcnuggets', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '6-chicken-mcnuggets', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'apple-slices', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-egg-cheese-bagel', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-egg-cheese-biscuit', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-egg-cheese-mcgriddles', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'baked-hot-apple-pie', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'big-breakfast', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'big-breakfast-w-hotcakes', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'big-mac', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'cheeseburger', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'chocolate-chip-cookie', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'coca-cola-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'coca-cola-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'coca-cola-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'coca-cola-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'creamy-ranch-sauce', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'dasani-water', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-coke-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-coke-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-coke-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-coke-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-dr-pepper-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-dr-pepper-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-dr-pepper-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'diet-dr-pepper-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'double-cheeseburger', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'double-quarter-pounder-w-cheese', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'dr-pepper-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'dr-pepper-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'dr-pepper-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'dr-pepper-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'egg-mcmuffin', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'filet-o-fish', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'french-fries-kids', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'french-fries-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'french-fries-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'french-fries-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fruit-maple-oatmeal', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hamburger', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hash-browns', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'honey', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'honey-mustard-sauce', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hot-caramel-sundae', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hot-fudge-sundae', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hotcakes', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'hotcakes-sausage', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'iced-tea-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'iced-tea-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'iced-tea-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'iced-tea-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'ketchup-packet', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-frappe-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-frappe-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-chocolate-shake-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-chocolate-shake-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-chocolate-shake-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-coffee-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-coffee-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-coffee-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-frappe-caramel-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mango-pineapple-smoothie-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mango-pineapple-smoothie-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mango-pineapple-smoothie-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-banana-smoothie-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-banana-smoothie-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-banana-smoothie-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-shake-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-shake-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-strawberry-shake-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-vanilla-shake-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-vanilla-shake-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-vanilla-shake-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcchicken', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcdouble', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcflurry-w-oreo-cookies-snack-size', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'quarter-pounder-w-cheese', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-biscuit', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-biscuit-w-egg', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-burrito', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-mcgriddles', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-mcmuffin', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-mcmuffin-w-egg', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sausage-egg-cheese-mcgriddles', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'spicy-buffalo-sauce', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sprite-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sprite-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sprite-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sprite-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'steak-egg-cheese-biscuit', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-n-sour-sauce', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-tea-extra-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-tea-large', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-tea-medium', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-tea-small', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'tangy-barbeque-sauce', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'triple-cheeseburger', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'vanilla-cone', true, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '1-4-lb-pico-guacamole-burger', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '1-4-lb-sweet-bbq-bacon-burger', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '10-buttermilk-crispy-tenders', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '2-buttermilk-crispy-tenders', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '4-buttermilk-crispy-tenders', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, '6-buttermilk-crispy-tenders', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'artisan-grilled-chicken-sandwich', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-mcdouble', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-ranch-grilled-chicken-salad', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'bacon-ranch-salad-w-buttermilk-crispy-chicken', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'big-mac-sauce', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'buttermilk-crispy-chicken-sandwich', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'classic-chicken-sandwich', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'egg-white-delight-mcmuffin', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-10-pc-nuggets-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-20-pc-nuggets-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-4-pc-nuggets-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-40-pc-nuggets-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-6-pc-nuggets-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-artisan-grilled-chicken-sandwich-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-bacon-egg-cheese-biscuit', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-bacon-egg-cheese-mcgriddles', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-bacon-egg-cheese-mcgriddles-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-big-mac-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-buttermilk-crispy-chicken-sandwich-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-double-quarter-pounder-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-egg-mcmuffin', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-egg-mcmuffin-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-filet-o-fish-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-large-bacon-egg-cheese-biscuit-small-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-large-sausage-biscuit-egg-small-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-quarter-pounder-medium-coke-medium-fries', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-regular-bacon-egg-cheese-biscuit-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-regular-sausage-biscuit-egg-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-biscuit', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-burrito-small-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-mcgriddles', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-mcgriddles-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-mcmuffin', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-mcmuffin-egg-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-egg-cheese-mcgriddles', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'extra-value-meal-w-sausage-egg-cheese-mcgriddles-medium-coffee', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fanta-orange-extra-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fanta-orange-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fanta-orange-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fanta-orange-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fat-free-chocolate-milk-jug', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'fruit-n-yogurt-parfait', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'habanero-ranch-sauce', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'honest-kids-appley-ever-after-organic-juice-drink', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'kiddie-cone', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mayonnaise', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-americano-w-espresso-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-americano-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-americano-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-cappuccino-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-cappuccino-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-cappuccino-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-cappuccino-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-cappuccino-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-cappuccino-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-iced-coffee-w-light-cream-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-iced-coffee-w-light-cream-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-iced-coffee-w-light-cream-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-latte-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-latte-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-latte-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-macchiato-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-macchiato-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-macchiato-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-caramel-mocha-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-frappe-chocolate-chip-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-frappe-chocolate-chip-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-frappe-chocolate-chip-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-cappuccino-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-cappuccino-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-cappuccino-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-iced-coffee-w-light-cream-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-iced-coffee-w-light-cream-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-iced-coffee-w-light-cream-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-latte-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-latte-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-french-vanilla-latte-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-hot-chocolate-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-iced-caramel-mocha-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-iced-coffee-w-light-cream-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-iced-latte-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-iced-mocha-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-latte-w-whole-milk-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-latte-w-whole-milk-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-latte-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mocha-frappe-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mocha-frappe-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mocha-frappe-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mccafe-mocha-w-whole-milk-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcflurry-w-m-ms-candies-regular-size', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcflurry-w-m-ms-candies-snack-size', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mcflurry-w-oreo-cookies-regular-size', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'mustard', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'newmans-own-creamy-french-dressing', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'newmans-own-creamy-southwest-dressing', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'newmans-own-low-fat-balsamic-vinaigrette', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'newmans-own-low-fat-family-recipe-italian-dressing', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'newmans-own-ranch-dressing', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'oatmeal-raisin-cookie', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'powerade-mountain-berry-blast-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'pico-guacamole-w-artisan-grilled-chicken', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'pico-guacamole-w-buttermilk-crispy-chicken', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'powerade-mountain-berry-blast-extra-small', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'powerade-mountain-berry-blast-large', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'powerade-mountain-berry-blast-medium', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'side-salad', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'signature-sauce', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'southwest-buttermilk-crispy-chicken-salad', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'southwest-grilled-chicken-salad', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'strawberry-cream-pie', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'strawberry-sundae', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-bbq-bacon-w-artisan-grilled-chicken', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'sweet-bbq-bacon-w-buttermilk-crispy-chicken', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'tartar-sauce-cup', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;

insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)
select c.id, 'yoplait-go-gurt-low-fat-strawberry-yogurt', false, 'https://www.mcdonalds.com/us/en-us/full-menu.html', now()
from chains c where c.name = 'McDonald''s'
on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu, source = excluded.source, checked_at = excluded.checked_at;
