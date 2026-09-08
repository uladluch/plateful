"""Сборка пака для приложения.

Контракт (его же читает plateful/Menu/MenuPack.swift):

    manifest.json  {format, version, url, sha256, itemCount, releasedAt}
    pack           {format, version, source, observed, stale,
                    sections: [name],            порядок разделов в меню
                    chains: [{name, itemCount}],
                    items:  [{chain, key, name, category, section, serving,
                              kcal, protein, carbs, fat, image,
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
