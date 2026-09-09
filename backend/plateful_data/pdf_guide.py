"""Гид по питанию в PDF: единственный источник для сетей, чей сайт не читается.

Разведка двенадцати крупнейших сетей показала, что общий читатель страниц
берёт меньшинство: остальные рисуют меню скриптом, и в HTML нет ни ссылок
на блюда, ни цифр. Зато почти у каждой такой сети есть PDF с полной
таблицей — тот самый документ, которым она исполняет 21 CFR 101.11. Один
файл даёт всю сеть разом, без обхода двухсот страниц.

Разбор простой: строка блюда — это название и хвост из чисел в известном
порядке. Сложное здесь не разбор, а две проверки, без которых гид молча
портит каталог.

**Страна.** У Wendy's на собственном домене лежит `2025-02/Core Menu.pdf`
без единого признака страны в адресе — и это британский гид: «Pain au
Chocolat», «Curry Bean Burger» и колонка «Salt» в граммах вместо натрия
в миллиграммах. Прочитать его как американский значит записать 0.46 вместо
460 и не заметить. Поэтому страна определяется по самим числам, а не по
заголовку: заголовки в этих PDF повёрнуты на 90° и склеиваются в кашу,
а натрий в миллиграммах ни с чем не спутать.

**Порядок колонок.** Он свой у каждой сети и задаётся вручную — прочитать
его из шапки нельзя по той же причине. Зато можно проверить: если колонки
съехали, макросы перестанут сходиться с калориями. Атуотер, которым мы и
так проверяем каждую позицию, здесь работает проверкой самой раскладки.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, replace

from . import validate
from .slug import slugify

#: Хвост-сноска: «Local Favorites **», «Bacon**».
_FOOTNOTE_MARKS = "*†‡§ "

#: Число, «меньше единицы» или прочерк — всё, что бывает в клетке таблицы.
_VALUE = re.compile(r"^(?:<\s*)?\d+(?:[.,]\d+)?$|^[-–—]$|^N/?A$", re.I)

# Натрий в миллиграммах у любого блюда идёт сотнями; соль в граммах — единицами.
# Медиана ниже этого значит, что перед нами не американский гид.
MIN_MEDIAN_SODIUM_MG = 50.0

# Насколько в среднем макросы вправе расходиться с калориями, прежде чем
# мы решим, что дело не в блюдах, а в раскладке колонок.
#
# Меряем медиану отклонения в обе стороны, а не долю ошибок валидатора:
# тот считает ошибкой только перебор (макросы дают больше калорий, чем
# заявлено), а съехавшая колонка чаще даёт недобор — и он проходит как
# предупреждение про алкоголь. На переставленных местами белке и клетчатке
# у Subway валидатор не сказал ничего, а медиана отклонения подскочила
# с 1% до 17%.
MAX_ATWATER_DRIFT = 0.10


class WrongGuide(Exception):
    """Гид не тот: другая страна или другая раскладка колонок."""


#: Порция текстом в хвосте названия: «Asiago Cheese Bagel 1 Bagel»,
#: «Sweet Cream Cold Foam 3 swirls», «Chicken Salad 1/2 Salad».
_SERVING_TAIL = re.compile(
    r"\s+(\d+(?:/\d+)?(?:\.\d+)?\s+[A-Za-z][\w.'’-]*(?:\s+[A-Za-z][\w.'’-]*){0,2})$")

#: Порция, у которой число стоит вторым: «Approx 8», «About 11». Число
#: уезжает в клетки раньше, чем `_SERVING_TAIL` успевает его увидеть, —
#: у Auntie Anne's так съезжала на колонку каждая штучная позиция, и
#: «Approx 8 690 39 …» читалось как 8 ккал при 1900 г углеводов.
_SERVING_WORD_FIRST = re.compile(
    r"(?i)\s+((?:approx(?:imately)?|about|serves)\.?\s+\d+(?:\.\d+)?)(?=\s+\d)")


def pull_serving(line: str) -> tuple[str, str | None]:
    """Вынимает из строки порцию вида «Approx 8», стоящую перед числами.

    Разбиение строки берёт первый же ряд чисел, поэтому такую порцию надо
    убрать раньше: иначе она становится первой клеткой и сдвигает всю
    этикетку на колонку.
    """
    match = _SERVING_WORD_FIRST.search(line)
    if not match:
        return line, None
    return (line[:match.start()] + line[match.end():]), match.group(1).strip()

#: Вся «строка блюда» — одна порция: «1 Bowl», «1/2 Stuffer». Значит имя
#: перенесено на предыдущую строку, и там его и надо брать. Пока этого не
#: делали, у Panera девять пар блюд оказывались неразличимы: половинка
#: боула и целый назывались «1/2 Bowl» и «1 Bowl» вместо своих имён.
_SERVING_ONLY = re.compile(
    r"^\d+(?:/\d+)?(?:\.\d+)?\s+[A-Za-z][\w.'’-]*(?:\s+[A-Za-z][\w.'’-]*){0,2}$")

#: Строка блюда, названная одним размером: «Small», «Medium», «Sack
#: (serves 3)». Блюдо у неё — заголовок строкой выше. У White Castle так
#: подана вся вторая страница, и без этого правила «Small» из пяти разных
#: разделов сталкивались друг с другом одним ключом.
_SIZE_ONLY = re.compile(
    r"^(?:small|medium|large|regular|sack|kids?|jr\.?|single|double|triple)"
    r"(?:\s*\([^)]*\))?$", re.I)


@dataclass(frozen=True)
class Layout:
    """Порядок числовых колонок в гиде одной сети.

    `None` — колонка есть, но нам не нужна (проценты дневной нормы,
    добавленный сахар, витамины). `count` — сколько чисел в строке блюда:
    строка с другим числом клеток не блюдо, а заголовок раздела или
    перенос, и угадывать по ней нечего.
    """
    columns: tuple[str | None, ...]
    count: int
    #: Строку блюда разрывает вёрстка: имя в левой колонке на двух строках,
    #: числа правее и между ними. Читать такой гид надо по координатам.
    positioned: bool = False
    #: Строка блюда называется не блюдом, а порцией: у Quiznos под
    #: заголовком «Turkey Ranch & Swiss» идут три строки «Small Sub»,
    #: «Medium Sub», «Large Sub». Имя брать со строки выше.
    name_from_heading: bool = False
    #: Насколько далеко должны стоять символы, чтобы между ними считался
    #: пробел. У White Castle шрифт разрежен, и при обычном допуске имя
    #: рассыпается на буквы: «The Ori gi nal Sl i der», а «2.5» читается
    #: как два числа «2.» и «5» и сдвигает всю этикетку.
    tolerance: float = 3.0
    #: Порция стоит текстом в хвосте названия, а не отдельной колонкой.
    #: У Subway это число граммов среди чисел, у Panera — «1 Bagel» прямо
    #: в имени, и без отделения половинка салата и целый салат становятся
    #: одной позицией.
    serving_in_name: bool = False


@dataclass(frozen=True)
class GuideItem:
    name: str
    values: dict[str, float | None]
    #: Порция словами, если гид пишет её текстом: «1 Bagel», «3 swirls».
    serving: str | None = None
    #: Заголовок раздела, под которым позиция стоит в гиде. Единственное
    #: место, откуда у новой позиции может взяться категория: с сайта её
    #: не возьмёшь, а без неё блюдо не ложится ни в один раздел меню.
    category: str | None = None
    #: Внешний раздел гида: SANDWICHES, WRAPS, SALADS, PROTEIN BOWLS.
    #: Он и есть то, что отличает три разных «Steak Philly» друг от друга.
    section: str | None = None


#: Subway, U.S. NUTRITION INFORMATION. Порядок — как на этикетке FDA.
SUBWAY = Layout(
    columns=("serving", "kcal", "fat", "sat_fat", "trans_fat", "cholesterol",
             "sodium", "carbs", "fiber", "sugar", None, "protein",
             None, None, None, None),
    count=16,
)

#: Panera Bread® Nutrition Guide. Порция стоит текстом в названии, а среди
#: чисел вместо неё — калории из жира, которые нам не нужны.
PANERA = Layout(
    columns=("kcal", None, "fat", "sat_fat", "trans_fat", "cholesterol",
             "sodium", "carbs", "fiber", "sugar", "protein", None),
    count=12, serving_in_name=True, positioned=True)

#: Quiznos, US Base Nutritionals. Порция граммами первой колонкой, за
#: калориями идут калории из жира — они нам не нужны.
QUIZNOS = Layout(
    columns=("serving", "kcal", None, "fat", "sat_fat", "trans_fat",
             "cholesterol", "sodium", "carbs", "fiber", "sugar", "protein"),
    count=12, name_from_heading=True)

#: Frisch's Big Boy. Первая клетка — прочерк на месте порции: сеть её не
#: публикует, но колонку в таблице держит.
FRISCHS = Layout(
    columns=(None, "kcal", "fat", "sat_fat", "trans_fat", "cholesterol",
             "sodium", "carbs", "fiber", "sugar", "protein"),
    count=11)

#: Red Lobster, US Nutrition.
RED_LOBSTER = Layout(
    columns=("kcal", None, "fat", "sat_fat", "trans_fat", "cholesterol",
             "sodium", "carbs", "fiber", "sugar", "protein"),
    count=11)

#: Auntie Anne's. Порция стоит текстом в хвосте названия («Approx 8»,
#: «Small (16 fl oz)»), за клетчаткой идёт добавленный сахар — его мы не
#: ведём.
AUNTIE_ANNES = Layout(
    columns=("kcal", "fat", "sat_fat", "trans_fat", "cholesterol", "sodium",
             "carbs", "fiber", "sugar", None, "protein"),
    count=11, serving_in_name=True)

#: White Castle. Порция граммами первой колонкой, за калориями идут
#: калории из жира, а в хвосте — витамины в процентах от нормы и пометки
#: аллергенов; ни того, ни другого мы не ведём.
WHITE_CASTLE = Layout(
    columns=("serving", "kcal", None, "fat", "sat_fat", "trans_fat",
             "cholesterol", "sodium", "carbs", "fiber", "sugar", "protein"),
    count=12, tolerance=4.0)

LAYOUTS = {"subway": SUBWAY, "panera-bread": PANERA, "quiznos": QUIZNOS,
           "frisch-s-big-boy": FRISCHS, "red-lobster": RED_LOBSTER,
           "auntie-anne-s": AUNTIE_ANNES, "white-castle": WHITE_CASTLE}


def _number(token: str) -> float | None:
    """«<1» — не ноль и не единица, а «меньше грамма».

    Схема такого не хранит, а выдумать середину значит соврать точнее, чем
    знаешь. Поэтому неизвестно.
    """
    if token.startswith("<") or token in ("-", "–", "—") or token.upper() in ("NA", "N/A"):
        return None
    return float(token.replace(",", "."))


#: Доля строк, которые гид позволяет выбросить как неразличимые. Больше —
#: значит раскладка не та, и выбрасывать уже нечего: надо разбираться.
MAX_AMBIGUOUS = 0.10

#: Пометки аллергенов в хвосте строки: гид ставит крестик или решётку в
#: колонке каждого аллергена. Числами они не являются, и пока их не
#: убирали, счёт клеток с конца обрывался на первой же — у White Castle
#: так пропадали все 49 бургеров, а разбирались одни соусы.
_FLAG_TOKENS = frozenset("#xX*•·-–—✓✔◆●○□■")


def _split(line: str, count: int) -> tuple[str, list[str]] | None:
    """Название и хвост из `count` клеток. None — строка не про блюдо."""
    tokens = line.split()
    while tokens and all(ch in _FLAG_TOKENS for ch in tokens[-1]):
        tokens.pop()
    tail = 0
    while tail < len(tokens) and _VALUE.match(tokens[len(tokens) - 1 - tail]):
        tail += 1
    if tail < count:
        return None
    # Сноски из имени убираем: «**» у Subway значит «не во всех точках»,
    # это факт о доступности, а не часть названия блюда.
    name = " ".join(tokens[:len(tokens) - tail]).strip().rstrip(_FOOTNOTE_MARKS)
    if not name:
        return None
    # Берём первые `count` клеток: дальше идут проценты дневной нормы,
    # а они плавают от гида к гиду.
    return name, tokens[len(tokens) - tail:][:count]


# Заголовок раздела — короткая строка с заглавной буквы. Сноски длинны и
# заканчиваются точкой, но не все: перенос сноски «…see values for salad
# dressing portion» выглядел заголовком и раздал свою категорию 57
# позициям. Отличает их регистр первой буквы — заголовки в гидах пишут
# с заглавной или капсом, продолжения строк нет.
MAX_HEADING = 48

# Имя группы бывает склеено с пояснением в одной строке: «Protein Pockets
# Values include 9" wrap (pocket)…». Пока строка отбрасывалась целиком за
# длину, обёртка и карман попадали в одну группу — и две разные позиции
# становились неразличимы. Режем по началу пояснения.
_EXPLANATION = re.compile(
    r"\s+(?:Values?\s+(?:include|are)|Double\s+values|Amount\s+on)\b.*$", re.I)

#: Хвост в скобках: «Soup (8 oz. bowl)».
_PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*$")


def _outer(line: str) -> str | None:
    """Внешний раздел гида — заголовок капсом.

    У гида два уровня: капсом идёт формат подачи (SANDWICHES, WRAPS,
    SALADS, PROTEIN BOWLS), а под ним обычным регистром — группа блюд
    (Cheesesteaks, Chicken, Italians). Одно и то же название встречается
    в нескольких форматах: «Steak Philly» есть обёрткой, салатом и боулом,
    и это три разных блюда с разными числами, а не повтор строки.
    """
    text = _EXPLANATION.sub("", line.strip()).strip().rstrip(_FOOTNOTE_MARKS)
    if not text or len(text) > MAX_HEADING:
        return None
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 4 or not all(c.isupper() for c in letters):
        return None
    return text


def _heading(line: str) -> str | None:
    text = _EXPLANATION.sub("", line.strip())
    text = _PARENTHETICAL.sub("", text).strip().rstrip(_FOOTNOTE_MARKS)
    if not text or len(text) > MAX_HEADING or text.endswith((".", ":", ",")):
        return None
    if not text[0].isupper():
        return None
    return text


#: Описание блюда в хвосте названия. Quiznos пишет «Classic Italian - with
#: capicola, salami, ham…»: до тире имя, после — состав. Отличаем состав от
#: части названия по регистру: имя блюда сеть пишет с прописной, состав со
#: строчной. Поэтому «Chick-fil-A® Nuggets» и «Bacon - Egg & Cheese» целы,
#: а полстроки состава в имя не уезжает.
_DESCRIPTION = re.compile(r"^(.+?)\s+[-–—]\s+([a-z(].*)$", re.S)


def without_description(name: str) -> str:
    """Имя блюда без хвоста-состава."""
    match = _DESCRIPTION.match(name)
    return match.group(1).strip() if match else name


def parse(text: str, layout: Layout) -> list[GuideItem]:
    items: list[GuideItem] = []
    category: str | None = None
    previous_category: str | None = None
    section: str | None = None
    #: Последняя строка не-позиция. Она либо заголовок раздела, либо
    #: перенесённое имя блюда — что именно, становится ясно только по
    #: следующей строке.
    pending: str | None = None

    for line in text.splitlines():
        if not line.strip():
            continue
        line, pulled = (pull_serving(line) if layout.serving_in_name
                        else (line, None))
        split = _split(line, layout.count)
        if not split:
            # Не позиция. Заголовок капсом меняет формат подачи, обычный —
            # группу блюд внутри него.
            if _PAGE_MARKER.match(line.strip()):
                continue
            pending = _PAGE_IN_HEADING.sub("", line.strip())
            if outer := _outer(line):
                section = outer
            elif heading := _heading(line):
                previous_category, category = category, _PAGE_IN_HEADING.sub("", heading)
            continue
        name, cells = split
        serving = pulled
        if serving:
            pass
        elif layout.serving_in_name and (tail := _SERVING_TAIL.search(name)):
            serving = tail.group(1)
            name = name[:tail.start()].strip() or name
        elif layout.name_from_heading and pending:
            serving, name = name, pending
            if category == pending:
                category = previous_category
        elif pending and _SIZE_ONLY.match(name):
            # Имя — один размер: блюдо стоит заголовком выше.
            serving, name = name, pending
            if category == pending:
                category = previous_category
        elif layout.serving_in_name and pending and _SERVING_ONLY.match(name):
            # Имя перенесено на предыдущую строку, а здесь осталась порция.
            serving, name = name, pending
            # Эта строка была именем, а не заголовком группы: возвращаем ту,
            # что стояла до неё.
            if category == pending:
                category = previous_category
        name = without_description(name)
        values = {field: _number(cell)
                  for field, cell in zip(layout.columns, cells)
                  if field is not None}
        items.append(GuideItem(name=name, values=values, serving=serving,
                               category=category, section=section))
    return items


def check_american(items: list[GuideItem]) -> None:
    """Натрий в миллиграммах или соль в граммах — вот и вся разница."""
    sodium = [i.values["sodium"] for i in items
              if i.values.get("sodium") is not None]
    if not sodium:
        raise WrongGuide("в гиде нет натрия — не американская этикетка")
    median = statistics.median(sodium)
    if median < MIN_MEDIAN_SODIUM_MG:
        raise WrongGuide(
            f"медиана натрия {median:g} — это соль в граммах, а не натрий "
            f"в миллиграммах: гид не американский")


def atwater_drift(items: list[GuideItem]) -> list[float]:
    """Насколько макросы каждой строки расходятся с её калориями."""
    drift = []
    for item in items:
        values = item.values
        if any(values.get(f) is None for f in ("kcal", "protein", "carbs", "fat")):
            continue
        if values["kcal"] < validate.ATWATER_FLOOR_KCAL:
            continue
        expected = validate.atwater_kcal(values["protein"], values["carbs"],
                                         values["fat"])
        drift.append(abs(expected - values["kcal"]) / values["kcal"])
    return drift


def check_layout(items: list[GuideItem]) -> None:
    """Съехавшие колонки видны по тому, что макросы перестают сходиться."""
    drift = atwater_drift(items)
    if not drift:
        raise WrongGuide("ни одной строки с четырьмя макросами — раскладка не та")

    median = statistics.median(drift)
    if median > MAX_ATWATER_DRIFT:
        raise WrongGuide(
            f"макросы расходятся с калориями в среднем на {median:.0%} "
            f"({len(drift)} строк) — колонки прочитаны не в том порядке")


#: Доля страниц, на которых должна встретиться строка, чтобы считаться
#: колонтитулом. Название блюда не повторяется на трети гида, а «© 2026
#: Panera Bread» и «Effective: 6/17/2026 Edition: 1» стоят на всех.
FURNITURE_SHARE = 0.30

#: Меньше — и повторяемость перестаёт что-либо значить.
MIN_PAGES_FOR_FURNITURE = 8

#: Номер страницы: «Page 31», «- 12 -», просто «7». Не заголовок и не имя
#: блюда, но выглядит и тем и другим, и у Panera попадал в категорию.
_PAGE_MARKER = re.compile(r"^(?:page\s*)?[-–—\s]*\d{1,3}[-–—\s]*$", re.I)

#: Номер страницы, приклеенный к заголовку раздела: «Chicken Subs (Page 1
#: of 9)». В гиде это колонтитул, а у нас он уезжал в имя блюда и
#: доезжал до карточки: «Carbonara, Chicken Subs (Page 1 of 9), Small Sub».
_PAGE_IN_HEADING = re.compile(r"\s*\(\s*page\s+\d+\s+of\s+\d+\s*\)\s*$", re.I)


def without_furniture(pages: list[str]) -> str:
    """Страницы в один текст, без колонтитулов.

    Колонтитул неотличим от заголовка раздела по виду — он такой же
    короткий и с заглавной буквы, — и потому становился то категорией, то
    перенесённым именем блюда. У Panera из-за этого пять позиций получали
    в имя «Effective: 6/17/2026 Edition: 1» и переставали различаться.

    Отличает его повторяемость: содержание на каждой странице разное.
    """
    # На коротком гиде повторяемость ничего не значит: у Subway три
    # страницы, и настоящий заголовок «Cheesesteaks» стоит на двух из них.
    # Колонтитул виден только там, где страниц много.
    if len(pages) < MIN_PAGES_FOR_FURNITURE:
        return "\n".join(pages)

    seen: Counter = Counter()
    for page in pages:
        seen.update({line.strip() for line in page.splitlines() if line.strip()})

    threshold = max(2, int(len(pages) * FURNITURE_SHARE))
    furniture = {line for line, n in seen.items() if n >= threshold}

    return "\n".join(
        "\n".join(line for line in page.splitlines()
                   if line.strip() not in furniture)
        for page in pages)


@dataclass(frozen=True)
class Line:
    """Строка страницы с координатами: где она стоит и чем начинается."""
    top: float
    x0: float
    text: str


#: Насколько правее левого поля должна начинаться строка, чтобы считаться
#: строкой одних чисел. Названия всегда прижаты к полю; строка, у которой
#: имени нет, начинается заметно правее — у Panera это 22 против 257
#: пунктов. Доля от ширины страницы здесь не годится: она давала границу
#: в 332 пункта, строки чисел оказывались левее неё и разбирались как
#: целые, а именем становилась порция — «1/2 Bowl» вместо блюда.
VALUES_INDENT = 60.0

#: На сколько пунктов имя может отстоять от своей строки чисел. Больше —
#: это заголовок раздела, а не имя: по виду они неразличимы (оба короткие,
#: с заглавной, без чисел), а по месту — вполне. Имя жмётся к своей
#: строке, заголовок стоит на отдалении.
NAME_PROXIMITY = 15.0


def parse_positioned(pages: list[list[Line]], layout: Layout) -> list[GuideItem]:
    """Разбор по координатам — для гидов, где имя не на одной строке с числами.

    У Panera название занимает две строки левой колонки, а числа стоят
    правее и вертикально между ними:

        y=171  Catering Asian Sesame Chicken Salad -
        y=180                         1 Container 1260 640 71 9 …
        y=186  serves 5

    Построчное чтение здесь бессильно: оно видит строку без чисел, строку
    без имени и ещё одну без чисел. По координатам же правило простое —
    **строка имени принадлежит ближайшей по вертикали строке чисел**. На
    этой странице оно разводит всё без единой ошибки, а середины между
    двумя блюдами не бывает: расстояние до своей строки чисел втрое меньше.
    """
    items: list[GuideItem] = []
    # Раздел живёт через страницы: у Panera «SANDWICHES» открывает одну, а
    # блюда под ним идут ещё на двух. Сбрасывать его на каждой странице
    # значило оставить без раздела всех, кроме первых.
    category: str | None = None
    section: str | None = None

    for lines in pages:
        if not lines:
            continue
        boundary = min(line.x0 for line in lines) + VALUES_INDENT

        values_rows: list[tuple[Line, list[str]]] = []
        name_lines: list[Line] = []
        whole_rows: list[tuple[Line, str, list[str]]] = []
        # То, что действовало на конец прошлой страницы, действует и здесь,
        # пока не встретится новый заголовок.
        headings: list[tuple[float, str | None, str | None]] = [
            (float("-inf"), section, category)]

        for line in sorted(lines, key=lambda l: l.top):
            split = _split(line.text, layout.count)
            if split and line.x0 < boundary:
                # Имя и числа на одной строке — геометрия тут не нужна и
                # только помешает: такая строка сама себе имя.
                whole_rows.append((line, split[0], split[1]))
                continue
            if split:
                values_rows.append((line, split[1]))
            elif _PAGE_MARKER.match(line.text.strip()):
                continue
            else:
                # Заголовок или имя — решится ниже по расстоянию до чисел.
                name_lines.append(line)

        # Что из левой колонки — имя, а что заголовок. Имя жмётся к своей
        # строке чисел; заголовок стоит на отдалении и достаётся категории.
        def distance(line: Line) -> float:
            return min((abs(v[0].top - line.top) for v in values_rows),
                       default=float("inf"))

        # Заголовок капсом — заголовок всегда, как бы близко к числам он ни
        # стоял: имена блюд капсом не пишут. На плотных страницах Panera
        # раздел стоял в четырнадцати пунктах от первой же строки чисел, и
        # проверка близости уводила его в имя — 518 позиций остались без
        # раздела. Мелкий заголовок разбираем по расстоянию: тут он и правда
        # неотличим от имени иначе.
        headings_at = set()
        for line in sorted(name_lines, key=lambda l: l.top):
            if outer := _outer(line.text):
                section, category = outer, None
                headings.append((line.top, section, category))
                headings_at.add(id(line))
            elif distance(line) > NAME_PROXIMITY and (heading := _heading(line.text)):
                category = heading
                headings.append((line.top, section, category))
                headings_at.add(id(line))
        name_lines = [line for line in name_lines
                      if id(line) not in headings_at
                      and distance(line) <= NAME_PROXIMITY]

        def emit(row: Line, name: str, cells: list[str]) -> None:
            name = re.sub(r"\s*[-–—]\s*$", "", name.strip()).strip()
            if not name:
                return
            serving = None
            if layout.serving_in_name and (tail := _SERVING_TAIL.search(name)):
                serving, name = tail.group(1), name[:tail.start()].strip() or name
            here = [h for h in headings if h[0] < row.top]
            items.append(GuideItem(
                name=name,
                values={field: _number(cell)
                        for field, cell in zip(layout.columns, cells)
                        if field is not None},
                serving=serving,
                section=here[-1][1] if here else None,
                category=here[-1][2] if here else None))

        for row, name, cells in whole_rows:
            emit(row, name, cells)

        for row, cells in values_rows:
            # Своё имя — из строк, для которых эта строка чисел ближайшая.
            mine = sorted(
                (line for line in name_lines
                 if min(values_rows, key=lambda v: abs(v[0].top - line.top))[0] is row),
                key=lambda l: l.top)
            # Порция у таких гидов стоит в начале строки чисел, а не в
            # хвосте имени: «1 Container 1260 640 …».
            head = _split(row.text, layout.count)
            if layout.serving_in_name and head and head[0]:
                emit(row, " ".join(l.text for l in mine) + " " + head[0], cells)
            else:
                emit(row, " ".join(l.text for l in mine), cells)

    return items


def dedupe(items: list[GuideItem]) -> list[GuideItem]:
    """Снимает строки, повторённые слово в слово.

    У Panera страница 30 печатает часть таблицы дважды: одинаковые имя,
    раздел, порция и все числа. Такой повтор не несёт информации, и снять
    его безопасно — в отличие от повтора с разными числами, который значит
    два разных блюда и разбирается уточнением имени.
    """
    seen: set[tuple] = set()
    unique: list[GuideItem] = []
    for item in items:
        mark = (item.name, item.section, item.category, item.serving,
                tuple(sorted(item.values.items())))
        if mark in seen:
            continue
        seen.add(mark)
        unique.append(item)
    return unique


def qualify(items: list[GuideItem]) -> list[GuideItem]:
    """Уточняет имена, которые без раздела неразличимы.

    «Steak Philly» в гиде Subway встречается трижды — обёрткой, салатом и
    боулом, с разными числами. Это три блюда, а не повтор строки, и по
    одному имени их не развести: ключ позиции считается из имени, и без
    уточнения два из трёх молча потерялись бы.

    Уточняем в том же виде, что принят в каталоге, — «Название, Раздел».
    Его понимает `variants.py`: одинаковые начала он склеит в одно блюдо
    с переключателем, то есть человек увидит один «Steak Philly» и выбор
    подачи, а не три карточки подряд.
    """
    counts = Counter(slugify(item.name) for item in items)
    once = {key for key, n in counts.items() if n == 1}

    qualified = [
        item if slugify(item.name) in once or not item.section
        else replace(item, name=f"{item.name}, {item.section.title()}")
        for item in items
    ]

    # Раздела не хватило — уточняем ещё и группой внутри него.
    counts = Counter(slugify(item.name) for item in qualified)
    once = {key for key, n in counts.items() if n == 1}
    qualified = [
        item if slugify(item.name) in once or not item.category
        else replace(item, name=f"{item.name} ({item.category})")
        for item in qualified
    ]

    # Раздела и группы не хватило — уточняем порцией. У Panera половинка
    # салата и целый салат стоят в одной группе и различаются только ею.
    counts = Counter(slugify(item.name) for item in qualified)
    once = {key for key, n in counts.items() if n == 1}
    qualified = [
        item if slugify(item.name) in once or not item.serving
        else replace(item, name=f"{item.name}, {item.serving}")
        for item in qualified
    ]

    duplicated = {key for key, n in Counter(slugify(i.name)
                                            for i in qualified).items() if n > 1}
    if not duplicated:
        return qualified

    # Две строки, которые мы не умеем различить. Завести их обе нельзя —
    # вторая молча затрёт первую; выбрать одну тоже нельзя, неизвестно
    # какая. Обе выбрасываем.
    #
    # Пока выбрасывался весь гид, одна матричная страница отменяла всю
    # сеть: у White Castle девять неразличимых строк из 249 стоили нам
    # остальных 240. Но и молчать нельзя — на Subway так потерялись 48
    # позиций из 162, и заметили это только вручную. Поэтому потеря
    # громкая: выброшенное перечислено и посчитано.
    kept = [i for i in qualified if slugify(i.name) not in duplicated]
    share = 1 - len(kept) / len(qualified)
    if share > MAX_AMBIGUOUS:
        # Неразличима половина гида — значит он устроен не так, как мы
        # думаем, и спасать тут нечего.
        raise WrongGuide(
            f"неразличима {share:.0%} строк: {', '.join(sorted(duplicated)[:5])}")
    print(f"  неразличимых строк выброшено: {len(qualified) - len(kept)}"
          f" ({', '.join(sorted(duplicated)[:4])})")
    return kept


def _checked(items: list[GuideItem]) -> list[GuideItem]:
    if not items:
        raise WrongGuide("ни одной строки блюда — раскладка или файл не те")
    check_american(items)
    check_layout(items)
    return qualify(dedupe(items))


def read(text: str, *, layout: Layout) -> list[GuideItem]:
    """Текст гида → позиции. Бросает `WrongGuide`, если гид не тот."""
    return _checked(parse(text, layout))


def read_pages(pages: list[list[Line]], *, layout: Layout) -> list[GuideItem]:
    """То же, но по координатам — для гидов, где строка разорвана.

    Колонтитулы снимаются здесь же: по координатам они видны так же плохо,
    как в тексте, и точно так же становились бы именами блюд.
    """
    seen: Counter = Counter()
    for page in pages:
        seen.update({line.text for line in page})
    if len(pages) >= MIN_PAGES_FOR_FURNITURE:
        threshold = max(2, int(len(pages) * FURNITURE_SHARE))
        furniture = {text for text, n in seen.items() if n >= threshold}
        pages = [[line for line in page if line.text not in furniture]
                 for page in pages]
    return _checked(parse_positioned(pages, layout))
