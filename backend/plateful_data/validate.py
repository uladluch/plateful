"""Валидация каталога.

Парсеры ломаются тихо: съехала колонка, граммы приняты за миллиграммы,
LLM выдумала число. Все эти поломки дают одно и то же — макросы, которые
не сходятся с калориями. Поэтому главная проверка здесь одна.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Коэффициенты Атуотера: ккал на грамм
KCAL_PER_G_PROTEIN = 4.0
KCAL_PER_G_CARB = 4.0
KCAL_PER_G_FAT = 9.0

# Проверка Атуотера асимметрична, и это принципиально.
#
# Макросы НЕ МОГУТ дать больше энергии, чем заявлено калорий: если сумма
# 4П+4У+9Ж заметно превышает kcal — одно из чисел неверно. Это ошибка.
#
# Обратное — законно. Алкоголь даёт 7 ккал/г и не входит ни в один макрос,
# поэтому у коктейлей калорий всегда больше, чем объясняют Б/У/Ж. В сиде
# MenuStat таких позиций 873 из 1049 срабатываний, все — Beverages.
# Поэтому «калорий больше, чем объясняют макросы» — предупреждение,
# и только откровенно дикий разрыв считаем ошибкой.
ATWATER_OVERCOUNT_TOLERANCE = 0.25   # макросы > калорий → ошибка
ATWATER_UNDERCOUNT_TOLERANCE = 0.30  # калорий > макросов → предупреждение
ATWATER_UNDERCOUNT_ERROR = 0.75      # ...но не настолько же
ATWATER_FLOOR_KCAL = 50.0  # ниже этого относительная ошибка бессмысленна

# Потолки. Целые пироги и «12 бисквитов» в меню действительно есть,
# поэтому верхняя граница — защита от съехавшей колонки, а не от обжорства.
MAX_KCAL = 5000.0
WARN_KCAL = 2000.0
MAX_PROTEIN_G = 250.0
MAX_CARB_G = 500.0
MAX_FAT_G = 400.0

# Доли этикетки: насыщенные и трансжиры входят в общий жир, сахар и
# клетчатка — в углеводы. Доля больше целого значит сломанное число, а не
# необычное блюдо: «Sierra Mist, 12 fl oz» с 37 г углеводов и 370 г сахара,
# «Diet Dr Pepper» с нулём углеводов и 96 г сахара, трансжиры в 1470 г при
# 26 г жира всего. В сиде таких 109.
#
# Допуск в грамм — на округление: источник округляет до целых, и две
# независимо округлённые величины расходятся не больше чем на грамм. Дальше
# разрыв сразу измеряется десятками, серединки нет.
FRACTION_TOLERANCE_G = 1.0

# (доля, целое, как назвать в отчёте)
LABEL_FRACTIONS = (
    ("sat_fat", "fat", "насыщенные жиры", "жир"),
    ("trans_fat", "fat", "трансжиры", "жир"),
    ("sugar", "carbs", "сахар", "углеводы"),
    ("fiber", "carbs", "клетчатка", "углеводы"),
)

# Потолки остальной этикетки. Верхние границы щедрые: «50 Naked Wings»
# у Hooters честно несут 2680 мг холестерина, а солонка размером с блюдо
# на компанию доходит до 25 г натрия. Это защита от съехавшей колонки.
MAX_CHOLESTEROL_MG = 5000.0
MAX_SODIUM_MG = 30000.0

# Пороги дифф-проверки: если кроул перевернул сеть сильнее — это поломка
# адаптера, а не обновление меню. Релиз собирать нельзя.
MAX_CHANGED_SHARE = 0.30
MAX_DROPPED_SHARE = 0.20


SUGAR_ALCOHOL_TOLERANCE = 0.60
_SUGAR_ALCOHOL_HINTS = (
    "no sugar added", "sugar free", "sugar-free", "diet ", "light ice cream",
)


def _has_sugar_alcohols(item) -> bool:
    # `category` есть у позиции из источника, но не у снятой со страницы
    # сети: там её неоткуда взять. Проверка обязана работать на обеих —
    # она стоит и перед сборкой пака, и перед записью кроула.
    haystack = f"{item.name} {getattr(item, 'category', None) or ''}".lower()
    return any(hint in haystack for hint in _SUGAR_ALCOHOL_HINTS)


@dataclass(frozen=True)
class Problem:
    chain: str
    name: str
    kind: str
    detail: str
    severity: str = "error"  # error блокирует релиз, warning идёт в отчёт


def atwater_kcal(protein: float, carbs: float, fat: float) -> float:
    return (
        protein * KCAL_PER_G_PROTEIN
        + carbs * KCAL_PER_G_CARB
        + fat * KCAL_PER_G_FAT
    )


def broken_label_fields(item) -> list[tuple[str, str]]:
    """Поля этикетки, которым нельзя верить: (имя поля, объяснение).

    Одно правило на двух потребителей: check_item делает из него
    предупреждение в отчёте, build_seed — гасит поле перед сборкой пака.
    Разъедься они, и в паке оказалось бы то, на что отчёт уже пожаловался.
    """
    broken: list[tuple[str, str]] = []

    for field, whole_field, part_name, whole_name in LABEL_FRACTIONS:
        part = getattr(item, field, None)
        whole = getattr(item, whole_field, None)
        if part is None or whole is None:
            continue
        if part < 0:
            broken.append((field, f"{part_name}={part} отрицательные"))
        elif part > whole + FRACTION_TOLERANCE_G:
            broken.append((field, f"{part_name}={part:.0f} г больше, чем "
                                  f"{whole_name} целиком ({whole:.0f} г)"))

    for field, ceiling, name in (("cholesterol", MAX_CHOLESTEROL_MG, "холестерин"),
                                 ("sodium", MAX_SODIUM_MG, "натрий")):
        value = getattr(item, field, None)
        if value is None:
            continue
        if value < 0:
            broken.append((field, f"{name}={value} отрицательный"))
        elif value > ceiling:
            broken.append((field, f"{name}={value:.0f} мг выше потолка {ceiling:.0f}"))

    return broken


def strip_broken_label(items):
    """Гасит недостоверные поля этикетки, оставляя позицию в каталоге."""
    cleaned = []
    for item in items:
        broken = broken_label_fields(item)
        cleaned.append(replace(item, **{field: None for field, _ in broken})
                       if broken else item)
    return cleaned


def check_item(item) -> list[Problem]:
    """Проверки одной позиции. Возвращает список проблем, пустой — если всё чисто."""
    problems: list[Problem] = []

    def add(kind: str, detail: str, severity: str = "error") -> None:
        problems.append(Problem(item.chain, item.name, kind, detail, severity))

    for field, value, ceiling in (
        ("kcal", item.kcal, MAX_KCAL),
        ("protein", item.protein, MAX_PROTEIN_G),
        ("carbs", item.carbs, MAX_CARB_G),
        ("fat", item.fat, MAX_FAT_G),
    ):
        if value < 0:
            add("range", f"{field}={value} отрицательное")
        elif value > ceiling:
            add("range", f"{field}={value} выше потолка {ceiling:.0f}")

    # Этикетка. Её проблемы не отменяют позицию: калории и макросы могут
    # быть в полном порядке, и выкидывать из каталога стейк из-за его
    # трансжиров незачем. Поэтому только предупреждение — а само сломанное
    # число гасит build_seed по этому же правилу (broken_label_fields).
    for field, detail in broken_label_fields(item):
        add("label", detail, "warning")

    if item.kcal > WARN_KCAL:
        add("portion", f"{item.kcal:.0f} ккал — вероятно целая порция на компанию", "warning")

    if item.kcal >= ATWATER_FLOOR_KCAL:
        expected = atwater_kcal(item.protein, item.carbs, item.fat)
        if expected > 0:
            drift = (expected - item.kcal) / item.kcal
            # Сахарные спирты (мальтит, эритрит) дают ~2 ккал/г вместо 4, но
            # считаются в углеводах. У «no sugar added» макросы законно
            # объясняют больше калорий, чем заявлено.
            if _has_sugar_alcohols(item) and drift <= SUGAR_ALCOHOL_TOLERANCE:
                pass
            elif drift > ATWATER_OVERCOUNT_TOLERANCE:
                # Макросы дают больше энергии, чем заявлено калорий — так не бывает.
                add("atwater", f"макросы дают {expected:.0f} ккал против заявленных "
                               f"{item.kcal:.0f} (+{drift:.0%})")
            elif -drift > ATWATER_UNDERCOUNT_TOLERANCE:
                gap = -drift
                severity = "error" if gap > ATWATER_UNDERCOUNT_ERROR else "warning"
                add("atwater", f"{item.kcal:.0f} ккал, макросы объясняют только "
                               f"{expected:.0f} ({gap:.0%}) — алкоголь или потерянный макрос",
                    severity)

    return problems


def check_catalog(items) -> list[Problem]:
    out: list[Problem] = []
    for item in items:
        out.extend(check_item(item))
    return out


def errors(problems) -> list[Problem]:
    return [p for p in problems if p.severity == "error"]


def check_diff(previous: dict[str, dict], current: dict[str, dict]) -> tuple[bool, str]:
    """Сравнивает прошлый и текущий кроул одной сети.

    Возвращает (ok, объяснение). ok=False → crawls.status='held', релиз не собирать.
    Это единственное, что стоит между редизайном сайта сети и стёртой из
    приложения сетью.
    """
    if not previous:
        return True, "первый кроул, сравнивать не с чем"

    dropped = set(previous) - set(current)
    changed = sum(
        1 for k, v in current.items()
        if k in previous and previous[k] != v
    )

    dropped_share = len(dropped) / len(previous)
    changed_share = changed / len(previous)

    if dropped_share > MAX_DROPPED_SHARE:
        return False, f"пропало {dropped_share:.0%} позиций ({len(dropped)} из {len(previous)})"
    if changed_share > MAX_CHANGED_SHARE:
        return False, f"изменилось {changed_share:.0%} позиций ({changed} из {len(previous)})"

    return True, f"пропало {len(dropped)}, изменилось {changed} из {len(previous)}"
