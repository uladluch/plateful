"""Сборка пака для приложения.

Контракт (его же читает plateful/Menu/MenuPack.swift):

    manifest.json  {format, version, url, sha256, itemCount, releasedAt}
    pack           {format, version, source, observed, stale,
                    sections: [name],            порядок разделов в меню
                    chains: [{name, itemCount}],
                    items:  [{chain, key, name, category, section, serving,
                              kcal, protein, carbs, fat,
                              sugar?, satFat?, transFat?, cholesterol?,
                              sodium?, fiber?, flags?, image,
                              variant?: {group, label, order, kind, base},
                              source?, observed?, stale?}]}

`section` — раздел, в котором приложение покажет позицию: категория
источника, а поверх неё выделенный завтрак. Порядок разделов лежит в паке,
а не в приложении: у источника его нет вовсе, а менять его хочется
публикацией, не релизом.

`variant` — порция или опция одного блюда («Small», «10», «w/ Egg»).
Позиции с одинаковым `group` внутри сети приложение показывает одной
карточкой с переключателем.

Происхождение (`source`, `observed`, `stale`) вынесено на уровень пака, а у
позиции появляется только там, где отличается. В сиде все позиции из одного
среза MenuStat, поэтому у них этих полей нет вовсе; после ручной правки у
конкретной позиции будет свой источник и своя дата. Приложению это нужно:
обещание «показывать дату и источник» — один из трёх дифференциаторов.

Один и тот же формат у сида в бандле и у скачанного обновления, чтобы у
MenuRepository был ровно один декодер.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from collections import Counter
from dataclasses import dataclass

from .archetype import classify
from .taxonomy import SECTION_ORDER, section
from .variants import assign_groups
from datetime import date
from pathlib import Path

PACK_FORMAT = 1

DEFAULT_SOURCE = "menustat-2018"
DEFAULT_OBSERVED = "2018-12-31"


def _mode(values, fallback):
    """Самое частое значение — оно и станет умолчанием пака."""
    counted = Counter(values)
    return counted.most_common(1)[0][0] if counted else fallback


# ── Готовность сети ────────────────────────────────────────────────────
#
# Сеть попадает в приложение целиком или не попадает вовсе. Наполовину
# собранная выглядит хуже, чем отсутствующая: человек открывает меню,
# видит блюда без снимков и цифры пятилетней давности вперемешку со
# свежими — и перестаёт верить и тем, и другим. Отсутствие сети он
# объясняет себе сам, а битую карточку объясняет качеством приложения.
#
# Порог не «всё до последней позиции»: у сети всегда найдётся напиток,
# который она сама нигде не сфотографировала. Десятая часть — это то, что
# не бросается в глаза при листании.
PHOTO_SHARE = 0.90
FRESH_SHARE = 0.90


@dataclass(frozen=True)
class Readiness:
    """Насколько сеть готова показаться человеку."""
    items: int
    photos: float
    fresh: float

    @property
    def ok(self) -> bool:
        return self.photos >= PHOTO_SHARE and self.fresh >= FRESH_SHARE

    def __str__(self) -> str:
        return f"{self.items:>5} поз.  снимки {self.photos:5.0%}  свежих {self.fresh:5.0%}"


def readiness(rows) -> dict[str, Readiness]:
    """Готовность каждой сети. `rows` — (сеть, есть снимок, свежая, снята с меню).

    Архивные позиции в счёт не идут: у снятого с меню блюда снимка нет и
    не будет, а дата у него старая по определению. Судить по ним готовность
    сети — значит наказывать её за то, что мы честно храним её прошлое.
    """
    counts: dict[str, list[int]] = {}
    for chain, has_photo, fresh, off_menu in rows:
        if off_menu:
            continue
        bucket = counts.setdefault(chain, [0, 0, 0])
        bucket[0] += 1
        bucket[1] += bool(has_photo)
        bucket[2] += bool(fresh)
    return {chain: Readiness(n, photos / n, fresh / n)
            for chain, (n, photos, fresh) in counts.items() if n}


def pack_rows(built: dict):
    """Строки готовности из собранного пака — он несёт всё нужное сам."""
    default_stale = bool(built.get("stale", True))
    for item in built["items"]:
        yield (item["chain"], bool(item.get("photo")),
               not bool(item.get("stale", default_stale)),
               bool(item.get("offMenu")))


def unready(built: dict) -> dict[str, Readiness]:
    """Сети собранного пака, которые показывать нельзя."""
    return {chain: score for chain, score in readiness(pack_rows(built)).items()
            if not score.ok}


def build(items, *, version: int, source: str, observed: str) -> dict:
    chains = Counter(i.chain for i in items)
    # Размерные варианты одного блюда склеиваются в группу: приложение
    # покажет их переключателем вместо четырёх карточек колы подряд.
    groups = assign_groups(items)

    sources = [getattr(i, "source", None) or source for i in items]
    observations = [getattr(i, "observed", None) or observed for i in items]
    staleness = [bool(getattr(i, "stale", True)) for i in items]

    pack_source = _mode(sources, source or DEFAULT_SOURCE)
    pack_observed = _mode(observations, observed or DEFAULT_OBSERVED)
    pack_stale = _mode(staleness, True)

    encoded = []
    for item, item_source, item_observed, item_stale in zip(
        items, sources, observations, staleness
    ):
        row = {
            "chain": item.chain,
            "key": item.ext_key,
            "name": item.name,
            "category": item.category,
            # Раздел меню. Считается здесь, а не на клиенте: правило одно на
            # 96 сетей, и ошибку в нём чинит публикация пака.
            "section": section(item.name, item.category),
            "serving": item.serving,
            "kcal": item.kcal,
            "protein": item.protein,
            "carbs": item.carbs,
            "fat": item.fat,
            # Архетип блюда: по нему приложение подбирает снимок. Считается
            # здесь, а не на клиенте, чтобы ошибочно назначенную картинку
            # можно было исправить публикацией пака, без релиза.
            "image": classify(item.name, item.category),
        }
        # Остальная этикетка. Она есть почти везде — источник берёт её из
        # того же обязательного раскрытия, что и калории (21 CFR 101.11), —
        # но приходит не всегда, поэтому только там, где число есть.
        for field, key in (("sugar", "sugar"), ("sat_fat", "satFat"),
                           ("trans_fat", "transFat"),
                           ("cholesterol", "cholesterol"),
                           ("sodium", "sodium"), ("fiber", "fiber")):
            value = getattr(item, field, None)
            if value is not None:
                row[key] = value

        # Пометки позиции: детская порция, на компанию, не во всех точках,
        # сезонное. Едут только там, где есть, — у 86% блюд их нет вовсе.
        if flags := tuple(getattr(item, "flags", ()) or ()):
            row["flags"] = list(flags)

        if variant := groups.get((item.chain, item.ext_key)):
            group, label, order, kind, base = variant
            row["variant"] = {"group": group, "label": label,
                              "order": order, "kind": kind, "base": base}
        # Только отличия от умолчаний пака — иначе пак раздувается втрое.
        if item_source != pack_source:
            row["source"] = item_source
        if item_observed != pack_observed:
            row["observed"] = item_observed
        if item_stale != pack_stale:
            row["stale"] = item_stale
        photo = getattr(item, "photo", None)
        if photo:
            row["photo"] = photo
        if getattr(item, "off_menu", False):
            row["offMenu"] = True
        encoded.append(row)

    # Даты релиза здесь нет намеренно: пак должен байт-в-байт совпадать при
    # пересборке из того же исходника, иначе CI не сможет проверить, что файл
    # в бандле актуален. Дата — свойство манифеста и таблицы releases.
    return {
        "format": PACK_FORMAT,
        "version": version,
        "source": pack_source,
        "observed": pack_observed,
        "stale": pack_stale,
        # Только те разделы, что реально встретились, — в общем порядке.
        "sections": [name for name in SECTION_ORDER
                     if any(row["section"] == name for row in encoded)],
        "chains": [
            {"name": name, "itemCount": count}
            for name, count in sorted(chains.items())
        ],
        "items": encoded,
    }


def _raw_deflate(payload: bytes) -> bytes:
    """Сырой DEFLATE, без zlib-обёртки.

    Именно его понимает Data.decompressed(using: .zlib) на стороне iOS:
    у Apple `.zlib` означает raw deflate, а не zlib-контейнер. zlib.compress()
    добавляет двухбайтовый заголовок и adler32 в хвосте — с ними распаковка
    на устройстве падает.
    """
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    return compressor.compress(payload) + compressor.flush()


def write(pack: dict, *, json_path: Path, deflate_path: Path | None = None) -> dict:
    """Пишет пак и возвращает метаданные для манифеста."""
    payload = json.dumps(pack, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_bytes(payload)

    meta = {
        "version": pack["version"],
        "itemCount": len(pack["items"]),
        "releasedAt": date.today().isoformat(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }

    if deflate_path:
        compressed = _raw_deflate(payload)
        deflate_path.parent.mkdir(parents=True, exist_ok=True)
        deflate_path.write_bytes(compressed)
        meta["compressedBytes"] = len(compressed)
        # Манифест проверяет сжатые байты: клиент считает хеш до распаковки.
        meta["compressedSha256"] = hashlib.sha256(compressed).hexdigest()

    return meta


def manifest(meta: dict, *, url: str) -> dict:
    return {
        "format": PACK_FORMAT,
        "version": meta["version"],
        "url": url,
        "sha256": meta.get("compressedSha256", meta["sha256"]),
        "itemCount": meta["itemCount"],
        "releasedAt": meta["releasedAt"],
    }
