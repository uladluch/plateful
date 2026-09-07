"""MenuStat 2018 — загрузка и очистка.

Источник: Harvard Dataverse, doi:10.7910/DVN/K4NYTR, лицензия CC0 1.0.
Оригинальный menustat.org мёртв, зеркало Dataverse — единственный живой доступ.

Файл называется .tab, но на деле это CSV с кавычками. 71 172 строки, 50 колонок.
"""

from __future__ import annotations

import csv
import io
import re
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

from .slug import slugify

DATAVERSE_FILE_IDS = {
    2008: 6191166, 2010: 6191164, 2012: 6191168, 2013: 6191161,
    2014: 6191162, 2015: 6191163, 2017: 6191165, 2018: 6191167,
}
LATEST_YEAR = 2018
DOWNLOAD_URL = "https://dataverse.harvard.edu/api/access/datafile/{file_id}?format=original"

SOURCE = "menustat-2018"
OBSERVED_AT = "2018-12-31"

# Строки с этой пометкой — перестановки комбо (напиток × гарнир × основное),
# а не отдельные позиции меню. Их 41 052 из 71 172, и без фильтра каталог
# распухает дублями.
COMBO_BUILD_MARKER = "Accompanying Item"

_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class Item:
    chain: str
    ext_key: str
    name: str
    category: str | None
    serving: str | None
    kcal: float
    protein: float
    carbs: float
    fat: float
    sat_fat: float | None
    sodium: float | None
    sugar: float | None
    fiber: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def download(year: int = LATEST_YEAR, cache: Path | None = None) -> str:
    """Скачивает годовой срез. При наличии кэша читает с диска."""
    if cache and cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")

    url = DOWNLOAD_URL.format(file_id=DATAVERSE_FILE_IDS[year])
    with urllib.request.urlopen(url, timeout=300) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(raw, encoding="utf-8")
    return raw


def _num(value: str | None) -> float | None:
    """MenuStat пишет пропуски как пустое, NA, N/A и иногда как текст."""
    if value is None:
        return None
    v = value.strip()
    if not v or v.upper() in {"NA", "N/A", "NULL", "-"}:
        return None
    try:
        return round(float(v), 1)
    except ValueError:
        return None


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    v = _WS.sub(" ", value).strip()
    return v or None


def _ext_key(name: str) -> str:
    """Стабильный ключ позиции внутри сети.

    К нему цепляются overrides, поэтому он не должен меняться от кроула
    к кроулу: только нормализованное имя, без регистра и пунктуации.
    """
    return slugify(name)


def _serving(row: dict) -> str | None:
    household = _clean_text(row.get("Serving_Size_household"))
    if household:
        return household
    size = _clean_text(row.get("Serving_Size"))
    unit = _clean_text(row.get("Serving_Size_Unit"))
    if size and unit:
        return f"{size} {unit}"
    return size


def parse(raw: str) -> list[Item]:
    """Сырой файл → чистый каталог.

    Три шага очистки, каждый обязателен:
      1. выбросить combo-перестановки
      2. выбросить строки без всех четырёх макросов
      3. дедуп по (сеть, нормализованное имя) — берём первое вхождение
    """
    reader = csv.DictReader(io.StringIO(raw))
    seen: dict[tuple[str, str], Item] = {}

    for row in reader:
        if row.get("Customizable_Builds", "").strip() == COMBO_BUILD_MARKER:
            continue

        chain = _clean_text(row.get("Restaurant"))
        name = _clean_text(row.get("Item_Name"))
        if not chain or not name:
            continue

        kcal = _num(row.get("Calories"))
        protein = _num(row.get("Protein"))
        carbs = _num(row.get("Carbohydrates"))
        fat = _num(row.get("Total_Fat"))
        if None in (kcal, protein, carbs, fat):
            continue

        key = (chain, _ext_key(name))
        if key in seen:
            continue

        seen[key] = Item(
            chain=chain,
            ext_key=key[1],
            name=name,
            category=_clean_text(row.get("Food_Category")),
            serving=_serving(row),
            kcal=kcal,
            protein=protein,
            carbs=carbs,
            fat=fat,
            sat_fat=_num(row.get("Saturated_Fat")),
            sodium=_num(row.get("Sodium")),
            sugar=_num(row.get("Sugar")),
            fiber=_num(row.get("Dietary_Fiber")),
        )

    return sorted(seen.values(), key=lambda i: (i.chain, i.name))
