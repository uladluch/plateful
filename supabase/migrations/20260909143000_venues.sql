-- Точки сетей: где именно стоит ресторан и когда он открыт.
--
-- До этого приложение спрашивало «что рядом» у карты Apple и опознавало
-- ответ по имени. Так нельзя знать заранее, что показываешь: на Таймс-сквер
-- из 48 заведений вокруг опознались две, остальные сорок шесть — чужие сети,
-- которых у нас нет. И наоборот, «Sonic Drive-In» приходилось отличать от
-- «Sonicare» правилом про границу слова. Свой список точек снимает оба
-- вопроса: на карте ровно то, чему у нас есть меню.
--
-- Условия Apple Maps запрещают складывать результаты их поиска в свою базу —
-- и мы этого не делаем: точки берутся у самих сетей, из тех же публичных
-- источников, что и меню. Адрес и часы работы — факты, а не творчество
-- (Feist v. Rural), и сети публикуют их сами.

create table venues (
  id          bigint generated always as identity primary key,
  chain_id    bigint not null references chains(id) on delete cascade,
  -- Номер магазина у самой сети. Он переживает переезд вывески и смену
  -- франчайзи, поэтому ключ обновления — он, а не адрес.
  ext_key     text not null,
  latitude    double precision not null check (latitude between -90 and 90),
  longitude   double precision not null check (longitude between -180 and 180),
  address1    text not null,
  city        text not null,
  state       text,
  postal_code text,
  country     text not null default 'US',
  phone       text,
  -- Часы одной формы для всех сетей: {"mon":{"open":"06:00","close":"23:00"}}.
  -- День без записи — закрыто; сутки напролёт — 00:00/23:59, как отдаёт сеть.
  hours            jsonb,
  -- Драйв-тру работает дольше зала, и человеку у которого нет машины это
  -- меняет ответ. Поэтому вторыми часами, а не вместо первых.
  drive_thru_hours jsonb,
  amenities   text[] not null default '{}',
  source      text not null,
  observed_at timestamptz not null default now(),
  unique (chain_id, ext_key)
);

comment on table venues is 'Заведения сетей. Источник — сама сеть, не карта Apple.';
comment on column venues.amenities is 'drive_thru, delivery, breakfast, wifi, mobile_ordering, parking, playground.';

-- Отбор идёт прямоугольником вокруг человека, поэтому индекс по паре.
create index venues_geo on venues (latitude, longitude);
create index venues_chain on venues (chain_id);

alter table venues enable row level security;
-- Политик нет намеренно: наружу таблица видна только через `venues_near`,
-- и выкачать её целиком одним запросом нельзя.

-- Ценник — свойство сети, а не точки.
--
-- Среднего чека по конкретному ресторану не существует ни в одном открытом
-- источнике. У RBI цены лежат в `restaurantPosData`, но во всём публичном
-- датасете такой документ один и тот пустой: настоящие цены отдаёт только
-- заказной API по конкретному магазину. Yelp ценник отдаёт, но запрещает
-- хранить дольше суток. Поэтому у нас — полоса по сети, проставленная
-- руками, а ценник конкретной точки показывает карточка места Apple.
alter table chains add column price_tier smallint check (price_tier between 1 and 4);
comment on column chains.price_tier is '1 = $, 4 = $$$$. Полоса по сети: среднего чека по точке в открытых источниках нет.';

-- Что рядом: единственная дверь к `venues` для приложения.
--
-- `security definer`, потому что политик на таблице нет: клиенту разрешён
-- этот вопрос и только он — точки вокруг заданной координаты, не больше
-- сотни за раз и не дальше двадцати километров.
--
-- Сети приходят списком от самого клиента: правда о том, чьи меню он умеет
-- показать, лежит в его паке, а не в базе. Пак и база расходятся — в паке
-- едут только готовые сети, — и булавка сети, меню которой не открыть,
-- была бы обманом.
create or replace function public.venues_near(
  lat         double precision,
  lng         double precision,
  radius_m    double precision default 5000,
  only_chains text[] default null,
  max_results integer default 60)
returns table (
  chain            text,
  ext_key          text,
  latitude         double precision,
  longitude        double precision,
  address          text,
  phone            text,
  hours            jsonb,
  drive_thru_hours jsonb,
  amenities        text[],
  distance_m       double precision)
language sql
stable
security definer
set search_path = public
as $$
  with limits as (
    select least(greatest(radius_m, 100), 20000)  as radius,
           least(greatest(max_results, 1), 100)   as cap
  ),
  box as (
    select radius,
           cap,
           radius / 111320.0 as dlat,
           -- На широте 60° градус долготы вдвое короче; косинус снизу
           -- ограничен, чтобы у полюсов не получилось деления на ноль.
           radius / (111320.0 * greatest(cos(radians(lat)), 0.01)) as dlng
      from limits
  ),
  near as (
    select c.name as chain,
           v.ext_key,
           v.latitude,
           v.longitude,
           concat_ws(', ', v.address1, v.city, v.state) as address,
           v.phone,
           v.hours,
           v.drive_thru_hours,
           v.amenities,
           6371000 * 2 * asin(sqrt(
             power(sin(radians(v.latitude - lat) / 2), 2)
             + cos(radians(lat)) * cos(radians(v.latitude))
             * power(sin(radians(v.longitude - lng) / 2), 2))) as distance_m,
           box.radius,
           box.cap
      from venues v
      join chains c on c.id = v.chain_id
      cross join box
     where v.latitude  between lat - box.dlat and lat + box.dlat
       and v.longitude between lng - box.dlng and lng + box.dlng
       and (only_chains is null or c.name = any(only_chains))
  )
  select chain, ext_key, latitude, longitude, address, phone,
         hours, drive_thru_hours, amenities, distance_m
    from near
   where distance_m <= radius
   order by distance_m
   limit (select cap from box);
$$;

comment on function public.venues_near is 'Точки наших сетей вокруг координаты, ближайшие первыми.';

revoke all on function public.venues_near(double precision, double precision,
                                          double precision, text[], integer) from public;
grant execute on function public.venues_near(double precision, double precision,
                                             double precision, text[], integer) to anon, authenticated;
