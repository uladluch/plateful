"""Einstein Bros. Bagels — снимки блюд со страниц меню на её сайте.

Сайт — WordPress. Страница `/menu` перечисляет подразделы
(«/menu/lunch/deli-favorites»), а блюда лежат на страницах подразделов:
каждое — блок `.bbm-item` со снимком, имя — в `alt` картинки и в ссылке.
Снимки на домене сети; в `srcset` есть исходник (650×650 или 2048×2048),
берём самый крупный.

Этикетки на сайте нет — цифры у подрядчика (`adapters/nutritionix.py`).
Отдаёт только с американского адреса: иначе 403.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "einstein-bros"
CHAIN = "Einstein Bros. Bagels"
DOMAIN = "einsteinbros.com"
MENU_URL = "https://www.einsteinbros.com/menu"

_SECTION = re.compile(r'href="(/menu/[a-z0-9\-]+/[a-z0-9\-]+)"')
#: Блок блюда — от его начала до начала следующего.
_ITEM_START = '<div class="bbm-item">'
_ALT = re.compile(r'alt="([^"]+)"')
_LINK_NAME = re.compile(r'class="bbm-item-name"[^>]*>\s*<a[^>]*>(.*?)</a>', re.S)
_SRCSET = re.compile(r'srcset="([^"]+)"')
_SRC = re.compile(r'src="(https://www\.einsteinbros\.com/wp-content/uploads/[^"]+)"')


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def _largest(block: str) -> str | None:
    """Самый крупный адрес из `srcset`, иначе `src`."""
    if m := _SRCSET.search(block):
        best, width = None, -1
        for part in m.group(1).split(","):
            bits = part.split()
            if len(bits) == 2 and bits[1].endswith("w") and bits[1][:-1].isdigit():
                if int(bits[1][:-1]) > width:
                    best, width = bits[0], int(bits[1][:-1])
        if best:
            return best
    return m.group(1) if (m := _SRC.search(block)) else None


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, char in (("&amp;", "&"), ("&#038;", "&"), ("&#8217;", "'"),
                         ("&#039;", "'"), ("&reg;", " "), ("&nbsp;", " ")):
        text = text.replace(entity, char)
    return " ".join(text.replace("®", " ").replace("™", " ").split())


def catalog() -> list[Shot]:
    from ..slug import slugify

    landing = curl_get(MENU_URL, BROWSER_HEADERS, timeout=60) or ""
    sections = sorted(set(_SECTION.findall(landing)))
    if not sections:
        raise SystemExit("меню Einstein Bros не открылось")

    shots: list[Shot] = []
    seen: set[str] = set()
    for section in sections:
        url = f"https://www.{DOMAIN}{section}"
        page = curl_get(url, BROWSER_HEADERS, timeout=60)
        if not page:
            continue
        for block in page.split(_ITEM_START)[1:]:
            name_match = _LINK_NAME.search(block) or _ALT.search(block)
            image = _largest(block)
            if not name_match or not image:
                continue
            name = _clean(name_match.group(1))
            key = slugify(name)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                              image_url=image, source_url=url))
    return shots
