"""Red Lobster — снимки блюд со страниц разделов меню.

Меню сети открывается без выбора ресторана: восемнадцать разделов, в
каждом карточки блюд, и у карточки есть и имя, и снимок. Снимок стоит не
в `<img>`, а фоном в стиле карточки — поэтому обычный сбор картинок со
страницы его не видит и находит одни заглушки.

Файлы лежат на CDN сети под именем «код позиции + идентификатор ассета»,
и размер задаётся прямо в пути. Просим квадрат 800: он есть, и кадрировать
его не надо, тогда как ходовой 640x360 пришлось бы резать по краям — а у
блюда края и есть тарелка.

Этикетку сеть публикует гидом (`pdf_guide.RED_LOBSTER`), поэтому здесь
только снимки.

**Сейчас этим маршрутом не ходим.** После нескольких запросов сеть
ставит капчу ShieldSquare, а капча — это прямо сказанное «не ходите сюда
автоматом». Обходить её мы не будем: разбор оставлен, потому что первый
запрос проходит и разметка разобрана верно, — но включать этот источник
можно, только если сеть перестанет так отвечать.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get

SLUG = "red-lobster"
CHAIN = "Red Lobster"
DOMAIN = "redlobster.com"
MENU_URL = "https://www.redlobster.com/menu"

#: Разделы меню сеть держит выпадающим списком на странице **раздела**.
#: Сама страница меню приходит пустой оболочкой и рисуется скриптом,
#: поэтому список читаем не с неё, а с любого раздела — отсюда и нужен
#: заход, с которого начинается обход.
_SECTION = re.compile(r'<option value="([a-z0-9-]+)">')

#: Раздел, с которого начинаем: он есть у сети всегда.
FIRST_SECTION = "starters"

#: Карточка блюда: ссылка, снимок фоном, имя заголовком. Порядок в
#: разметке постоянен, поэтому берём одним выражением — так имя и снимок
#: не разъедутся, как разъезжались бы при сборе по отдельности.
_CARD = re.compile(
    r'href="(?P<href>/menu/[^"]+)"[^>]*>.{0,400}?'
    r"background-image:\s*url\('(?P<image>https://[^']*?/ecomm-image/)"
    r"(?P<size>[^/]+)/(?P<file>[^']+?)(?:\?[^']*)?'\)"
    r'.{0,400}?menu__item-title">\s*(?P<name>[^<]+?)\s*</',
    re.S)

#: Заглушка на месте отсутствующего снимка — не снимок.
_PLACEHOLDER = "_placeholder"

#: Размер, который отдаёт CDN. Квадрат кадрировать не надо.
SIZE = "800x800"


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def sections(html: str) -> list[str]:
    # «Специальные предложения» — витрина из блюд других разделов.
    return [s for s in dict.fromkeys(_SECTION.findall(html)) if s != "specials"]


def cards(html: str, base: str) -> list[tuple[str, str, str]]:
    """(имя, адрес снимка, адрес страницы блюда) со страницы раздела."""
    found = []
    for match in _CARD.finditer(html):
        file = match.group("file")
        if _PLACEHOLDER in file:
            continue
        found.append((
            " ".join(match.group("name").split()),
            f"{match.group('image')}{SIZE}/{file}",
            f"https://www.{DOMAIN}{match.group('href')}"))
    return found


def catalog(pause: float = 1.0, log=print) -> list[Shot]:
    """Снимки всех блюд меню — по разделу на запрос."""
    from ..slug import slugify

    front = curl_get(f"{MENU_URL}/{FIRST_SECTION}", BROWSER_HEADERS, timeout=45)
    if not front:
        raise SystemExit("меню Red Lobster не открылось")
    names = sections(front) or [FIRST_SECTION]
    log(f"  разделов: {len(names)}")

    shots: list[Shot] = []
    seen: set[str] = set()
    for section in names:
        page = curl_get(f"{MENU_URL}/{section}", BROWSER_HEADERS, timeout=45)
        if not page:
            continue
        for name, image, source in cards(page, section):
            key = slugify(name)
            if not key or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=CHAIN, ext_key=key, name=name,
                              image_url=image, source_url=source))
        time.sleep(pause)
    return shots
