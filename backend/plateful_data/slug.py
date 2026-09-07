"""Единственная реализация slug/ext_key для всего конвейера.

Один и тот же алгоритм используют:
  - chains.slug          (загрузчик, адаптеры)
  - items.ext_key        (menustat.parse, адаптеры)
  - SQL в миграциях:     regexp_replace(lower(name), '[^a-z0-9]+', '-', 'g')

Если он разойдётся хотя бы в одном месте, overrides перестанут находить
позиции, а загрузчик — сети. Поэтому менять только здесь и в SQL синхронно.
"""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _NON_ALNUM.sub("-", text.lower()).strip("-")
