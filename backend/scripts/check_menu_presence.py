#!/usr/bin/env python3
"""Сверяет каталог с сегодняшним меню сети.

    python3 backend/scripts/check_menu_presence.py mcdonalds

Каталог собран из среза MenuStat 2018. За годы часть блюд снята: у McDonald's
это больше половины позиций. Молча показывать их — та самая претензия, за
которую ругают конкурентов, поэтому отсутствие в меню фиксируется как факт
и доезжает до карточки блюда.

**Мы смотрим национальное меню США.** У McDonald's это mcdonalds.com/us/en-us,
у остальных — их американский сайт. Региональные различия существуют, но
требуют геопозиции и другого источника; MenuStat тоже собирался национально,
так что данные согласованы между собой.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import chick_fil_a, mcdonalds
from plateful_data.adapters.base import Fetcher, curl_get

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"

# Порог намеренно мягкий: ошибочно пометить живое блюдо снятым хуже, чем
# оставить снятое непомеченным. Сомнение — в пользу того, что блюдо есть.
PRESENT_THRESHOLD = 0.78

_SIZE = re.compile(r"\b(small|medium|large|kids?|jr|extra small|child|snack size)\b", re.I)
_MCD_PRODUCT = re.compile(r'/us/en-us/product/([a-z0-9\-]+)\.html')


def normalized(name: str) -> str:
    text = _SIZE.sub(" ", re.sub(r"[^a-z0-9 ]+", " ", name.lower()))
    return " ".join(sorted(text.split()))


def mcdonalds_menu() -> tuple[list[str], str]:
    url = "https://www.mcdonalds.com/us/en-us/full-menu.html"
    page = curl_get(url, mcdonalds.BROWSER_HEADERS)
    if not page:
        return [], url
    return [s.replace("-", " ") for s in sorted(set(_MCD_PRODUCT.findall(page)))], url


def chick_fil_a_menu() -> tuple[list[str], str]:
    fetcher = Fetcher()
    names = []
    for url in chick_fil_a.item_urls(fetcher):
        page = fetcher.get(url)
        if page and (name := chick_fil_a._item_name(page)):
            names.append(name)
    return names, chick_fil_a.MENU_URL


SOURCES = {"mcdonalds": (mcdonalds.CHAIN, mcdonalds_menu),
           "chick-fil-a": (chick_fil_a.CHAIN, chick_fil_a_menu)}


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", choices=sorted(SOURCES))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chain, loader = SOURCES[args.chain]
    live_names, source = loader()
    if not live_names:
        print(f"{chain}: меню не прочиталось, сверять не с чем", file=sys.stderr)
        return 1

    catalog = [i for i in json.loads(PACK.read_text())["items"] if i["chain"] == chain]
    live = [normalized(n) for n in live_names]

    on_menu, off_menu = [], []
    for item in catalog:
        target = normalized(item["name"])
        best = max((difflib.SequenceMatcher(None, target, n).ratio() for n in live),
                   default=0.0)
        (on_menu if best >= PRESENT_THRESHOLD else off_menu).append(item)

    print(f"{chain}: в меню сегодня {len(live_names)} позиций")
    print(f"  из каталога есть:  {len(on_menu)}")
    print(f"  снято с меню:      {len(off_menu)}\n")
    for item in off_menu[:12]:
        print(f"    {item['name'][:46]}")
    if len(off_menu) > 12:
        print(f"    … ещё {len(off_menu) - 12}")

    if args.dry_run:
        return 0

    statements = [
        "insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)\n"
        f"select c.id, {sql_text(item['key'])}, {'true' if present else 'false'},"
        f" {sql_text(source)}, now()\n"
        f"from chains c where c.name = {sql_text(chain)}\n"
        "on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu,"
        " source = excluded.source, checked_at = excluded.checked_at;"
        for present, group in ((True, on_menu), (False, off_menu))
        for item in group]

    out = ROOT / "backend" / "data" / f"presence-{args.chain}.sql"
    out.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    applied = subprocess.run(["supabase", "db", "query", "--linked", "-f", str(out)],
                             capture_output=True, text=True)
    print(f"\nзаписано {len(statements)}" if applied.returncode == 0
          else f"\nSQL не применился: {applied.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
