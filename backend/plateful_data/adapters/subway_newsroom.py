"""Subway — снимки блюд из её собственной медиатеки для прессы.

Сайт сети рисует меню скриптом, а гид по питанию — PDF без картинок.
Зато у Subway есть открытая медиатека: `newsroom.subway.com` с разделами
по видам блюд, и у каждого снимка ссылка «Hi Res» на исходник в два-три
мегабайта. Имя блюда стоит прямо в имени файла.

Часть снимков подписана фотографом со стороны — «Credit: … Getty Images
for Subway». Их не берём: разрешение сети на её материалы не покрывает
чужое авторство, а разбираться с ним отдельно ради десятка кадров не
стоит.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

SLUG = "subway"
CHAIN = "Subway"
DOMAIN = "newsroom.subway.com"
MENU_URL = "https://newsroom.subway.com/Menu-Items"

#: Разделы медиатеки с блюдами. «Restaurants», «Lifestyle» и «Logos» —
#: не еда, их не трогаем.
SECTIONS = ("Sandwiches", "Cookies", "Salads", "Sauces", "Sidekicks")

_LINK = re.compile(r'href="(/download/[^"]+\.(?:png|jpe?g))"', re.I)

#: Служебные хвосты в имени файла: «_newHR», «_v1», «-0», «001».
_TAIL = re.compile(r"(?:[_-](?:new)?hr|[_-]v\d+|[_-]?\d{2,3})$", re.I)
#: Порядковый номер в начале: «2-Subway Footlong Cookie».
_LEAD = re.compile(r"^\d+[-_]\s*")
#: Номер дубля в скобках: «Ultimate BMT (1)» — второй кадр того же блюда.
_TAKE = re.compile(r"\s*\(\d+\)\s*$")
#: Чужое авторство в имени файла.
_CREDITED = re.compile(r"credit|getty", re.I)


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def dish_name(path: str) -> str | None:
    """«/download/All+American+Club_newHR.png» → «All American Club»."""
    stem = urllib.parse.unquote(path.rsplit("/", 1)[-1]).rsplit(".", 1)[0]
    stem = stem.replace("+", " ")
    if _CREDITED.search(stem):
        return None
    stem = _LEAD.sub("", stem)
    stem = _TAIL.sub("", stem)
    stem = _TAKE.sub("", stem)
    stem = stem.replace("_", " ").strip()
    return " ".join(stem.split()) or None


def catalog() -> list[Shot]:
    """Снимки блюд из медиатеки — по запросу на раздел."""
    from ..slug import slugify

    shots: list[Shot] = []
    seen: set[str] = set()
    for section in SECTIONS:
        page = curl_get(f"https://{DOMAIN}/{section}?per_page=100",
                        {"User-Agent": USER_AGENT}, timeout=60)
        if not page:
            continue
        for path in dict.fromkeys(_LINK.findall(page)):
            name = dish_name(path)
            key = slugify(name or "")
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                              image_url=f"https://{DOMAIN}{path}",
                              source_url=f"https://{DOMAIN}/{section}"))
    return shots
