"""Что можно достать со страницы блюда, не зная сети.

Адаптеры McDonald's и Chick-fil-A написаны руками, каждый под свой сайт.
Так нельзя масштабировать: сетей 96, и третья потребует третьего разбора
с нуля. Между тем сайты сетей похожи сильнее, чем кажется — почти все
собраны на одних и тех же движках и выкладывают блюдо в одном из трёх
машиночитаемых видов:

    1. JSON-LD    <script type="application/ld+json"> со schema.org
                  Product / MenuItem и вложенным NutritionInformation.
                  Это то, что сайты кладут ради Google, и потому оно
                  аккуратное и стабильное.
    2. JSON в HTML   __NEXT_DATA__ у Next.js, data-wp-context у WordPress,
                  просто "nutrition":[...] — данные для гидратации фронта.
    3. Open Graph  og:title и og:image. Названия и снимка хватает, чтобы
                  сверить меню и забрать графику, даже когда цифр нет.

Извлекатели идут лесенкой и складываются: каждый добавляет то, чего не
нашли предыдущие. Сеть, у которой сработал любой из трёх, подключается
без своего кода — нужен только адрес меню.

Разведка — `backend/scripts/probe_chain.py`: показывает по одной странице,
какой вид у сети и что с него читается.
"""

from __future__ import annotations

import html as html_entities
import json
import re
from dataclasses import dataclass, replace
from urllib.parse import urljoin, urlparse

from .base import to_number

# Поля этикетки в том виде, в каком их называет schema.org.
_SCHEMA_NUTRIENTS = {
    "calories": "kcal",
    "proteinContent": "protein",
    "carbohydrateContent": "carbs",
    "fatContent": "fat",
    "sugarContent": "sugar",
    "saturatedFatContent": "sat_fat",
    "transFatContent": "trans_fat",
    "cholesterolContent": "cholesterol",
    "sodiumContent": "sodium",
    "fiberContent": "fiber",
}

# Те же поля, как их называют фронтенды сетей. Ключи приходят и в
# snake_case, и в camelCase, поэтому сравниваем по нормализованному виду.
_LOOSE_NUTRIENTS = {
    "calories": "kcal", "energy": "kcal", "kcal": "kcal",
    "protein": "protein",
    "carbs": "carbs", "carbohydrates": "carbs", "totalcarbohydrates": "carbs",
    "fat": "fat", "totalfat": "fat",
    "sugar": "sugar", "sugars": "sugar", "totalsugars": "sugar",
    "saturatedfat": "sat_fat", "satfat": "sat_fat",
    "transfat": "trans_fat", "transfattyacid": "trans_fat",
    "cholesterol": "cholesterol",
    "sodium": "sodium",
    "fiber": "fiber", "dietaryfiber": "fiber",
}

NUTRIENTS = ("kcal", "protein", "carbs", "fat",
             "sugar", "sat_fat", "trans_fat", "cholesterol", "sodium", "fiber")

# Потолки правдоподобия. Во вшитом JSON лежит всё состояние страницы, и
# ключ «calories» там встречается не только у еды: разведка по Taco Bell
# принесла блюдо на 6 700 205 ккал — это был чужой идентификатор, из
# которого `to_number` выкусил цифры. Число вне диапазона — не число.
_CEILINGS = {"kcal": 5000.0, "protein": 250.0, "carbs": 500.0, "fat": 400.0,
             "sugar": 500.0, "sat_fat": 200.0, "trans_fat": 100.0,
             "cholesterol": 5000.0, "sodium": 30000.0, "fiber": 200.0}

# Одинокий «calories» посреди чужого JSON — почти наверняка совпадение.
# У настоящего блока питания полей несколько.
MIN_NUTRIENTS_PER_BLOCK = 2


def _plausible(field: str, value: float | None) -> float | None:
    ceiling = _CEILINGS.get(field)
    if value is None or value < 0 or (ceiling and value > ceiling):
        return None
    return value


@dataclass(frozen=True)
class PageFacts:
    """Всё, что удалось прочитать со страницы одного блюда."""

    name: str | None = None
    photo: str | None = None
    allergens: str | None = None
    ingredients: str | None = None

    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    sugar: float | None = None
    sat_fat: float | None = None
    trans_fat: float | None = None
    cholesterol: float | None = None
    sodium: float | None = None
    fiber: float | None = None

    #: Какие извлекатели сработали. Нужно для разведки: по нему видно,
    #: чем сеть отдаёт данные и стоит ли её брать.
    shapes: tuple[str, ...] = ()

    @property
    def has_nutrition(self) -> bool:
        return self.kcal is not None

    def merged(self, other: "PageFacts") -> "PageFacts":
        """Дополняет пустые поля значениями из `other`. Свои не трогает."""
        filled = {
            field: getattr(self, field) if getattr(self, field) is not None
            else getattr(other, field)
            for field in ("name", "photo", "allergens", "ingredients", *NUTRIENTS)
        }
        shapes = self.shapes + tuple(s for s in other.shapes if s not in self.shapes)
        return replace(self, **filled, shapes=shapes)


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z]", "", str(key).lower())


def _walk(node):
    """Все словари внутри произвольного JSON."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


# ── 1. JSON-LD ───────────────────────────────────────────────────────────

_LD = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
_PRODUCT_TYPES = {"product", "menuitem", "recipe", "fooditem"}


def from_json_ld(html: str) -> PageFacts:
    facts = PageFacts()
    for block in _LD.findall(html):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if not any(str(t).lower() in _PRODUCT_TYPES for t in types if t):
                continue

            values: dict[str, object] = {}
            if name := node.get("name"):
                values["name"] = html_entities.unescape(str(name)).strip()
            image = node.get("image")
            if isinstance(image, dict):
                image = image.get("url")
            if isinstance(image, list):
                image = next((i for i in image if isinstance(i, str)), None)
            if isinstance(image, str):
                values["photo"] = image

            nutrition = node.get("nutrition")
            if isinstance(nutrition, dict):
                for key, field in _SCHEMA_NUTRIENTS.items():
                    if key in nutrition:
                        if (n := _plausible(field, to_number(nutrition[key]))) is not None:
                            values[field] = n

            if values:
                facts = facts.merged(PageFacts(**values, shapes=("json-ld",)))
    return facts


# ── 2. JSON, вшитый в разметку ───────────────────────────────────────────

_BLOBS = (
    # Next.js кладёт всё состояние страницы одним куском.
    re.compile(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S),
    # WordPress Interactivity API — так отдаёт Chick-fil-A.
    re.compile(r"data-wp-context='(\{.*?\})'", re.S),
    # Голый массив нутриентов рядом с разметкой.
    re.compile(r'("nutrition"\s*:\s*\[.*?\])', re.S),
)

_ALLERGEN_KEYS = ("allergen", "allergens", "itemallergen", "containsallergens")
_INGREDIENT_KEYS = ("ingredients", "ingredientstatement", "itemingredientstatement")


def _nutrition_from_rows(rows) -> dict[str, float]:
    """[{"key":"calories","value":420}, ...] → {"kcal": 420.0}."""
    found: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _normalized_key(row.get("key") or row.get("label") or row.get("name") or "")
        field = _LOOSE_NUTRIENTS.get(key)
        value = to_number(row.get("value") if "value" in row else row.get("amount"))
        if field and (checked := _plausible(field, value)) is not None:
            found.setdefault(field, checked)
    return found


def from_embedded_json(html: str) -> PageFacts:
    facts = PageFacts()
    for pattern in _BLOBS:
        for block in pattern.findall(html):
            text = block.strip()
            if not text.startswith("{"):
                text = "{" + text + "}"
            try:
                data = json.loads(html_entities.unescape(text))
            except json.JSONDecodeError:
                continue

            values: dict[str, object] = {}
            for node in _walk(data):
                # Питание собираем поблочно: принимаем только те узлы, где
                # полей несколько. Иначе одинокий чужой ключ проезжает как
                # калорийность блюда.
                block: dict[str, float] = {}

                rows = node.get("nutrition")
                if isinstance(rows, list):
                    block.update(_nutrition_from_rows(rows))
                if isinstance(rows, dict):
                    for key, value in rows.items():
                        field = _LOOSE_NUTRIENTS.get(_normalized_key(key))
                        if field and (n := _plausible(field, to_number(value))) is not None:
                            block.setdefault(field, n)

                for key, value in node.items():
                    normalized = _normalized_key(key)
                    if normalized in _ALLERGEN_KEYS and isinstance(value, str) and value.strip():
                        values.setdefault("allergens", value.strip())
                        continue
                    if normalized in _INGREDIENT_KEYS and isinstance(value, str) and value.strip():
                        values.setdefault("ingredients", value.strip())
                        continue
                    field = _LOOSE_NUTRIENTS.get(normalized)
                    if field and isinstance(value, (int, float, str)):
                        if (n := _plausible(field, to_number(value))) is not None:
                            block.setdefault(field, n)

                if len(block) >= MIN_NUTRIENTS_PER_BLOCK:
                    for field, value in block.items():
                        values.setdefault(field, value)

            if values:
                facts = facts.merged(PageFacts(**values, shapes=("embedded-json",)))
    return facts


# ── 3. Open Graph ────────────────────────────────────────────────────────

_META = re.compile(
    r'<meta[^>]+(?:property|name)="og:(title|image)"[^>]+content="([^"]*)"', re.I)
# Хвост вроде «Nutrition and Ingredients | Chick-fil-A» — не часть названия.
#
# Дефис считается разделителем только с пробелами по обе стороны. Без этого
# «Chick-fil-A® Nuggets» превращалось в «Chick»: дефис внутри бренда ничем
# не отличался от тире между названием и хвостом, а `sub` берёт самое левое
# совпадение. Сеть с дефисом в названии — не редкость, а половина рынка.
_TITLE_TAIL = re.compile(r"\s*\|\s*[^|]*$|\s+[–—-]\s+.*$")


def from_open_graph(html: str, *, strip_tail: bool = True) -> PageFacts:
    found: dict[str, str] = {}
    for key, value in _META.findall(html):
        found.setdefault(key.lower(), html_entities.unescape(value).strip())

    values: dict[str, object] = {}
    if title := found.get("title"):
        values["name"] = _TITLE_TAIL.sub("", title).strip() if strip_tail else title
    if image := found.get("image"):
        values["photo"] = image
    return PageFacts(**values, shapes=("open-graph",)) if values else PageFacts()


# ── Всё вместе ───────────────────────────────────────────────────────────

def read_page(html: str) -> PageFacts:
    """Лесенка извлекателей: каждый добавляет то, чего не нашли раньше.

    Порядок — по убыванию надёжности. JSON-LD сеть кладёт ради поисковиков
    и потому держит в порядке; вшитый JSON — внутренняя кухня фронта и
    меняется чаще; Open Graph даёт только имя и картинку, зато есть почти
    везде.
    """
    facts = from_json_ld(html)
    facts = facts.merged(from_embedded_json(html))
    return facts.merged(from_open_graph(html))


def item_links(html: str, base_url: str, *, prefix: str | None = None) -> list[str]:
    """Ссылки на страницы блюд: свой хост, нужный путь, без повторов.

    `prefix` — начало пути раздела меню («/menu»). Без него берём все
    внутренние ссылки, что годится для разведки, но не для обхода.
    """
    host = urlparse(base_url).netloc
    prefix = prefix or urlparse(base_url).path.rstrip("/")

    links: dict[str, None] = {}
    for href in re.findall(r'href="([^"#?]+)"', html):
        url = urljoin(base_url, html_entities.unescape(href))
        parsed = urlparse(url)
        if parsed.netloc != host or not parsed.path.startswith(prefix):
            continue
        if parsed.path.rstrip("/") == prefix:
            continue
        links[url.rstrip("/")] = None
    return list(links)
