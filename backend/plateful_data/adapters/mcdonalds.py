"""McDonald's — снимок калькулятора питания, снятый браузером.

Сайт сети рисует меню скриптом, но всё нужное лежит на одной странице —
`about-our-food/nutrition-calculator.html`. В её разметке есть атрибут
`data-product-data`: 190 КБ JSON с разделами меню, продуктами, их
размерами и адресами снимков на Scene7. Этикетку каждой позиции отдаёт
`/dnaapp/itemDetails?country=US&language=en&item=<id>` — полная девятка
FDA плюс клетчатка, сахар, транс-жиры и холестерин.

Почему снимок, а не кроул. На эти адреса `curl` и Python получают HTTP
000 — соединение рвётся на рукопожатии TLS, сеть смотрит на отпечаток
клиента, а не на заголовки. Обойти это можно только настоящим браузером,
и мы его не подделываем: страницу открывает человек (или встроенный
браузер агента), скрипт `backend/data/collect/mcdonalds.js` снимает меню
и кладёт файл на диск. Дальше — обычный кроул, который сверяет снимок с
каталогом и версионирует, как всякий другой источник.

Две ловушки, на которых снимок теряет позиции:

* однопорционные блюда — Big Mac, Egg McMuffin, McChicken — не имеют
  массива `sizes`, и `itemId` у них равен ключу самого продукта. Пока
  сборщик читал только размеры, все бургеры проходили мимо: 185 позиций
  вместо 252;
* разделы в `categoryList` идут не по важности: первыми лежат витрины
  вроде «McValue®» и «Spicy Chicken McNuggets®». Если брать первый
  попавшийся, у Big Mac разделом окажется акция. Настоящие разделы
  перечислены в `SECTIONS`, витрины годятся лишь как последнее средство.

Комбо-наборы («… Meal») сборщик не приносит: их этикетка зависит от
выбранных стороны и напитка, и `itemDetails` отдаёт пустой список
нутриентов. Позицию без цифр в каталог не заводим.
"""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

CHAIN = "McDonald's"
SLUG = "mcdonald-s"
DOMAIN = "mcdonalds.com"
MENU_URL = "https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html"

BACKEND = Path(__file__).resolve().parents[2]
SNAPSHOT = BACKEND / "cache" / "mcdonalds.json"
SECTIONS_FILE = BACKEND / "cache" / "mcdonalds-sections.json"

#: Разделы меню сети → наш словарь категорий (тот же, что у menustat).
#: Порядок значим: он же задаёт, какой раздел выигрывает, когда позиция
#: лежит в нескольких. Витрины и акции сюда не входят намеренно.
SECTIONS = (
    ("Burgers", "Burgers"),
    ("Chicken & Fish Sandwiches", "Sandwiches"),
    ("Snack Wrap®", "Sandwiches"),
    ("McNuggets® & McCrispy® Strips", "Entrees"),
    ("Breakfast", "Entrees"),
    ("Fries & Sides", "Appetizers & Sides"),
    ("Sweets & Treats", "Desserts"),
    ("McCafé®", "Beverages"),
    ("Drinks", "Beverages"),
)

#: Витрины: раздел настоящий, но собран по цене или новинке, а не по еде.
#: Категорию по ним не выдаём — пусть лучше её не будет вовсе.
SHOWCASES = ("McValue®", "Spicy Chicken McNuggets®")

NUTRIENTS = ("kcal", "protein", "carbs", "fat", "sat_fat", "trans_fat",
             "cholesterol", "sodium", "sugar", "fiber")

#: Снимки лежат на Scene7, и без параметров он отдаёт своё умолчание —
#: 400 пикселей JPEG на белом фоне. Исходник квадратный, 1564, с
#: прозрачностью; просим его в нашем размере и с альфой, чтобы блюдо
#: легло на карточку любого фона.
IMAGE_SIZE = "?wid=1000&fmt=png-alpha"

#: Сеть пишет аллергены прозой («Wheat, Milk.», «Fish (pollock).»).
#: Приводим к девятке FDA; чего нет в словаре, то не выдумываем.
ALLERGENS = {
    "milk": "milk", "egg": "eggs", "eggs": "eggs", "wheat": "wheat",
    "soy": "soy", "sesame": "sesame", "peanut": "peanuts",
    "peanuts": "peanuts", "tree nuts": "treeNuts", "fish": "fish",
    "fish (pollock)": "fish", "shellfish": "shellfish",
}


@dataclass(frozen=True)
class Item:
    """Позиция из снимка — уже в наших терминах."""
    chain: str
    ext_key: str
    name: str
    category: str | None
    serving: str | None
    source: str
    source_url: str
    image_url: str | None
    allergens: tuple[str, ...]
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    sat_fat: float | None = None
    trans_fat: float | None = None
    cholesterol: float | None = None
    sodium: float | None = None
    sugar: float | None = None
    fiber: float | None = None


def category_of(item_id: str, sections: dict[str, list[str]],
                fallback: str | None = None) -> str | None:
    """Раздел меню в нашем словаре — по первому настоящему разделу.

    Запасной вариант — раздел, который сеть назвала главным у самой
    позиции. Витрину он подсовывает так же охотно, как `categoryList`,
    поэтому её отсеиваем и здесь.
    """
    for title, ours in SECTIONS:
        if item_id in sections.get(title, ()):
            return ours
    return None if fallback in SHOWCASES else fallback


def _image(raw: str | None) -> str | None:
    """Адрес снимка, годный для запроса.

    Имена ассетов сеть заводит руками, и в них попадают пробелы:
    «…1564x1564 (1)-1». Такой адрес не откроет ни urllib, ни бакет —
    экранируем путь, оставив разделители на месте.
    """
    if not raw:
        return None
    return urllib.parse.quote(raw, safe=":/") + IMAGE_SIZE


def _allergens(names: list[str]) -> tuple[str, ...]:
    found = []
    for raw in names:
        ours = ALLERGENS.get(raw.strip().lower())
        if ours and ours not in found:
            found.append(ours)
    return tuple(found)


def load(path: Path | None = None,
         sections_path: Path | None = None) -> list[Item]:
    """Снимок с диска — списком позиций.

    Снимок сырой: имена, разделы и аллергены сеть пишет по-своему, а
    разбирает их этот модуль. Так снятое можно перечитать другими
    правилами, не поднимая браузер заново.
    """
    from ..slug import slugify

    path = path or SNAPSHOT
    if not path.exists():
        raise SystemExit(
            f"снимка {path} нет — снимите его: откройте {MENU_URL} в браузере "
            f"и выполните backend/data/collect/mcdonalds.js")
    records = json.loads(path.read_text(encoding="utf-8"))

    sections_path = sections_path or SECTIONS_FILE
    sections = (json.loads(sections_path.read_text(encoding="utf-8"))
                if sections_path.exists() else {})

    items: list[Item] = []
    seen: set[str] = set()
    for record in records:
        name = " ".join(str(record.get("n") or "").split())
        if not name or record.get("kcal") is None:
            continue
        key = slugify(name)
        if key in seen:
            continue
        seen.add(key)
        grams = record.get("g")
        items.append(Item(
            chain=CHAIN, ext_key=key, name=name,
            category=category_of(record["id"], sections, record.get("cat")),
            serving=f"{grams} g" if grams else None,
            source=DOMAIN, source_url=MENU_URL,
            image_url=_image(record.get("img")),
            allergens=_allergens(record.get("alg") or []),
            **{n: record.get(n) for n in NUTRIENTS}))
    return items
