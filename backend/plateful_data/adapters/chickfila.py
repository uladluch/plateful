"""Chick-fil-A — снимки блюд со страниц меню на её сайте.

Сайт сети — WordPress, и меню он отдаёт готовой разметкой, а не скриптом:
каждое блюдо — карточка `article.c-card-menu-item-modal`, внутри имя в
`aria-label` и снимок на домене самой сети. Скриптом рисуется только
модальное окно с этикеткой, а оно нам не нужно — цифры сеть публикует
через подрядчика (`adapters/nutritionix.py`), отсюда берём фотографии.

Обходим десять разделов меню: одной страницы со всеми блюдами у сети нет,
а список разделов лежит в навигации на любой из них.

Размер просим через `?resize=`: WordPress отдаёт тысячу на тысячу, и это
ровно наш квадрат — кадрировать и растягивать ничего не приходится.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "chick-fil-a"
CHAIN = "Chick-fil-A"
DOMAIN = "chick-fil-a.com"
MENU_URL = "https://www.chick-fil-a.com/menu"

#: Разделы меню. Порядок как в навигации сети.
SECTIONS = ("breakfast", "entrees", "salads", "sides", "kidsmeals", "treats",
            "beverages", "coffee", "dipping-sauces-and-dressings",
            "family-style-meals")

_CARD = re.compile(r'<article[^>]+c-card-menu-item-modal.*?</article>', re.S)
_NAME = re.compile(r'<h3[^>]+c-card__heading[^>]*aria-label="([^"]+)"')
_IMAGE = re.compile(r'<img[^>]+src="(https://www\.chick-fil-a\.com/wp-content/'
                    r'uploads/[^"?]+)')
#: Тот же файл в нужном нам размере — параметр WordPress, не чужой сервис.
SIZE = "?resize=1000,1000"


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def unescape(text: str) -> str:
    """Имя из `aria-label`: без сущностей и без значка регистрации."""
    for entity, char in (("&amp;", "&"), ("&#038;", "&"), ("&#8217;", "'"),
                         ("&#039;", "'"),
                         ("&quot;", '"'), ("&reg;", " "), ("&nbsp;", " ")):
        text = text.replace(entity, char)
    return " ".join(text.replace("®", " ").replace("™", " ").split())


def catalog() -> list[Shot]:
    from ..slug import slugify

    shots: list[Shot] = []
    seen: set[str] = set()
    for section in SECTIONS:
        url = f"{MENU_URL}/{section}"
        page = curl_get(url, BROWSER_HEADERS, timeout=60)
        if not page:
            continue
        for card in _CARD.findall(page):
            name, image = _NAME.search(card), _IMAGE.search(card)
            if not name or not image:
                continue
            full = unescape(name.group(1))
            key = slugify(full)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=full,
                              image_url=image.group(1) + SIZE, source_url=url))
    if not shots:
        raise SystemExit("меню Chick-fil-A не открылось")
    return shots
