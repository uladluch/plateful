"""Сопоставление позиции с сайта сети и позиции в каталоге.

MenuStat 2018 писал «Chick Fil a Nuggets», сайт пишет «Chick-fil-A® Nuggets»,
и `slugify` даёт для них разные ключи. Поэтому имена сравниваются нестрого —
но с двумя условиями, каждое из которых оплачено ошибкой:

* **Размер и количество совпадают точно.** «4 Grilled Nuggets» и «8 Grilled
  Nuggets» — разные блюда, отличаются вдвое по всему, а по строке почти
  неразличимы. Подменить одно другим значит выдумать расхождение.
* **Одна запись каталога занимается один раз.** Пока это не соблюдалось,
  несколько живых позиций указывали на одну строку, и отчёт показывал её
  дважды с разными числами.

Живёт отдельно от вызывающих: правило нужно и сверке (`audit_chain.py`), и
кроулу (`crawl_chain.py`). Разъедься они — одна и та же пара позиций
считалась бы то одним блюдом, то разными.
"""

from __future__ import annotations

import difflib
import re

# Ниже этого сходства имён считаем, что позиция не найдена.
MATCH_THRESHOLD = 0.82

# Хвост со страниц сети: «… Nutrition and Ingredients».
_PAGE_SUFFIX = re.compile(r"\s*nutrition and ingredients\s*$")
_BRAND_WORDS = re.compile(r"\b(chick fil a|chickfila|mcdonalds)\b")

# Размер — не украшение названия, а другая позиция.
_SIZE_WORDS = {"small", "medium", "large", "kids", "jr"}

# Единица счёта. Блюдо отличает число, а не слово при нём: «8 ct Nuggets»
# и «8 Nuggets» — одно и то же, и пока «ct» попадало в размер, сайт и
# каталог расходились на пустом месте.
_COUNT_UNITS = {"ct", "count", "pc", "pcs", "piece", "pieces"}

# Формы одного слова. «Kid's Meal» на сайте и «Kids Meal» в каталоге — одна
# позиция; притяжательное «'s» до этого оставляло висеть отдельное «s».
_SYNONYMS = {"kid": "kids", "childs": "kids", "child": "kids"}


def normalized(name: str) -> str:
    text = name.lower().replace("®", " ").replace("™", " ").replace("’", "'")
    text = _PAGE_SUFFIX.sub("", text)
    # Притяжательное съедаем вместе с апострофом, иначе «kid's» даёт «kid s».
    text = re.sub(r"'s\b", "s", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    words = [_SYNONYMS.get(w, w) for w in _BRAND_WORDS.sub(" ", text).split()]
    return " ".join(w for w in words if w not in _COUNT_UNITS)


def portion(name: str) -> frozenset[str]:
    """Числа и слова размера из названия. Совпадать обязаны точно."""
    words = normalized(name).split()
    return frozenset(w for w in words if w.isdigit() or w in _SIZE_WORDS)


def comparable(name: str) -> str:
    """Имя без бренда, размеров и порядка слов — для нестрогого сравнения."""
    words = [w for w in normalized(name).split()
             if not w.isdigit() and w not in _SIZE_WORDS]
    return " ".join(sorted(words))


def similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, comparable(left), comparable(right)).ratio()


def match_all(live, stored: dict[str, dict], *,
              threshold: float = MATCH_THRESHOLD
              ) -> tuple[dict[str, dict], dict[str, float]]:
    """Сопоставляет один к одному.

    `live` — позиции с сайта (нужны `.ext_key` и `.name`), `stored` —
    каталог по ключу. Возвращает пары «ключ живой позиции → запись
    каталога» и лучшее достигнутое сходство для каждой живой позиции:
    по нему видно, промахнулись мы на волосок или не нашли вовсе.
    """
    pairs: list[tuple[float, str, str]] = []
    best: dict[str, float] = {}

    for item in live:
        size = portion(item.name)
        for key, record in stored.items():
            ratio = similarity(item.name, record["name"])
            # Лучшее сходство считаем по всем кандидатам, а не только по
            # прошедшим порог: иначе у каждой непойманной позиции в отчёте
            # стоит ноль, и «промахнулись на волосок» неотличимо от
            # «такого блюда у нас нет». Ровно там, где диагностика и нужна.
            best[item.ext_key] = max(best.get(item.ext_key, 0.0), ratio)
            if ratio >= threshold and portion(record["name"]) == size:
                pairs.append((ratio, item.ext_key, key))

    pairs.sort(reverse=True)
    matched: dict[str, dict] = {}
    used: set[str] = set()

    for ratio, live_key, stored_key in pairs:
        if live_key in matched or stored_key in used:
            continue
        matched[live_key] = stored[stored_key]
        used.add(stored_key)

    return matched, best
