"""Dickey's Barbecue Pit — снимки блюд из данных страниц меню.

Страницы меню несут всё меню в самой разметке: объекты вида
`{"id":…, "image":{"url":…}, "onlineOrderingLabel":…}`, снимки — на S3
сети. Имя блюда — `onlineOrderingLabel`, тот же текст, что на кнопке
заказа. Разделов два: повседневное меню и кейтеринг.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "dickey-s-barbeque-pit"
CHAIN = "Dickey's Barbecue Pit"
MENU_URL = "https://www.dickeys.com/menu"
PAGES = ("https://www.dickeys.com/menu/everyday", "https://www.dickeys.com/menu/catering")

_START = re.compile(r'\{"id":\d+,"image":\{"url"')
_DECODER = json.JSONDecoder()


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def catalog() -> list[Shot]:
    from ..slug import slugify

    shots: list[Shot] = []
    seen: set[str] = set()
    for url in PAGES:
        page = curl_get(url, BROWSER_HEADERS, timeout=60) or ""
        for hit in _START.finditer(page):
            try:
                item, _ = _DECODER.raw_decode(page, hit.start())
            except ValueError:
                continue
            name = " ".join(str(item.get("onlineOrderingLabel") or "").split())
            image = (item.get("image") or {}).get("url")
            key = slugify(name)
            if not name or not image or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                              image_url=image, source_url=url))
    if not shots:
        raise SystemExit("меню Dickey's не открылось")
    return shots
