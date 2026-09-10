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

from plateful_data import archetype, pack

#: Строки живого меню. В карточки их группирует `pack.readiness` — тем же
#: правилом, что и порог в сборке пака.
SQL = """
select c.name as chain, c.slug, i.name as item,
  coalesce(i.variant_group, c.slug || ':' || i.ext_key) as card,
  (exists (select 1 from item_photos f
     where f.chain_id = i.chain_id and f.ext_key = i.ext_key)) as photo,
  (not i.stale) as fresh
from items i join chains c on c.id = i.chain_id
where i.valid_to is null and i.kcal is not null and i.protein is not null
  and i.carbs is not null and i.fat is not null
  and not exists (select 1 from menu_presence p
                  where p.chain_id = i.chain_id and p.ext_key = i.ext_key
                    and p.on_menu is false);
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
    parser.add_argument("--record", action="store_true",
                        help="записать срез в readiness_runs — для истории и для publish auto")
    args = parser.parse_args()

    rows = query(SQL)
    slugs = {r["chain"]: r["slug"] for r in rows}
    scored = [(score, {"chain": chain, "slug": slugs.get(chain, chain)})
              for chain, score in pack.readiness(
                  (r["chain"], r["card"], r["photo"], r["fresh"], False,
                   archetype.needs_own_photo(r["item"]))
                  for r in rows).items()]
    scored.sort(key=lambda pair: (not pair[0].ok, -pair[0].photos, -pair[0].fresh))

    print(f"── Порог: свежих {pack.FRESH_SHARE:.0%}. Снимки не держат — "
          "показаны, чтобы видеть, за кого браться ──")
    ready = shown = 0
    for score, row in scored:
        if score.ok:
            ready += 1
        # Прячем только тех, кто и не готов, и без единого снимка:
        # сказать про них нечего, кроме «нужен источник».
        elif not args.all and score.photos == 0:
            continue
        shown += 1
        need = []
        without = round(score.dishes * (1 - score.photos))
        if without:
            need.append(f"без снимка {without} блюд")
        if score.fresh < pack.FRESH_SHARE:
            need.append("обновить ещё "
                        f"{int(score.cards * pack.FRESH_SHARE - score.cards * score.fresh) + 1}")
        print(f"  {'✓' if score.ok else '·'} {row['slug'][:24]:24} {score}"
              f"   {', '.join(need)}")
    hidden = len(scored) - shown
    print(f"\nГотовы: {ready}. Не готовы и без единого снимка: {hidden}.")
    if args.record:
        snapshot = {row["slug"]: {"photos": round(score.photos, 3), "fresh": round(score.fresh, 3),
                                  "cards": score.cards, "dishes": score.dishes, "ok": score.ok}
                    for score, row in scored}
        payload = json.dumps(snapshot, ensure_ascii=False).replace("'", "''")
        query(f"insert into readiness_runs (ready, chains) values ({ready}, '{payload}'::jsonb);")
        print("срез записан в readiness_runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
