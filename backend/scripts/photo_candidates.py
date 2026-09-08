#!/usr/bin/env python3
"""Готовит контактные листы кандидатов для ручного отбора.

    python3 backend/scripts/photo_candidates.py bacon pizza steak

Оценка по метаданным отбирает мусор лишь частично: у «bacon» первым пришёл
человек у фритюрницы, у «steak» — полка с вином. Теги и заголовки не говорят,
что на снимке. Поэтому кандидаты скачиваются, склеиваются в лист с номерами,
и выбор делается глазами.

Результат: PNG-лист на каждый архетип и candidates.json со списком, из
которого apply_photo_choice.py забирает выбранный номер.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw

from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/private/tmp/claude-501/-Users-uladluch-Developer-plateful/"
           "612631b9-7bde-474b-8bad-c3ec8cb8b36a/scratchpad/candidates")

# Wikimedia Commons вместо Openverse: у того анонимный лимит выбирается
# за полсотни запросов, а здесь при честном User-Agent и паузе в секунду
# ограничений на такой объём нет.
API = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 400
# Только то, что можно использовать коммерчески и перерабатывать: кадрируем
# в квадрат, а это переработка, поэтому ND исключён.
ALLOWED_MARKERS = ("cc0", "public domain", "cc by 2.0", "cc by 3.0", "cc by 4.0",
                   "cc by-sa 2.0", "cc by-sa 3.0", "cc by-sa 4.0", "cc-by-sa")
FORBIDDEN_MARKERS = ("-nd", "noderiv", "non-commercial", "-nc")
COUNT, CELL, LABEL, COLS = 8, 170, 20, 4

# Запросы точнее, чем имя архетипа: «pizza slice» приводил к лососю.
QUERIES = {
    "bacon": "bacon", "baked-potato": "jacket potato baked",
    "bowl": "burrito bowl chicken rice", "burrito": "burrito",
    "cheese": "cheese slices plate", "chicken-nuggets": "chicken nuggets",
    "chicken-strips": "chicken tenders fried", "dessert": "chocolate dessert plate",
    "fruit": "fruit bowl fresh", "fried-chicken": "fried chicken",
    "hot-dog": "hot dog", "ice-cream": "ice cream cone",
    "ingredients": "vegetables ingredients cutting board", "juice": "orange juice glass",
    "milk": "milk carton dairy", "pizza": "pizza cheese whole",
    "steak": "steak dinner plate", "taco": "tacos plate mexican food",
    "wrap": "wrap sandwich tortilla", "yogurt": "yogurt bowl granola",
    "breakfast-sandwich": "breakfast sandwich bacon egg",
    "sandwich": "club sandwich plate",
    "ingredients": "fresh vegetables board",
}


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def search(query: str) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": 24,
              "gsrnamespace": 6, "prop": "imageinfo",
              "iiprop": "url|extmetadata|size", "iiurlwidth": THUMB_WIDTH}
    request = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        pages = json.load(response).get("query", {}).get("pages", {})

    results = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = _clean(meta.get("LicenseShortName", {}).get("value", "")).lower()
        if any(bad in licence for bad in FORBIDDEN_MARKERS):
            continue
        if not any(good in licence for good in ALLOWED_MARKERS):
            continue
        if (info.get("width") or 0) < 500:
            continue
        results.append({
            "title": page.get("title", "")[5:],
            "url": info.get("thumburl") or info.get("url"),
            "full_url": info.get("url"),
            "license": _clean(meta.get("LicenseShortName", {}).get("value", "")),
            "creator": _clean(meta.get("Artist", {}).get("value", ""))[:60],
            "license_url": _clean(meta.get("LicenseUrl", {}).get("value", "")),
            "source": "wikimedia",
            "page": info.get("descriptionurl"),
            "width": info.get("width"),
        })
    return results[:COUNT]


def thumbnail(url: str) -> Image.Image | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            image = Image.open(io.BytesIO(response.read())).convert("RGB")
    except Exception:
        return None
    side = min(image.size)
    return image.crop(((image.width - side) // 2, (image.height - side) // 2,
                       (image.width - side) // 2 + side,
                       (image.height - side) // 2 + side)).resize((CELL, CELL))


def main() -> int:
    archetypes = sys.argv[1:]
    if not archetypes:
        print("укажите архетипы", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    index_path = OUT / "candidates.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}

    for archetype in archetypes:
        query = QUERIES.get(archetype, archetype.replace("-", " "))
        try:
            results = search(query)
        except Exception as error:
            print(f"  ! {archetype}: {error}")
            continue

        rows = (len(results) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * CELL, max(rows, 1) * (CELL + LABEL)), "white")
        draw = ImageDraw.Draw(sheet)
        kept = []

        for position, result in enumerate(results):
            image = thumbnail(result.get("url"))
            if image is None:
                continue
            slot = len(kept)
            x, y = (slot % COLS) * CELL, (slot // COLS) * (CELL + LABEL)
            sheet.paste(image, (x, y))
            draw.text((x + 4, y + CELL + 4),
                      f"{slot}  {result.get('license')}  {(result.get('title') or '')[:24]}",
                      fill="black")
            kept.append(result)

        sheet.save(OUT / f"{archetype}.png")
        index[archetype] = kept
        print(f"  {archetype:<20} кандидатов {len(kept)} → {archetype}.png")
        time.sleep(0.8)

    index_path.write_text(json.dumps(index, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nлисты в {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
