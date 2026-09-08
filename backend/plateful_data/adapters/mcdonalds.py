"""McDonald's: студийные снимки блюд со страницы калькулятора питания.

Страница позиции — пустая оболочка, товар подгружается скриптом, а
внутренние JSON-эндпоинты закрыты. Зато страница калькулятора отдаёт разом
все плитки блюд: PNG с прозрачным фоном на Adobe Scene7, 1564×1564.

Обычный запрос сеть отвергает (обрыв TLS). С полным набором браузерных
заголовков отвечает нормально — Playwright для этого не нужен.

Название блюда зашито в имя файла в CamelCase:
    DC_202201_0007-005_QuarterPounderwithCheese_1564x1564-1
        → «Quarter Pounder with Cheese»
"""

from __future__ import annotations

import re

from .base import curl_get

CHAIN = "McDonald's"
SOURCE = "mcdonalds.com"
CALCULATOR_URL = "https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html"

# Сеть смотрит не только на User-Agent: без остальных заголовков рвёт TLS.
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "upgrade-insecure-requests": "1",
}

_TILE = re.compile(r'https://s7d1\.scene7\.com/is/image/mcdonalds/[^"\s\\&]+')
# Мусор в имени файла: даты, коды артикулов, ракурсы, размеры.
_JUNK = re.compile(
    r"^(DC|MCD|US)$|^\d+$|^\d{4}XX$|^r\d+$|^\d+x\d+.*$|^[A-Z]\d$"
    r"|^(HR|Light|Alt|Glass|WithCan|Bag|Box|Cup|Broken)$", re.I)
_WORDS = re.compile(r"[A-Z][a-z]+|[A-Z]+(?![a-z])|\d+|[a-z]+")
# Пресет в конце пути, а не двоеточие после «https».
_PRESET = re.compile(r":[A-Za-z0-9\-]+$")


def item_name(url: str) -> str | None:
    """Читаемое название из имени файла."""
    try:
        stem = url.split("/mcdonalds/")[1].split(":")[0]
    except IndexError:
        return None
    parts = [p for p in re.split(r"[_\-]", stem) if p and not _JUNK.match(p)]
    words: list[str] = []
    for part in parts:
        words.extend(_WORDS.findall(part))
    name = " ".join(words)
    return name if len(name) > 3 else None


def photo_pairs(fetcher) -> list[tuple[str, str, str]]:
    """(название, ссылка на снимок, страница-источник)."""
    page = curl_get(CALCULATOR_URL, BROWSER_HEADERS)
    if not page:
        return []

    pairs = []
    for url in sorted({u for u in _TILE.findall(page)
                       if "nutrition-calculator-tile" in u and "menu-category" not in u}):
        name = item_name(url)
        if not name:
            continue
        # Пресет `nutrition-calculator-tile` режет снимок в широкий формат
        # 1000×600. Без пресета Scene7 отдаёт исходный квадрат целиком.
        image_url = f"{_PRESET.sub('', url)}?fmt=png-alpha&wid=1000"
        pairs.append((name, image_url, CALCULATOR_URL))
    return pairs
