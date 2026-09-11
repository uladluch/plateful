"""Сети на Sanity — снимки блюд из публичного GROQ, по адресу из базы.

Sanity — контент-база, на которой сидят сайты многих сетей, и у части из
них набор данных открыт на чтение: запрос GROQ без токена отдаёт
документы вместе со ссылками на снимки. У RBI своя схема и свой адаптер
(`sanity_rbi`); здесь — общий случай: документ с полями `name` и `image`.

Адрес запроса лежит в `chains.photo_source_url`, например
`https://9tlw6prn.apicdn.sanity.io/v2021-10-21/data/query/production` —
в нём и проект, и набор данных. Подключить новую сеть на Sanity значит
найти эти два слова в разметке её сайта (`cdn.sanity.io/images/<проект>/
<набор>/`) и записать строку в базу, а не писать код.

Тип документа по умолчанию — `product`; если у сети иначе, он пишется
после `#` в том же адресе: `…/production#menuItem`.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .base import USER_AGENT


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def _clean(name: str) -> str:
    return " ".join(str(name).replace("®", " ").replace("™", " ").split())


def catalog(source_url: str, chain: str) -> list[Shot]:
    from ..slug import slugify

    base, _, doc_type = source_url.partition("#")
    doc_type = doc_type or "product"
    query = (f'*[_type == "{doc_type}" && defined(image.asset) && '
             '!(_id in path("drafts.**"))]{name, "img": image.asset->url}')
    request = urllib.request.Request(f"{base}?query={urllib.parse.quote(query)}",
                                     headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        docs = json.load(response).get("result") or []

    shots: list[Shot] = []
    seen: set[str] = set()
    for doc in docs:
        name, image = _clean(doc.get("name") or ""), doc.get("img")
        key = slugify(name)
        if not name or not image or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=chain, ext_key=key, name=name,
                          image_url=image, source_url=base))
    if not shots:
        raise SystemExit(f"Sanity {chain}: документов со снимком нет по {base}#{doc_type}")
    return shots
