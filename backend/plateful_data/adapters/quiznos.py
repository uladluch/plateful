"""Quiznos — снимки блюд со страницы меню.

Вся сеть умещается на одной странице: у каждой позиции карточка, а при
ней скрытая модалка с названием и снимком. Снимок стоит не в `<img>`, а
атрибутом отложенной загрузки — обычный сбор картинок со страницы его не
видит.

Адреса ведут на оптимизатор страниц (nitrocdn), который отдаёт урезанные
копии: 750x750 вместо исходных 916x916, а «wide» и вовсе кадрирован в
полосу. Оригинал лежит у сети на своём домене — берём его: и качество
выше, и источник честнее.

Этикетку сеть публикует гидом (`pdf_guide.QUIZNOS`), поэтому здесь только
снимки.
"""

from __future__ import annotations

import html as html_entities
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "quiznos"
CHAIN = "Quiznos"
DOMAIN = "quiznos.com"
MENU_URL = "https://www.quiznos.com/menu"

#: Название в заголовке модалки, следом за ним — снимок.
_CARD = re.compile(
    r'modal-title"[^>]*>\s*(?P<name>[^<]+?)\s*</h1>'
    r'.{0,900}?nitro-lazy-bg="(?P<image>[^"]+)"',
    re.S)

#: Хвост, которым оптимизатор помечает урезанную копию.
_RESIZED = re.compile(r"-\d+x\d+-c-\w+(?=\.\w+$)")

#: Путь через оптимизатор: всё до домена сети — его, а не наше.
_OPTIMIZER = re.compile(r"^https?://[^/]*nitrocdn\.com/.*?/(www\.[^/]+/)")


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def original(url: str) -> str:
    """Адрес исходного снимка на домене сети.

    «…nitrocdn.com/<хеш>/assets/images/optimized/rev-x/www.quiznos.com/
    wp-content/uploads/2021/06/classic-750x0-c-default.jpg»
        → «https://www.quiznos.com/wp-content/uploads/2021/06/classic.jpg»
    """
    url = _OPTIMIZER.sub(r"https://\1", url)
    # «wide» — не размер, а другой кадр: полоса вместо квадрата.
    return _RESIZED.sub("", url).replace("-wide.", ".")


def catalog() -> list[Shot]:
    """Снимки всех блюд — одна страница на всю сеть."""
    from ..slug import slugify

    page = curl_get(MENU_URL, BROWSER_HEADERS, timeout=60)
    if not page:
        raise SystemExit("меню Quiznos не открылось")

    shots: list[Shot] = []
    seen: set[str] = set()
    for match in _CARD.finditer(page):
        # В разметке амперсанд стоит сущностью: «Ham &#038; Swiss».
        name = " ".join(html_entities.unescape(match.group("name")).split())
        key = slugify(name)
        if not key or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                          image_url=original(match.group("image")),
                          source_url=MENU_URL))
    return shots
