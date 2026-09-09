#!/usr/bin/env python3
"""Заливает seed-пак в Postgres. Два режима.

1. Через Supabase CLI — пароль базы не нужен, CLI поднимает временную роль
   по своему access-токену. Так удобнее всего локально:

       python3 backend/scripts/load_seed.py --emit-sql backend/data/seed-sql
       for f in backend/data/seed-sql/*.sql; do supabase db query --linked -f "$f"; done

2. Напрямую по строке подключения — быстрее (COPY одной командой), для CI:

       cp backend/.env.example backend/.env   # и вписать SUPABASE_DB_URL
       python3 backend/scripts/load_seed.py

Строку подключения брать в дашборде: Project Settings → Database →
Connection string → URI (пулер, порт 6543). Она содержит пароль базы, поэтому
живёт только в .env (он в .gitignore) или в GitHub Secrets.

Оба режима идемпотентны: сносят прежние строки с source='menustat-2018'
и заливают заново. Данные других источников (адаптеры сетей) не трогают.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.slug import slugify


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "backend" / "data" / "catalog.json"
SOURCE = "menustat-2018"
OBSERVED = "2018-12-31"


# Management API не любит гигантские запросы, поэтому SQL режем на куски.
CHUNK = 2500

COLUMNS = ("chain_id", "ext_key", "name", "category", "serving_text",
           "kcal", "protein", "carbs", "fat",
           "sugar", "sat_fat", "trans_fat", "cholesterol", "sodium", "fiber",
           "flags", "source", "observed_at", "stale")


def sql_literal(value, cast: str | None = None) -> str:
    if value is None:
        return f"NULL::{cast}" if cast else "NULL"
    if isinstance(value, (int, float)):
        text = repr(value)
    else:
        text = "'" + str(value).replace("'", "''") + "'"
    return f"{text}::{cast}" if cast else text


def sql_array(values, cast: str | None = None) -> str:
    """Литерал text[]. Пустой массив — не NULL: колонка объявлена not null."""
    inner = ",".join('"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'
                     for v in values or ())
    literal = "'{" + inner + "}'"
    return f"{literal}::{cast}" if cast else literal


def emit_sql(items: list[dict], out_dir: Path) -> list[Path]:
    """SQL-файлы для `supabase db query --linked -f`.

    chain_id не хардкодим: сети уже в базе, соединяемся по slug. Поэтому
    файлы переживают пересоздание базы с другими id.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in out_dir.glob("*.sql"):
        stale_file.unlink()

    written: list[Path] = []
    chunks = [items[i:i + CHUNK] for i in range(0, len(items), CHUNK)]

    head = out_dir / "000-reset.sql"
    head.write_text(
        "-- Сгенерировано load_seed.py --emit-sql. Руками не править.\n"
        f"delete from items where source = '{SOURCE}';\n", encoding="utf-8")
    written.append(head)

    for n, chunk in enumerate(chunks, start=1):
        rows = []
        for pos, i in enumerate(chunk):
            # В первой строке — явные касты: иначе колонка сплошь из NULL
            # получит тип unknown и INSERT упадёт.
            cast = (lambda t: t if pos == 0 else None)
            rows.append("(" + ",".join((
                sql_literal(slugify(i["chain"]), cast("text")),
                sql_literal(i["key"], cast("text")),
                sql_literal(i["name"], cast("text")),
                sql_literal(i.get("category"), cast("text")),
                sql_literal(i.get("serving"), cast("text")),
                sql_literal(i["kcal"], cast("numeric")),
                sql_literal(i["protein"], cast("numeric")),
                sql_literal(i["carbs"], cast("numeric")),
                sql_literal(i["fat"], cast("numeric")),
                sql_literal(i.get("sugar"), cast("numeric")),
                sql_literal(i.get("satFat"), cast("numeric")),
                sql_literal(i.get("transFat"), cast("numeric")),
                sql_literal(i.get("cholesterol"), cast("numeric")),
                sql_literal(i.get("sodium"), cast("numeric")),
                sql_literal(i.get("fiber"), cast("numeric")),
                sql_array(i.get("flags"), cast("text[]")),
            )) + ")")

        path = out_dir / f"{n:03d}-items.sql"
        path.write_text(
            f"-- Сгенерировано load_seed.py --emit-sql. Кусок {n} из {len(chunks)}.\n"
            f"insert into items ({', '.join(COLUMNS)})\n"
            "select c.id, v.ext_key, v.name, v.category, v.serving_text,\n"
            "       v.kcal, v.protein, v.carbs, v.fat,\n"
            "       v.sugar, v.sat_fat, v.trans_fat, v.cholesterol,"
            " v.sodium, v.fiber, v.flags,\n"
            f"       '{SOURCE}', date '{OBSERVED}', true\n"
            "from (values\n" + ",\n".join(rows) + "\n"
            ") as v(chain_slug, ext_key, name, category, serving_text,"
            " kcal, protein, carbs, fat, sugar, sat_fat, trans_fat,"
            " cholesterol, sodium, fiber, flags)\n"
            "join chains c on c.slug = v.chain_slug;\n", encoding="utf-8")
        written.append(path)

    tail = out_dir / "999-counts.sql"
    tail.write_text(
        "update chains c set item_count = coalesce(sub.n, 0)\n"
        "from (select chain_id, count(*) n from items where valid_to is null\n"
        "      group by chain_id) sub\n"
        "where sub.chain_id = c.id;\n"
        "select count(*) as items_current from items where valid_to is null;\n",
        encoding="utf-8")
    written.append(tail)
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", type=Path, default=PACK)
    ap.add_argument("--emit-sql", type=Path, metavar="DIR",
                    help="не подключаться к базе, а записать SQL для supabase db query")
    args = ap.parse_args()

    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    items = pack["items"]
    print(f"Пак v{pack['version']}: {len(items):,} позиций, {len(pack['chains'])} сетей")

    if args.emit_sql:
        files = emit_sql(items, args.emit_sql)
        print(f"SQL: {len(files)} файлов в {args.emit_sql}")
        print("Применить:  for f in %s/*.sql; do supabase db query --linked -f \"$f\"; done"
              % args.emit_sql)
        return 0

    try:
        import psycopg
        from dotenv import load_dotenv
    except ImportError as exc:
        raise SystemExit(f"{exc.name} не установлен: pip install -r backend/requirements.txt"
                         " (или используйте --emit-sql, ему зависимости не нужны)")

    load_dotenv(ROOT / "backend" / ".env")
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        print("SUPABASE_DB_URL не задан. См. backend/.env.example,"
              " либо используйте --emit-sql", file=sys.stderr)
        return 2

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Сети: заводим недостающие, существующие не трогаем.
            cur.executemany(
                """insert into chains (name, slug, source_kind)
                   values (%s, %s, 'seed') on conflict (slug) do nothing""",
                [(c["name"], slugify(c["name"])) for c in pack["chains"]],
            )
            cur.execute("select slug, id from chains")
            chain_id = dict(cur.fetchall())

            missing = {i["chain"] for i in items if slugify(i["chain"]) not in chain_id}
            if missing:
                print(f"Сети не найдены: {sorted(missing)[:5]}", file=sys.stderr)
                return 1

            cur.execute("delete from items where source = %s", (SOURCE,))
            print(f"  снято прежних seed-строк: {cur.rowcount:,}")

            with cur.copy(
                """copy items (chain_id, ext_key, name, category, serving_text,
                               kcal, protein, carbs, fat,
                               sugar, sat_fat, trans_fat, cholesterol,
                               sodium, fiber, flags,
                               source, observed_at, stale)
                   from stdin"""
            ) as copy:
                for i in items:
                    copy.write_row((
                        chain_id[slugify(i["chain"])], i["key"], i["name"],
                        i.get("category"), i.get("serving"),
                        i["kcal"], i["protein"], i["carbs"], i["fat"],
                        i.get("sugar"), i.get("satFat"),
                        i.get("transFat"), i.get("cholesterol"),
                        i.get("sodium"), i.get("fiber"),
                        i.get("flags") or [],
                        SOURCE, OBSERVED, True,
                    ))

            cur.execute("""update chains c set item_count = sub.n
                           from (select chain_id, count(*) n from items
                                 where valid_to is null group by chain_id) sub
                           where sub.chain_id = c.id""")
            cur.execute("select count(*) from items where valid_to is null")
            total = cur.fetchone()[0]
        conn.commit()

    print(f"Готово: {total:,} текущих позиций в базе")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
