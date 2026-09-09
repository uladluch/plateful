#!/usr/bin/env python3
"""Кто из сетей готов к показу, а кому чего не хватает.

    python3 backend/scripts/readiness.py            # у порога и выше
    python3 backend/scripts/readiness.py --all      # все сети

Порог — тот же, что у сборщика пака (`plateful_data.pack`): сеть едет в
приложение целиком или не едет вовсе. Здесь он только показывается, чтобы
было видно, за какую сеть браться следующей и чего именно ей не хватает.
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

SQL = """
select c.name as chain, c.slug,
  count(*) as items,
  count(*) filter (where exists (select 1 from item_photos f
      where f.chain_id = i.chain_id and f.ext_key = i.ext_key)) as photos,
  count(*) filter (where not i.stale) as fresh
from items i join chains c on c.id = i.chain_id
where i.valid_to is null and i.kcal is not null and i.protein is not null
  and i.carbs is not null and i.fat is not null
  and not exists (select 1 from menu_presence p
                  where p.chain_id = i.chain_id and p.ext_key = i.ext_key
                    and p.on_menu is false)
group by c.name, c.slug;
"""


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="показать и безнадёжные")
    args = parser.parse_args()

    rows = query(SQL)
    scored = []
    for row in rows:
        n = row["items"]
        if not n:
            continue
        score = pack.Readiness(n, row["photos"] / n, row["fresh"] / n)
        scored.append((score, row))
    scored.sort(key=lambda pair: (-pair[0].photos, -pair[0].fresh))

    print(f"── Порог: снимки {pack.PHOTO_SHARE:.0%}, свежих {pack.FRESH_SHARE:.0%} ──")
    ready = shown = 0
    for score, row in scored:
        if score.ok:
            ready += 1
        # Безнадёжные — ни одного снимка — прячем: их сотня, и они все
        # ждут одного и того же, источника изображений.
        elif not args.all and score.photos == 0:
            continue
        shown += 1
        need = []
        if score.photos < pack.PHOTO_SHARE:
            need.append(f"снимков ещё {int(row['items'] * pack.PHOTO_SHARE) - row['photos']}")
        if score.fresh < pack.FRESH_SHARE:
            need.append(f"обновить ещё {int(row['items'] * pack.FRESH_SHARE) - row['fresh']}")
        print(f"  {'✓' if score.ok else '·'} {row['slug'][:24]:24} {score}"
              f"   {', '.join(need)}")
    hidden = len(scored) - shown
    print(f"\nГотовы: {ready}. Без единого снимка и потому скрыто: {hidden}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
