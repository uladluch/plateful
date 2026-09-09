#!/usr/bin/env python3
"""Ищет свободно лицензированные фотографии реальных блюд сетей.

    python3 backend/scripts/find_photos.py --chain "McDonald's" --top 20

Источник — Openverse: поисковик по изображениям под Creative Commons,
объединяет Flickr CC, Wikimedia Commons, музеи и другие. API открытый,
у каждой картинки известна лицензия и автор.

Ничего не назначается автоматически. Поиск по «Whopper» отдаёт и сам бургер,
и вывеску ресторана, и домашнюю копию — выбирать обязан человек. Скрипт
только собирает кандидатов в таблицу для просмотра.

Лицензии: берём только коммерчески допустимые. BY и BY-SA требуют указать
автора — экран атрибуции обязателен. BY-ND запрещает изменения, а обрезка
под квадрат — уже изменение, поэтому ND не берём.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.base import USER_AGENT

import re

# Размер и количество мешают поиску: фотограф подписывает снимок «Chicken
# McNuggets», а не «10 Chicken McNuggets». Убираем их из запроса, а
# размерные варианты одной позиции ищем один раз.
_PORTION = re.compile(r"\b\d+(\s*(ct|pc|piece|pieces|in|oz|inch))?\b|\b(small|medium|large|kids?|jr\.?|regular|grande|venti|tall)\b|, ?$", re.I)


def search_name(name: str) -> str:
    cleaned = _PORTION.sub(" ", name.split(",")[0].replace("w/", "with"))
    return " ".join(cleaned.split())

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "backend" / "data" / "catalog.json"
OUT = ROOT / "backend" / "data" / "photo-candidates"

API = "https://api.openverse.org/v1/images/"
ALLOWED = {"cc0", "pdm", "by", "by-sa"}   # без nd и nc
PER_ITEM = 4

# Что не ищем: у соусов и ингредиентов фото не нужно, а у напитков картинка
# по архетипу лучше случайного стакана.
SKIP_ARCHETYPES = {"sauce", "ingredients", "cheese", "bacon", "egg", "soda", "water",
                   "milk", "tea", "juice", "drink"}


def search(query: str) -> list[dict]:
    params = {"q": query, "license_type": "commercial", "page_size": 12}
    request = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        results = json.load(response).get("results", [])
    return [r for r in results if r.get("license") in ALLOWED][:PER_ITEM]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", required=True)
    parser.add_argument("--top", type=int, default=20,
                        help="сколько позиций сети взять (по порядку пака)")
    args = parser.parse_args()

    pack = json.loads(PACK.read_text(encoding="utf-8"))
    items = [i for i in pack["items"]
             if i["chain"] == args.chain and i.get("image") not in SKIP_ARCHETYPES]
    if not items:
        print(f"нет позиций у {args.chain}", file=sys.stderr)
        return 1
    items = items[:args.top]

    # Одна выдача на базовое название, не на каждый размер
    seen: dict[str, dict] = {}
    for item in items:
        seen.setdefault(search_name(item["name"]), item)
    items = list(seen.values())

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{args.chain.lower().replace(' ', '-').replace(chr(39), '')}.csv"
    rows = 0

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["item_key", "item", "archetype", "title", "license",
                         "creator", "source", "page", "image_url", "approve"])
        for item in items:
            query = f"{args.chain} {search_name(item['name'])}"
            try:
                found = search(query)
            except Exception as error:
                print(f"  ! {item['name']}: {error}")
                continue
            for r in found:
                writer.writerow([
                    item["key"], item["name"], item.get("image"), (r.get("title") or "")[:80],
                    r.get("license"), r.get("creator") or "", r.get("source"),
                    r.get("foreign_landing_url"), r.get("url"), ""])
                rows += 1
            print(f"  {search_name(item['name'])[:40]:<40} кандидатов: {len(found)}")
            time.sleep(0.7)

    print(f"\n{rows} кандидатов → {out.relative_to(ROOT)}")
    print("Колонка approve: поставьте 1 у снимка, который брать.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
