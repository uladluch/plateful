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
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, PngImagePlugin

# Пресс-снимки несут в себе целые абзацы метаданных: у Subway в медиатеке
# это подпись, права и история правок, и Pillow отказывается их читать,
# считая раздутый текстовый блок попыткой его положить. Файлы наши,
# скачаны с домена сети, и разбирать их безопасно.
PngImagePlugin.MAX_TEXT_CHUNK = 32 * 1024 * 1024

from plateful_data import matching
from plateful_data.adapters import photo_sources
from plateful_data.adapters.base import USER_AGENT

ROOT = Path(__file__).resolve().parents[2]
BUCKET_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos"
SIDE = 1000

def source(slug: str) -> photo_sources.Source:
    """Откуда у сети снимки — из `chains`, не из кода.

    Вид платформы, адрес меню и строка прав лежат рядом с сетью, и
    подключить новую на известной платформе значит записать строку.
    """
    rows = query("select slug, name, photo_source_kind, photo_source_url, photo_rights"
                 f" from chains where slug = {sql_text(slug)};")
    if not rows:
        raise SystemExit(f"сети {slug} нет в chains")
    row = rows[0]
    if not row["photo_source_kind"]:
        raise SystemExit(f"{slug}: источник снимков не записан — сначала "
                         "probe_photo_sources.py и строка в chains.photo_source_kind")
    return photo_sources.Source(row["slug"], row["name"], row["photo_source_kind"],
                                row["photo_source_url"], row["photo_rights"])


def with_photo_source() -> list[str]:
    """Сети, у которых источник снимков записан."""
    return [r["slug"] for r in query(
        "select slug from chains where photo_source_kind is not null order by slug;")]


def shots(slug: str) -> tuple[str, list]:
    """Название сети и её позиции со снимками — по реестру платформ."""
    src = source(slug)
    return src.name, photo_sources.shots(src)


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


def clean_url(url: str) -> str:
    """Адрес, пригодный для запроса.

    Двумя разными бедами занят один и тот же шаг. У Starbucks часть
    ссылок несёт нулевой пробел (U+200B) — редакторский мусор из CMS,
    который в адресе не значит ничего, как и любой форматирующий символ.
    У Chick-fil-A в имени файла живёт знак ®, и такой адрес — уже не
    URI, а IRI: браузер кодирует его сам, а `urllib` отказывается
    отправлять что угодно за пределами ASCII.
    """
    text = "".join(ch for ch in url if unicodedata.category(ch) != "Cf")
    return urllib.parse.quote(text, safe=":/?#[]@!$&'()*+,;=~%-._")


#: Пауза перед каждым обращением к архиву. Wayback Machine — общий
#: ресурс, и полторы сотни параллельных запросов кладут его для нас на
#: час; по одному раз в пару секунд он отдаёт ровно.
ARCHIVE_PAUSE = 2.5
_ARCHIVE_HOST = "web.archive.org"


def download(url: str) -> Image.Image:
    if _ARCHIVE_HOST in url:
        time.sleep(ARCHIVE_PAUSE)
    request = urllib.request.Request(clean_url(url), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return Image.open(io.BytesIO(response.read())).convert("RGBA")


def download_any(item) -> Image.Image:
    """Снимок по первому адресу, который отдался.

    У Taco Bell лучший формат есть не у всех файлов, и адаптер даёт
    запасные — тот же снимок меньше. Ошибка — только если не отдался ни
    один.
    """
    error: Exception | None = None
    for url in (item.image_url, *getattr(item, "fallbacks", ())):
        try:
            return download(url)
        except Exception as exc:  # noqa: BLE001 — пробуем следующий адрес
            error = exc
    raise error or RuntimeError("нет адресов")


def squared(image: Image.Image) -> Image.Image:
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    src = source(args.chain)
    if not src.rights:
        raise SystemExit(f"{args.chain}: строка прав не записана (chains.photo_rights)")
    license_text, page = src.rights, src.url
    chain_id, catalog, have = catalog_keys(args.chain)

    name, items = src.name, photo_sources.shots(src)
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
            image = squared(download_any(item))
        except Exception as error:
            print(f"   ! {key}: {error}")
            continue
        filename = f"{args.chain}--{key}.png"
        path = workdir / filename
        image.save(path, "PNG", optimize=True)
        upload = subprocess.run(
            ["supabase", "storage", "cp", str(path), f"ss:///photos/{filename}",
             "--linked", "--experimental", "--content-type", "image/png",
             "--cache-control", "max-age=31536000, immutable"],
            capture_output=True, text=True)
        # «Уже есть» — не отказ. Имя файла складывается из сети и ключа
        # позиции, значит объект с этим именем клали мы и из того же
        # источника; строку в `item_photos` прошлый заход дописать не
        # успел, и без этой ветки она не появится уже никогда.
        if upload.returncode != 0 and "KeyAlreadyExists" not in upload.stderr:
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
