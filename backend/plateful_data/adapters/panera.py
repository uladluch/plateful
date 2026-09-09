"""Panera Bread — открытый индекс снимков блюд.

Сайт закрыт бот-защитой: и разметка, и GraphQL отвечают 403 всему, что не
похоже на браузер отпечатком TLS. А вот хранилище ассетов — нет. Panera
работает на Adobe Experience Manager, и AEM выкладывает рядом с каждой
папкой ассетов её опись: `<путь>.asset.json` со списком файлов.

Опись снимков блюд лежит по постоянному адресу и читается обычным
запросом; сами снимки — тоже, и в исходном размере 2048 пикселей.

Этикетку сеть так не отдаёт — она в PDF-гиде, и каталог собран из него.
Здесь только снимки: ключ описи — слаг блюда, который сопоставляется с
каталогом тем же правилом имён, что и всё остальное.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .base import USER_AGENT, curl_get

SLUG = "panera-bread"
CHAIN = "Panera Bread"
DOMAIN = "panerabread.com"
MENU_URL = "https://www.panerabread.com/en-us/menu.html"

_DAM = ("https://www.panerabread.com/content/dam/panerabread/menu-omni/"
        "integrated-web")

#: Папки ассетов, по убыванию качества кадра. AEM выкладывает опись рядом
#: с каждой; одно и то же блюдо лежит в нескольких, и первая непустая
#: побеждает — «detail» это карточка блюда, «grid» плитка в списке.
_FOLDERS = ("detail/dark", "detail", "grid/rect", "grid")


@dataclass(frozen=True)
class Shot:
    """Снимок блюда — в тех же полях, что и позиция любого источника."""
    chain: str
    ext_key: str
    name: str
    image_url: str


def catalog() -> list[Shot]:
    """Все снимки блюд из описей ассетов.

    Имя получаем из слага: у Panera они человеческие
    («broccoli-cheddar-soup-cup»), и правило сопоставления имён читает их
    не хуже, чем полные названия.
    """
    found: dict[str, tuple[str, str]] = {}
    for folder in _FOLDERS:
        body = curl_get(f"{_DAM}/{folder}.asset.json",
                        {"User-Agent": USER_AGENT}, timeout=60)
        if not body:
            continue
        for slug, meta in (json.loads(body).get("assetInfo") or {}).items():
            found.setdefault(slug, (folder, (meta.get("extensions") or ["jpg"])[0]))
    if not found:
        raise SystemExit("описи снимков Panera не открылись")

    return [Shot(chain=CHAIN, ext_key=slug, name=slug.replace("-", " "),
                 image_url=f"{_DAM}/{folder}/{slug}.{extension}")
            for slug, (folder, extension) in sorted(found.items())]
