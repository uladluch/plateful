#!/usr/bin/env python3
"""Контактные листы кандидатов для конкретных блюд конкретной сети.

    python3 backend/scripts/item_photo_candidates.py "McDonald's" big-mac cheeseburger

Ищет на Wikimedia Commons снимки именно этого блюда этой сети. Автоматически
ничего не назначает: по запросу «Whopper» приходит и бургер, и вывеска
ресторана, и чья-то домашняя копия. Выбор — глазами по листу.
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
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"
OUT = Path("/private/tmp/claude-501/-Users-uladluch-Developer-plateful/"
           "612631b9-7bde-474b-8bad-c3ec8cb8b36a/scratchpad/items")

API = "https://commons.wikimedia.org/w/api.php"
THUMB, CELL, LABEL, COLS, COUNT = 400, 150, 18, 6, 6
ALLOWED = ("cc0", "public domain", "cc by 2.0", "cc by 3.0", "cc by 4.0",
           "cc by-sa 2.0", "cc by-sa 3.0", "cc by-sa 4.0")
FORBIDDEN = ("-nd", "noderiv", "non-commercial", "-nc")

_PORTION = re.compile(r"\b\d+\s*(ct|pc|oz|in)?\b|\b(small|medium|large|kids?|jr)\b", re.I)


def clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def search(query: str) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": 20,
              "gsrnamespace": 6, "prop": "imageinfo",
              "iiprop": "url|extmetadata|size", "iiurlwidth": THUMB}
    request = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}",
                                     headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        pages = json.load(response).get("query", {}).get("pages", {})

    out = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = clean(meta.get("LicenseShortName", {}).get("value", "")).lower()
        if any(b in licence for b in FORBIDDEN) or not any(a in licence for a in ALLOWED):
            continue
        if (info.get("width") or 0) < 500:
            continue
        out.append({"title": page.get("title", "")[5:],
                    "thumb": info.get("thumburl"), "full_url": info.get("url"),
                    "license": clean(meta.get("LicenseShortName", {}).get("value", "")),
                    "creator": clean(meta.get("Artist", {}).get("value", ""))[:60],
                    "license_url": clean(meta.get("LicenseUrl", {}).get("value", "")),
                    "page": info.get("descriptionurl")})
    return out[:COUNT]


def cell(url: str) -> Image.Image | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            image = Image.open(io.BytesIO(response.read())).convert("RGB")
    except Exception:
        return None
    side = min(image.size)
    box = ((image.width - side) // 2, (image.height - side) // 2)
    return image.crop((*box, box[0] + side, box[1] + side)).resize((CELL, CELL))


def main() -> int:
    if len(sys.argv) < 3:
        print("укажите сеть и ключи позиций", file=sys.stderr)
        return 1
    chain, keys = sys.argv[1], sys.argv[2:]

    items = {i["key"]: i for i in json.loads(PACK.read_text())["items"]
             if i["chain"] == chain}
    OUT.mkdir(parents=True, exist_ok=True)
    index_path = OUT / "candidates.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}

    rows = []
    for key in keys:
        item = items.get(key)
        if not item:
            print(f"  ! нет позиции {key} у {chain}")
            continue
        name = _PORTION.sub(" ", item["name"].split(",")[0]).strip()
        results = search(f"{chain} {name}")
        images = [(r, cell(r["thumb"])) for r in results]
        images = [(r, im) for r, im in images if im]
        index[f"{chain}|{key}"] = [r for r, _ in images]
        rows.append((key, item["name"], images))
        print(f"  {item['name'][:38]:<38} кандидатов {len(images)}")
        time.sleep(0.8)

    if rows:
        height = sum(CELL + LABEL + 18 for _ in rows)
        sheet = Image.new("RGB", (COLS * CELL, height), "white")
        draw = ImageDraw.Draw(sheet)
        y = 0
        for key, name, images in rows:
            draw.rectangle([0, y, COLS * CELL, y + 18], fill="#222")
            draw.text((4, y + 4), f"{key}   {name}", fill="white")
            y += 18
            for i, (result, image) in enumerate(images[:COLS]):
                sheet.paste(image, (i * CELL, y))
                draw.text((i * CELL + 3, y + CELL + 3),
                          f"{i} {result['license'][:10]} {result['title'][:20]}", fill="black")
            y += CELL + LABEL
        path = OUT / f"{chain.lower().replace(' ', '-').replace(chr(39), '')}.png"
        sheet.save(path)
        print(f"\nлист: {path}")

    index_path.write_text(json.dumps(index, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
