#!/usr/bin/env python3
"""Привязки снимков, которые сегодняшнее правило считает чужими.

    python3 backend/scripts/relink_photos.py                 # показать
    python3 backend/scripts/relink_photos.py panera-bread    # одну сеть
    python3 backend/scripts/relink_photos.py --apply         # убрать

Правило сопоставления (`plateful_data.matching`) меняется, а привязки в
`item_photos` остаются такими, какими их поставило прошлое правило. Пока
оно было мягче, «Burritos, Black Olives» получал снимок целого буррито,
а «Farmhouse Egg Sandwich» — снимок «Maplehouse». Здесь такие находятся
и убираются; следом `chain_photos.py <сеть> --apply` ставит то, что даёт
сегодняшнее правило.

Чужая привязка — когда снимок с той же подписью у сети **ещё есть**, а
правило этой позиции его больше не отдаёт: ни его, ни тот же файл под
другим именем. Если снимка у сети уже нет — блюдо сняли, — привязку не
трогаем: она была верной, когда ставилась, и другой не будет.

Запускать одну, не рядом с `chain_photos.py`: обе заводят временную роль
в базе, и от нескольких сразу срабатывает её предохранитель.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from plateful_data import matching
import chain_photos


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    finally:
        Path(path).unlink(missing_ok=True)
    start = proc.stdout.find("[")
    return json.loads(proc.stdout[start:]) if start >= 0 else []


def sql_text(value) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def foreign(slug: str) -> tuple[list[dict], dict[str, dict], dict]:
    """Чужие привязки сети, её каталог и то, что правило даёт теперь."""
    rows = query("select i.ext_key, i.name from items i join chains c on c.id = i.chain_id"
                 f" where c.slug = {sql_text(slug)} and i.valid_to is null;")
    stored = query("select f.chain_id, f.ext_key, f.title from item_photos f"
                   f" join chains c on c.id = f.chain_id where c.slug = {sql_text(slug)};")
    if not rows or not stored:
        return [], {}, {}
    catalog = {r["ext_key"]: r for r in rows}
    _, shots = chain_photos.shots(slug)
    file_of = {s.name: s.image_url.split("?")[0] for s in shots}
    now = matching.photo_pairs(shots, catalog)

    def differs(link: dict) -> bool:
        got = now.get(link["ext_key"])
        return got is None or (got.name != link["title"]
                               and got.image_url.split("?")[0] != file_of[link["title"]])

    wrong = [f for f in stored if f["ext_key"] in catalog and f["title"] in file_of
             and differs(f)]
    return wrong, catalog, now


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chains", nargs="*",
                        help="по умолчанию — все, у кого в chains записан источник снимков")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    total = 0
    for slug in args.chains or chain_photos.with_photo_source():
        try:
            wrong, catalog, now = foreign(slug)
        except SystemExit as stop:
            print(f"{slug:24} источник не открылся: {stop}")
            continue
        if not wrong:
            continue
        total += len(wrong)
        print(f"{slug:24} чужих привязок {len(wrong)}")
        for link in wrong[:6]:
            got = now.get(link["ext_key"])
            print(f"      {catalog[link['ext_key']]['name'][:40]:40}"
                  f" было ← {link['title'][:26]:26}"
                  f" станет ← {got.name[:26] if got else '—'}")
        if args.apply:
            keys = ", ".join(sql_text(link["ext_key"]) for link in wrong)
            query(f"delete from item_photos where chain_id = {wrong[0]['chain_id']}"
                  f" and ext_key in ({keys});")
    print(f"итого: {total} ({'убрано' if args.apply else 'только показ'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
