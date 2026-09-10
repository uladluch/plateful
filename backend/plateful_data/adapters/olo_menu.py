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

import html
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
#: Отдаёт меню только с американского адреса — иначе 403.
APPLEBEES = Brand("applebee-s", "Applebee's", "https://www.applebees.com/en/menu")

BRANDS = {b.slug: b for b in (CHILIS, APPLEBEES)}

#: Снимок на общем CDN Olo. Подпись `s=` делает адрес неизменяемым.
_IMAGE = re.compile(r"https://olo-images-live\.imgix\.net/\S+?\.jpg\?[^\"'\\ ]+")
_WIDTH = re.compile(r"[?&]w=(\d+)")

_DECODER = json.JSONDecoder()
#: Карточка продукта в разметке: снимок, следом имя. Две выкладки:
#: у Hardee's и Carl's Jr — `<img>` и `<h3>`, у Krystal (Nuxt) — фон
#: `background-image` и `.item-title-text`.
_MARKUP = re.compile(
    r'<img[^>]+src="(https://olo-images-live\.imgix\.net/[^"]+)"[^>]*>\s*</span>'
    r'\s*<h3>(.*?)</h3>'
    r'|background-image:url\((https://olo-images-live\.imgix\.net/[^)]+)\).*?'
    r'class="item-title-text"[^>]*>(.*?)</div>', re.S)


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
    # Две выкладки одного Olo: у Chili's ключи в camelCase («oloProductId»,
    # «name», «images»), у Applebee's — в PascalCase («ChainProductId»,
    # «Name», «ImageLarge»). Данные те же, CDN тот же.
    for hit in re.finditer(r'"(?:oloProductId|ChainProductId)"', text):
        for start in range(hit.start(), max(-1, hit.start() - 6000), -1):
            if text[start] != "{" or start in starts:
                continue
            try:
                obj, end = _DECODER.raw_decode(text, start)
            except ValueError:
                continue
            if isinstance(obj, dict) and end > hit.start() and (obj.get("name") or obj.get("Name")):
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
    # Третья выкладка Olo — у Hardee's и Carl's Jr продукты не в JSON, а
    # прямо в разметке: карточка `.inner-box`, снимок в `<img>`, имя в
    # `<h3>`. CDN и подпись адреса те же, значит и адаптер тот же.
    for image_a, name_a, image_b, name_b in _MARKUP.findall(page):
        image, name = (image_a or image_b), (name_a or name_b)
        name = " ".join(html.unescape(name).replace("®", " ").split())
        # У Krystal имена капсом — приводим к обычному регистру, чтобы
        # подпись снимка читалась как имя, а не как вывеска.
        if name.isupper():
            name = name.title()
        key = slugify(name)
        if not name or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=brand.name, ext_key=key, name=name,
                          image_url=html.unescape(image), source_url=brand.menu_url))
    for product in products(page):
        name = " ".join(str(product.get("name") or product.get("Name") or "").split())
        image = largest(product.get("images")) or (
            str(product.get("ImageLarge") or "") if str(product.get("ImageLarge") or "")
            .startswith("https://olo-images-live.") else None)
        key = slugify(name)
        if not name or not image or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=brand.name, ext_key=key, name=name,
                          image_url=image, source_url=brand.menu_url))
    return shots
