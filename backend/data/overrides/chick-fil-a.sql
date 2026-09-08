-- Сверка Chick-Fil-A с сайтом сети, 2026-09-08.
-- Сгенерировано audit_chain.py. Правки живут отдельно от данных
-- кроула и переживают его.

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'bacon-egg-cheese-biscuit', '{"carbs": 38.0, "fat": 23.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: carbs: 41→38, fat: 21→23', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'bacon-egg-cheese-muffin', '{"carbs": 28.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: carbs: 32→28', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chick-n-minis', '{"kcal": 360.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 350→360', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chick-fil-a-chicken-biscuit', '{"kcal": 460.0, "protein": 19.0, "carbs": 45.0, "fat": 23.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 450→460, protein: 17→19, carbs: 50→45, fat: 21→23', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'egg-white-grill', '{"protein": 27.0, "carbs": 29.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: protein: 25→27, carbs: 31→29', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'hash-brown-scramble-burrito', '{"kcal": 700.0, "fat": 40.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 680→700, fat: 38→40', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'hash-browns', '{"kcal": 270.0, "fat": 18.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 240→270, fat: 16→18', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'sausage-egg-cheese-biscuit', '{"kcal": 620.0, "protein": 22.0, "carbs": 38.0, "fat": 42.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 600→620, protein: 20→22, carbs: 41→38, fat: 40→42', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chick-fil-a-chicken-sandwich', '{"kcal": 420.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 440→420', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chick-fil-a-deluxe-sandwich', '{"kcal": 490.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 500→490', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chick-fil-a-nuggets', '{"kcal": 250.0, "carbs": 11.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 260→250, carbs: 9→11', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'spicy-deluxe-sandwich', '{"carbs": 47.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: carbs: 43→47', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();

insert into overrides (chain_id, ext_key, patch, reason, author)
select c.id, 'chocolate-chunk-cookie', '{"kcal": 370.0, "source": "chick-fil-a.com", "observed": "2026-09-08", "stale": false}'::jsonb,
       'Сверено с chick-fil-a.com 2026-09-08: kcal: 350→370', 'audit'
from chains c where c.name = 'Chick-Fil-A'
on conflict (chain_id, ext_key) do update
  set patch = excluded.patch, reason = excluded.reason, updated_at = now();
