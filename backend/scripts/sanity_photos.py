#!/usr/bin/env python3
"""Снимки блюд из Sanity CMS сети — в наш бакет и в `item_photos`.

    python3 backend/scripts/sanity_photos.py burger-king            # показать
    python3 backend/scripts/sanity_photos.py burger-king --apply    # залить

Идёт после `crawl_chain.py <сеть> --sanity --replace --apply`: снимок
цепляется к позиции каталога по тому же ключу, который кроул считает из
имени, — значит, сначала позиция, потом её фотография.

Снимок не хотлинкуется, а перекладывается к нам. У сети свой CDN и своя
жизнь: адрес меняется вместе с версией ассета, а карточка обязана открыться
и через год. Плюс права: строка «использовано с разрешения» лежит рядом
с файлом, а не в чужой инфраструктуре.

Sanity отдаёт исходный квадрат (1333 или 1600) — кадрировать нечего, но
приводим к нашему размеру, чтобы все снимки в каталоге были одного веса.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from plateful_data.adapters import sanity_rbi
from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
BUCKET_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos"
SIDE = 1000

#: Условия использования — у каждой сети свои, как в refresh_chain.CHAINS.
RIGHTS = {
    "burger-king": ("© Burger King Company LLC. Used with permission. Source: bk.com",
                    "https://www.bk.com/menu"),
    "firehouse-subs": ("© Firehouse Restaurant Group, Inc. Used with permission. "
                       "Source: firehousesubs.com", "https://www.firehousesubs.com/menu"),
    "popeyes": ("© Popeyes Louisiana Kitchen, Inc. Used with permission. Source: popeyes.com",
                "https://www.popeyes.com/menu"),
}


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    finally:
        Path(path).unlink(missing_ok=True)
    start = proc.stdout.find("[")
    return json.loads(proc.stdout[start:]) if start >= 0 else []


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def catalog_keys(slug: str) -> tuple[int, set[str], set[str]]:
    """id сети, ключи её текущих позиций и ключи, у которых снимок уже есть."""
    rows = query(f"select id from chains where slug = {sql_text(slug)};")
    if not rows:
        raise SystemExit(f"сети {slug} нет в chains")
    chain_id = rows[0]["id"]
    keys = {r["ext_key"] for r in query(
        f"select ext_key from items where chain_id = {chain_id} and valid_to is null;")}
    have = {r["ext_key"] for r in query(
        f"select ext_key from item_photos where chain_id = {chain_id};")}
    return chain_id, keys, have


def download(url: str) -> Image.Image:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return Image.open(io.BytesIO(response.read())).convert("RGBA")


def squared(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", choices=sorted(sanity_rbi.BRANDS))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    brand = sanity_rbi.BRANDS[args.chain]
    license_text, page = RIGHTS[args.chain]
    chain_id, keys, have = catalog_keys(args.chain)

    items = [i for i in sanity_rbi.fetch(brand) if i.image_url]
    matched = [i for i in items if i.ext_key in keys]
    todo = [i for i in matched if i.ext_key not in have]
    print(f"{brand.name}: снимков в Sanity {len(items)}, из них позиций в каталоге {len(matched)},"
          f" без снимка {len(todo)}")
    if args.limit:
        todo = todo[:args.limit]
    for item in todo[:8]:
        print(f"   {item.ext_key:40} ← {item.image_url.split('?')[0].rsplit('/', 1)[-1]}")
    if not args.apply or not todo:
        return 0

    workdir = Path(tempfile.mkdtemp(prefix="sanity-photos-"))
    statements = []
    done = 0
    for item in todo:
        try:
            image = squared(download(item.image_url))
        except Exception as error:
            print(f"   ! {item.ext_key}: {error}")
            continue
        filename = f"{args.chain}--{item.ext_key}.png"
        path = workdir / filename
        image.save(path, "PNG", optimize=True)
        upload = subprocess.run(
            ["supabase", "storage", "cp", str(path), f"ss:///photos/{filename}",
             "--linked", "--experimental", "--content-type", "image/png",
             "--cache-control", "max-age=31536000, immutable"],
            capture_output=True, text=True)
        if upload.returncode != 0:
            print(f"   ! {item.ext_key}: загрузка не удалась: {upload.stderr.strip()[:120]}")
            continue
        statements.append(
            "insert into item_photos (chain_id, ext_key, url, license, license_url,"
            " creator, title, source_page)\n"
            f"values ({chain_id}, {sql_text(item.ext_key)}, {sql_text(f'{BUCKET_URL}/{filename}')},"
            f" {sql_text(license_text)}, null, {sql_text(brand.name)}, {sql_text(item.name)},"
            f" {sql_text(page)})\n"
            "on conflict (chain_id, ext_key) do update set url = excluded.url,"
            " license = excluded.license, creator = excluded.creator,"
            " title = excluded.title, source_page = excluded.source_page;")
        done += 1
        if done % 25 == 0:
            print(f"   загружено {done}/{len(todo)}")

    if statements:
        sql = ROOT / "backend" / "data" / "crawls" / f"{args.chain}-photos.sql"
        sql.parent.mkdir(parents=True, exist_ok=True)
        sql.write_text("\n".join(statements) + "\n", encoding="utf-8")
        result = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-f", str(sql)],
            capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return 1
    print(f"Записано снимков: {done}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
