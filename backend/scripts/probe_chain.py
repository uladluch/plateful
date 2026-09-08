#!/usr/bin/env python3
"""Разведка сайта сети: чем он отдаёт данные и что с него читается.

    python3 backend/scripts/probe_chain.py https://www.chick-fil-a.com/menu/entrees/...
    python3 backend/scripts/probe_chain.py --menu https://www.wendys.com/menu
    python3 backend/scripts/probe_chain.py --survey

Подключение новой сети начинается отсюда. Скрипт берёт одну страницу
(или страницу меню и первые несколько блюд с неё), прогоняет общий
извлекатель `adapters/site.py` и печатает, что нашлось: имя, снимок,
этикетка, аллергены, состав — и каким видом разметки они отданы.

Если сработал любой из трёх видов, сеть подключается без своего кода.
Если не сработал ни один — сайт рисует всё скриптом, и это отдельный
разговор, а не «дописать регулярку».

Вежливость обычная: пауза между запросами, честный User-Agent, только
домен самой сети.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.base import Fetcher, curl_get
from plateful_data.adapters.mcdonalds import BROWSER_HEADERS
from plateful_data.adapters.site import NUTRIENTS, item_links, read_page

# Сети, до которых руки ещё не дошли. Адрес раздела меню — всё, что нужно
# для разведки; сюда же дописывать новые.
KNOWN_MENUS = {
    "wendys": "https://www.wendys.com/menu",
    "burger-king": "https://www.bk.com/menu",
    "taco-bell": "https://www.tacobell.com/food",
    "subway": "https://www.subway.com/en-US/MenuNutrition/Menu",
    "popeyes": "https://www.popeyes.com/menu",
    "kfc": "https://www.kfc.com/menu",
    "dunkin": "https://www.dunkindonuts.com/en/menu",
    "starbucks": "https://www.starbucks.com/menu",
    "panera": "https://www.panerabread.com/en-us/menu.html",
    "arbys": "https://arbys.com/menu",
    "sonic": "https://www.sonicdrivein.com/menu",
    "jack-in-the-box": "https://www.jackinthebox.com/menu",
}


def fetch(url: str, fetcher: Fetcher) -> str | None:
    """Обычным запросом, а при отказе — через curl.

    Часть сетей за Akamai не отвечает Python-у вовсе: там смотрят на
    отпечаток TLS-рукопожатия. Тот же адрес curl отдаёт нормально.
    """
    return fetcher.get(url) or curl_get(url, BROWSER_HEADERS, robots=fetcher.robots)


def describe(url: str, html: str) -> str:
    facts = read_page(html)
    label = [f"{f}={getattr(facts, f):g}" for f in NUTRIENTS
             if getattr(facts, f) is not None]

    lines = [f"  {url}"]
    lines.append(f"    разметка:  {', '.join(facts.shapes) or 'ничего не сработало'}")
    lines.append(f"    название:  {facts.name or '—'}")
    lines.append(f"    снимок:    {(facts.photo or '—')[:88]}")
    lines.append(f"    этикетка:  {', '.join(label) if label else '—'}")
    if facts.allergens:
        lines.append(f"    аллергены: {facts.allergens[:70]}")
    if facts.ingredients:
        lines.append(f"    состав:    {facts.ingredients[:70]}…")
    return "\n".join(lines)


def probe_menu(url: str, fetcher: Fetcher, depth: int) -> None:
    index = fetch(url, fetcher)
    if not index:
        print(f"  меню не отдалось: {url}")
        return

    links = item_links(index, url)
    print(f"  ссылок в меню: {len(links)}")
    print(describe(url, index))
    for link in links[:depth]:
        page = fetch(link, fetcher)
        if page:
            print(describe(link, page))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?", help="страница блюда")
    parser.add_argument("--menu", help="страница меню: пройти по первым блюдам")
    parser.add_argument("--survey", action="store_true",
                        help="пройтись по всем известным сетям")
    parser.add_argument("--depth", type=int, default=2,
                        help="сколько блюд смотреть с меню")
    args = parser.parse_args()

    fetcher = Fetcher()
    if args.survey:
        for chain, menu in KNOWN_MENUS.items():
            print(f"\n=== {chain} ===")
            probe_menu(menu, fetcher, args.depth)
        return 0
    if args.menu:
        probe_menu(args.menu, fetcher, args.depth)
        return 0
    if not args.url:
        parser.error("нужен адрес: url, --menu или --survey")

    page = fetch(args.url, fetcher)
    if not page:
        print("страница не отдалась")
        return 1
    print(describe(args.url, page))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
