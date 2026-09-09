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


# ── Сопоставление снимков ───────────────────────────────────────────────
#
# У снимка правила мягче, чем у цифр, и по делу: этикетка у стакана 16 и
# 20 унций разная, а фотография — одна и та же. Более того, сеть её одну и
# снимает: в описи ассетов Panera на «Cafe Blend Light Roast Coffee» лежит
# один файл, а в каталоге у него четыре строки с разными порциями.
#
# Поэтому здесь, в отличие от `match_all`, мера порции из имени убирается,
# а один снимок разрешено отдать нескольким строкам каталога. Для цифр так
# делать нельзя — там подмена размера означает выдуманное расхождение.

#: Мера в названии: «16 fl oz», «(473 mL)», «2 oz», «12 inch».
_MEASURE = re.compile(
    r"\(?\b\d+(?:\.\d+)?\s*(?:fl\s*)?(?:oz|ml|l|g|kg|lb|inch|in|cal)\b[^,()]*\)?",
    re.I)
#: Довески подачи, которые к самому блюду отношения не имеют.
_SERVING_WORDS = re.compile(
    r"\b(?:with\s+ice|bottle|can|jug|group|serves\s+\d+|drive\s*-?\s*thru)\b", re.I)


def dish(name: str) -> str:
    """Имя блюда без мер и подачи — то, что видно на фотографии."""
    text = _MEASURE.sub(" ", name)
    text = _SERVING_WORDS.sub(" ", text)
    # Пустые скобки и повисшие разделители после вычистки.
    text = re.sub(r"\(\s*\)|\s+-\s+$|,\s*$", " ", text)
    return comparable(text)


#: Сходство, ниже которого не смотрим даже при полном вхождении слов.
#: Между ним и обычным порогом лежат промахи на волосок: «Muffin —
#: Blueberry» против «blueberry muffin paradise» — 0.78, и это одно блюдо.
NEAR_THRESHOLD = 0.75


def _covers(short: str, long: str) -> bool:
    """Все слова короткого имени есть в длинном.

    Одного сходства строк мало: сеть добавляет к имени слово-другое
    («paradise», «catering»), и длина штрафует верную пару. Но и одного
    вхождения мало — «banana» лежит в «banana bread» и в «banana
    smoothie». Поэтому спрашиваем оба условия сразу.
    """
    left, right = set(short.split()), set(long.split())
    if len(left) > len(right):
        left, right = right, left
    return bool(left) and left <= right


def photo_pairs(shots, stored: dict[str, dict], *,
                threshold: float = MATCH_THRESHOLD) -> dict[str, object]:
    """Ключ строки каталога → снимок, который ей подходит.

    Снимок может достаться нескольким строкам: у блюда с четырьмя
    порциями фотография одна.
    """
    by_dish: dict[str, list] = {}
    for shot in shots:
        by_dish.setdefault(dish(shot.name), []).append(shot)

    chosen: dict[str, object] = {}
    for key, record in stored.items():
        # Гид уточняет имя разделом и подачей: «Carbonara, Chicken Subs,
        # Small Sub». Снимку это лишнее — он у блюда один на все подачи,
        # поэтому пробуем и голову имени, до первой запятой.
        head = record["name"].split(",", 1)[0]
        for wanted in dict.fromkeys((dish(record["name"]), dish(head))):
            if not wanted:
                continue
            if exact := by_dish.get(wanted):
                chosen[key] = exact[0]
                break
        if key in chosen:
            continue
        wanted = dish(record["name"].split(",", 1)[0]) or dish(record["name"])
        if not wanted:
            continue
        best_shot, best_ratio, best_name = None, 0.0, ""
        for name, group in by_dish.items():
            ratio = difflib.SequenceMatcher(None, wanted, name).ratio()
            if ratio > best_ratio:
                best_shot, best_ratio, best_name = group[0], ratio, name
        if best_shot is None:
            continue
        if best_ratio >= threshold or (best_ratio >= NEAR_THRESHOLD
                                       and _covers(wanted, best_name)):
            chosen[key] = best_shot
    return chosen


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
                # При равном сходстве строку занимает пара с одинаковым
                # ключом: «Small Barq's Root Beer» и «Small Barqs Root Beer»
                # оба дают 1.0 против одной строки, и если её займёт чужой,
                # свой пойдёт заводиться под уже занятый ключ.
                pairs.append((ratio, item.ext_key == key, item.ext_key, key))

    pairs.sort(reverse=True)
    matched: dict[str, dict] = {}
    used: set[str] = set()

    for ratio, _same_key, live_key, stored_key in pairs:
        if live_key in matched or stored_key in used:
            continue
        matched[live_key] = stored[stored_key]
        used.add(stored_key)

    return matched, best
