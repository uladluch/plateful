#!/usr/bin/env python3
"""Точки сетей в базу: где стоит ресторан и когда он открыт.

    python3 backend/scripts/import_venues.py                 # все сети RBI
    python3 backend/scripts/import_venues.py burger-king
    python3 backend/scripts/import_venues.py --dry-run        # только показать

Источник — сама сеть. Карта Apple остаётся способом нарисовать местность и
показать карточку места, но список того, что мы показываем, теперь наш:
на карте ровно те заведения, чьё меню приложение умеет открыть.

Пропавшие точки удаляются — закрытый ресторан хуже, чем ненайденный. Но
только если сеть отдала правдоподобное количество: оборванная выгрузка не
должна вычистить базу.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import mcdonalds_venues, rbi_venues, sanity_rbi
from plateful_data.adapters.rbi_venues import Venue

#: Ниже этой доли от того, что уже лежит в базе, выгрузка считается
#: оборванной и ничего не удаляет. Пять процентов — тот же порог, которым
#: `export_pack.py` защищает пак от обеднения.
KEEP_RATIO = 0.95

#: Сколько строк в одном запросе. Шесть тысяч ресторанов одним `values`
#: дают файл на пару мегабайт; частями надёжнее и видно, где оборвалось.
BATCH = 500


#: Сколько раз повторить запрос к базе и с какой паузой.
#:
#: CLI на каждый вызов заводит временную роль, и подряд идущие вызовы —
#: свои ли, из соседней сессии ли — упирают пулер в предохранитель: «too
#: many authentication failures». Это проходит само за десяток секунд.
#: Обход McDonald's идёт два часа, и уронить его на последнем шаге из-за
#: такого — обиднее всего, что тут может случиться.
ATTEMPTS = 5
BACKOFF = 15.0


def run_sql(sql: str) -> list[dict]:
    if not sql.strip():
        return []
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        for attempt in range(1, ATTEMPTS + 1):
            proc = subprocess.run(
                ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json",
                 "-f", path],
                capture_output=True, text=True)
            if proc.returncode == 0:
                start = proc.stdout.find("[")
                return json.loads(proc.stdout[start:]) if start >= 0 else []
            if attempt == ATTEMPTS:
                raise SystemExit(f"supabase db query упал:\n{proc.stderr}")
            print(f"  · база не ответила (попытка {attempt}), жду {BACKOFF:.0f} с")
            time.sleep(BACKOFF * attempt)
    finally:
        Path(path).unlink(missing_ok=True)
    return []


def text(value: object) -> str:
    if value in (None, ""):
        return "null::text"
    return "'" + str(value).replace("'", "''") + "'"


def jsonb(value: object) -> str:
    """Тип пишем даже у пустого значения.

    Без него `values` из одних `null` в колонке получает тип `text`, и
    вставка падает на несовпадении с `jsonb`. У сетей RBI хоть у одной
    точки драйв-тру был заполнен, и тип выводился правильно; у McDonald's
    этой колонки нет ни у кого — и весь обход не записался.
    """
    if not value:
        return "null::jsonb"
    return text(json.dumps(value, ensure_ascii=False, sort_keys=True)) + "::jsonb"


def array(values: tuple[str, ...]) -> str:
    if not values:
        return "'{}'::text[]"
    inner = ", ".join(text(v) for v in values)
    return f"array[{inner}]::text[]"


def row_sql(v: Venue) -> str:
    return (f"({text(v.chain)}, {text(v.ext_key)}, {v.latitude!r}, {v.longitude!r}, "
            f"{text(v.address1)}, {text(v.city)}, {text(v.state)}, "
            f"{text(v.postal_code)}, {text(v.country)}, {text(v.phone)}, "
            f"{jsonb(v.hours)}, {jsonb(v.drive_thru_hours)}, {array(v.amenities)}, "
            f"{text(v.source)})")


def upsert_sql(batch: list[Venue]) -> str:
    """Вставка пачки. Совпало по (сеть, номер магазина) — обновляем.

    `observed_at` обновляется всегда: по нему потом видно, какие точки сеть
    в этот раз не показала, и они удаляются отдельным шагом.
    """
    if not batch:
        return ""
    values = ",\n    ".join(row_sql(v) for v in batch)
    return f"""
insert into venues (chain_id, ext_key, latitude, longitude, address1, city,
                    state, postal_code, country, phone, hours,
                    drive_thru_hours, amenities, source, observed_at)
select c.id, i.ext_key, i.latitude, i.longitude, i.address1, i.city,
       i.state, i.postal_code, i.country, i.phone, i.hours,
       i.drive_thru_hours, i.amenities, i.source, now()
  from (values
    {values}
  ) as i(slug, ext_key, latitude, longitude, address1, city, state,
         postal_code, country, phone, hours, drive_thru_hours, amenities, source)
  join chains c on c.slug = i.slug
on conflict (chain_id, ext_key) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  address1 = excluded.address1,
  city = excluded.city,
  state = excluded.state,
  postal_code = excluded.postal_code,
  country = excluded.country,
  phone = excluded.phone,
  hours = excluded.hours,
  drive_thru_hours = excluded.drive_thru_hours,
  amenities = excluded.amenities,
  source = excluded.source,
  observed_at = now();
"""


def existing(slug: str) -> int:
    rows = run_sql("select count(*) as n from venues v join chains c on c.id = v.chain_id"
                   f" where c.slug = {text(slug)};")
    return int(rows[0]["n"]) if rows else 0


def sweep_sql(slug: str) -> str:
    """Удалить точки, которых сеть в этот раз не показала."""
    return f"""
delete from venues v
 using chains c
 where c.id = v.chain_id
   and c.slug = {text(slug)}
   and v.observed_at < now() - interval '1 hour';
"""


#: Сети, у которых мы умеем брать точки. RBI отдаёт четыре сразу одним
#: датасетом, McDonald's — своим локатором.
KNOWN = list(sanity_rbi.BRANDS) + ["mcdonald-s"]


def fetch(slug: str) -> list[Venue]:
    if slug == "mcdonald-s":
        return mcdonalds_venues.sweep()
    return rbi_venues.fetch(sanity_rbi.BRANDS[slug])


def title(slug: str) -> str:
    brand = sanity_rbi.BRANDS.get(slug)
    return brand.name if brand else "McDonald's"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chains", nargs="*", default=[],
                        help="слаги сетей; без аргументов — все, что умеем")
    parser.add_argument("--dry-run", action="store_true",
                        help="не писать в базу, только показать, что нашлось")
    args = parser.parse_args()

    slugs = args.chains or KNOWN
    unknown = [s for s in slugs if s not in KNOWN]
    if unknown:
        print(f"Не знаю таких сетей: {', '.join(unknown)}. "
              f"Есть: {', '.join(KNOWN)}", file=sys.stderr)
        return 2

    total = 0
    for slug in slugs:
        venues = fetch(slug)
        with_hours = sum(1 for v in venues if v.hours)
        print(f"{title(slug)}: {len(venues)} точек, "
              f"часы у {with_hours} ({100 * with_hours // max(len(venues), 1)}%)")

        if args.dry_run or not venues:
            total += len(venues)
            continue

        was = existing(slug)
        for start in range(0, len(venues), BATCH):
            run_sql(upsert_sql(venues[start:start + BATCH]))

        # Выгрузка заметно беднее прошлой — что-то оборвалось, и удалять
        # по такой нельзя: пусть лучше повисит закрытая точка, чем
        # исчезнет половина сети.
        if was and len(venues) < was * KEEP_RATIO:
            print(f"  было {was}, стало {len(venues)} — пропавшие не удаляю")
        else:
            run_sql(sweep_sql(slug))
        total += len(venues)

    print(f"\nВсего {total} точек")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
