"""Jersey Mike's — снимки блюд из открытого API их меню.

Сайт сети рисует меню скриптом, но берёт его запросом, который открыт и
нам: `bapi.prd.jerseymikes.com/api/v0/stores/0/menu`. Ноль вместо номера
ресторана — это национальное меню, то самое, что сеть показывает до
выбора точки.

Что там есть: сорок пять блюд, у каждого свои размеры (Mini, Regular,
Giant, Wrap, Bowl), и у размера — свой снимок 1125×633. Итого сто
тридцать три фотографии на сто тридцать пять позиций.

Чего там нет: этикетки. Калории лежат отдельно, у каждого ингредиента, и
сумма по составу — не то же самое, что опубликованная сетью этикетка:
она учитывает готовку и порядок сборки. Поэтому цифры берём там, где сеть
их публикует официально, — `adapters/nutritionix.py`, — а отсюда только
снимки.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

SLUG = "jersey-mike-s-subs"
CHAIN = "Jersey Mike's Subs"
DOMAIN = "jerseymikes.com"
MENU_URL = "https://www.jerseymikes.com/menu"

#: Ноль вместо номера ресторана — национальное меню.
API_URL = ("https://bapi.prd.jerseymikes.com/api/v0/stores/0/menu"
           "?dispositionType=TAKE_OUT&menuType=TAKE_OUT")


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def catalog() -> list[Shot]:
    """Снимки всех блюд меню, по одному на размер.

    Имя составляем как «Блюдо, Размер» — так же, как называет позиции
    этикетка сети («#1 BLT, Giant»), чтобы снимок и цифры сходились без
    угадывания.
    """
    from ..slug import slugify

    body = curl_get(API_URL, {"User-Agent": USER_AGENT,
                              "Accept": "application/json"}, timeout=60)
    if not body:
        raise SystemExit("меню Jersey Mike's не открылось")
    menu = json.loads(body).get("data") or {}

    shots: list[Shot] = []
    seen: set[str] = set()
    for product in menu.get("menuPlus") or []:
        name = " ".join(str(product.get("name") or "").split())
        if not name:
            continue
        for size in product.get("sizes") or []:
            image = size.get("imageUrl") or size.get("smallImageUrl")
            if not image:
                continue
            label = " ".join(str(size.get("label") or "").split())
            full = f"{name}, {label}" if label else name
            key = slugify(full)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=full,
                              image_url=image, source_url=MENU_URL))
    return shots
