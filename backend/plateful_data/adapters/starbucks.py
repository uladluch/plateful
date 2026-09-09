"""Starbucks — снимки блюд и напитков из меню его же сайта.

Сайт рисует меню скриптом, но берёт его открытым запросом:
`starbucks.com/apiproxy/v1/ordering/menu`. Ответ — дерево разделов, в
листьях продукты: имя, форма подачи («Iced», «Hot»), размеры и адрес
снимка на Adobe Scene7.

Снимок отдаётся исходником 1800×1800 на белом, а параметрами — квадратом
любого размера и с прозрачностью. Просим тысячу с альфой: блюдо ляжет на
карточку любого фона, и вес втрое меньше исходного.

Этикетку сеть публикует у подрядчика (`adapters/nutritionix.py`), там её
три с половиной тысячи строк — по строке на каждое сочетание напитка,
молока и размера. Снимков триста тридцать: сеть снимает **напиток**, а не
каждый его вариант. Поэтому один снимок достаётся всем вариантам своего
напитка — это работа `matching.photo_pairs`, здесь мы только приносим
пары «имя → адрес».
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

SLUG = "starbucks"
CHAIN = "Starbucks"
DOMAIN = "starbucks.com"
MENU_URL = "https://www.starbucks.com/menu"
API_URL = "https://www.starbucks.com/apiproxy/v1/ordering/menu"

#: Scene7 без параметров отдаёт исходник — 1800 пикселей на белом фоне.
#: Просим наш размер и прозрачность.
IMAGE_SIZE = "?wid=1000&fmt=png-alpha"


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def products(menu: object):
    """Все продукты дерева меню, на любой глубине."""
    if isinstance(menu, dict):
        if menu.get("productNumber") and menu.get("name"):
            yield menu
        for value in menu.values():
            yield from products(value)
    elif isinstance(menu, list):
        for value in menu:
            yield from products(value)


def catalog() -> list[Shot]:
    """Снимки меню — один запрос на всю сеть.

    Имя даём и голое, и с формой подачи («Latte» и «Latte, Iced»):
    этикетка называет напитки то так, то так, а лишняя пара ничего не
    стоит — сопоставление возьмёт ту, что совпала точнее.
    """
    from ..slug import slugify

    body = curl_get(API_URL, {"User-Agent": USER_AGENT,
                              "Accept": "application/json"}, timeout=90)
    if not body:
        raise SystemExit("меню Starbucks не открылось")

    shots: list[Shot] = []
    seen: set[str] = set()
    for product in products(json.loads(body)):
        image = product.get("imageURL")
        name = " ".join(str(product.get("name") or "").split())
        if not image or not name:
            continue
        form = " ".join(str(product.get("formCode") or "").split())
        for full in (name, f"{name}, {form}" if form else name):
            key = slugify(full)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=full,
                              image_url=image + IMAGE_SIZE,
                              source_url=MENU_URL))
    return shots
