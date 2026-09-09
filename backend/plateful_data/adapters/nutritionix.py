"""Этикетка сети со страницы её поставщика данных о питании.

Закон о маркировке меню обязывает сети публиковать этикетку, но считает и
публикует её за них, как правило, не сама сеть, а подрядчик — Nutritionix
(Syndigo). Сеть загружает туда свои цифры, а тот показывает их и на сайте
сети (виджет «Nutrition & Allergen Info», который стоит у Jersey Mike's,
Panera, Taco Bell и десятков других), и у себя по постоянному адресу
`nutritionix.com/<сеть>/menu/premium`.

Для нас это разом закрывает то, чего не давал срез MenuStat: **свежую
этикетку почти по всей базе**. Из девяноста сетей каталога страница есть у
восьмидесяти четырёх. Отдаётся обычным запросом, robots.txt разрешает.

Что там есть: калории, жиры, насыщенные, транс, холестерин, натрий,
углеводы, клетчатка, сахар и белок — то есть вся десятка FDA, — плюс
разделы меню и размер прямо в названии позиции («#1 BLT, Bowl»).
Чего нет: снимков. Их по-прежнему берём у самой сети.

Набор колонок у брендов разный: у одних есть «Calories from Fat», у
других «Added Sugars». Поэтому шапку читаем с каждой страницы, а не
зашиваем — раскладка тут не постоянная, в отличие от гидов в PDF.

Права. Цифры принадлежат сетям и опубликованы ими же — это те самые
значения, что стоят на их собственных сайтах, только собранные в одном
месте. Источником в каталоге пишем адрес, откуда взяли, а не сеть: обещание
«показываем, откуда цифра» держится ровно тогда, когда мы не выдаём чужую
страницу за свою.
"""

from __future__ import annotations

import html as html_entities
import re
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

DOMAIN = "nutritionix.com"
MENU_URL = "https://www.nutritionix.com/{slug}/menu/premium"

#: Наш слаг сети → её слаг у поставщика. Угадывается почти всегда, но
#: не всегда: «Dunkin' Donuts» там просто `dunkin`, «Checker's
#: Drive-In/Rallys» — `checkers`, «Dickey's Barbeque Pit» пишется
#: через `barbecue`. Поэтому карта, а не правило.
#:
#: Шести сетей каталога у поставщика нет вовсе: 7-Eleven, BJ's,
#: Boston Market, Captain D's, Casey's и Perkins.
SLUGS = {
    "applebee-s": "applebees",
    "arby-s": "arbys",
    "auntie-anne-s": "auntie-annes",
    "baskin-robbins": "baskin-robbins",
    "bob-evans": "bob-evans",
    "bojangles": "bojangles",
    "bonefish-grill": "bonefish-grill",
    "burger-king": "burger-king",
    "california-pizza-kitchen": "california-pizza-kitchen",
    "carl-s-jr": "carls-jr",
    "carrabba-s-italian-grill": "carrabbas-italian-grill",
    "checker-s-drive-in-rallys": "checkers",
    "chick-fil-a": "chick-fil-a",
    "chili-s": "chilis",
    "chipotle": "chipotle",
    "chuck-e-cheese": "chuck-e-cheeses",
    "church-s-chicken": "churchs-chicken",
    "ci-ci-s-pizza": "cicis-pizza",
    "culver-s": "culvers",
    "dairy-queen": "dairy-queen",
    "del-taco": "del-taco",
    "denny-s": "dennys",
    "dickey-s-barbeque-pit": "dickeys-barbecue-pit",
    "dominos": "dominos",
    "dunkin-donuts": "dunkin",
    "einstein-bros": "einstein-bros-bagels",
    "el-pollo-loco": "el-pollo-loco",
    "famous-dave-s": "famous-daves",
    "firehouse-subs": "firehouse-subs",
    "five-guys": "five-guys",
    "friendly-s": "friendlys",
    "frisch-s-big-boy": "frischs-big-boy",
    "golden-corral": "golden-corral",
    "hardee-s": "hardees",
    "hooters": "hooters",
    "ihop": "ihop",
    "in-n-out-burger": "in-n-out-burger",
    "jack-in-the-box": "jack-in-the-box",
    "jamba-juice": "jamba",
    "jason-s-deli": "jasons-deli",
    "jersey-mike-s-subs": "jersey-mikes-subs",
    "jimmy-john-s": "jimmy-johns",
    "joe-s-crab-shack": "joes-crab-shack",
    "kfc": "kfc",
    "krispy-kreme": "krispy-kreme",
    "krystal": "krystal",
    "little-caesars": "little-caesars-pizza",
    "long-john-silver-s": "long-john-silvers",
    "longhorn-steakhouse": "longhorn-steakhouse",
    "marco-s-pizza": "marcos-pizza",
    "mcalister-s-deli": "mcalisters-deli",
    "mcdonald-s": "mcdonalds",
    "moe-s-southwest-grill": "moes-southwest-grill",
    "noodles-company": "noodles-company",
    "o-charley-s": "ocharleys",
    "olive-garden": "olive-garden",
    "on-the-border": "on-the-border-mexican-grill-cantina",
    "outback-steakhouse": "outback-steakhouse",
    "panda-express": "panda-express",
    "panera-bread": "panera-bread",
    "papa-john-s": "papa-johns",
    "papa-murphy-s": "papa-murphys",
    "pf-chang-s": "pf-changs",
    "pizza-hut": "pizza-hut",
    "popeyes": "popeyes",
    "potbelly-sandwich-shop": "potbelly",
    "qdoba": "qdoba",
    "quiznos": "quiznos",
    "red-lobster": "red-lobster",
    "red-robin": "red-robin",
    "romano-s-macaroni-grill": "romanos-macaroni-grill",
    "round-table-pizza": "round-table-pizza",
    "ruby-tuesday": "ruby-tuesday",
    "sbarro": "sbarro",
    "sheetz": "sheetz",
    "sonic": "sonic",
    "starbucks": "starbucks",
    "steak-n-shake": "steak-n-shake",
    "subway": "subway",
    "taco-bell": "taco-bell",
    "tgi-friday-s": "tgi-fridays",
    "the-capital-grille": "the-capital-grille",
    "tim-hortons": "tim-hortons",
    "wawa": "wawa",
    "wendy-s": "wendys",
    "whataburger": "whataburger",
    "white-castle": "white-castle",
    "wingstop": "wingstop",
    "yard-house": "yard-house",
    "zaxby-s": "zaxbys",
}

#: Шапка колонки: «Total Fat (g) Sort by Total Fat (grams)» — нам нужна
#: часть до «Sort by».
_HEADER = re.compile(r'<th[^>]*id="(inmGrid_c\d+)"[^>]*>(.*?)</th>', re.S)
_SORT_TAIL = re.compile(r"\s*Sort by.*$", re.I | re.S)

#: Строка блюда и её клетки. Значение берём из `title`, а не из текста
#: клетки: там оно с единицей и полное — «1,050mg Sodium» против «1,050»,
#: и «<5mg Cholesterol» против обрезанного «5».
_ROW = re.compile(r'<tr class="(?:odd|even)">(.*?)</tr>', re.S)
_NAME = re.compile(r'class="nmItem"[^>]*title="([^"]+)"')
_CELL = re.compile(r'<td class="col" title="([^"]*)"[^>]*headers="(inmGrid_c\d+)"')

#: Заголовок раздела меню.
_SECTION = re.compile(r'<tr class="subCategory">.*?<h3>(.*?)</h3>', re.S)
#: Строки идут вперемешку с заголовками — режем документ по ним.
_ROW_OR_SECTION = re.compile(
    r'<tr class="subCategory">.*?<h3>(?P<section>.*?)</h3>'
    r'|<tr class="(?:odd|even)">(?P<row>.*?)</tr>', re.S)

#: Названия колонок → наши поля. Всё, чего нет в словаре, пропускаем:
#: «Calories from Fat» и «Added Sugars» мы не ведём.
COLUMNS = {
    "calories": "kcal",
    "total fat": "fat",
    "saturated fat": "sat_fat",
    "trans fat": "trans_fat",
    "cholesterol": "cholesterol",
    "sodium": "sodium",
    "total carbohydrates": "carbs",
    "total carbohydrate": "carbs",
    "carbohydrates": "carbs",
    "dietary fiber": "fiber",
    "sugars": "sugar",
    "total sugars": "sugar",
    "protein": "protein",
}

#: Число из «1,050mg Sodium», «<5mg Cholesterol», «470 Calories».
_NUMBER = re.compile(r"<?\s*(-?[\d,]+(?:\.\d+)?)")


@dataclass(frozen=True)
class Item:
    """Позиция со страницы поставщика — уже в наших терминах."""
    chain: str
    ext_key: str
    name: str
    category: str | None
    serving: str | None
    source: str
    source_url: str
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


def _clean(raw: str) -> str:
    return " ".join(html_entities.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


def columns(page: str) -> dict[str, str]:
    """Идентификатор колонки → наше поле. Читается с самой страницы."""
    found: dict[str, str] = {}
    for ident, title in _HEADER.findall(page):
        label = _SORT_TAIL.sub("", _clean(title)).strip()
        # «Total Fat (g)» → «total fat»
        key = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip().lower()
        if field := COLUMNS.get(key):
            found[ident] = field
    return found


def number(raw: str) -> float | None:
    """«1,050mg Sodium» → 1050.0.

    «<1g» читаем как единицу, а не как ноль и не как половину: сеть
    говорит «меньше грамма», и взять названную границу — единственное
    чтение, которое ничего не выдумывает. Для сахара и натрия оно к тому
    же осторожное в нужную сторону.
    """
    if not raw:
        return None
    match = _NUMBER.search(html_entities.unescape(raw))
    if not match:
        return None
    try:
        return round(float(match.group(1).replace(",", "")), 1)
    except ValueError:
        return None


def parse(page: str, chain: str, url: str) -> list[Item]:
    """Все позиции со страницы бренда."""
    from ..slug import slugify

    fields = columns(page)
    if len(fields) < 4:
        raise SystemExit(f"на {url} не разобралась шапка таблицы: {fields}")

    items: list[Item] = []
    seen: set[str] = set()
    section: str | None = None
    for match in _ROW_OR_SECTION.finditer(page):
        if match.group("section") is not None:
            section = _clean(match.group("section")) or None
            continue
        row = match.group("row")
        name_match = _NAME.search(row)
        if not name_match:
            continue
        name = _clean(name_match.group(1))
        key = slugify(name)
        # Одно и то же блюдо стоит в нескольких разделах — «Favorites» и
        # своём. Берём первое вхождение: у него раздел настоящий.
        if not key or key in seen:
            continue
        seen.add(key)

        values = {field: number(raw)
                  for raw, ident in _CELL.findall(row)
                  if (field := fields.get(ident))}
        items.append(Item(
            chain=chain, ext_key=key, name=name,
            category=section, serving=None,
            source=DOMAIN, source_url=url,
            **{f: v for f, v in values.items() if v is not None}))
    return items


def fetch(slug: str, chain: str) -> list[Item]:
    """Этикетка сети по **нашему** слагу."""
    their = SLUGS.get(slug)
    if not their:
        raise SystemExit(
            f"{slug} не описан в nutritionix.SLUGS — у поставщика такой сети нет")
    url = MENU_URL.format(slug=their)
    page = curl_get(url, {"User-Agent": USER_AGENT}, timeout=90)
    if not page:
        raise SystemExit(f"{url} не открылся")
    return parse(page, chain, url)
