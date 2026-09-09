"""Сети на Olo — снимки блюд из меню, вшитого в страницу заказа.

Olo — платформа онлайн-заказа под брендом сети, на ней сидят десятки
американских сетей. Фронт у неё один и тот же: меню приходит вместе со
страницей, объектами продуктов, а снимки лежат на общем CDN
`olo-images-live.imgix.net`.

У продукта есть имя, раздел меню и несколько снимков разного назначения
(«marketplace-product», «mobile-app», «mobile-app-large») — берём самый
крупный. Адрес подписан: параметры размера в нём менять нельзя, подпись
станет неверной, поэтому берём как отдают и кадрируем у себя.

Этикетки тут нет — только диапазон калорий («1450-3040 cal.»), потому что
Olo показывает калории комбинируемого блюда вилкой. Цифры берём у
подрядчика сети (`adapters/nutritionix.py`), отсюда только снимки.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    menu_url: str


CHILIS = Brand("chili-s", "Chili's", "https://www.chilis.com/menu")

BRANDS = {b.slug: b for b in (CHILIS,)}

#: Снимок на общем CDN Olo. Подпись `s=` делает адрес неизменяемым.
_IMAGE = re.compile(r"https://olo-images-live\.imgix\.net/\S+?\.jpg\?[^\"'\\ ]+")
_WIDTH = re.compile(r"[?&]w=(\d+)")

_DECODER = json.JSONDecoder()


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def products(page: str) -> list[dict]:
    """Объекты продуктов из страницы меню.

    Страница несёт их внутри строкового литерала, поэтому сначала снимаем
    экранирование, а объекты достаём разбором от ближайшей левой скобки:
    регуляркой не вырезать — внутри вложенные скобки и кавычки.
    """
    text = page.replace('\\"', '"').replace("\\u0026", "&").replace("\\/", "/")
    found: list[dict] = []
    starts: set[int] = set()
    for hit in re.finditer(r'"oloProductId"', text):
        for start in range(hit.start(), max(-1, hit.start() - 6000), -1):
            if text[start] != "{" or start in starts:
                continue
            try:
                obj, end = _DECODER.raw_decode(text, start)
            except ValueError:
                continue
            if isinstance(obj, dict) and end > hit.start() and obj.get("name"):
                starts.add(start)
                found.append(obj)
                break
    return found


def largest(images: object) -> str | None:
    """Самый крупный из снимков продукта."""
    if not isinstance(images, list):
        return None
    urls = [str(i.get("url") or "") for i in images if isinstance(i, dict)]
    urls = [u for u in urls if u.startswith("https://olo-images-live.")]
    if not urls:
        return None
    return max(urls, key=lambda u: int(m.group(1)) if (m := _WIDTH.search(u)) else 0)


def catalog(brand: Brand) -> list[Shot]:
    """Снимки меню сети — один запрос."""
    from ..slug import slugify

    page = curl_get(brand.menu_url, BROWSER_HEADERS, timeout=90)
    if not page:
        raise SystemExit(f"меню {brand.name} не открылось")

    shots: list[Shot] = []
    seen: set[str] = set()
    for product in products(page):
        name = " ".join(str(product.get("name") or "").split())
        image = largest(product.get("images"))
        key = slugify(name)
        if not name or not image or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=brand.name, ext_key=key, name=name,
                          image_url=image, source_url=brand.menu_url))
    return shots
