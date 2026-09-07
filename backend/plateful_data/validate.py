"""Валидация каталога.

Парсеры ломаются тихо: съехала колонка, граммы приняты за миллиграммы,
LLM выдумала число. Все эти поломки дают одно и то же — макросы, которые
не сходятся с калориями. Поэтому главная проверка здесь одна.
"""

from __future__ import annotations

from dataclasses import dataclass

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

# Пороги дифф-проверки: если кроул перевернул сеть сильнее — это поломка
# адаптера, а не обновление меню. Релиз собирать нельзя.
MAX_CHANGED_SHARE = 0.30
MAX_DROPPED_SHARE = 0.20


SUGAR_ALCOHOL_TOLERANCE = 0.60
_SUGAR_ALCOHOL_HINTS = (
    "no sugar added", "sugar free", "sugar-free", "diet ", "light ice cream",
)


def _has_sugar_alcohols(item) -> bool:
    haystack = f"{item.name} {item.category or ''}".lower()
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
