"""Размерные варианты одного блюда.

«Coca Cola, Small» и «Coca Cola, Large» — это одно блюдо в двух размерах,
а не два блюда. В каталоге MenuStat они лежат отдельными строками, и без
склейки приложение показывает четыре карточки колы подряд.

Группировка считается здесь, а не в приложении: ошибочную склейку тогда
чинит публикация пака, а не релиз в App Store.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .slug import slugify

# Порядок показа. Меньше — левее в переключателе.
_ORDER = {
    "kids": 0, "kid's": 0, "child": 0, "mini": 1, "snack": 1, "jr": 1,
    "extra small": 2, "short": 2, "small": 3, "tall": 4, "cup": 4,
    "regular": 5, "medium": 6, "grande": 6, "bowl": 6,
    "large": 7, "venti": 8, "extra large": 9,
}

_VOLUME = re.compile(r"^\d+(\.\d+)?\s*(fl\s*)?oz$", re.I)
_PORTION = re.compile(r"^\d*\s*slices?$", re.I)


def size_label(name: str) -> tuple[str, str] | None:
    """(название без размера, подпись размера) — или ничего.

    Размер всегда идёт последним сегментом после запятой: «Coca Cola, Large».
    Всё остальное после запятой — часть названия блюда («Cobb Salad w/
    Nuggets»), и трогать его нельзя.
    """
    if "," not in name:
        return None
    base, _, tail = name.rpartition(",")
    label = tail.strip()
    if not label:
        return None

    key = label.lower()
    if key in _ORDER or _VOLUME.match(label) or _PORTION.match(label):
        return base.strip(), label
    return None


def _rank(label: str) -> tuple[int, float, str]:
    key = label.lower()
    if key in _ORDER:
        return (0, _ORDER[key], label)
    if match := re.match(r"^(\d+(?:\.\d+)?)", label):
        # Объёмы упорядочиваем числом: 12 oz раньше 32 oz.
        return (1, float(match.group(1)), label)
    return (2, 0.0, label)


def assign_groups(items) -> dict[tuple[str, str], tuple[str, str, int]]:
    """(сеть, ext_key) → (ключ группы, подпись размера, позиция в переключателе).

    Ключ обязательно с сетью: ext_key уникален только внутри сети, и «Coca
    Cola, Small» есть у половины каталога. По одному ext_key сети затирали
    друг другу позиции — у McDonald\'s кола получала 0, 0, 1, 2 вместо
    0, 1, 2, 3, потому что последней записывала сеть с тремя размерами.

    Группа заводится только там, где вариантов больше одного: одинокая
    «Apple Slices, 1 Package» переключателя не заслуживает.
    """
    buckets: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for item in items:
        parsed = size_label(item.name)
        if not parsed:
            continue
        base, label = parsed
        buckets[(item.chain, slugify(base))].append((item.ext_key, label))

    assigned: dict[tuple[str, str], tuple[str, str, int]] = {}
    for (chain, group_key), members in buckets.items():
        if len(members) < 2:
            continue
        for position, (ext_key, label) in enumerate(
                sorted(members, key=lambda pair: _rank(pair[1]))):
            assigned[(chain, ext_key)] = (group_key, label, position)
    return assigned
