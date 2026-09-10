"""Culver's — снимки блюд из данных страниц меню.

Сайт на Next.js: у каждого раздела («/menu/butterburgers») своя страница,
и в её `__NEXT_DATA__` лежат блюда раздела с именем и снимком на
`cdn.culvers.com`. Список разделов — в навигации `/menu`.

Этикетки в этих данных нет — цифры у подрядчика
(`adapters/nutritionix.py`). Отдаёт только с американского адреса.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "culver-s"
CHAIN = "Culver's"
DOMAIN = "culvers.com"
MENU_URL = "https://www.culvers.com/menu"

_SECTION = re.compile(r'href="(/menu/[a-z0-9\-]+)"')
_NEXT_DATA = re.compile(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
#: Снимок самого блюда, а не плитка раздела.
_ITEM_IMAGE = "cdn.culvers.com/menu/images/item/"


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def _items(node):
    if isinstance(node, dict):
        image = node.get("image") or node.get("imageUrl")
        if node.get("name") and isinstance(image, str) and _ITEM_IMAGE in image:
            yield node["name"], image
        for value in node.values():
            yield from _items(value)
    elif isinstance(node, list):
        for value in node:
            yield from _items(value)


def catalog() -> list[Shot]:
    from ..slug import slugify

    landing = curl_get(MENU_URL, BROWSER_HEADERS, timeout=60) or ""
    sections = sorted(set(_SECTION.findall(landing)))
    if not sections:
        raise SystemExit("меню Culver's не открылось")

    shots: list[Shot] = []
    seen: set[str] = set()
    for section in sections:
        url = f"https://www.{DOMAIN}{section}"
        page = curl_get(url, BROWSER_HEADERS, timeout=60) or ""
        match = _NEXT_DATA.search(page)
        if not match:
            continue
        for raw, image in _items(json.loads(match.group(1))):
            name = " ".join(str(raw).replace("®", " ").replace("™", " ").split())
            key = slugify(name)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                              image_url=image, source_url=url))
    return shots
