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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import rbi_venues, sanity_rbi
from plateful_data.adapters.rbi_venues import Venue

#: Ниже этой доли от того, что уже лежит в базе, выгрузка считается
#: оборванной и ничего не удаляет. Пять процентов — тот же порог, которым
#: `export_pack.py` защищает пак от обеднения.
KEEP_RATIO = 0.95

#: Сколько строк в одном запросе. Шесть тысяч ресторанов одним `values`
#: дают файл на пару мегабайт; частями надёжнее и видно, где оборвалось.
BATCH = 500


def run_sql(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json",
             "-f", path],
            capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"supabase db query упал:\n{exc.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)
    start = proc.stdout.find("[")
    return json.loads(proc.stdout[start:]) if start >= 0 else []


def text(value: object) -> str:
    if value in (None, ""):
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def jsonb(value: object) -> str:
    if not value:
        return "null"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chains", nargs="*", default=[],
                        help="слаги сетей; без аргументов — все сети RBI")
    parser.add_argument("--dry-run", action="store_true",
                        help="не писать в базу, только показать, что нашлось")
    args = parser.parse_args()

    slugs = args.chains or list(sanity_rbi.BRANDS)
    unknown = [s for s in slugs if s not in sanity_rbi.BRANDS]
    if unknown:
        print(f"Не знаю таких сетей: {', '.join(unknown)}. "
              f"Есть: {', '.join(sanity_rbi.BRANDS)}", file=sys.stderr)
        return 2

    total = 0
    for slug in slugs:
        brand = sanity_rbi.BRANDS[slug]
        venues = rbi_venues.fetch(brand)
        with_hours = sum(1 for v in venues if v.hours)
        print(f"{brand.name}: {len(venues)} точек, "
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
