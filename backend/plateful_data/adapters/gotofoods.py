"""Бренды GoTo Foods — Auntie Anne's, Moe's, McAlister's, Jamba и другие.

Семь сетей одной компании живут на одном сайте-движке и в одном
пространстве Contentful (`zqt8tllj2cy0`): разница между ними — только
домен. Как и у RBI в Sanity, это значит, что один разбор покрывает всех.

Меню приходит не запросом, а вместе со страницей — во flight-данных
Next.js App Router. Разметка отдаёт их кусками
`self.__next_f.push([1,"…"])`, которые надо склеить в один поток и уже в
нём искать объекты. В объекте продукта есть имя, снимок на CDN,
аллергены и раздел — всё, кроме этикетки: в `nutrition` у него одни
калории, и то не всегда.

Этикетка лежит рядом, но в другом виде: на странице блюда сеть кладёт
для поисковиков schema.org `NutritionInformation` — калории, жиры,
углеводы, белок и натрий. Пяти полей мало для полной этикетки FDA, но
достаточно, чтобы позиция считалась живой и обновилась: остальное в
каталоге уже есть из гида.

Поэтому обход двухступенчатый: список блюд снимается с одной страницы
меню, а этикетка — со страницы каждого блюда. Это честный обход
собственного меню сети, с паузой и по robots.txt.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

#: Заголовки настоящего браузера тут не нужны: сайт отвечает и нам.
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

#: Куски flight-потока Next.js.
_CHUNK = re.compile(r'self\.__next_f\.push\(\[1,\s*"((?:[^"\\]|\\.)*)"\]\)')

#: Этикетка для поисковиков — единственное место, где есть макросы.
_LABEL = re.compile(r'"nutrition":\{"@type":"NutritionInformation"[^}]*\}')

#: «340 calories», «5g», «990mg» → 340.0, 5.0, 990.0
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")

#: Ключи schema.org → наши.
LABEL_FIELDS = {
    "calories": "kcal", "fatContent": "fat", "carbohydrateContent": "carbs",
    "proteinContent": "protein", "sodiumContent": "sodium",
    "saturatedFatContent": "sat_fat", "transFatContent": "trans_fat",
    "cholesterolContent": "cholesterol", "sugarContent": "sugar",
    "fiberContent": "fiber",
}

#: Девятка FDA в терминах сети.
ALLERGENS = ("milk", "eggs", "fish", "shellfish", "treeNuts", "peanuts",
             "wheat", "soy", "sesame")
_ALLERGEN_ALIASES = {"egg": "eggs", "tree nuts": "treeNuts", "treenuts": "treeNuts",
                     "peanut": "peanuts", "shellfish": "shellfish", "gluten": "wheat"}


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    domain: str


AUNTIE_ANNES = Brand("auntie-anne-s", "Auntie Anne's", "auntieannes.com")
MOES = Brand("moe-s-southwest-grill", "Moe's Southwest Grill", "moes.com")
MCALISTERS = Brand("mcalister-s-deli", "McAlister's Deli", "mcalistersdeli.com")
JAMBA = Brand("jamba-juice", "Jamba Juice", "jamba.com")

BRANDS = {b.slug: b for b in (AUNTIE_ANNES, MOES, MCALISTERS, JAMBA)}


@dataclass(frozen=True)
class Product:
    """Позиция меню — уже в наших терминах."""
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


def flight(html: str) -> str:
    """Склеенный поток flight-данных Next.js.

    Куски приходят по одному на `push` и рвутся посреди значения, поэтому
    искать в них поодиночке бессмысленно: сначала склеить, потом читать.
    """
    return "".join(json.loads('"' + chunk + '"') for chunk in _CHUNK.findall(html))


_DECODER = json.JSONDecoder()


def objects(text: str, marker: str) -> list[dict]:
    """Объекты JSON из потока, в которых встретился `marker`.

    Регулярным выражением объект не вырезать: внутри вложенные скобки и
    экранированные кавычки. Поэтому от каждой находки идём влево до
    открывающей скобки, от которой разбор доходит до конца объекта.
    """
    found: list[dict] = []
    starts: set[int] = set()
    for hit in re.finditer(re.escape(marker), text):
        for start in range(hit.start(), max(-1, hit.start() - 6000), -1):
            if text[start] != "{" or start in starts:
                continue
            try:
                obj, end = _DECODER.raw_decode(text, start)
            except ValueError:
                continue
            if isinstance(obj, dict) and end > hit.start():
                starts.add(start)
                found.append(obj)
                break
    return found


def _number(raw: object) -> float | None:
    if raw is None:
        return None
    match = _NUMBER.search(str(raw))
    return round(float(match.group(0)), 1) if match else None


#: Имя перед этикеткой в том же куске schema.org.
_LD_NAME = re.compile(r'"name":"((?:[^"\\]|\\.)*)"')


def label(html: str, name: str | None = None) -> dict[str, float]:
    """Этикетка со страницы блюда — из schema.org для поисковиков.

    На странице блюда сеть показывает и соседние: этикеток там несколько,
    и первая попавшаяся принадлежит не тому продукту. Берём ту, перед
    которой стоит нужное имя, — schema.org кладёт его в том же объекте.
    """
    stream = flight(html) or html
    fallback: dict[str, float] = {}
    for match in _LABEL.finditer(stream):
        try:
            raw = json.loads("{" + match.group(0) + "}")["nutrition"]
        except ValueError:
            continue
        values = {ours: value for theirs, ours in LABEL_FIELDS.items()
                  if (value := _number(raw.get(theirs))) is not None}
        if not values.get("kcal"):
            continue
        if name is None:
            return values
        names = _LD_NAME.findall(stream[max(0, match.start() - 800):match.start()])
        if names and names[-1].strip().lower() == name.strip().lower():
            return values
        fallback = fallback or values
    # Имя не совпало ни разу — лучше ничего, чем чужие цифры.
    return {} if name is not None else fallback


def _allergens(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[str] = []
    for item in raw:
        name = str(item).strip().lower()
        ours = _ALLERGEN_ALIASES.get(name, name if name in ALLERGENS else None)
        if ours and ours not in out:
            out.append(ours)
    return tuple(out)


def _hero(images: object) -> str | None:
    if not isinstance(images, list):
        return None
    by_type = {i.get("type"): i.get("url") for i in images if isinstance(i, dict)}
    return by_type.get("hero") or by_type.get("thumbnail") or None


def listing(brand: Brand, html: str) -> list[dict]:
    """Сырые продукты со страницы меню — как их отдаёт сеть.

    Одна страница несёт всё меню бренда: разделы там для показа, а
    продукты лежат общим списком.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for product in objects(flight(html), '"seoUrl":'):
        url = product.get("seoUrl")
        name = " ".join(str(product.get("name") or "").split())
        if not url or not name or url in seen:
            continue
        seen.add(url)
        out.append(product)
    return out


def _product_url(brand: Brand, seo_url: str) -> str:
    """`global-lab/classic-pretzels/original-pretzel` → адрес страницы блюда.

    Первый сегмент — служебный («global-lab»), сеть его в адресе не
    показывает.
    """
    tail = seo_url.split("/", 1)[1] if "/" in seo_url else seo_url
    return f"https://www.{brand.domain}/menu/{tail}"


def catalog(brand: Brand) -> list[Product]:
    """Меню бренда одним запросом — без этикетки, зато со снимками.

    Страница меню несёт весь список, поэтому снимки обходятся в один
    запрос на сеть. Этикетка так не берётся: за ней надо на страницу
    каждого блюда, и не у всякого она там есть.
    """
    from ..slug import slugify

    menu_url = f"https://www.{brand.domain}/menu"
    page = curl_get(menu_url, HEADERS, timeout=60)
    if not page:
        raise SystemExit(f"{brand.domain} не отдал меню")

    items: list[Product] = []
    seen: set[str] = set()
    for row in listing(brand, page):
        name = " ".join(str(row.get("name") or "").split())
        key = slugify(name)
        if key in seen:
            continue
        seen.add(key)
        items.append(Product(
            chain=brand.name, ext_key=key, name=name, category=None, serving=None,
            source=brand.domain, source_url=_product_url(brand, str(row.get("seoUrl"))),
            image_url=_hero(row.get("images")),
            allergens=_allergens(row.get("allergens")),
            kcal=_number((row.get("nutrition") or {}).get("calories"))))
    return items


def fetch(brand: Brand, *, pause: float = 1.0, limit: int | None = None,
          log=print) -> list[Product]:
    """Меню бренда: список с одной страницы, этикетка — со страниц блюд.

    Позиции без калорий возвращаются тоже: заводить их кроул не станет, но
    знать, что сеть их подаёт, полезно — иначе они выглядели бы снятыми.
    """
    import time

    from ..slug import slugify

    menu_url = f"https://www.{brand.domain}/menu"
    page = curl_get(menu_url, HEADERS, timeout=60)
    if not page:
        raise SystemExit(f"{brand.domain} не отдал меню")
    rows = listing(brand, page)
    log(f"  меню: {len(rows)} позиций")
    if limit:
        rows = rows[:limit]

    items: list[Product] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, 1):
        name = " ".join(str(row.get("name") or "").split())
        key = slugify(name)
        if key in seen:
            continue
        seen.add(key)

        url = _product_url(brand, str(row.get("seoUrl")))
        detail = curl_get(url, HEADERS, timeout=60) or ""
        values = label(detail, name)
        # Калории сеть показывает и в списке — если на странице блюда
        # этикетки нет, хотя бы они.
        if "kcal" not in values:
            if kcal := _number((row.get("nutrition") or {}).get("calories")):
                values["kcal"] = kcal

        items.append(Product(
            chain=brand.name, ext_key=key, name=name,
            category=(row.get("category") or {}).get("name")
                     if isinstance(row.get("category"), dict) else None,
            serving=None, source=brand.domain, source_url=url,
            image_url=_hero(row.get("images")),
            allergens=_allergens(row.get("allergens")),
            **values))
        if number % 20 == 0:
            log(f"  просмотрено {number}/{len(rows)}")
        time.sleep(pause)
    return items
