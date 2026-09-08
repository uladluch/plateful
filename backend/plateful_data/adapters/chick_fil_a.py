"""Chick-fil-A: нутриенты лежат готовым JSON в HTML страницы позиции.

    "nutrition":[{"key":"calories","label":"Calories","value":420},
                 {"key":"protein","label":"Protein","value":"29g"}, ...]

robots.txt (проверено 2026-09-08) запрещает только /wp-admin/ и URL с
?query- — раздел /menu открыт.
"""

from __future__ import annotations

import html as html_entities
import json
import re

from ..slug import slugify
from .base import Fetcher, LiveItem, to_number

CHAIN = "Chick-Fil-A"
SOURCE = "chick-fil-a.com"
MENU_URL = "https://www.chick-fil-a.com/menu"

# Ссылки на сайте абсолютные, но на всякий случай ловим и относительные.
_HREF = re.compile(r'href="(?:https://www\.chick-fil-a\.com)?(/menu/[a-z0-9/-]+?)"')
_NUTRITION = re.compile(r'"nutrition":(\[.*?\])', re.S)
_OG_TITLE = re.compile(r'property="og:title" content="([^"]*)"')


def _item_name(page: str) -> str | None:
    """Имя из og:title.

    В `<title>` попадает хвост вроде «Nutrition and Ingredients», а сущности
    приходят экранированными — отсюда и unescape.
    """
    match = _OG_TITLE.search(page)
    if not match:
        return None
    name = html_entities.unescape(match.group(1)).split("|")[0].strip()
    return name or None


def _nutrition(html: str) -> dict[str, float | None]:
    match = _NUTRITION.search(html)
    if not match:
        return {}
    try:
        rows = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return {row.get("key"): to_number(row.get("value"))
            for row in rows if isinstance(row, dict)}


def _paths(html: str) -> list[str]:
    return list(dict.fromkeys(_HREF.findall(html)))


def item_urls(fetcher: Fetcher) -> list[str]:
    """Позиции со всех категорий.

    Главная /menu перечисляет лишь часть блюд, поэтому сначала собираем
    страницы категорий, потом позиции с каждой.
    """
    index = fetcher.get(MENU_URL)
    if not index:
        return []

    paths = _paths(index)
    categories = [p for p in paths if p.count("/") == 2]
    items = {p for p in paths if p.count("/") == 3}

    for category in categories:
        page = fetcher.get(f"https://www.chick-fil-a.com{category}")
        if page:
            items.update(p for p in _paths(page) if p.count("/") == 3)

    return [f"https://www.chick-fil-a.com{path}" for path in sorted(items)]


def fetch(fetcher: Fetcher | None = None, limit: int | None = None) -> list[LiveItem]:
    fetcher = fetcher or Fetcher()
    urls = item_urls(fetcher)
    if limit:
        urls = urls[:limit]
    print(f"{CHAIN}: страниц позиций — {len(urls)}")

    items: list[LiveItem] = []
    for url in urls:
        html = fetcher.get(url)
        if not html:
            continue
        name = _item_name(html)
        values = _nutrition(html)
        kcal = values.get("calories")
        if not name or kcal is None:
            continue
        items.append(LiveItem(
            chain=CHAIN, ext_key=slugify(name), name=name,
            kcal=kcal,
            protein=values.get("protein"),
            carbs=values.get("carbs"),
            fat=values.get("fat"),
            source=SOURCE, source_url=url))
    return items
