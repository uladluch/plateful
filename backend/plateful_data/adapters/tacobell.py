"""Taco Bell — меню с сайта сети, снимки из архивной копии сайта.

Сайт отдаёт всё меню в `__NEXT_DATA__` страницы `/food`: 266 продуктов
и их варианты, у каждого — имя, код и адреса снимков на домене сети.
Сама страница открывается откуда угодно. А вот файлы `tacobell.com/images/…`
Akamai отдаёт только из США: любой другой адрес он уводит на страницу
бренда yum.com, и снимки не грузятся даже в браузере.

Поэтому с американского адреса файлы берём с сайта, а иначе — из Wayback
Machine, публичной архивной копии того же сайта. Это те же файлы сети, с теми же правами (разрешение сети на
её снимки); архив лишь хранит копию. Адрес с `id_` возвращает файл как
есть, без обвязки архива.

Архив не любит спешки: полторы сотни параллельных запросов — и он
перестаёт отвечать на час. Поэтому `chain_photos.py` делает паузу перед
каждым обращением к нему (`ARCHIVE_PAUSE`), а размер пробуем от большего
к меньшему: 640×650 есть не у всех, 269×269 — у всех.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "taco-bell"
CHAIN = "Taco Bell"
DOMAIN = "tacobell.com"
MENU_URL = "https://www.tacobell.com/food"

#: Архивная копия файла как есть — без рамки и скриптов архива.
ARCHIVE = "https://web.archive.org/web/2026id_/"
#: Форматы сети, от лучшего к худшему. 750×340 — баннер, блюдо в нём
#: обрезано, его не берём.
FORMATS = ("640x650", "750x660", "269x269")

_NEXT_DATA = re.compile(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str
    #: Запасные адреса того же снимка, если первого нет в архиве.
    fallbacks: tuple[str, ...] = ()


def _products(node):
    """Все объекты с именем и снимком, на любой глубине."""
    if isinstance(node, dict):
        if node.get("name") and (node.get("images") or node.get("picture")):
            yield node
        for value in node.values():
            yield from _products(value)
    elif isinstance(node, list):
        for value in node:
            yield from _products(value)


def _image_urls(product: dict) -> list[str]:
    """Адреса снимка продукта, от лучшего формата к худшему."""
    images = list(product.get("images") or [])
    if isinstance(product.get("picture"), dict):
        images.append(product["picture"])
    by_format = {im.get("format"): im.get("url") for im in images
                 if isinstance(im, dict) and im.get("url")}
    urls = [by_format[f] for f in FORMATS if f in by_format]
    # Формат 640×650 у сети есть и там, где страница его не перечисляет:
    # имя файла одно и то же, меняется только хвост.
    if urls and "640x650" not in by_format:
        urls.insert(0, re.sub(r"_\d+x\d+\.jpg$", "_640x650.jpg", urls[-1]))
    return urls


def catalog() -> list[Shot]:
    from ..slug import slugify

    page = curl_get(MENU_URL, BROWSER_HEADERS, timeout=90)
    match = _NEXT_DATA.search(page or "")
    if not match:
        raise SystemExit("меню Taco Bell не открылось")
    data = json.loads(match.group(1))

    shots: list[Shot] = []
    seen: set[str] = set()
    for product in _products(data):
        name = " ".join(str(product["name"]).split())
        urls = _image_urls(product)
        key = slugify(name)
        if not key or key in seen or not urls:
            continue
        seen.add(key)
        # Сначала сам сайт — с американского адреса он отдаёт файлы;
        # архив — запасной путь на случай, если адрес снова не тот.
        attempts = (*urls, *(ARCHIVE + u for u in urls))
        shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                          image_url=attempts[0], source_url=MENU_URL,
                          fallbacks=attempts[1:]))
    return shots
