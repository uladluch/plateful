"""Реестр источников снимков: платформа → как читать.

Откуда у сети снимки, записано в базе — `chains.photo_source_kind` и
`chains.photo_source_url`, — а не в цепочке `if` внутри скрипта. Подключить
сеть на известной платформе значит записать строку, а не написать код:
Krystal сидит на Olo так же, как Chili's и Applebee's.

Виды делятся на два рода. **Платформенные** — Olo, Sanity, Contentful —
читают любую сеть по адресу из базы. **Именные** — Panera, Starbucks,
McDonald's — это одна сеть со своим устройством сайта; вид назван по ней,
и адрес из базы им не нужен. Когда именных на одной платформе наберётся
две, их место — в платформенном.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import (chickfila, collected, culvers, einstein_bros, gotofoods, jersey_mikes,
               mcdonalds, olo_menu, panera, quiznos, sanity_rbi, starbucks,
               subway_newsroom, tacobell)


@dataclass(frozen=True)
class Source:
    """Строка `chains`: что нужно адаптеру, чтобы прочитать сеть."""
    slug: str
    name: str
    kind: str
    url: str | None
    rights: str | None


def _with_image(items) -> list:
    return [item for item in items if item.image_url]


#: Вид → чтение. Порядок — платформенные, потом именные.
KINDS: dict[str, Callable[[Source], list]] = {
    "olo": lambda s: olo_menu.catalog(olo_menu.Brand(s.slug, s.name, s.url)),
    "sanity-rbi": lambda s: _with_image(sanity_rbi.fetch(sanity_rbi.BRANDS[s.slug])),
    "contentful-gotofoods": lambda s: _with_image(gotofoods.catalog(gotofoods.BRANDS[s.slug])),
    "collected": lambda s: collected.catalog(s.slug, s.name, s.url),
    "mcdonalds-snapshot": lambda s: _with_image(mcdonalds.load()),
    "panera-aem": lambda s: panera.catalog(),
    "starbucks-scene7": lambda s: starbucks.catalog(),
    "jerseymikes-api": lambda s: jersey_mikes.catalog(),
    "quiznos-site": lambda s: quiznos.catalog(),
    "subway-newsroom": lambda s: subway_newsroom.catalog(),
    "chickfila-wordpress": lambda s: chickfila.catalog(),
    "tacobell-nextjs": lambda s: tacobell.catalog(),
    "culvers-nextjs": lambda s: culvers.catalog(),
    "einstein-wordpress": lambda s: einstein_bros.catalog(),
}


def shots(source: Source) -> list:
    """Позиции сети со снимками — по виду источника из базы."""
    try:
        read = KINDS[source.kind]
    except KeyError:
        raise SystemExit(f"{source.slug}: вид источника «{source.kind}» не известен; "
                         f"известны: {', '.join(sorted(KINDS))}") from None
    return read(source)


def sql_check() -> str:
    """Список видов для ограничения в миграции — чтобы база и код не разошлись."""
    return ", ".join(f"'{kind}'" for kind in KINDS)
