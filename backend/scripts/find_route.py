#!/usr/bin/env python3
"""Каким способом брать данные у сети — определяется само, а не руками.

    python3 backend/scripts/find_route.py --limit 20        # показать
    python3 backend/scripts/find_route.py --limit 20 --apply # записать в chains

Разбор каждой сети по отдельности не масштабируется: Panera потребовала
девяти заходов, и это при готовом гиде. А сетей девяносто. Здесь дешёвая
часть работы делается один раз для всех: найти сайт и понять, **чем** он
отдаёт меню. Дорогая — вписать раскладку колонок гида, проверить план
кроула — остаётся человеку, но уже зная, куда идти.

Маршруты, по убыванию отдачи:

* `sanity`   — контент-база с картинками и этикеткой, публичный GROQ.
               Так устроены все бренды RBI; один запрос отдаёт всё меню.
* `pdf`      — официальный гид по питанию, один файл на сеть.
* `html`     — этикетка прямо в разметке, берётся общим извлекателем.
* `graphql`  — свой API; нужен разбор запросов, но данные там есть.
* `rendered` — меню рисуется скриптом, зацепиться не за что.
* `blocked`  — сайт не пускает.

Домен угадывается из названия и **проверяется**: мало открыть страницу,
надо убедиться, что это сайт той самой сети, а не однофамильца. «Wawa»
и «Sonic» — слова из словаря, и по ним легко приехать не туда.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import site
from plateful_data.adapters.base import USER_AGENT, curl_get

BROWSER = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

#: Слова, которые сеть обычно не включает в домен: «Jersey Mike's Subs» →
#: jerseymikes.com, «BJ's Restaurant & Brewhouse» → bjsrestaurants.com.
_GENERIC = ("subs", "restaurant", "restaurants", "brewhouse", "grill", "grille",
            "pizza", "cafe", "coffee", "kitchen", "donuts", "bakery", "bar",
            "house", "shack", "express", "company", "co")

#: Меньше этого страница не бывает: отказ бот-защиты весит десятки байт,
#: настоящая страница — десятки килобайт.
MIN_PAGE = 1024

#: Страницы, где сеть держит питание. Порядок — по частоте.
_MENU_PATHS = ("/menu", "/menu/", "/nutrition", "/our-menu", "/food",
               "/menu-nutrition", "/nutrition-information")


@dataclass
class Route:
    slug: str
    name: str
    domain: str | None = None
    kind: str = "unknown"
    note: str = ""
    detail: dict = field(default_factory=dict)


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


def fetch(url: str, timeout: int = 25) -> tuple[int, str]:
    """Страница как есть. Код 0 — не ответил вовсе."""
    request = urllib.request.Request(url, headers=BROWSER)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            if body:
                return response.status, body
            # Пустое тело с кодом 200 — бот-защита, только вежливая.
            # Спрашиваем curl-ом, у которого другой отпечаток TLS.
            fallback = curl_get(url, BROWSER, timeout=timeout) or ""
            # «Not found» в десять байт — тоже отказ, просто не кодом.
            # Без этой проверки olivegarden.com засчитывался как открытый
            # 200, и сеть числилась «домен не найден по названию».
            if len(fallback) >= MIN_PAGE:
                return 200, fallback
            return 403, ""
    except urllib.error.HTTPError as error:
        # 403 у Python и 200 у curl — обычное дело: сайт смотрит на
        # отпечаток TLS-рукопожатия, а не на заголовки. Половина сетей
        # объявлялась «закрытой», хотя curl их открывает.
        if error.code in (403, 429):
            body = curl_get(url, BROWSER, timeout=timeout) or ""
            if len(body) >= MIN_PAGE:
                return 200, body
        return error.code, ""
    except Exception:
        body = curl_get(url, BROWSER, timeout=timeout) or ""
        # Короткий ответ — не страница, а отказ: «Not found» весит десять
        # байт и приходит с кодом 403, который curl в теле не показывает.
        return (200, body) if len(body) >= MIN_PAGE else (403 if body else 0, "")


def domain_candidates(name: str) -> list[str]:
    """Домены-кандидаты из названия сети, от точного к урезанному."""
    words = re.sub(r"[^a-z0-9 ]+", " ", name.lower()).split()
    # Полное имя — первым кандидатом: «Round Table Pizza» это
    # roundtablepizza.com, а не roundtable.com, и «BJ's Restaurant &
    # Brewhouse» — bjsrestaurants.com, тогда как bjs.com оптовый клуб.
    # Дефис в названии сеть чаще всего сохраняет: «In-N-Out Burger» это
    # in-n-out.com, «7-Eleven» — 7-eleven.com. Слитная форма для них не
    # существует, и без дефисного кандидата домен не найти вовсе.
    seen: list[str] = ["".join(words) + ".com", "-".join(words) + ".com",
                       "".join(words) + "s.com"]
    for trim in (0, 1, 2):
        core = words[:len(words) - trim] if trim else words
        if not core:
            continue
        # Хвостовые общие слова сеть в домен обычно не берёт.
        while len(core) > 1 and core[-1] in _GENERIC:
            core = core[:-1]
        for suffix in ("", "s"):
            host = "".join(core) + suffix + ".com"
            if host not in seen:
                seen.append(host)
    return seen[:6]


def confirms(html: str, name: str) -> bool:
    """Это правда сайт этой сети, а не однофамильца.

    «Wawa» и «Sonic» — слова из словаря; открывшаяся страница ещё ничего
    не значит. Просим совпадение имени и признак того, что там кормят.
    """
    text = html[:200_000].lower()
    flat = re.sub(r"[^a-z0-9]+", "", text)
    # Просим **все** значимые слова названия, а не самое длинное: по одному
    # слову «Dairy Queen» подтверждалась на dairy.com, «Yard House» — на
    # yard.com. Общие слова из требования исключены, но если после этого
    # не осталось ничего (у «BJ's Restaurant & Brewhouse» общее всё),
    # берём имя целиком — иначе сеть не подтвердится никогда.
    words = [w for w in re.sub(r"[^a-z0-9 ]+", " ", name.lower()).split() if len(w) >= 3]
    significant = [w for w in words if w not in _GENERIC] or words
    if any(w not in flat for w in significant):
        return False
    return any(word in text for word in
               ("menu", "nutrition", "order", "restaurant", "food", "calories"))


def find_domain(name: str) -> tuple[str | None, str]:
    """Домен сети. Второй результат — почему он такой.

    Отказ 403 на первом же кандидате значит «сайт есть, но нас не пускает»,
    а не «домен не тот»: goldencorral.com закрыт бот-защитой, и перебор
    дальше приводил к goldencorrals.com — сквоттеру, который открылся и
    прошёл проверку по имени. Заблокированный настоящий домен лучше
    открытого чужого.
    """
    blocked: str | None = None
    for host in domain_candidates(name):
        for prefix in ("https://www.", "https://"):
            status, html = fetch(prefix + host, timeout=20)
            if status == 200 and confirms(html, name):
                return host, "ok"
            # 451 — сеть закрылась от нашего региона целиком: домен верный,
            # но смотреть нам не дадут. Это не «не нашли», а «не пускают».
            if status in (403, 429, 451) and blocked is None:
                blocked = host
    return (blocked, "blocked") if blocked else (None, "")


def sanity_project(html: str, domain: str) -> str | None:
    """Идентификатор проекта Sanity из бандла приложения сети."""
    bundles = re.findall(r'src="(/_expo/static/js/web/[^"]+\.js|/_next/static/[^"]+\.js)"', html)
    for path in bundles[:3]:
        body = curl_get(f"https://www.{domain}{path}", BROWSER, timeout=90)
        if not body:
            continue
        if match := re.search(r'sanityProjectId\\?"?\s*[:=]\s*\\?"([a-z0-9]{6,12})', body):
            return match.group(1)
    return None


def nutrition_pdf(domain: str, html: str) -> str | None:
    """Ссылка на гид по питанию, если она есть прямо на странице."""
    for href in re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I):
        if re.search(r"nutrition|nutritional|allerg", href, re.I):
            return href if href.startswith("http") else f"https://www.{domain}{href}"
    return None


def probe(route: Route) -> Route:
    if not route.domain:
        route.domain, why = find_domain(route.name)
        if why == "blocked":
            route.kind = "blocked"
            route.note = f"{route.domain} закрыт бот-защитой"
            return route
    if not route.domain:
        route.kind, route.note = "unknown", "домен не найден по названию"
        return route

    for path in _MENU_PATHS:
        url = f"https://www.{route.domain}{path}"
        status, html = fetch(url)
        if status != 200 or not html:
            continue
        route.detail["menu_url"] = url

        if pdf := nutrition_pdf(route.domain, html):
            route.kind, route.note = "pdf", f"гид: {pdf}"
            route.detail["pdf"] = pdf
            return route

        facts = site.read_page(html)
        if facts.has_nutrition:
            route.kind, route.note = "html", f"этикетка в разметке ({', '.join(facts.shapes)})"
            return route

        if project := sanity_project(html, route.domain):
            route.kind, route.note = "sanity", f"Sanity project {project}"
            route.detail["sanity"] = project
            return route

        if re.search(r"graphql|/api/(menu|products|nutrition)", html, re.I):
            route.kind, route.note = "graphql", "свой API в разметке"
            return route

        if site.item_links(html, url):
            route.kind, route.note = "rendered", "ссылки на блюда есть, этикетки нет"
        else:
            route.kind, route.note = "rendered", "меню рисуется скриптом"
        return route

    route.kind, route.note = "blocked", "ни одна страница меню не открылась"
    return route


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--only", nargs="*", help="разведать именно эти сети")
    args = parser.parse_args()

    where = ("where c.source_url is null and c.probed_at is null"
             if not args.only else
             f"where c.slug in ({', '.join(sql_text(s) for s in args.only)})")
    rows = query(
        "select c.slug, c.name, c.item_count, c.source_url from chains c "
        f"{where} order by c.item_count desc limit {args.limit};")

    print(f"── Разведка маршрутов: {len(rows)} сетей ──")
    found: list[Route] = []
    for row in rows:
        route = probe(Route(slug=row["slug"], name=row["name"],
                            domain=(row.get("source_url") or "").split("/")[2].removeprefix("www.")
                            if row.get("source_url") else None))
        found.append(route)
        mark = {"sanity": "★", "pdf": "✓", "html": "✓"}.get(route.kind, "×")
        print(f"  {mark} {route.slug:24} {route.kind:9} {route.domain or '—':26} {route.note[:60]}")

    if not args.apply:
        print("\nНичего не записано. Повторите с --apply.")
        return 0

    statements = []
    for route in found:
        url = route.detail.get("pdf") or route.detail.get("menu_url")
        kind = {"sanity": "json_api", "pdf": "pdf", "html": "json_in_html",
                "graphql": "json_api", "rendered": "rendered",
                "blocked": "blocked"}.get(route.kind)
        if kind is None:
            continue
        statements.append(
            f"update chains set source_kind = {sql_text(kind)},"
            f" source_url = coalesce(source_url, {sql_text(url)}),"
            f" source_note = {sql_text(route.note)}, probed_at = now()"
            f" where slug = {sql_text(route.slug)};")
    if statements:
        path = Path(tempfile.mkdtemp()) / "routes.sql"
        path.write_text("\n".join(statements), encoding="utf-8")
        subprocess.run(["supabase", "db", "query", "--linked", "--agent=no", "-f", str(path)],
                       capture_output=True, text=True)
    print(f"\nЗаписано маршрутов: {len(statements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
