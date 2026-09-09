#!/usr/bin/env python3
"""Ищет у сети официальный гид по питанию — PDF на её собственном домене.

    python3 backend/scripts/find_guide.py --limit 30
    python3 backend/scripts/find_guide.py --limit 30 --apply

Гид — самый дешёвый источник этикетки: один файл даёт всю сеть разом, и
для сетей, чьё меню рисуется скриптом, это часто единственный путь. Но
`find_route.py` ищет ссылку на него только на странице меню, а лежит он
обычно глубже: на странице «Nutrition», в подвале или вовсе только в
карте сайта.

**Только домен сети.** Поиск в интернете первым делом выносит агрегаторы
и Scribd — оттуда брать нельзя: рушится обещание «показываем, откуда
цифра», да и файл там бывает чужой и старый.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.base import BROWSER_HEADERS, curl_get

#: Страницы, где сеть держит гид. Порядок — по частоте.
PAGES = ("/nutrition", "/nutrition-information", "/menu/nutrition",
         "/nutritional-information", "/food/nutrition", "/our-food/nutrition",
         "/menu/nutrition-information", "/allergens", "/nutrition-allergens",
         "/", "/menu")

#: Ссылка на файл, который похож на гид, а не на меню-листовку.
_PDF = re.compile(r'href="([^"]+\.pdf[^"]*)"', re.I)
_LOOKS_LIKE_GUIDE = re.compile(r"nutrition|nutritional|allerg", re.I)

#: В карте сайта PDF попадаются реже, зато там он один на всю сеть.
_LOC = re.compile(r"<loc>([^<]+)</loc>")


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    finally:
        Path(path).unlink(missing_ok=True)
    start = proc.stdout.find("[")
    return json.loads(proc.stdout[start:]) if start >= 0 else []


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def guides_on(domain: str) -> list[str]:
    """Адреса гидов, найденные на домене сети."""
    found: list[str] = []
    for path in PAGES:
        page = curl_get(f"https://www.{domain}{path}", BROWSER_HEADERS, timeout=30)
        if not page:
            continue
        for href in _PDF.findall(page):
            if not _LOOKS_LIKE_GUIDE.search(href):
                continue
            url = urljoin(f"https://www.{domain}{path}", href)
            if url not in found:
                found.append(url)
        if found:
            break

    if not found:
        sitemap = curl_get(f"https://www.{domain}/sitemap.xml", BROWSER_HEADERS, timeout=40)
        for url in _LOC.findall(sitemap or ""):
            if url.lower().endswith(".pdf") and _LOOKS_LIKE_GUIDE.search(url):
                found.append(url)
    return found


def looks_readable(url: str) -> tuple[bool, str]:
    """Открывается ли файл и правда ли это PDF.

    Ссылка на гид бывает битой годами: у TGI Fridays она ведёт в пустоту,
    и без проверки такой адрес осел бы в базе как рабочий источник.
    """
    body = curl_get(url, BROWSER_HEADERS, timeout=60, binary=True)
    if not body:
        return False, "не открылся"
    if not body[:5].startswith(b"%PDF"):
        return False, f"не PDF ({len(body)} байт)"
    return True, f"{len(body) // 1024} КБ"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    where = ("where c.source_kind is distinct from 'pdf' and c.source_url is not null"
             if not args.only else
             f"where c.slug in ({', '.join(sql_text(s) for s in args.only)})")
    rows = query(
        "select c.slug, c.name, c.source_url,"
        " (select count(*) from items i where i.chain_id = c.id and i.valid_to is null) as items"
        f" from chains c {where} order by items desc limit {args.limit};")

    print(f"── Поиск гидов: {len(rows)} сетей ──")
    found: list[tuple[str, str]] = []
    for row in rows:
        source = row.get("source_url") or ""
        domain = source.split("/")[2].removeprefix("www.") if "//" in source else None
        if not domain:
            print(f"  × {row['slug']:24} домен неизвестен")
            continue
        guide = None
        for candidate in guides_on(domain):
            ok, why = looks_readable(candidate)
            if ok:
                guide, note = candidate, why
                break
        if guide:
            found.append((row["slug"], guide))
            print(f"  ✓ {row['slug']:24} {note:>8}  {guide[:70]}")
        else:
            print(f"  · {row['slug']:24} гида нет")

    if not args.apply:
        print(f"\nНайдено гидов: {len(found)}. Ничего не записано, повторите с --apply.")
        return 0

    statements = [
        f"update chains set source_kind = 'pdf', source_url = {sql_text(url)},"
        f" source_note = 'гид найден на домене сети', probed_at = now()"
        f" where slug = {sql_text(slug)};" for slug, url in found]
    if statements:
        path = Path(tempfile.mkdtemp()) / "guides.sql"
        path.write_text("\n".join(statements), encoding="utf-8")
        subprocess.run(["supabase", "db", "query", "--linked", "--agent=no", "-f", str(path)],
                       capture_output=True, text=True)
    print(f"\nЗаписано гидов: {len(statements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
