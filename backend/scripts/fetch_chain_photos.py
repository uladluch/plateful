#!/usr/bin/env python3
"""Забирает официальные снимки блюд со страниц сети.

    python3 backend/scripts/fetch_chain_photos.py chick-fil-a \
        --rights "© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com"

Берётся og:image страницы позиции — это тот же студийный файл, который сеть
показывает у себя в меню, обычно PNG на прозрачном фоне.

**Права на эти снимки принадлежат сети.** Использование законно ровно
настолько, насколько сеть его разрешила: подпись об источнике и владельце
не заменяет разрешение, а лишь выполняет его условие. Поэтому --rights
обязателен и пишется в базу рядом с каждым файлом — через полгода никто
не вспомнит, на что именно соглашались.

Вежливость обычная: пауза между запросами, честный User-Agent, robots.txt.
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.adapters import chick_fil_a
from plateful_data.adapters.base import USER_AGENT, Fetcher

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"
BUCKET_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos"
SIDE = 1000
MATCH_THRESHOLD = 0.82

ADAPTERS = {"chick-fil-a": chick_fil_a}

_OG_IMAGE = re.compile(r'property="og:image"[^>]*content="([^"]+)"')
_SIZE_WORDS = {"small", "medium", "large", "kids", "kid", "ct", "count", "jr"}
_PAGE_SUFFIX = re.compile(r"\s*nutrition and ingredients\s*$")
_BRAND = re.compile(r"\b(chick fil a|chickfila|mcdonalds)\b")


def normalized(name: str) -> str:
    text = name.lower().replace("®", " ").replace("™", " ").replace("'", "")
    text = _PAGE_SUFFIX.sub("", text)
    return " ".join(_BRAND.sub(" ", re.sub(r"[^a-z0-9 ]+", " ", text)).split())


def portion(name: str) -> frozenset[str]:
    return frozenset(w for w in normalized(name).split()
                     if w.isdigit() or w in _SIZE_WORDS)


def comparable(name: str) -> str:
    return " ".join(sorted(w for w in normalized(name).split()
                           if not w.isdigit() and w not in _SIZE_WORDS))


def match(page_name: str, catalog: dict[str, dict]) -> str | None:
    """Ключ позиции или ничего.

    Размеры обязаны совпасть точно, а порог высокий: поставить снимок не тому
    блюду хуже, чем не поставить вовсе.
    """
    target, size = comparable(page_name), portion(page_name)
    best, score = None, 0.0
    for key, item in catalog.items():
        if portion(item["name"]) != size:
            continue
        ratio = difflib.SequenceMatcher(None, target, comparable(item["name"])).ratio()
        if ratio > score:
            best, score = key, ratio
    return best if score >= MATCH_THRESHOLD else None


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", choices=sorted(ADAPTERS))
    parser.add_argument("--rights", required=True,
                        help="на каких условиях сеть разрешила использование")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    adapter = ADAPTERS[args.chain]
    catalog = {i["key"]: i for i in json.loads(PACK.read_text())["items"]
               if i["chain"] == adapter.CHAIN}

    fetcher = Fetcher()
    urls = adapter.item_urls(fetcher)
    if args.limit:
        urls = urls[:args.limit]
    print(f"{adapter.CHAIN}: страниц {len(urls)}, позиций в каталоге {len(catalog)}\n")

    statements, taken, unmatched = [], 0, []
    with tempfile.TemporaryDirectory() as tmp:
        for url in urls:
            page = fetcher.get(url)
            if not page:
                continue
            name = adapter._item_name(page)
            image_match = _OG_IMAGE.search(page)
            if not name or not image_match:
                continue

            key = match(name, catalog)
            if key is None:
                unmatched.append(name)
                continue

            try:
                request = urllib.request.Request(image_match.group(1),
                                                 headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:
                    image = Image.open(io.BytesIO(response.read()))
            except Exception as error:
                print(f"  ! {name[:34]}: {error}")
                continue

            transparent = image.mode in ("RGBA", "LA") or "transparency" in image.info
            print(f"  ✓ {key:<34} {image.size[0]}x{image.size[1]} "
                  f"{'PNG прозрачный' if transparent else image.mode}")
            taken += 1
            if args.dry_run:
                continue

            # Прозрачную предметную съёмку вписываем целиком: обрезка съест
            # края булки и соус рядом.
            if transparent:
                image = image.convert("RGBA")
                canvas = Image.new("RGBA", (SIDE, SIDE), (0, 0, 0, 0))
                image.thumbnail((SIDE, SIDE), Image.LANCZOS)
                canvas.paste(image, ((SIDE - image.width) // 2, (SIDE - image.height) // 2))
                prepared, suffix, mime = canvas, "png", "image/png"
            else:
                image = image.convert("RGB")
                side = min(image.size)
                left, top = (image.width - side) // 2, (image.height - side) // 2
                prepared = image.crop((left, top, left + side, top + side)) \
                                .resize((SIDE, SIDE), Image.LANCZOS)
                suffix, mime = "jpg", "image/jpeg"

            filename = f"{args.chain}--{key}.{suffix}"
            path = Path(tmp) / filename
            prepared.save(path, "PNG" if suffix == "png" else "JPEG",
                          **({} if suffix == "png" else {"quality": 88}), optimize=True)

            upload = subprocess.run(
                ["supabase", "storage", "cp", str(path), f"ss:///photos/{filename}",
                 "--linked", "--experimental", "--content-type", mime,
                 "--cache-control", "max-age=31536000, immutable"],
                capture_output=True, text=True)
            if upload.returncode != 0 and "Duplicate" not in upload.stderr:
                print(f"    загрузка не прошла: {upload.stderr.strip()[:70]}")
                continue

            statements.append(
                "insert into item_photos (chain_id, ext_key, url, license, creator,"
                " title, source_page)\n"
                f"select c.id, {sql_text(key)}, {sql_text(f'{BUCKET_URL}/{filename}')},"
                f" {sql_text(args.rights)}, {sql_text(adapter.CHAIN)},"
                f" {sql_text(name)}, {sql_text(url)}\n"
                f"from chains c where c.name = {sql_text(adapter.CHAIN)}\n"
                "on conflict (chain_id, ext_key) do update set url = excluded.url,"
                " license = excluded.license, creator = excluded.creator,"
                " title = excluded.title, source_page = excluded.source_page;")

    print(f"\nснимков взято {taken}, не сопоставлено {len(unmatched)}")
    if unmatched:
        print("  " + ", ".join(u[:26] for u in unmatched[:8]))

    if statements and not args.dry_run:
        out = ROOT / "backend" / "data" / f"photos-{args.chain}.sql"
        out.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
        applied = subprocess.run(["supabase", "db", "query", "--linked", "-f", str(out)],
                                 capture_output=True, text=True)
        print(f"в базу записано {len(statements)}" if applied.returncode == 0
              else f"SQL не применился: {applied.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
