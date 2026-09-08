#!/usr/bin/env python3
"""Один вход для агента: взять следующие сети из очереди и сделать по ним шаг.

    python3 backend/scripts/vacuum.py                 # показать очередь
    python3 backend/scripts/vacuum.py --probe 5       # разведать 5 сетей
    python3 backend/scripts/vacuum.py --crawl 2 --apply
    python3 backend/scripts/vacuum.py --probe 5 --crawl 2 --apply

Смысл в том, чтобы знание накапливалось. Разведка раньше печатала результат
в терминал и забывала его: для одного запуска руками это нормально, для
агента, который приходит время от времени, — нет. Он заново обходил бы те же
сайты, чтобы заново узнать, что Wendy's рисует меню скриптом.

Поэтому каждый шаг пишет вывод в `chains`: чем сеть отдаёт данные
(`source_kind`), когда смотрели (`probed_at`), что именно увидели
(`source_note`). Следующий запуск читает `crawl_queue` и берётся за то, до
чего руки ещё не дошли.

Что решает человек, а не скрипт: **адрес меню**. У 83 сетей из 96 его нет,
и найти его — единственная часть работы, где нужно понимать, национальный
это сайт США или страница франшизы. Скрипт такие сети просто показывает
в очереди со словами «найти адрес меню».
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import site
from plateful_data.adapters.base import Fetcher, curl_get

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Сколько страниц блюд смотреть при разведке. Двух хватает, чтобы отличить
# «сайт отдаёт этикетку» от «не отдаёт»; больше — уже кроул.
PROBE_DEPTH = 2

# Страница-заглушка от CDN выглядит для разбора так же, как меню,
# нарисованное скриптом: ни ссылок на блюда, ни цифр. Разница же
# принципиальная — первое значит «нас не пустили», второе «пустили, но
# смотреть нечем», и лечится это разными способами. Sonic отдал 403 и был
# записан как rendered, то есть в очереди оказался не в той корзине.
_WALL_MARKERS = (
    "attention required", "just a moment", "access denied",
    "please enable javascript and cookies", "cf-browser-verification",
    "/cdn-cgi/challenge-platform", "request unsuccessful", "incapsula",
    "akamai reference", "you have been blocked",
)


def looks_like_a_wall(html: str) -> bool:
    head = html[:4000].lower()
    return any(marker in head for marker in _WALL_MARKERS)


def query(sql: str) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        proc = subprocess.run(
            ["supabase", "db", "query", "--linked", "--agent=no", "-o", "json", "-f", path],
            capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"supabase db query упал:\n{exc.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)
    start = proc.stdout.find("[")
    return json.loads(proc.stdout[start:]) if start >= 0 else []


def execute(sql: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    try:
        subprocess.run(["supabase", "db", "query", "--linked", "--agent=no", "-f", path],
                       capture_output=True, text=True, check=True)
    finally:
        Path(path).unlink(missing_ok=True)


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def queue() -> list[dict]:
    return query("select slug, name, item_count, source_url, source_kind, status,"
                 " todo, source_note from crawl_queue order by todo, weight desc;")


def show(rows: list[dict]) -> None:
    buckets: dict[str, list[dict]] = {}
    for row in rows:
        buckets.setdefault(row["todo"], []).append(row)

    print("\n── Очередь ──")
    for todo in ("кроулить", "разведать", "найти адрес меню",
                 "нужен другой способ", "свежее", "на паузе"):
        chains = buckets.get(todo, [])
        if not chains:
            continue
        names = ", ".join(c["slug"] for c in chains[:6])
        more = f" … ещё {len(chains) - 6}" if len(chains) > 6 else ""
        print(f"  {todo:22} {len(chains):3}  {names}{more}")


def probe(chain: dict) -> tuple[str | None, str]:
    """Смотрит, чем сеть отдаёт данные. Возвращает (source_kind, заметка).

    `None` вместо вида значит «ничего не узнали»: приговор не выносим и
    `probed_at` не ставим, чтобы следующий заход попробовал снова. Записать
    «blocked» из-за таймаута — вычеркнуть сеть навсегда по случайности.

    Разведка идёт по двум страницам блюд, и этого достаточно: вопрос не
    «сколько позиций у сети», а «есть ли этикетка в HTML вообще».
    """
    fetcher = Fetcher()
    menu_url = chain["source_url"]

    index = fetcher.get(menu_url) or curl_get(menu_url, BROWSER_HEADERS,
                                              robots=fetcher.robots)
    if not index:
        if fetcher.forbidden:
            # Отличаем «сайт запретил» от «файл не прочитался»: первое
            # окончательно, второе — наша неудача, а не его отказ.
            if getattr(fetcher.robots, "_unreachable", set()):
                return None, "robots.txt не отдался — попробуем в другой раз"
            return "blocked", "robots.txt запрещает страницу меню"
        return "blocked", "страница меню не отдалась: 403, обрыв TLS или таймаут"

    if looks_like_a_wall(index):
        return "blocked", "вместо меню страница бот-защиты — нас не пустили"

    links = site.item_links(index, menu_url)
    facts = site.read_page(index)
    if facts.has_nutrition:
        return "json_in_html", f"этикетка прямо на странице меню ({', '.join(facts.shapes)})"

    if not links:
        return "rendered", "в HTML меню нет ссылок на блюда — рисуется скриптом"

    for link in links[:PROBE_DEPTH]:
        page = fetcher.get(link) or curl_get(link, BROWSER_HEADERS, robots=fetcher.robots)
        if not page:
            continue
        item = site.read_page(page)
        if item.has_nutrition:
            shapes = ", ".join(item.shapes)
            extra = []
            if item.photo:
                extra.append("снимок")
            if item.allergens:
                extra.append("аллергены")
            note = f"этикетка со страницы блюда ({shapes})"
            if extra:
                note += ", есть " + " и ".join(extra)
            return "json_in_html", note

    return "rendered", f"ссылок в меню {len(links)}, но этикетки в HTML нет"


def record(slug: str, kind: str, note: str) -> None:
    execute(f"update chains set source_kind = {sql_text(kind)},"
            f" source_note = {sql_text(note)}, probed_at = now()"
            f" where slug = {sql_text(slug)};")


def run_probes(rows: list[dict], limit: int) -> None:
    todo = [r for r in rows if r["todo"] == "разведать"][:limit]
    if not todo:
        print("\nРазведывать нечего.")
        return

    print(f"\n── Разведка: {len(todo)} сетей ──")
    for chain in todo:
        kind, note = probe(chain)
        if kind is None:
            print(f"  ? {chain['slug']:20} {'—':14} {note}")
            continue
        record(chain["slug"], kind, note)
        mark = "✓" if kind not in ("rendered", "blocked") else "×"
        print(f"  {mark} {chain['slug']:20} {kind:14} {note}")


def run_crawls(rows: list[dict], limit: int, apply: bool) -> None:
    todo = [r for r in rows if r["todo"] == "кроулить"][:limit]
    if not todo:
        print("\nКроулить нечего.")
        return

    print(f"\n── Кроул: {len(todo)} сетей ──")
    for chain in todo:
        command = [sys.executable, str(SCRIPTS / "crawl_chain.py"), chain["slug"]]
        if apply:
            command.append("--apply")
        result = subprocess.run(command, cwd=ROOT)
        # Кроул возвращает 1 при held — это его работа, а не поломка.
        print(f"  {chain['slug']}: код {result.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", type=int, default=0, metavar="N",
                        help="разведать N сетей, до которых ещё не доходили")
    parser.add_argument("--crawl", type=int, default=0, metavar="N",
                        help="обойти N сетей, у которых подошёл срок")
    parser.add_argument("--apply", action="store_true",
                        help="кроулу разрешено писать в базу")
    args = parser.parse_args()

    rows = queue()
    show(rows)

    if args.probe:
        run_probes(rows, args.probe)
    if args.crawl:
        run_crawls(rows, args.crawl, args.apply)
    if args.probe or args.crawl:
        show(queue())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
