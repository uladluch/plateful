#!/usr/bin/env python3
"""Подбирает студийные снимки блюд через Pexels.

    export PEXELS_API_KEY=...        # или строка в backend/.env
    python3 backend/scripts/pexels_dish_photos.py --dry-run
    python3 backend/scripts/pexels_dish_photos.py --only cheeseburger fries

Зачем вместо Wikimedia: там любительские снимки — то, что человек снял
телефоном в зале. На Pexels лежит профессиональная предметная съёмка,
и лицензия разрешает коммерческое использование **без атрибуции**.
Это ровно тот уровень, что у сетей на их собственных сайтах.

Ключ бесплатный и выдаётся сразу: https://www.pexels.com/api/
Лимит 200 запросов в час — на 56 архетипов хватает с запасом.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.archetype import all_archetypes

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plateful" / "Assets.xcassets" / "Dishes"
CREDITS = ROOT / "backend" / "data" / "photo-credits.json"
API = "https://api.pexels.com/v1/search"
SIDE = 800

# Запросы под предметную съёмку: слово «studio» и «white background»
# заметно поднимают долю чистых кадров без интерьера и людей.
QUERIES = {
    "cheeseburger": "cheeseburger studio", "hamburger": "hamburger white background",
    "chicken-sandwich": "fried chicken sandwich", "chicken-nuggets": "chicken nuggets",
    "chicken-strips": "chicken tenders", "chicken-wings": "chicken wings",
    "fried-chicken": "fried chicken", "fries": "french fries",
    "hash-browns": "hash browns", "baked-potato": "baked potato",
    "taco": "tacos", "burrito": "burrito", "bowl": "burrito bowl",
    "pizza": "pizza", "sub-sandwich": "submarine sandwich", "wrap": "wrap sandwich",
    "sandwich": "club sandwich", "breakfast-sandwich": "breakfast sandwich",
    "salad": "fresh salad bowl", "soup": "bowl of soup", "pasta": "pasta dish",
    "steak": "grilled steak", "seafood": "grilled salmon", "ribs": "barbecue ribs",
    "hot-dog": "hot dog", "chips": "tortilla chips", "side-dish": "side dish",
    "side-vegetables": "steamed vegetables", "bread": "bread rolls",
    "bagel": "bagel", "egg": "scrambled eggs", "bacon": "bacon strips",
    "cheese": "cheese slices", "sauce": "dipping sauce", "ingredients": "fresh ingredients",
    "fruit": "fresh fruit bowl", "yogurt": "yogurt parfait", "cookie": "cookies",
    "donut": "donuts", "cake": "cake slice", "dessert": "dessert plate",
    "ice-cream": "ice cream cone", "milkshake": "milkshake", "smoothie": "smoothie",
    "coffee": "coffee cup", "iced-coffee": "iced coffee", "tea": "cup of tea",
    "juice": "orange juice glass", "soda": "cola glass ice", "drink": "soft drink glass",
    "water": "glass of water", "milk": "glass of milk", "slush": "slushie drink",
    "beer": "glass of beer", "wine": "glass of wine", "cocktail": "cocktail",
    "plated-meal": "restaurant plated meal",
}


def api_key() -> str | None:
    if key := os.environ.get("PEXELS_API_KEY"):
        return key
    env = ROOT / "backend" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("PEXELS_API_KEY="):
                return line.partition("=")[2].strip().strip('"').strip("'")
    return None


def search(query: str, key: str) -> list[dict]:
    params = {"query": query, "per_page": 8, "orientation": "square", "size": "medium"}
    request = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}",
                                     headers={"Authorization": key})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response).get("photos", [])


def square(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pick", type=int, default=0, help="какой по счёту снимок брать")
    args = parser.parse_args()

    key = api_key()
    if not key:
        print("Нет PEXELS_API_KEY. Ключ бесплатный: https://www.pexels.com/api/\n"
              "Положите его в backend/.env строкой PEXELS_API_KEY=...", file=sys.stderr)
        return 2

    archetypes = args.only or all_archetypes()
    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    saved = 0

    for archetype in archetypes:
        query = QUERIES.get(archetype, archetype.replace("-", " "))
        try:
            photos = search(query, key)
        except Exception as error:
            print(f"  ! {archetype}: {error}")
            continue
        if not photos:
            print(f"  — {archetype:<20} ничего не нашлось")
            continue

        chosen = photos[min(args.pick, len(photos) - 1)]
        print(f"  {archetype:<20} {chosen['photographer'][:22]:<24} {chosen['alt'][:40]}")
        if args.dry_run:
            time.sleep(0.3)
            continue

        try:
            source = chosen["src"]["large"]
            with urllib.request.urlopen(
                    urllib.request.Request(source, headers={"Authorization": key}),
                    timeout=60) as response:
                image = Image.open(io.BytesIO(response.read())).convert("RGB")
        except Exception as error:
            print(f"    не скачалось: {error}")
            continue

        folder = ASSETS / f"dish-{archetype}.imageset"
        folder.mkdir(parents=True, exist_ok=True)
        square(image).save(folder / "dish.jpg", "JPEG", quality=84, optimize=True)
        (folder / "Contents.json").write_text(json.dumps({
            "images": [{"filename": "dish.jpg", "idiom": "universal", "scale": "1x"},
                       {"idiom": "universal", "scale": "2x"},
                       {"idiom": "universal", "scale": "3x"}],
            "info": {"author": "xcode", "version": 1},
        }, indent=2) + "\n")

        # Pexels атрибуции не требует, но автора сохраняем: захотим показать —
        # данные уже будут, и это просто порядочно.
        credits[archetype] = {"title": chosen.get("alt"), "creator": chosen.get("photographer"),
                              "license": "Pexels licence", "license_url": "https://www.pexels.com/license/",
                              "source": "pexels", "page": chosen.get("url")}
        saved += 1
        time.sleep(0.3)

    if not args.dry_run:
        CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"\nсохранено {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
