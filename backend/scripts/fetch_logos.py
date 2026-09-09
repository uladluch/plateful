#!/usr/bin/env python3
"""Собирает логотипы сетей в каталог ассетов приложения.

    python3 backend/scripts/fetch_logos.py

Два источника, по порядку:
  1. Wikidata P154 → файл на Wikimedia Commons. Логотипы из простых букв и
     фигур там помечены PD-textlogo: авторским правом не защищены.
  2. Иконка с сайта самой сети (apple-touch-icon) — это тот же логотип,
     который сеть сама отдаёт браузерам.

Использование чужого знака, чтобы обозначить именно эту сеть, — номинативное
использование: так работают все агрегаторы. Знак не изменяем, аффилиацию не
подразумеваем, в описании приложения стоит прямой отказ от неё.

Источник и лицензия каждого файла пишутся в backend/data/logos.json.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.base import USER_AGENT, Fetcher
from plateful_data.slug import slugify

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "backend" / "data" / "catalog.json"
ASSETS = ROOT / "plateful" / "Assets.xcassets" / "Logos"
REPORT = ROOT / "backend" / "data" / "logos.json"

WIKIDATA = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
LOGO_WIDTH = 256

# Отсекаем однофамильцев: «Subway» это ещё и метро, «Sonic» — ёж.
RESTAURANT_HINTS = ("restaurant", "chain", "food", "coffee", "pizza", "burger",
                    "bakery", "cafe", "convenience", "store", "eatery", "grill")

_ICON_LINK = re.compile(
    r'<link[^>]+rel="[^"]*apple-touch-icon[^"]*"[^>]+href="([^"]+)"', re.I)
_ICON_LINK_REVERSED = re.compile(
    r'<link[^>]+href="([^"]+)"[^>]+rel="[^"]*apple-touch-icon[^"]*"', re.I)


def api(url: str, params: dict) -> dict:
    request = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def wikidata_entity(name: str) -> str | None:
    """Сущность сети, или ничего.

    Первое попавшееся брать нельзя: по запросу «Sonic» Wikidata первым отдаёт
    ежа, и мы бы поставили его логотип сети закусочных. Лучше остаться без
    логотипа, чем с чужим.
    """
    for query in (name, f"{name} restaurant"):
        results = api(WIKIDATA, {"action": "wbsearchentities", "format": "json",
                                 "language": "en", "type": "item", "limit": 5,
                                 "search": query}).get("search", [])
        for hit in results:
            description = (hit.get("description") or "").lower()
            if any(word in description for word in RESTAURANT_HINTS):
                return hit["id"]
    return None


def wikidata_claims(qid: str) -> tuple[str | None, str | None]:
    claims = api(WIKIDATA, {"action": "wbgetentities", "format": "json",
                            "ids": qid, "props": "claims"})["entities"][qid].get("claims", {})

    def first(prop: str):
        try:
            return claims[prop][0]["mainsnak"]["datavalue"]["value"]
        except (KeyError, IndexError):
            return None

    return first("P154"), first("P856")


def commons_logo(filename: str) -> tuple[str, str] | None:
    """Ссылка на PNG нужной ширины и лицензия."""
    pages = api(COMMONS, {"action": "query", "format": "json",
                          "titles": f"File:{filename}", "prop": "imageinfo",
                          "iiprop": "url|extmetadata",
                          "iiurlwidth": LOGO_WIDTH}).get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        licence = info.get("extmetadata", {}).get(
            "LicenseShortName", {}).get("value", "unknown")
        return url, re.sub(r"<[^>]+>", "", licence)
    return None


def site_icon(site: str, fetcher: Fetcher) -> str | None:
    page = fetcher.get(site)
    if page:
        for pattern in (_ICON_LINK, _ICON_LINK_REVERSED):
            match = pattern.search(page)
            if match:
                return urllib.parse.urljoin(site, match.group(1))
    return urllib.parse.urljoin(site, "/apple-touch-icon.png")


def download(url: str) -> bytes | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        return data if data[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1") \
            or data[:3] == b"\xff\xd8\xff" else None
    except Exception:
        return None


def write_imageset(slug: str, data: bytes) -> None:
    """Каталог ассетов, чтобы в коде работало Image(\"logo-<slug>\")."""
    folder = ASSETS / f"logo-{slug}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "logo.png").write_bytes(data)
    (folder / "Contents.json").write_text(json.dumps({
        "images": [{"filename": "logo.png", "idiom": "universal", "scale": "1x"},
                   {"idiom": "universal", "scale": "2x"},
                   {"idiom": "universal", "scale": "3x"}],
        "info": {"author": "xcode", "version": 1},
        "properties": {"preserves-vector-representation": True},
    }, indent=2) + "\n")


def main() -> int:
    chains = [c["name"] for c in json.loads(PACK.read_text(encoding="utf-8"))["chains"]]
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "Contents.json").write_text(
        json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n")

    fetcher = Fetcher(delay=2.0)
    report: dict[str, dict] = {}
    saved = 0

    for chain in chains:
        slug = slugify(chain)
        entry: dict[str, str] = {"chain": chain}
        try:
            qid = wikidata_entity(chain)
        except Exception as error:
            print(f"  ! {chain}: Wikidata {error}")
            qid = None

        logo_file = site = None
        if qid:
            entry["wikidata"] = qid
            try:
                logo_file, site = wikidata_claims(qid)
            except Exception as error:
                print(f"  ! {chain}: claims {error}")

        data = None
        if logo_file:
            found = commons_logo(logo_file)
            if found:
                url, licence = found
                data = download(url)
                if data:
                    entry |= {"source": "wikimedia", "file": logo_file, "license": licence}

        if data is None and site:
            url = site_icon(site, fetcher)
            data = download(url)
            if data:
                entry |= {"source": "chain-site", "url": url, "license": "trademark, nominative use"}

        if data:
            write_imageset(slug, data)
            saved += 1
            print(f"  ✓ {chain[:26]:<26} {entry.get('source'):<12} {entry.get('license', '')[:28]}")
        else:
            entry["source"] = "none"
            print(f"  — {chain[:26]:<26} логотип не найден")

        report[slug] = entry

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nсохранено {saved} из {len(chains)}")
    print(f"источники и лицензии: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
