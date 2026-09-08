#!/usr/bin/env python3
"""Перекачивает снимки архетипов в большем разрешении.

    python3 backend/scripts/upscale_dish_photos.py

Первый подбор делался под строку списка — 320 пикселей. Для крупной картинки
на карточке блюда этого мало: на трёхкратном экране она будет мыльной.
Оригиналы качаются заново по ссылке на страницу источника, сохранённой
в photo-credits.json, и кадрируются в 800.
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

from PIL import Image

from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plateful" / "Assets.xcassets" / "Dishes"
CREDITS = ROOT / "backend" / "data" / "photo-credits.json"
COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"
SIDE = 800


def commons_file_url(page: str) -> str | None:
    """Полноразмерный файл по ссылке на страницу описания."""
    match = re.search(r"/File:(.+)$", page or "")
    if not match:
        return None
    title = urllib.parse.unquote(match.group(1))
    params = {"action": "query", "format": "json", "titles": f"File:{title}",
              "prop": "imageinfo", "iiprop": "url", "iiurlwidth": SIDE * 2}
    request = urllib.request.Request(f"{COMMONS}?{urllib.parse.urlencode(params)}",
                                     headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        pages = json.load(response).get("query", {}).get("pages", {})
    for page_data in pages.values():
        info = (page_data.get("imageinfo") or [{}])[0]
        return info.get("thumburl") or info.get("url")
    return None


def openverse_file_url(title: str) -> str | None:
    """Оригинал по заголовку.

    Часть снимков подбиралась через Openverse, и в атрибуции осталась ссылка
    на страницу Flickr, а не на файл. Ищем по точному заголовку — этого
    достаточно, чтобы вернуть тот же самый снимок.
    """
    params = {"q": title, "license_type": "commercial", "page_size": 8}
    request = urllib.request.Request(
        f"{OPENVERSE}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        results = json.load(response).get("results", [])
    for result in results:
        if result.get("title") == title:
            return result.get("url")
    return None


def square(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def main() -> int:
    credits = json.loads(CREDITS.read_text())
    upgraded, skipped = 0, []

    for archetype, credit in sorted(credits.items()):
        folder = ASSETS / f"dish-{archetype}.imageset"
        if not folder.exists():
            continue
        current = Image.open(folder / "dish.jpg")
        if current.width >= SIDE:
            continue

        page = credit.get("page") or ""
        url = None
        try:
            if "commons.wikimedia.org" in page:
                url = commons_file_url(page)
            elif credit.get("title"):
                url = openverse_file_url(credit["title"])
        except Exception as error:
            print(f"  ! {archetype}: {error}")

        if not url:
            skipped.append(archetype)
            continue

        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                image = Image.open(io.BytesIO(response.read())).convert("RGB")
        except Exception as error:
            print(f"  ! {archetype}: {error}")
            skipped.append(archetype)
            continue

        if min(image.size) < 400:
            skipped.append(archetype)
            continue

        square(image).save(folder / "dish.jpg", "JPEG", quality=82, optimize=True)
        upgraded += 1
        print(f"  ✓ {archetype:<20} {image.size[0]}x{image.size[1]} → {SIDE}")
        time.sleep(0.6)

    print(f"\nувеличено {upgraded}, осталось мелкими {len(skipped)}")
    if skipped:
        print("  " + ", ".join(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
