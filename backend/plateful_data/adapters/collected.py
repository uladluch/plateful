"""Снимки, снятые браузером и положенные файлом.

Часть сетей отдаёт меню только настоящему браузеру: страница приходит
пустой оболочкой и рисуется скриптом. Ходить туда скриптом нечем, но и
заводить каждой сети свой адаптер незачем — от них нужно одно и то же:
имя блюда и адрес снимка.

Поэтому файл общий: `backend/cache/<сеть>-photos.json` со списком
`[{"name": "...", "image": "https://..."}]`. Снимает его человек (или
встроенный браузер) со страницы меню, принимает
`backend/scripts/catch_snapshot.py`, а дальше снимки идут тем же путём,
что и у всех: сопоставление по имени, перекладывание в наш бакет, строка
прав рядом с файлом.

Сам файл в репозиторий не едет — как и гиды: его приносят руки, а не
скрипт, и весит он столько же.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
CACHE = BACKEND / "cache"


@dataclass(frozen=True)
class Shot:
    chain: str
    ext_key: str
    name: str
    image_url: str
    source_url: str


def path_for(slug: str) -> Path:
    return CACHE / f"{slug}-photos.json"


def available() -> list[str]:
    """Сети, для которых снимок уже снят."""
    return sorted(p.name.removesuffix("-photos.json")
                  for p in CACHE.glob("*-photos.json"))


def catalog(slug: str, chain: str, source_url: str) -> list[Shot]:
    """Снимки сети из снятого файла."""
    from ..slug import slugify

    path = path_for(slug)
    if not path.exists():
        raise SystemExit(
            f"снимка {path} нет — откройте меню сети в браузере, соберите "
            f"пары «имя → картинка» и примите их catch_snapshot.py")

    shots: list[Shot] = []
    seen: set[str] = set()
    for row in json.loads(path.read_text(encoding="utf-8")):
        name = " ".join(str(row.get("name") or "").split())
        image = str(row.get("image") or "")
        key = slugify(name)
        if not name or not image or key in seen:
            continue
        seen.add(key)
        shots.append(Shot(chain=chain, ext_key=key, name=name,
                          image_url=image, source_url=source_url))
    return shots
