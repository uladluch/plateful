#!/usr/bin/env python3
"""Снимки блюд сети — в наш бакет и в `item_photos`.

    python3 backend/scripts/chain_photos.py burger-king            # показать
    python3 backend/scripts/chain_photos.py burger-king --apply    # залить

Откуда брать снимки, решает сама сеть: у брендов RBI это их Sanity CMS,
у McDonald's — снимок калькулятора питания. Разница ровно в одной функции;
всё остальное — приведение к квадрату, перекладывание в бакет, строка
прав — общее, потому что это про нас, а не про сеть.

Идёт после `crawl_chain.py <сеть> … --replace --apply`: снимок цепляется
к позиции каталога по тому же ключу, который кроул считает из имени, —
значит, сначала позиция, потом её фотография.

Снимок не хотлинкуется, а перекладывается к нам. У сети свой CDN и своя
жизнь: адрес меняется вместе с версией ассета, а карточка обязана открыться
и через год. Плюс права: строка «использовано с разрешения» лежит рядом
с файлом, а не в чужой инфраструктуре.

Sanity отдаёт исходный квадрат (1333 или 1600), Scene7 у McDonald's —
1564: кадрировать нечего, но приводим к нашему размеру, чтобы все снимки
в каталоге были одного веса.
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

from plateful_data import matching
from plateful_data.adapters import (collected, gotofoods, jersey_mikes, mcdonalds,
                                    panera, quiznos, sanity_rbi)
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
    "tim-hortons": ("© Tim Hortons. Used with permission. Source: timhortons.com",
                    "https://www.timhortons.com/menu"),
    mcdonalds.SLUG: ("© McDonald's Corporation. Used with permission. "
                     "Source: mcdonalds.com", mcdonalds.MENU_URL),
    panera.SLUG: ("© Panera Bread. Used with permission. Source: panerabread.com",
                  panera.MENU_URL),
    quiznos.SLUG: ("© Quiznos. Used with permission. Source: quiznos.com",
                   quiznos.MENU_URL),
    jersey_mikes.SLUG: ("© Jersey Mike's Franchise Systems, Inc. Used with "
                        "permission. Source: jerseymikes.com", jersey_mikes.MENU_URL),
    "white-castle": ("© White Castle System, Inc. Used with permission. "
                     "Source: whitecastle.com", "https://www.whitecastle.com/menu"),
    **{b.slug: (f"© {b.name}. Used with permission. Source: {b.domain}",
                f"https://www.{b.domain}/menu")
       for b in gotofoods.BRANDS.values()},
}


#: Как сеть называется в каталоге — для строки прав и подписи снимка.
CHAIN_NAMES = {"white-castle": "White Castle"}


def shots(slug: str) -> tuple[str, list]:
    """Название сети и её позиции со снимками — откуда бы они ни брались."""
    if slug == mcdonalds.SLUG:
        return mcdonalds.CHAIN, [i for i in mcdonalds.load() if i.image_url]
    if slug == panera.SLUG:
        return panera.CHAIN, panera.catalog()
    if slug == quiznos.SLUG:
        return quiznos.CHAIN, quiznos.catalog()
    if slug == jersey_mikes.SLUG:
        return jersey_mikes.CHAIN, jersey_mikes.catalog()
    if slug in collected.available():
        name = CHAIN_NAMES.get(slug, slug)
        return name, collected.catalog(slug, name, RIGHTS[slug][1])
    if brand := gotofoods.BRANDS.get(slug):
        return brand.name, [i for i in gotofoods.catalog(brand) if i.image_url]
    brand = sanity_rbi.BRANDS[slug]
    return brand.name, [i for i in sanity_rbi.fetch(brand) if i.image_url]


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


def catalog_keys(slug: str) -> tuple[int, dict[str, dict], set[str]]:
    """id сети, её текущие позиции по ключу и ключи со снимком."""
    rows = query(f"select id from chains where slug = {sql_text(slug)};")
    if not rows:
        raise SystemExit(f"сети {slug} нет в chains")
    chain_id = rows[0]["id"]
    # Только живое меню: снятому с меню блюду снимок не нужен, а в
    # сопоставлении оно мешает — у Quiznos архивные строки 2018 года
    # разбирали снимки вместо нынешних сабов.
    catalog = {r["ext_key"]: r for r in query(
        f"select i.ext_key, i.name from items i where i.chain_id = {chain_id}"
        " and i.valid_to is null and not exists ("
        "  select 1 from menu_presence p where p.chain_id = i.chain_id"
        "   and p.ext_key = i.ext_key and p.on_menu is false);")}
    have = {r["ext_key"] for r in query(
        f"select ext_key from item_photos where chain_id = {chain_id};")}
    return chain_id, catalog, have


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
    parser.add_argument("chain", choices=sorted(RIGHTS))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    license_text, page = RIGHTS[args.chain]
    chain_id, catalog, have = catalog_keys(args.chain)

    name, items = shots(args.chain)
    # Тем же правилом, что сопоставляет цифры. По точному ключу снимок
    # терялся всюду, где сеть называет блюдо иначе: «Hash Browns, Small»
    # в каталоге и «Small Hash Browns» у сети — одно блюдо для кроула и
    # разные для снимков, и карточка оставалась без картинки.
    # Правило для снимков мягче, чем для цифр: этикетка у стакана 16 и 20
    # унций разная, а фотография одна, и сеть её одну и снимает. Поэтому
    # один снимок разрешено отдать нескольким строкам каталога.
    chosen = matching.photo_pairs(items, catalog)
    todo = [(shot, key) for key, shot in chosen.items() if key not in have]
    print(f"{name}: снимков у сети {len(items)}, сматчено с каталогом {len(chosen)},"
          f" без снимка {len(todo)}")
    if args.limit:
        todo = todo[:args.limit]
    for item, key in todo[:8]:
        print(f"   {key:40} ← {item.name[:40]}")
    if not args.apply or not todo:
        return 0

    workdir = Path(tempfile.mkdtemp(prefix="chain-photos-"))
    statements = []
    done = 0
    for item, key in todo:
        try:
            image = squared(download(item.image_url))
        except Exception as error:
            print(f"   ! {key}: {error}")
            continue
        filename = f"{args.chain}--{key}.png"
        path = workdir / filename
        image.save(path, "PNG", optimize=True)
        upload = subprocess.run(
            ["supabase", "storage", "cp", str(path), f"ss:///photos/{filename}",
             "--linked", "--experimental", "--content-type", "image/png",
             # Флаг до Storage не долетает: CLI 2.95.4 его молча
             # теряет, и объект отдаётся с `Cache-Control: no-cache`.
             # Приложение это не задевает — оно ходит не за оригиналом,
             # а за `/render/image/`, у которого заголовок свой и
             # правильный. Флаг оставлен на день, когда починят.
             "--cache-control", "max-age=31536000, immutable"],
            capture_output=True, text=True)
        if upload.returncode != 0:
            print(f"   ! {key}: загрузка не удалась: {upload.stderr.strip()[:120]}")
            continue
        statements.append(
            "insert into item_photos (chain_id, ext_key, url, license, license_url,"
            " creator, title, source_page)\n"
            f"values ({chain_id}, {sql_text(key)}, {sql_text(f'{BUCKET_URL}/{filename}')},"
            f" {sql_text(license_text)}, null, {sql_text(name)}, {sql_text(item.name)},"
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
