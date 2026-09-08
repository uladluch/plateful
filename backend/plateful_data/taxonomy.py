"""Разделы меню — одни и те же для всех 96 сетей.

Источник даёт 12 категорий, и они уже единообразны: `Sandwiches`,
`Entrees`, `Beverages` и так далее. Не хватает двух вещей, и обе решаются
правилом, а не разбором сетей по очереди.

**Порядок.** У пака его нет вовсе: разделы шли в порядке первого вхождения,
то есть по алфавиту названий блюд. У McDonald's меню открывалось напитками,
а соусы стояли выше картошки. Порядок задаётся здесь, один на весь каталог,
и едет в паке — значит меняется публикацией, а не релизом.

**Завтрак.** Он не категория, а время дня, и в источнике размазан по
`Sandwiches` (193 позиции), `Entrees` (123) и `Baked Goods`. У McDonald's из
14 «сэндвичей» 11 — завтраки. Вытаскиваем правилом по названию.

Правило намеренно осторожное: одного слова мало. «Bagel» — это и
«Bacon, Egg & Cheese Bagel», и «Blueberry Bagel»; «Burrito» — и
«Steak & Egg Burrito», и «Bean & Cheese Burrito». Поэтому либо слово,
которое само по себе значит завтрак, либо носитель завтрака плюс начинка.
Пропустить завтрак не страшно — он останется в своей категории; записать
в завтрак обед хуже, человек не найдёт блюдо там, где искал.
"""

from __future__ import annotations

import re

BREAKFAST = "Breakfast"

# Порядок разделов. Сначала то, ради чего пришли, в конце — напитки и
# добавки. Архив приложение всегда держит последним, здесь его нет.
SECTION_ORDER = (
    BREAKFAST,
    "Burgers",
    "Sandwiches",
    "Entrees",
    "Pizza",
    "Salads",
    "Soup",
    "Appetizers & Sides",
    "Fried Potatoes",
    "Baked Goods",
    "Desserts",
    "Beverages",
    "Toppings & Ingredients",
)

# Категории, из которых блюдо может уехать в завтрак. Напиток, десерт,
# пицца, салат, суп и добавка завтраком не становятся никогда: кофе в
# восемь утра — всё ещё кофе, и искать его будут в напитках.
_BREAKFAST_SOURCES = frozenset({
    "Sandwiches", "Entrees", "Baked Goods", "Appetizers & Sides", "Fried Potatoes",
})

# Слова, которые сами по себе означают завтрак.
_EXPLICIT = re.compile(
    r"\b(breakfast|mc\s?muffins?|mc\s?griddles?|hot\s?cakes?|pancakes?|"
    r"french toast|omelet(te)?s?|scrambled eggs?|hash\s?browns?|"
    r"oatmeal|grits|benedict|frittata|sausage gravy|egg whites?)\b", re.I)

# Носители завтрака: тесто, на котором его подают. Сами по себе ничего не
# значат — «Blueberry Bagel» это выпечка.
_CARRIERS = re.compile(r"\b(biscuits?|bagels?|croissants?|english muffins?|"
                       r"burritos?|platters?|muffins?)\b", re.I)
# Носители общего назначения: этим нужна именно яичная начинка. «Bacon
# Ranch Sandwich» — обед, «Bacon, Egg & Cheese Sandwich» — завтрак.
_GENERIC_CARRIERS = re.compile(r"\b(sandwich(es)?|wraps?|bowls?|tacos?|"
                               r"flatbreads?|rolls?|toast)\b", re.I)
# Начинки, которые вместе с носителем делают блюдо завтраком.
_FILLINGS = re.compile(r"\b(eggs?|sausages?|bacon|ham|steak|gravy)\b", re.I)
_EGG = re.compile(r"\beggs?\b", re.I)

# «Waffle» слишком занят: вафельный рожок, вафельная картошка, вафельный
# крендель. Настоящую вафлю оставляем источнику.
_NOT_BREAKFAST = re.compile(r"\b(waffle (cone|bowl|fries|potato)|pretzel)\b", re.I)


def is_breakfast(name: str, category: str | None) -> bool:
    if category not in _BREAKFAST_SOURCES:
        return False
    if _NOT_BREAKFAST.search(name):
        return False
    if _EXPLICIT.search(name):
        return True
    if _CARRIERS.search(name) and _FILLINGS.search(name):
        return True
    return bool(_GENERIC_CARRIERS.search(name) and _EGG.search(name))


def section(name: str, category: str | None) -> str | None:
    """Раздел, в котором приложение покажет позицию."""
    if is_breakfast(name, category):
        return BREAKFAST
    return category
