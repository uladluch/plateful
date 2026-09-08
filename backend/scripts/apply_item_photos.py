#!/usr/bin/env python3
"""Ставит выбранные снимки конкретных блюд.

    python3 backend/scripts/apply_item_photos.py "McDonald's" big-mac=0 mcchicken=3

Скачивает выбранного кандидата, кадрирует в квадрат, кладёт в бакет photos
и записывает строку в item_photos вместе с лицензией и автором.

Снимок без известной лицензии не проходит: атрибуция обязательна.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = Path("/private/tmp/claude-501/-Users-uladluch-Developer-plateful/"
                  "612631b9-7bde-474b-8bad-c3ec8cb8b36a/scratchpad/items/candidates.json")
BUCKET_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos"
SIDE = 600   # крупнее архетипных: этот снимок открывают в карточке


def square(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def sql_text(value) -> str:
    if value is None or value == "":
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    if len(sys.argv) < 3:
        print("укажите сеть и выборы вида key=index", file=sys.stderr)
        return 1
    chain, choices = sys.argv[1], sys.argv[2:]
    candidates = json.loads(CANDIDATES.read_text())

    statements, uploaded = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        for choice in choices:
            key, _, index = choice.partition("=")
            options = candidates.get(f"{chain}|{key}")
            if not options or not index.isdigit() or int(index) >= len(options):
                print(f"  ! {key}: нет кандидата {index}")
                continue
            chosen = options[int(index)]
            if not chosen.get("license"):
                print(f"  ! {key}: лицензия неизвестна, пропускаю")
                continue

            try:
                request = urllib.request.Request(chosen["full_url"],
                                                 headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:
                    image = Image.open(io.BytesIO(response.read())).convert("RGB")
            except Exception as error:
                print(f"  ! {key}: {error}")
                continue

            slug = chain.lower().replace(" ", "-").replace("'", "")
            name = f"{slug}--{key}.jpg"
            path = Path(tmp) / name
            square(image).save(path, "JPEG", quality=84, optimize=True)

            upload = subprocess.run(
                ["supabase", "storage", "cp", str(path), f"ss:///photos/{name}",
                 "--linked", "--experimental", "--content-type", "image/jpeg",
                 "--cache-control", "max-age=31536000, immutable"],
                capture_output=True, text=True)
            if upload.returncode != 0 and "Duplicate" not in upload.stderr:
                print(f"  ! {key}: загрузка не прошла — {upload.stderr.strip()[:80]}")
                continue

            statements.append(
                "insert into item_photos (chain_id, ext_key, url, license, license_url,"
                " creator, title, source_page)\n"
                f"select c.id, {sql_text(key)}, {sql_text(f'{BUCKET_URL}/{name}')},"
                f" {sql_text(chosen['license'])}, {sql_text(chosen.get('license_url'))},"
                f" {sql_text(chosen.get('creator'))}, {sql_text(chosen.get('title'))},"
                f" {sql_text(chosen.get('page'))}\n"
                f"from chains c where c.name = {sql_text(chain)}\n"
                "on conflict (chain_id, ext_key) do update set url = excluded.url,"
                " license = excluded.license, license_url = excluded.license_url,"
                " creator = excluded.creator, title = excluded.title,"
                " source_page = excluded.source_page;")
            uploaded += 1
            print(f"  ✓ {key:<28} {chosen['license']:<14} {chosen['title'][:34]}")

    if statements:
        out = ROOT / "backend" / "data" / "item-photos.sql"
        out.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
        applied = subprocess.run(["supabase", "db", "query", "--linked", "-f", str(out)],
                                 capture_output=True, text=True)
        print(f"\nзаписей в базу: {uploaded}" if applied.returncode == 0
              else f"\nSQL не применился: {applied.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
