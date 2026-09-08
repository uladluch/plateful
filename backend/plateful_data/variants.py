"""Варианты одного блюда: порции и опции.

«Coca Cola, Small» и «Coca Cola, Large» — одно блюдо в двух порциях.
«4 Chicken McNuggets» и «10 Chicken McNuggets» — тоже, только счёт стоит
перед названием. «Big Breakfast» и «Big Breakfast w/ Hotcakes» — не порции,
а два исполнения одного блюда. Во всех трёх случаях в списке должна быть
одна карточка с переключателем, а не четыре карточки колы подряд.

Три правила, по убыванию надёжности:

    Coca Cola, Large          → порция в хвосте после запятой
    10 Chicken McNuggets      → счёт или вес перед названием
    Big Breakfast w/ Hotcakes → опция после «w/»

Считается здесь, а не в приложении: ошибочную склейку тогда чинит
публикация пака, а не релиз в App Store.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .slug import slugify

SIZE = "size"
OPTION = "option"

# Порядок показа для словарных порций. Меньше — левее в переключателе.
_ORDER = {
    "kids": 0, "kid's": 0, "child": 0, "mini": 1, "snack": 1, "jr": 1,
    "extra small": 2, "short": 2, "small": 3, "tall": 4, "cup": 4,
    "regular": 5, "medium": 6, "grande": 6, "bowl": 6,
    "large": 7, "venti": 8, "extra large": 9,
}

_VOLUME = re.compile(r"^\d+(\.\d+)?\s*(fl\s*)?oz$", re.I)
_PORTION = re.compile(r"^\d*\s*slices?$", re.I)
# Мера в хвосте: «6 in», «12"», «2 Liter», «20 fl oz». Начинается с числа —
# значит это размер, а не продолжение названия.
_MEASURE = re.compile(r"^\d+(\.\d+)?\s*(\"|''|in|inch|liter|l|ml|g|oz|lb|pc|ct)?\.?$", re.I)

# Сколько разных блюд должны разделить один и тот же хвост, чтобы он
# считался словом размера этой сети.
MIN_SHARED_BASES = 3
# Длиннее двух слов — это уже не размер, а часть названия: у хвоста
# «Egg & Cheese Biscuit» тоже три разных начала («Bacon», «Sausage»,
# «Steak»), и без ограничения по длине бекон, сосиска и стейк склеились бы
# в одно блюдо.
MAX_LEARNED_WORDS = 2
# Союзы выдают перечисление ингредиентов, а не размер.
_NOT_A_SIZE = re.compile(r"(&|\bw/|\bwith\b|\bfor\b)", re.I)

# Счёт или вес перед названием: «10 Chicken McNuggets», «3 Piece Strips»,
# «12 oz Top Sirloin». Единица необязательна — чаще её просто нет.
_COUNT = re.compile(r"^(\d+(?:\.\d+)?)\s*(oz|lb|pc|pcs|piece|pieces|ct|count)?\s+(\S.*)$",
                    re.I)
# Опция после «w/»: то, чем одно исполнение блюда отличается от другого.
# Только «w/» и «with» — «&» разрезало бы «Bacon, Egg & Cheese Biscuit»
# посередине названия.
_WITH = re.compile(r"\s+w(?:/|ith)\s+", re.I)

# Подпись для того исполнения, у которого добавки нет вовсе.
PLAIN = "Plain"


def _split_tail(name: str) -> tuple[str, str] | None:
    if "," not in name:
        return None
    base, _, tail = name.rpartition(",")
    base, label = base.strip(), tail.strip()
    return (base, label) if base and label else None


def learn_size_words(items) -> dict[str, set[str]]:
    """Сеть → хвосты, которые она использует как размеры.

    Словари размеров у сетей свои: «Shorti» у Wawa, «RT 44» у Sonic,
    «6 in» у Subway, «Venti Iced» у Starbucks, «High Calorie» у Bob Evans.
    Перечислять их по сетям — та самая работа поштучно, которой быть не
    должно, и любая новая сеть её потребует снова.

    Поэтому размер узнаём по поведению: сеть повторяет слово размера у
    многих разных блюд. «Large» стоит у сотни позиций, «Egg & Cheese
    Biscuit» — тоже у нескольких, и от него защищает длина хвоста.
    """
    bases: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in items:
        parsed = _split_tail(item.name)
        if not parsed:
            continue
        base, label = parsed
        if len(label.split()) > MAX_LEARNED_WORDS or _NOT_A_SIZE.search(label):
            continue
        bases[(item.chain, label.lower())].add(base.lower())

    learned: dict[str, set[str]] = defaultdict(set)
    for (chain, label), seen in bases.items():
        if len(seen) >= MIN_SHARED_BASES:
            learned[chain].add(label)
    return learned


def size_label(name: str, known: set[str] = frozenset()) -> tuple[str, str] | None:
    """(название без порции, подпись порции) — или ничего.

    Порция стоит последним сегментом после запятой: «Coca Cola, Large».
    Всё остальное после запятой — часть названия блюда («Cobb Salad,
    w/ Nuggets»), и трогать его нельзя.
    """
    parsed = _split_tail(name)
    if not parsed:
        return None
    base, label = parsed

    key = label.lower()
    if (key in _ORDER or key in known
            or _VOLUME.match(label) or _PORTION.match(label) or _MEASURE.match(label)):
        return base, label
    return None


def count_label(name: str) -> tuple[str, str] | None:
    """«10 Chicken McNuggets» → («Chicken McNuggets», «10»).

    Единица счёта сохраняется, когда она есть: «12 oz» — это размер стейка,
    а голое «12» рядом с «16» на сегменте прочтётся так же, как унции.
    """
    match = _COUNT.match(name)
    if not match:
        return None
    number, unit, base = match.groups()
    return base.strip(), f"{number} {unit.lower()}" if unit else number


def option_label(name: str) -> tuple[str, str] | None:
    """«Big Breakfast w/ Hotcakes» → («Big Breakfast», «Hotcakes»)."""
    parts = _WITH.split(name, maxsplit=1)
    if len(parts) != 2:
        return None
    base, option = (p.strip() for p in parts)
    return (base, option) if base and option else None


def _rank(label: str) -> tuple[int, float, str]:
    key = label.lower()
    if key in _ORDER:
        return (0, _ORDER[key], label)
    if match := re.match(r"^(\d+(?:\.\d+)?)", label):
        # Числовые порции упорядочиваем числом: 4 раньше 10, 12 oz раньше 32 oz.
        return (1, float(match.group(1)), label)
    if label == PLAIN:
        # Блюдо без добавок — первым: от него отсчитываются остальные.
        return (2, -1.0, label)
    return (2, 0.0, label)


def _group_key(base: str) -> str:
    """Ключ группы. Последнее слово в единственном числе.

    «1 Mini Cheeseburger» и «2 Mini Cheeseburgers» — одно блюдо; без этого
    множественное число разводит их по разным группам.
    """
    words = base.split()
    if words and len(words[-1]) > 3 and words[-1].lower().endswith("s"):
        words[-1] = words[-1][:-1]
    return slugify(" ".join(words))


def _parse(name: str, known: set[str] = frozenset()) -> tuple[str, str, str] | None:
    """(база, подпись, вид варианта) — по первому сработавшему правилу."""
    if parsed := size_label(name, known):
        return (*parsed, SIZE)
    if parsed := count_label(name):
        return (*parsed, SIZE)
    if parsed := option_label(name):
        return (*parsed, OPTION)
    return None


def assign_groups(items) -> dict[tuple[str, str], tuple[str, str, int, str]]:
    """(сеть, ext_key) → (ключ группы, подпись, позиция, вид варианта).

    Ключ обязательно с сетью: ext_key уникален только внутри сети, и «Coca
    Cola, Small» есть у половины каталога. Пока ключом был один ext_key,
    сети затирали друг другу позиции — у McDonald's кола получала
    0, 0, 1, 2, потому что последней записывала сеть с тремя размерами.

    Группа заводится только там, где вариантов больше одного: одинокая
    «Apple Slices, 1 Package» переключателя не заслуживает.
    """
    learned = learn_size_words(items)
    buckets: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    bases: dict[tuple[str, str], str] = {}

    for item in items:
        parsed = _parse(item.name, learned.get(item.chain, frozenset()))
        if not parsed:
            continue
        base, label, kind = parsed
        bucket = (item.chain, _group_key(base))
        buckets[bucket].append((item.ext_key, label, kind))
        bases[bucket] = base

    # Блюдо без добавок — участник своей же группы опций: «Big Breakfast»
    # стоит рядом с «Big Breakfast w/ Hotcakes», а не отдельной карточкой.
    plain_of = {(chain, _group_key(base)): base for (chain, _), base in bases.items()}
    for item in items:
        bucket = (item.chain, _group_key(item.name))
        if bucket in plain_of and any(kind == OPTION for _, _, kind in buckets[bucket]):
            buckets[bucket].append((item.ext_key, PLAIN, OPTION))

    assigned: dict[tuple[str, str], tuple[str, str, int, str]] = {}
    for (chain, group_key), members in buckets.items():
        if len(members) < 2:
            continue
        # Смешанную группу — часть порции, часть опции — считаем порциями:
        # порция важнее, из неё складываются калории.
        kind = SIZE if any(k == SIZE for _, _, k in members) else OPTION
        ordered = sorted(members, key=lambda member: _rank(member[1]))
        for position, (ext_key, label, _) in enumerate(ordered):
            assigned[(chain, ext_key)] = (group_key, label, position, kind)
    return assigned
