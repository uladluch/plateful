#!/usr/bin/env python3
"""Материализует разделы и варианты в базу.

    python3 backend/scripts/sync_taxonomy.py

Правила живут в конвейере (`plateful_data/taxonomy.py`, `variants.py`) и
считаются одинаково для всех 96 сетей — разбирать рестораны по очереди не
нужно. Пак получает их при сборке; этот скрипт кладёт тот же результат в
`items`, чтобы его видел SQL: «сколько у сети завтраков», «все размеры
этого блюда», выборки для поиска по заведениям рядом.

Значения производные. Скрипт перезаписывает их целиком, поэтому запускать
его нужно после каждой правки правил — и до `export_pack.py`, чтобы база и
пак говорили одно и то же.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.taxonomy import section
from plateful_data.variants import assign_groups

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backend" / "data" / "taxonomy-sql"
PAGE = 5000
# Management API не любит гигантские запросы.
CHUNK = 2000


class Row:
    """Утиный двойник menustat.Item — assign_groups читает три поля."""
    __slots__ = ("chain", "ext_key", "name", "category")

    def __init__(self, chain: str, ext_key: str, item: dict):
        self.chain = chain
        self.ext_key = ext_key
        self.name = item["name"]
        self.category = item.get("category")


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as handle:
        handle.write(sql)
        path = handle.name
    try:
        result = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"supabase db query упал:\n{error.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)
    return json.loads(result.stdout[result.stdout.index("["):])


def fetch_all() -> list[Row]:
    rows: list[Row] = []
    offset = 0
    while True:
        page = query("select ext_key, chain, item from items_export "
                     f"order by item_id limit {PAGE} offset {offset};")
        if not page:
            break
        rows.extend(Row(r["chain"], r["ext_key"], r["item"]) for r in page)
        offset += PAGE
    return rows


def literal(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="только записать SQL, не применять")
    args = parser.parse_args()

    rows = fetch_all()
    if not rows:
        print("База пуста — сначала load_seed.py", file=sys.stderr)
        return 1
    print(f"позиций в базе: {len(rows):,}")

    groups = assign_groups(rows)
    values = []
    for row in rows:
        variant = groups.get((row.chain, row.ext_key))
        group, label, order, kind = variant[:4] if variant else (None, None, None, None)
        values.append((row.chain, row.ext_key, section(row.name, row.category),
                       group, label, order, kind))

    sections = sum(1 for v in values if v[2])
    print(f"разделов проставлено {sections:,}, вариантов {len(groups):,}")

    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.sql"):
        stale.unlink()

    chunks = [values[i:i + CHUNK] for i in range(0, len(values), CHUNK)]
    files = []
    for number, chunk in enumerate(chunks, start=1):
        # Явные касты в первой строке: колонка сплошь из NULL иначе получит
        # тип unknown и UPDATE упадёт.
        rendered = []
        for position, value in enumerate(chunk):
            casts = ("text", "text", "text", "text", "text", "smallint", "text")
            rendered.append("(" + ",".join(
                literal(field) + (f"::{cast}" if position == 0 else "")
                for field, cast in zip(value, casts)) + ")")

        path = OUT / f"{number:03d}-taxonomy.sql"
        path.write_text(
            f"-- Сгенерировано sync_taxonomy.py. Кусок {number} из {len(chunks)}.\n"
            "update items i set section = v.section, variant_group = v.variant_group,\n"
            "  variant_label = v.variant_label, variant_order = v.variant_order,\n"
            "  variant_kind = v.variant_kind\n"
            "from (values\n" + ",\n".join(rendered) + "\n"
            ") as v(chain, ext_key, section, variant_group, variant_label,"
            " variant_order, variant_kind)\n"
            "join chains c on c.name = v.chain\n"
            "where i.chain_id = c.id and i.ext_key = v.ext_key and i.valid_to is null;\n",
            encoding="utf-8")
        files.append(path)

    print(f"SQL: {len(files)} файлов в {OUT}")
    if args.dry_run:
        return 0

    for path in files:
        applied = subprocess.run(["supabase", "db", "query", "--linked", "-f", str(path)],
                                 capture_output=True, text=True)
        if applied.returncode != 0:
            print(f"  {path.name}: {applied.stderr.strip()[:200]}", file=sys.stderr)
            return 1
        print(f"  {path.name} применён")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
