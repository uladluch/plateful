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
import unicodedata

# Ниже этого сходства имён считаем, что позиция не найдена.
MATCH_THRESHOLD = 0.82

# Хвост со страниц сети: «… Nutrition and Ingredients».
_PAGE_SUFFIX = re.compile(r"\s*nutrition and ingredients\s*$")
_BRAND_WORDS = re.compile(r"\b(chick fil a|chickfila|mcdonalds)\b")

# Размер — не украшение названия, а другая позиция. Слова здесь работают
# в обе стороны: `portion` требует их точного совпадения (значит «Giant» и
# «Mini» друг с другом не спутать), а `comparable` их выбрасывает из
# сравнения имён (значит «#1 BLT» и «BLT, Giant» — одно блюдо).
_SIZE_WORDS = {"small", "medium", "large", "kids", "jr", "giant", "mini",
               # Размеры Starbucks: у него это единственное, чем «Latte,
               # Tall» отличается от «Latte, Venti», и без них напиток
               # четырежды считался бы одним и тем же блюдом.
               "short", "tall", "grande", "venti", "trenta"}

# Подача — не размер, но для **снимка** такая же мелочь: сеть снимает
# блюдо один раз, а не отдельно в обёртке и в миске. Отбрасываем только
# при сопоставлении снимков: для цифр обёртка и миска — разные позиции с
# разной этикеткой.
# «Single» и «double» сюда не входят: двойной чизбургер выглядит иначе,
# чем одинарный, и пока они здесь были, «Whopper» получал снимок
# «Double Whopper».
_SERVING_SHAPES = {"regular", "wrap", "bowl", "tub", "sub", "half", "whole", "combo"}

# Единица счёта. Блюдо отличает число, а не слово при нём: «8 ct Nuggets»
# и «8 Nuggets» — одно и то же, и пока «ct» попадало в размер, сайт и
# каталог расходились на пустом месте.
_COUNT_UNITS = {"ct", "count", "pc", "pcs", "piece", "pieces"}

# Формы одного слова. «Kid's Meal» на сайте и «Kids Meal» в каталоге — одна
# позиция; притяжательное «'s» до этого оставляло висеть отдельное «s».
_SYNONYMS = {"kid": "kids", "childs": "kids", "child": "kids"}


def normalized(name: str) -> str:
    # Ударения долой: «Caffè Americano» у Starbucks и «Caffe Americano» в
    # каталоге — одно слово, а без этого «caffè» превращалось в «caff».
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("®", " ").replace("™", " ").replace("’", "'")
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
#: Хвост `[^,()]*` тут был ошибкой: он съедал всё до конца имени, и от
#: «20oz Bottle Coca-Cola» не оставалось ничего — пустой ключ совпадал
#: «точно» с любым другим пустым.
_MEASURE = re.compile(
    r"\(?\b\d+(?:\.\d+)?\s*(?:fl\s*)?(?:oz|ml|l|g|kg|lb|inch|in|cal)\b\.?\)?",
    re.I)
#: Довески подачи, которые к самому блюду отношения не имеют.
_SERVING_WORDS = re.compile(
    r"\b(?:with\s+ice|bottle|can|jug|jugs|gallon|group|serves\s+\d+|"
    r"drive\s*-?\s*thru|"
    # «Naturally Flavored» — обязательная пометка этикетки, а не блюдо.
    # У Panera она стоит у половины напитков, и из-за неё «Blueberry
    # Lavender Lemonade» не сходился со своим же снимком.
    r"naturally\s+flavored)\b", re.I)


#: Служебные слова, которыми сеть склеивает перечисление: «Grilled
#: Cheese **and** Tomato Soup Duet» против «Value Duet, Grilled Cheese &
#: Creamy Tomato Soup». Амперсанд исчезает сам при вычистке знаков, а
#: слово остаётся и штрафует верную пару. Только для снимков: цифрам
#: перечисление важно, там имя сравнивается строже.
_STOPWORDS = {"and", "the", "of", "a", "an"}


def dish(name: str) -> str:
    """Имя блюда без мер, подачи и размера — то, что видно на фотографии.

    Этикетка перечисляет каждое сочетание хлеба и размера — у Jersey
    Mike's это тысяча сто строк, — а снимков сеть выкладывает сто
    двадцать пять: по одному на блюдо и форму подачи. Значит для снимка
    и то и другое надо убрать, иначе «#1 BLT, Seeded Italian Bread,
    Giant» и «BLT, Giant» не сойдутся.
    """
    text = _MEASURE.sub(" ", name)
    text = _SERVING_WORDS.sub(" ", text)
    # Пустые скобки и повисшие разделители после вычистки.
    text = re.sub(r"\(\s*\)|\s+-\s+$|,\s*$", " ", text)
    words = [w for w in comparable(text).split()
             if w not in _SERVING_SHAPES and w not in _STOPWORDS]
    return " ".join(sorted(words))


#: Сходство, ниже которого не смотрим даже при полном вхождении слов.
#: Между ним и обычным порогом лежат промахи на волосок: «Muffin —
#: Blueberry» против «blueberry muffin paradise» — 0.78, и это одно блюдо.
NEAR_THRESHOLD = 0.75


#: Насколько похожи два слова, чтобы считаться одним в разном написании:
#: «tacos/taco», «steakhouse/steak» проходят, «farmhouse/maplehouse»,
#: «steamed/seasoned», «garlic/garden» — нет.
WORD_ALIKE = 0.8


def _words_agree(left: str, right: str) -> bool:
    """У каждого слова короткого имени есть пара в длинном.

    Буквенное сходство целых строк пропускает подмену одного слова:
    «Farmhouse Egg Sandwich» и «Maplehouse Egg Sandwich» набирают 0.82,
    а это разные блюда. Слова же врать не умеют: у «farmhouse» пары в
    другом имени нет. Допуск на написание нужен для форм одного слова —
    множественного числа, ударений, «steak/steakhouse».
    """
    a, b = left.split(), right.split()
    if len(a) > len(b):
        a, b = b, a
    return bool(a) and all(
        any(w == v or difflib.SequenceMatcher(None, w, v).ratio() >= WORD_ALIKE for v in b)
        for w in a)


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


#: Уточнение подачи в имени: «#1 BLT **on White** Regular», «Turkey Sub
#: **on Wheat**». Хлеб — не блюдо, и сеть его отдельно не снимает.
_ON_QUALIFIER = re.compile(r"\s+on\s+.*$", re.I)

#: То же про добавку: «Latte **w/ 2% Milk**», «Green Tea Latte with Oat
#: Milk». Для цифр молоко значимо — от него зависят калории, — а для
#: снимка нет: сеть снимает латте один раз.
_WITH_QUALIFIER = re.compile(r"\s+(?:w/|with)\s+.*$", re.I)


#: Чем сеть отделяет уточнение от названия: запятая у большинства,
#: « - » у Panera («Cookie - Tulip Shaped Shortbread»).
_SEGMENT = re.compile(r",|\s+-\s+|\s+–\s+")
_SEGMENT_JOIN = ", "


def shortenings(name: str) -> list[str]:
    """Имя блюда, от полного к самому короткому.

    Этикетка перечисляет каждое сочетание блюда, хлеба и размера, а сеть
    снимает блюдо один раз. Поэтому пробуем сначала имя целиком, потом
    без уточнений — до первой запятой и до «on». Годится первое, что
    совпало **точно**: укороченное имя легко спутать с чужим блюдом.
    """
    # Не одна голова, а все начала подряд. Первый сегмент не всегда
    # блюдо: у Panera это канал («Drive Thru, Blueberry Lavender
    # Lemonade, 20 fl oz»), и по нему не найти ничего. Прибавляя
    # сегменты слева направо, мы проходим и «Drive Thru», и «Drive Thru,
    # Blueberry Lavender Lemonade» — второе и есть блюдо.
    segments = _SEGMENT.split(name)
    heads = [_SEGMENT_JOIN.join(segments[:n]) for n in range(1, len(segments))]
    forms = [name, *heads]
    for cut in (_ON_QUALIFIER, _WITH_QUALIFIER):
        forms += [cut.sub("", form) for form in (name, *heads)]
    # И то и другое сразу: «Latte Macchiato w/ Whole Milk, Tall».
    forms += [_WITH_QUALIFIER.sub("", _ON_QUALIFIER.sub("", form)) for form in heads]
    return list(dict.fromkeys(d for form in forms if (d := dish(form))))


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
        for wanted in shortenings(record["name"]):
            # Только точное совпадение: укороченное имя рискует совпасть
            # с чужим блюдом, и нестрогое сравнение тут ошибётся молча.
            if exact := by_dish.get(wanted):
                # Под одним ключом бывает несколько снимков — «Brownie»
                # и «Kids Brownie» (размер из ключа вычищен). Берём тот,
                # чьё имя ближе всего к имени позиции, а не первый.
                own = normalized(record["name"])
                chosen[key] = min(exact, key=lambda shot: (
                    normalized(shot.name) != own,
                    -difflib.SequenceMatcher(None, own, normalized(shot.name)).ratio()))
                break
        if key in chosen:
            continue
        # Точного совпадения нет — ищем ближайшее, и **по всем формам**
        # имени, а не только по самой короткой. «Croque Monsieur on
        # Croissant Toast» и слаг «croissant-croque-monsieur-toast» —
        # одно и то же блюдо, но после отрезания «on» от него остаётся
        # половина, и по ней сходство выходит 0.65 вместо 0.97.
        best_shot, best_ratio, best_pair = None, 0.0, ("", "")
        # Односложную форму в нестрогое сравнение не пускаем, **если
        # есть длиннее**: по одному слову судить нельзя. «Cookie»
        # набирает 0.80 с «Coke» и перебивает верную пару «cookie
        # tulip». Но у Moe's блюда так и называются — «Homewrecker», —
        # и там одно слово это всё имя, а не огрызок.
        every = shortenings(record["name"])
        forms = [f for f in every if " " in f] or every
        for wanted in forms:
            for name, group in by_dish.items():
                # Сначала согласие по словам, потом сходство по буквам —
                # не наоборот. Иначе «Pastry - Chocolate Croissant»
                # выбирает по буквам «chocolate croissant straight»
                # (0.85), отвергает его по словам и уходит ни с чем, хотя
                # «chocolate croissant» (0.84) подходит по всем статьям.
                if not _words_agree(wanted, name):
                    continue
                ratio = difflib.SequenceMatcher(None, wanted, name).ratio()
                if ratio > best_ratio:
                    best_shot, best_ratio, best_pair = group[0], ratio, (wanted, name)
        if best_shot is not None and best_ratio >= NEAR_THRESHOLD:
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
