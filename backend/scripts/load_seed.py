#!/usr/bin/env python3
"""Заливает seed-пак в Postgres.

    cp backend/.env.example backend/.env   # и вписать SUPABASE_DB_URL
    python3 backend/scripts/load_seed.py

Строку подключения брать в дашборде Supabase: Project Settings → Database →
Connection string → URI (пулер, порт 6543). Она содержит пароль базы, поэтому
живёт только в .env (он в .gitignore) или в GitHub Secrets.

Идемпотентно: сносит прежние строки с source='menustat-2018' и заливает заново.
Данные других источников (адаптеры сетей) не трогает.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"
SOURCE = "menustat-2018"
OBSERVED = "2018-12-31"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", type=Path, default=PACK)
    args = ap.parse_args()

    load_dotenv(ROOT / "backend" / ".env")
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        print("SUPABASE_DB_URL не задан. См. backend/.env.example", file=sys.stderr)
        return 2

    try:
        import psycopg
    except ImportError:
        print("Нужен psycopg: pip install -r backend/requirements.txt", file=sys.stderr)
        return 2

    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    items = pack["items"]
    print(f"Пак v{pack['version']}: {len(items):,} позиций, {len(pack['chains'])} сетей")

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
                               kcal, protein, carbs, fat, source, observed_at, stale)
                   from stdin"""
            ) as copy:
                for i in items:
                    copy.write_row((
                        chain_id[slugify(i["chain"])], i["key"], i["name"],
                        i.get("category"), i.get("serving"),
                        i["kcal"], i["protein"], i["carbs"], i["fat"],
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
