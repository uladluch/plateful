#!/usr/bin/env python3
"""Подбирает по одной фотографии на каждый архетип блюда.

    python3 backend/scripts/pick_dish_photos.py            # все архетипы
    python3 backend/scripts/pick_dish_photos.py --only cheeseburger fries
    python3 backend/scripts/pick_dish_photos.py --dry-run  # только показать выбор

Источник — Openverse (Flickr CC, Wikimedia и другие). Берём только лицензии,
разрешающие коммерческое использование и переработку: cc0, pdm, by, by-sa.
`by-nd` запрещает изменения, а мы кадрируем в квадрат — это изменение.

Кандидаты оцениваются, а не берутся первым попавшимся: по запросу «fries»
приходят и вывески, и упаковка, и логотипы. Совпадение по тегам ценится выше
совпадения в заголовке — теги ставит автор снимка, а заголовок бывает шуткой.

Автор и лицензия каждого снимка попадают в backend/data/photo-credits.json,
из него собирается экран атрибуции в приложении: by и by-sa этого требуют.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.adapters.base import USER_AGENT
from plateful_data.archetype import all_archetypes

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plateful" / "Assets.xcassets" / "Dishes"
CREDITS = ROOT / "backend" / "data" / "photo-credits.json"

API = "https://api.openverse.org/v1/images/"
ALLOWED_LICENSES = {"cc0", "pdm", "by", "by-sa"}
SIDE = 320          # квадрат под строку списка и карточку
MIN_WIDTH = 500

# Запрос на архетип. Голое имя архетипа ищется плохо: «bowl» приводит
# к посуде, «drink» — к барным стойкам.
QUERIES = {
    "bacon": "bacon strips cooked",
    "bagel": "bagel bread",
    "baked-potato": "baked potato",
    "beer": "glass of beer",
    "bowl": "burrito bowl rice",
    "bread": "bread rolls bakery",
    "breakfast-sandwich": "breakfast sandwich egg muffin",
    "burrito": "burrito wrapped",
    "cake": "slice of cake dessert",
    "cheese": "cheese slices",
    "cheeseburger": "cheeseburger",
    "chicken-nuggets": "chicken nuggets",
    "chicken-sandwich": "fried chicken sandwich",
    "chicken-strips": "chicken tenders strips",
    "chicken-wings": "chicken wings",
    "chips": "tortilla chips",
    "cocktail": "cocktail glass",
    "coffee": "cup of coffee latte",
    "cookie": "chocolate chip cookies",
    "dessert": "dessert plate",
    "donut": "donuts glazed",
    "drink": "soft drink glass ice",
    "egg": "scrambled eggs",
    "fried-chicken": "fried chicken pieces",
    "fries": "french fries",
    "fruit": "fresh fruit",
    "hamburger": "hamburger",
    "hash-browns": "hash browns potato",
    "hot-dog": "hot dog",
    "ice-cream": "ice cream cone",
    "iced-coffee": "iced coffee glass",
    "ingredients": "food ingredients",
    "juice": "glass of juice",
    "milk": "glass of milk",
    "milkshake": "milkshake glass",
    "pasta": "pasta plate",
    "pizza": "pizza slice",
    "plated-meal": "restaurant meal plate",
    "ribs": "barbecue ribs",
    "salad": "green salad bowl",
    "sandwich": "sandwich halves",
    "sauce": "dipping sauce",
    "seafood": "grilled salmon plate",
    "side-dish": "side dish appetizer",
    "side-vegetables": "steamed vegetables",
    "slush": "slushie drink",
    "smoothie": "fruit smoothie",
    "soda": "soda glass with ice",
    "soup": "bowl of soup",
    "steak": "grilled steak",
    "sub-sandwich": "submarine sandwich",
    "taco": "tacos",
    "tea": "cup of tea",
    "water": "glass of water",
    "wine": "glass of wine",
    "wrap": "wrap sandwich",
    "yogurt": "yogurt parfait berries",
}

# Слова, выдающие снимок не блюда, а вывески, упаковки или интерьера.
PENALTY_WORDS = {"sign", "signage", "logo", "storefront", "exterior", "restaurant",
                 "building", "menu board", "billboard", "advertisement", "box",
                 "wrapper", "packaging", "coupon", "receipt", "toy", "costume",
                 "drawing", "cartoon", "illustration", "sculpture", "statue"}


def search(query: str) -> list[dict]:
    params = {"q": query, "license_type": "commercial", "page_size": 20}
    request = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response).get("results", [])


def score(result: dict, archetype: str, query: str) -> int:
    if result.get("license") not in ALLOWED_LICENSES:
        return -1
    if result.get("mature"):
        return -1
    width, height = result.get("width") or 0, result.get("height") or 0
    if width < MIN_WIDTH or height < MIN_WIDTH * 0.5:
        return -1

    title = (result.get("title") or "").lower()
    tags = {t.get("name", "").lower() for t in (result.get("tags") or [])}
    words = set(query.lower().split()) | {archetype.replace("-", " ")}

    points = 0
    # Теги ставит автор снимка, заголовок бывает шуткой — теги весомее.
    for word in words:
        if any(word in tag for tag in tags):
            points += 3
        if word in title:
            points += 1
    if any(bad in title or any(bad in tag for tag in tags) for bad in PENALTY_WORDS):
        points -= 6
    if width >= 1000:
        points += 1
    return points


def fetch_image(url: str) -> Image.Image | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            return Image.open(io.BytesIO(response.read())).convert("RGB")
    except Exception as error:
        print(f"      не скачалось: {error}")
        return None


def square(image: Image.Image) -> Image.Image:
    """Кадрирует по центру в квадрат и уменьшает."""
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)) \
                .resize((SIDE, SIDE), Image.LANCZOS)


def write_imageset(archetype: str, image: Image.Image) -> None:
    folder = ASSETS / f"dish-{archetype}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    image.save(folder / "dish.jpg", "JPEG", quality=82, optimize=True)
    (folder / "Contents.json").write_text(json.dumps({
        "images": [{"filename": "dish.jpg", "idiom": "universal", "scale": "1x"},
                   {"idiom": "universal", "scale": "2x"},
                   {"idiom": "universal", "scale": "3x"}],
        "info": {"author": "xcode", "version": 1},
    }, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="только эти архетипы")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    archetypes = args.only or all_archetypes()
    missing_query = [a for a in archetypes if a not in QUERIES]
    if missing_query:
        print(f"нет запроса для: {missing_query}", file=sys.stderr)
        return 1

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "Contents.json").write_text(
        json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n")

    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    saved = 0

    for archetype in archetypes:
        query = QUERIES[archetype]
        try:
            results = search(query)
        except Exception as error:
            print(f"  ! {archetype}: {error}")
            continue

        ranked = sorted(((score(r, archetype, query), r) for r in results),
                        key=lambda pair: -pair[0])
        best = next((r for points, r in ranked if points > 0), None)
        if best is None:
            print(f"  — {archetype:<20} подходящего снимка нет")
            continue

        points = ranked[0][0]
        print(f"  {archetype:<20} {points:>3} очк.  {best.get('license'):<6} "
              f"{(best.get('title') or '')[:44]}")

        if not args.dry_run:
            image = fetch_image(best.get("url"))
            if image is None:
                continue
            write_imageset(archetype, square(image))
            credits[archetype] = {
                "title": best.get("title"),
                "creator": best.get("creator"),
                "creator_url": best.get("creator_url"),
                "license": best.get("license"),
                "license_version": best.get("license_version"),
                "license_url": best.get("license_url"),
                "source": best.get("source"),
                "page": best.get("foreign_landing_url"),
            }
            saved += 1
        time.sleep(0.8)

    if not args.dry_run:
        CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"\nсохранено {saved}, атрибуция в {CREDITS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
