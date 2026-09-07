"""Сборка пака для приложения.

Контракт (см. .claude/skills/plateful-data):
  manifest.json  {version, url, sha256, itemCount, releasedAt}
  pack           {version, releasedAt, chains: [...], items: [...]}

Пак — единственный формат, который знает приложение. Один и тот же и для
seed в бандле, и для скачанного обновления, чтобы у MenuRepository был
ровно один декодер.

Сжатие — raw deflate (zlib), а не gzip: Foundation умеет его из коробки
через Data.decompressed(using: .zlib), и iOS-клиенту не нужна зависимость.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from collections import Counter
from datetime import date
from pathlib import Path

PACK_FORMAT = 1


def build(items, *, version: int, source: str, observed: str) -> dict:
    chains = Counter(i.chain for i in items)

    # Даты релиза здесь нет намеренно: пак должен байт-в-байт совпадать при
    # пересборке из того же исходника, иначе CI не сможет проверить, что файл
    # в бандле актуален. Дата — свойство манифеста и таблицы releases.
    return {
        "format": PACK_FORMAT,
        "version": version,
        "source": source,
        "observed": observed,
        "chains": [
            {"name": name, "itemCount": count}
            for name, count in sorted(chains.items())
        ],
        "items": [
            {
                "chain": i.chain,
                "key": i.ext_key,
                "name": i.name,
                "category": i.category,
                "serving": i.serving,
                "kcal": i.kcal,
                "protein": i.protein,
                "carbs": i.carbs,
                "fat": i.fat,
            }
            for i in items
        ],
    }


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
        # level 9, raw zlib-обёртка — то, что понимает Data.decompressed(using: .zlib)
        compressed = zlib.compress(payload, 9)
        deflate_path.parent.mkdir(parents=True, exist_ok=True)
        deflate_path.write_bytes(compressed)
        meta["compressedBytes"] = len(compressed)
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
