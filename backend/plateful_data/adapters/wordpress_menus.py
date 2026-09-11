"""Сети на WordPress — снимки блюд из разметки страниц меню.

WordPress — самая частая платформа сайтов сетей, но общая у них только
механика: страница меню, иногда разделы, снимки на своём домене в
`/wp-content/uploads/`. Карточку блюда каждая тема рисует по-своему: у
Ruby Tuesday снимок фоном и имя в `<h6 class="title">` после него, у
Five Guys наоборот — имя в начале карточки, снимок в конце. Общее правило
«ищи заголовок после картинки» у Five Guys склеило бы снимок со следующим
блюдом, поэтому выкладка — строка на сеть: регулярка с двумя группами.

Всё остальное — обход разделов, крупнейший вариант из `srcset`, очистка
имени — общее. Подключить новую WordPress-сеть значит добавить строку в
`LAYOUTS`, а адрес меню и права записать в `chains`.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from .base import BROWSER_HEADERS, curl_get


@dataclass(frozen=True)
class Layout:
    #: Карточка блюда: группы `name` и `image` (порядок в разметке любой).
    card: re.Pattern
    #: Разделы меню — страницы, на которых лежат блюда. Пусто — всё на одной.
    sections: re.Pattern | None = None


#: Не пересекать границу карточки: всё, что не начинает следующую.
def _within(boundary: str) -> str:
    return rf"(?:(?!{boundary}).)*?"


LAYOUTS: dict[str, Layout] = {
    "ruby-tuesday": Layout(re.compile(
        r"background-image:\s*url\((?P<image>https://www\.rubytuesday\.com/wp-content/uploads/[^)]+)\)"
        + _within("menu_items") + r'<h6 class="title">\s*(?P<name>.*?)</h6>', re.S)),
    "round-table-pizza": Layout(re.compile(
        r'class="item-img" style="background-image:\s*url\((?P<image>[^)]+)\);?"'
        + _within('class="menu-item"') + r"<h3>(?P<name>.*?)</h3>", re.S)),
    "sbarro": Layout(re.compile(
        r'data-lazy="\[(?P<image>[^"]+)\]"' + _within("data-lazy=")
        + r"<h3><a[^>]*>(?P<name>.*?)</a></h3>", re.S)),
    "five-guys": Layout(
        re.compile(r'card-menu-item-content">\s*<h3>(?P<name>.*?)</h3>'
                   + _within("data-comname=")
                   + r'card-menu-item-thumb"\s*>\s*<img[^>]+src="(?P<image>[^"]+)"', re.S),
        sections=re.compile(r'href="(https://www\.fiveguys\.com/menu/[a-z0-9\-]+/)"')),
}


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def _largest(image: str) -> str:
    """Самый крупный адрес, если снимков несколько.

    Sbarro кладёт в `data-lazy` список «[адрес, small], [адрес, xlarge]»;
    последний — исходник. У остальных адрес один.
    """
    urls = re.findall(r"https?://[^\s,\]]+", image)
    return (urls[-1] if urls else image).strip()


def _clean(name: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", name))
    return " ".join(text.replace("®", " ").replace("™", " ").split())


def catalog(slug: str, chain: str, menu_url: str) -> list[Shot]:
    from ..slug import slugify

    layout = LAYOUTS.get(slug)
    if layout is None:
        raise SystemExit(f"{slug}: выкладки WordPress нет в LAYOUTS")
    landing = curl_get(menu_url, BROWSER_HEADERS, timeout=60) or ""
    if not landing:
        raise SystemExit(f"меню {chain} не открылось: {menu_url}")
    pages = [(menu_url, landing)]
    if layout.sections:
        for url in sorted(set(layout.sections.findall(landing))):
            if url.rstrip("/") != menu_url.rstrip("/"):
                pages.append((url, curl_get(url, BROWSER_HEADERS, timeout=60) or ""))

    shots: list[Shot] = []
    seen: set[str] = set()
    for url, page in pages:
        for match in layout.card.finditer(page):
            name, image = _clean(match.group("name")), _largest(match.group("image"))
            key = slugify(name)
            if not name or not image.startswith("http") or key in seen:
                continue
            seen.add(key)
            shots.append(Shot(chain=chain, ext_key=key, name=name,
                              image_url=image, source_url=url))
    return shots
