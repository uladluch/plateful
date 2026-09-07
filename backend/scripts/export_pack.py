#!/usr/bin/env python3
"""Собирает пак из базы — с наложенными overrides.

    python3 backend/scripts/export_pack.py --version 2

Отличие от build_seed.py: тот делает bootstrap-пак напрямую из MenuStat и
детерминирован, поэтому CI может сверить его с файлом в бандле. Этот берёт
текущее состояние базы, то есть данные кроулов плюс ручные правки, — именно
он готовит паки для Storage начиная с v2.

Данные тянет через `supabase db query --linked`, которому хватает access-токена
CLI: пароль базы не нужен.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import pack

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
STORAGE_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs/v{v}.deflate"
PAGE = 5000


class Row:
    """Утиный двойник menustat.Item — pack.build читает только эти поля."""
    __slots__ = ("chain", "ext_key", "name", "category", "serving",
                 "kcal", "protein", "carbs", "fat")

    def __init__(self, item: dict, key: str):
        self.chain = item["chain"]
        self.ext_key = key
        self.name = item["name"]
        self.category = item.get("category")
        self.serving = item.get("serving")
        self.kcal = float(item["kcal"])
        self.protein = float(item["protein"])
        self.carbs = float(item["carbs"])
        self.fat = float(item["fat"])


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"supabase db query упал:\n{exc.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)

    start = proc.stdout.index("[")
    return json.loads(proc.stdout[start:])


def fetch_all() -> list[Row]:
    rows: list[Row] = []
    offset = 0
    while True:
        page = query(
            "select ext_key, item from items_export "
            f"order by item_id limit {PAGE} offset {offset};")
        if not page:
            break
        rows.extend(Row(r["item"], r["ext_key"]) for r in page)
        print(f"  получено {len(rows):,}")
        offset += PAGE
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, required=True)
    args = ap.parse_args()

    rows = fetch_all()
    if not rows:
        print("База пуста — сначала load_seed.py", file=sys.stderr)
        return 1
    rows.sort(key=lambda r: (r.chain, r.name))

    built = pack.build(rows, version=args.version, source="plateful-db", observed="")
    meta = pack.write(built,
                      json_path=DATA / f"pack-v{args.version}.json",
                      deflate_path=DATA / f"pack-v{args.version}.deflate")
    (DATA / "manifest.json").write_text(
        json.dumps(pack.manifest(meta, url=STORAGE_URL.format(v=args.version)),
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nПак v{meta['version']}: {meta['itemCount']:,} позиций")
    print(f"  {meta['bytes']/1e6:.2f} MB → deflate {meta['compressedBytes']/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
