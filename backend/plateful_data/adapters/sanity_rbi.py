"""Сети RBI — Burger King, Popeyes, Firehouse Subs — через их Sanity CMS.

Сайт bk.com рисует меню скриптом, и в HTML нет ни ссылок, ни цифр, ни
картинок. Но откуда-то он их берёт — и берёт из Sanity: контент-базы, к
которой фронт ходит **публичным GROQ-запросом без ключа**. Проект и датасет
зашиты в приложение (проект приходит LaunchDarkly-флагом `sanity-project-id`,
датасет собирается как `prod_<бренд>_<регион>`), и тот же адрес открыт
любому, кто его знает.

Что там лежит у каждой позиции: имя, снимок на CDN Sanity, полная этикетка
(калории, белки, углеводы, жиры, насыщенные, транс, холестерин, натрий,
сахар, клетчатка), четырнадцать аллергенов и иерархия продукта L1–L5.
У Burger King это 2302 документа, из них 1299 с картинкой и этикеткой сразу.

Но датасет — это **всё, что сеть когда-либо вводила**: тесты («PDP Test»),
заглушки («Dummy Item»), снятое, региональное. Что в меню сегодня, знает
документ `menu`: его разделы ссылаются на позиции, комбо и «пикеры»
(один бургер и три его комплекта). Поэтому берём не все `item`, а те, до
которых дотягивается живое меню, — это и есть «в меню сейчас».

RBI держит на одной платформе все свои бренды, поэтому адаптер общий, а
разница между сетями — в трёх строках `Brand`.

Вежливость та же, что везде: один GROQ на весь датасет вместо обхода
двухсот страниц — сети это дешевле, чем любой кроул.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .base import USER_AGENT

API_VERSION = "v2026-04-24"

#: Аллергены RBI → девятка FDA плюс европейские, которые сеть ведёт заодно.
ALLERGENS = ("milk", "eggs", "fish", "shellfish", "treeNuts", "peanuts",
             "wheat", "soy", "sesame",
             "gluten", "celery", "mustard", "lupin", "sulphurDioxide")

#: Ключи этикетки Sanity → наши.
NUTRITION = {
    "calories": "kcal", "proteins": "protein", "carbohydrates": "carbs",
    "fat": "fat", "saturatedFat": "sat_fat", "transFat": "trans_fat",
    "cholesterol": "cholesterol", "sodium": "sodium", "sugar": "sugar",
    "fiber": "fiber",
}


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    project: str
    dataset: str
    #: Документ живого меню. Их в датасете несколько (тест, реорганизация,
    #: «Nutrition Explorer»); этот — тот, что показывает сайт.
    menu_id: str
    domain: str


BURGER_KING = Brand(slug="burger-king", name="Burger King", project="kjfd81ul",
                    dataset="prod_bk_us", menu_id="menu_5492", domain="bk.com")

# Popeyes и Firehouse живут в одном проекте RBI — у каждого свой датасет.
FIREHOUSE = Brand(slug="firehouse-subs", name="Firehouse Subs", project="czqk28jt",
                  dataset="prod_fhs_us", menu_id="7041d454-5910-4521-b4b4-b31087260b6b",
                  domain="firehousesubs.com")

POPEYES = Brand(slug="popeyes", name="Popeyes", project="czqk28jt",
                dataset="prod_plk_us", menu_id="menu_1", domain="popeyes.com")

BRANDS = {b.slug: b for b in (BURGER_KING, FIREHOUSE, POPEYES)}


@dataclass(frozen=True)
class SanityItem:
    """Позиция из Sanity — уже в наших терминах."""
    chain: str
    ext_key: str
    name: str
    category: str | None
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


# ── GROQ ────────────────────────────────────────────────────────────────

#: Поля позиции. `name.en`, а не `name.locale.en`: во фронте это одно и то
#: же после трансформации, в датасете — только `en`.
ITEM_FIELDS = """{
  _id, "name": name.en, "image": image.asset._ref, region,
  "dummy": isDummyItem, "L2": productHierarchy.L2, "L3": productHierarchy.L3,
  nutrition, allergens
}"""

#: Живое меню: разделы → позиции. Ссылка на каждом уровне бывает двух
#: видов — прямая (`options[]->`) и завёрнутая в `option` (у пикеров и
#: слотов комбо: `options[].option->`). У Burger King до позиций три
#: уровня, у Firehouse пять: раздел → пикер → комбо → слот комбо →
#: позиция. Пока уровень понимал только один вид ссылки, слоты комбо
#: обрывали обход, и живое меню Firehouse выглядело как 72 позиции при
#: 753 настоящих. Один уровень принимает оба вида, глубина — с запасом.
_LEAF = ('{ "t": coalesce(@->_type, option->_type),'
         ' "id": coalesce(@->_id, option->_id) }')
_LEVEL = ('{ "t": coalesce(@->_type, option->_type),'
          ' "id": coalesce(@->_id, option->_id),'
          ' "opts": coalesce(@->options, option->options)[]%s }')


def _nested(depth: int) -> str:
    inner = _LEAF
    for _ in range(depth):
        inner = _LEVEL % inner
    return inner


MENU_QUERY = ('*[_id == $menu][0]{ "sections": options[]->{ "name": name.en,'
              ' "opts": options[]%s } }' % _nested(5))


def query(brand: Brand, groq: str, params: dict | None = None) -> object:
    """Один GROQ к публичному CDN Sanity."""
    qs = {"query": groq}
    for key, value in (params or {}).items():
        qs[f"${key}"] = json.dumps(value)
    url = (f"https://{brand.project}.apicdn.sanity.io/{API_VERSION}/data/query/"
           f"{brand.dataset}?{urllib.parse.urlencode(qs)}")
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Origin": f"https://www.{brand.domain}"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)["result"]


def image_url(project: str, dataset: str, ref: str | None, *,
              width: int = 1000) -> str | None:
    """`image-<id>-<w>x<h>-<fmt>` → адрес на CDN.

    Ссылка на ассет хранит размер и формат в самом идентификаторе; CDN
    отдаёт исходник, а параметрами режет под нас — квадрат 1000 в webp
    весит десятки килобайт вместо 400 у исходного PNG.
    """
    if not ref:
        return None
    m = re.match(r"^image-([a-f0-9]+)-(\d+x\d+)-([a-z0-9]+)$", ref)
    if not m:
        return None
    asset, size, fmt = m.groups()
    return (f"https://cdn.sanity.io/images/{project}/{dataset}/{asset}-{size}.{fmt}"
            f"?w={width}&h={width}&fit=max&fm=webp&q=85")


def on_menu_ids(brand: Brand) -> set[str]:
    """Идентификаторы позиций, до которых дотягивается живое меню."""
    tree = query(brand, MENU_QUERY, {"menu": brand.menu_id}) or {}
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if not isinstance(node, dict):
            return
        kind = node.get("_type") or node.get("t")
        ident = node.get("_id") or node.get("id")
        if kind == "item" and ident:
            found.add(ident)
        walk(node.get("opts"))

    walk(tree.get("sections"))
    return found


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def fetch(brand: Brand, *, only_on_menu: bool = True) -> list[SanityItem]:
    """Все позиции сети, годные для каталога.

    Годная — с именем, американская, не заглушка и, если просили, в живом
    меню. Этикетка бывает неполной, это решает кроул своими правилами;
    здесь мы только не выдумываем и не теряем.
    """
    docs = query(brand, f'*[_type == "item" && defined(name.en)]{ITEM_FIELDS}') or []
    live = on_menu_ids(brand) if only_on_menu else None
    source_url = f"https://www.{brand.domain}/menu"

    items: list[SanityItem] = []
    seen_keys: set[str] = set()
    for doc in docs:
        if doc.get("dummy") or doc.get("region") not in (None, "US"):
            continue
        if live is not None and doc["_id"] not in live:
            continue
        name = " ".join(str(doc.get("name", "")).split())
        if not name or re.search(r"\b(test|dummy|placeholder)\b", name, re.I):
            continue

        from ..slug import slugify
        key = slugify(name)
        # Один и тот же бургер лежит в датасете под двумя документами —
        # для разных касс. Имя одно, этикетка одна; вторая копия ничего
        # не добавляет, а ключ у обеих один.
        if key in seen_keys:
            continue
        seen_keys.add(key)

        nutrition = doc.get("nutrition") or {}
        values = {ours: _number(nutrition.get(theirs))
                  for theirs, ours in NUTRITION.items()}
        allergens = tuple(a for a in ALLERGENS
                          if (doc.get("allergens") or {}).get(a))

        items.append(SanityItem(
            chain=brand.name, ext_key=key, name=name,
            category=(doc.get("L2") or "").title() or None,
            source=brand.domain, source_url=source_url,
            image_url=image_url(brand.project, brand.dataset, doc.get("image")),
            allergens=allergens, **values))
    return items
