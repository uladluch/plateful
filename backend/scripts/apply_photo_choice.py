#!/usr/bin/env python3
"""Ставит выбранного кандидата в каталог ассетов.

    python3 backend/scripts/apply_photo_choice.py pizza=5 taco=1 steak=3

Номер — из контактного листа, который делает photo_candidates.py. Скрипт
скачивает полноразмерный файл, кадрирует по центру в квадрат и записывает
атрибуцию: лицензии by и by-sa требуют указать автора.
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plateful" / "Assets.xcassets" / "Dishes"
CREDITS = ROOT / "backend" / "data" / "photo-credits.json"
CANDIDATES = Path("/private/tmp/claude-501/-Users-uladluch-Developer-plateful/"
                  "612631b9-7bde-474b-8bad-c3ec8cb8b36a/scratchpad/candidates/candidates.json")
SIDE = 320


def square(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def main() -> int:
    if not CANDIDATES.exists():
        print("нет candidates.json — сначала photo_candidates.py", file=sys.stderr)
        return 1

    candidates = json.loads(CANDIDATES.read_text())
    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    applied = 0

    for argument in sys.argv[1:]:
        archetype, _, index = argument.partition("=")
        options = candidates.get(archetype)
        if not options or not index.isdigit() or int(index) >= len(options):
            print(f"  ! {archetype}: нет кандидата {index}")
            continue

        chosen = options[int(index)]
        url = chosen.get("full_url") or chosen.get("url")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                image = Image.open(io.BytesIO(response.read())).convert("RGB")
        except Exception as error:
            print(f"  ! {archetype}: {error}")
            continue

        folder = ASSETS / f"dish-{archetype}.imageset"
        folder.mkdir(parents=True, exist_ok=True)
        square(image).save(folder / "dish.jpg", "JPEG", quality=82, optimize=True)
        (folder / "Contents.json").write_text(json.dumps({
            "images": [{"filename": "dish.jpg", "idiom": "universal", "scale": "1x"},
                       {"idiom": "universal", "scale": "2x"},
                       {"idiom": "universal", "scale": "3x"}],
            "info": {"author": "xcode", "version": 1},
        }, indent=2) + "\n")

        credits[archetype] = {k: chosen.get(k) for k in
                              ("title", "creator", "license", "license_url", "source", "page")}
        applied += 1
        print(f"  ✓ {archetype:<20} {chosen.get('license'):<14} {(chosen.get('title') or '')[:40]}")

    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nобновлено {applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
