#!/usr/bin/env python3
"""Кроул одной сети: обойти меню, сверить с каталогом, записать новую версию.

    python3 backend/scripts/crawl_chain.py chick-fil-a --menu https://www.chick-fil-a.com/menu
    python3 backend/scripts/crawl_chain.py chick-fil-a           # адрес уже в chains
    python3 backend/scripts/crawl_chain.py chick-fil-a --apply   # записать в базу
    python3 backend/scripts/crawl_chain.py subway --guide URL    # гид в PDF вместо обхода
    python3 backend/scripts/crawl_chain.py burger-king --sanity  # контент-база сети (RBI)
    python3 backend/scripts/crawl_chain.py mcdonald-s --snapshot # снимок, снятый браузером

Без `--apply` не пишется ничего — ни в базу, ни на диск, кроме отчёта.
Так и задумано: человек сначала смотрит, что кроул собрался сделать.

Отличие от `audit_chain.py`: тот пишет ручные правки в `overrides`, точечно
и навсегда. Этот заводит новую версию позиции в `items` — закрывает старую
`valid_to` и вставляет свежую со своим источником и датой. Правки из
`overrides` при этом остаются сверху: они на то и отдельная таблица.

Источник может быть двух видов, а всё, что после него, — одно и то же.
Обход сайта и гид в PDF отличаются только тем, откуда взялись позиции;
дальше их одинаково сопоставляют с каталогом, проверяют и версионируют.
Для сетей, чей сайт рисует меню скриптом, гид — единственный путь, и один
файл даёт всю сеть разом.

Ходим по правилам `adapters/base.py`: пауза между запросами, честный
User-Agent с адресом проекта, только домен сети, никаких обходов защиты.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import crawl, pdf_guide, validate
from plateful_data.adapters import mcdonalds, sanity_rbi, site
from plateful_data.adapters.base import Fetcher, curl_get
from plateful_data.slug import slugify

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"

# Часть сетей за Akamai не отвечает Python-у: там смотрят на отпечаток TLS.
GUIDE_AGENT = "plateful-data/1.0 (+https://github.com/uladluch/plateful)"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class Crawled:
    """Позиция, снятая со страницы. Утиный двойник menustat.Item."""
    chain: str
    ext_key: str
    name: str
    source: str
    source_url: str
    #: Заголовок раздела из гида и порция. Нужны только заведению новой
    #: позиции: у обновления и то и другое уже есть в каталоге.
    category: str | None = None
    serving: str | None = None
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    sugar: float | None = None
    sat_fat: float | None = None
    trans_fat: float | None = None
    cholesterol: float | None = None
    sodium: float | None = None
    fiber: float | None = None


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


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def sql_number(value) -> str:
    return "null" if value is None else repr(float(value))


def chain_row(slug: str) -> dict:
    rows = query("select id, name, slug, source_url from chains "
                 f"where slug = {sql_text(slug)};")
    if not rows:
        raise SystemExit(f"сети {slug} нет в chains")
    return rows[0]


def previous_crawl(chain_id: int, source: str) -> dict[str, dict]:
    """Что видел прошлый кроул этой сети: строки, которые он же и записал.

    Пусто на первом кроуле — тогда дифф-проверке не с чем сравнивать, и
    она честно пропускает. Защита в этот момент держится на остальном:
    в базу едут только сопоставленные позиции с полной этикеткой, прошедшие
    Атуотера и не отличающиеся от каталога слишком сильно.
    """
    rows = query(
        "select ext_key, kcal, protein, carbs, fat from items"
        f" where chain_id = {chain_id} and valid_to is null"
        f" and source = {sql_text(source)};")
    return {r["ext_key"]: {k: float(v) for k, v in r.items()
                           if k != "ext_key" and v is not None}
            for r in rows}


def catalog(chain_id: int) -> dict[str, dict]:
    """Текущие позиции сети из базы, а не из пака.

    Пак — снимок; писать мы будем в базу, и сравнивать надо с ней же,
    иначе кроул увидит расхождение там, где его уже поправили.
    """
    rows = query(
        "select ext_key, name, kcal, protein, carbs, fat, sugar, sat_fat,"
        " trans_fat, cholesterol, sodium, fiber"
        f" from items where chain_id = {chain_id} and valid_to is null;")
    out = {}
    for row in rows:
        record = {"ext_key": row["ext_key"], "name": row["name"]}
        for key, value in row.items():
            if key not in ("ext_key", "name") and value is not None:
                record[key] = float(value)
        out[row["ext_key"]] = record
    return out


# Меню сети — обычно два уровня: страница меню ведёт на разделы, а разделы
# на блюда. Глубже не ходим: третий уровень у сетей — это уже аллергены,
# кастомизация и карточки заведений, то есть чужие страницы.
MAX_DEPTH = 2


def walk(menu_url: str, *, limit: int | None, browser: bool) -> list[Crawled]:
    """Обходит меню вширь и читает каждую страницу общим извлекателем.

    Страница, на которой нашлась этикетка, — блюдо. Страница без этикетки,
    но со ссылками внутрь меню, — раздел, и мы спускаемся в него. Так одна
    и та же функция работает и там, где блюда лежат прямо в меню, и там,
    где меню разбито по разделам.
    """
    fetcher = Fetcher()
    # И через curl спрашиваем robots.txt: браузерные заголовки нужны, чтобы
    # сайт нам ответил, а не чтобы обойти то, что он попросил не трогать.
    get = ((lambda url: curl_get(url, BROWSER_HEADERS, robots=fetcher.robots))
           if browser else fetcher.get)
    host = urlparse(menu_url).netloc.removeprefix("www.")

    index = get(menu_url)
    if not index:
        raise SystemExit(f"меню не открылось: {menu_url}")

    seen: set[str] = {menu_url.rstrip("/")}
    frontier = [(url, 1) for url in site.item_links(index, menu_url)]
    items: list[Crawled] = []
    visited = 0

    while frontier:
        if limit and len(items) >= limit:
            break
        url, depth = frontier.pop(0)
        if url in seen:
            continue
        seen.add(url)

        page = get(url)
        visited += 1
        if not page:
            continue

        facts = site.read_page(page)
        if facts.name and facts.has_nutrition:
            items.append(Crawled(
                chain="", ext_key=slugify(facts.name), name=facts.name,
                source=host, source_url=url,
                **{name: getattr(facts, name) for name in site.NUTRIENTS}))
        elif depth < MAX_DEPTH:
            # Не блюдо, а раздел: забираем его ссылки и идём дальше.
            frontier += [(link, depth + 1) for link in site.item_links(page, menu_url)
                         if link not in seen]

        if visited % 20 == 0:
            print(f"  просмотрено {visited}, снято {len(items)},"
                  f" в очереди {len(frontier)}")
    print(f"  просмотрено {visited} страниц, снято {len(items)}")
    if fetcher.forbidden:
        print(f"  robots.txt закрыл {len(fetcher.forbidden)} адресов")
    return items


def from_sanity(slug: str) -> list[Crawled]:
    """Позиции из Sanity CMS сети — для брендов RBI.

    Это не обход и не гид, а прямое чтение той базы, откуда сайт берёт
    меню. Один запрос — всё живое меню с этикеткой и картинками; тесты и
    заглушки отсеивает адаптер, обходом живого меню.
    """
    brand = sanity_rbi.BRANDS.get(slug)
    if brand is None:
        raise SystemExit(f"{slug} не описан в sanity_rbi.BRANDS — это бренд RBI?")
    print(f"  sanity: {brand.project}/{brand.dataset}, меню {brand.menu_id}")
    items = sanity_rbi.fetch(brand)
    print(f"  живое меню: {len(items)} позиций,"
          f" с картинкой {sum(1 for i in items if i.image_url)}")
    return [Crawled(chain=item.chain, ext_key=item.ext_key, name=item.name,
                    source=item.source, source_url=item.source_url,
                    category=item.category,
                    **{f: getattr(item, f) for f in
                       ("kcal", "protein", "carbs", "fat", "sugar", "sat_fat",
                        "trans_fat", "cholesterol", "sodium", "fiber")})
            for item in items]


def from_snapshot(slug: str) -> list[Crawled]:
    """Позиции из снимка, снятого браузером.

    Сеть, которая не отвечает ни curl, ни Python, всё равно отвечает
    настоящей странице — снимок снимают там (`backend/data/collect/`) и
    кладут в `backend/cache/`. Для кроула это такой же полный источник,
    как гид: сеть перечислила своё меню целиком, значит `--replace`
    законен.
    """
    if slug != mcdonalds.SLUG:
        raise SystemExit(f"снимок описан только для {mcdonalds.SLUG}")
    items = mcdonalds.load()
    print(f"  снимок: {len(items)} позиций,"
          f" с картинкой {sum(1 for i in items if i.image_url)},"
          f" с порцией {sum(1 for i in items if i.serving)}")
    return [Crawled(chain=item.chain, ext_key=item.ext_key, name=item.name,
                    source=item.source, source_url=item.source_url,
                    category=item.category, serving=item.serving,
                    **{f: getattr(item, f) for f in
                       ("kcal", "protein", "carbs", "fat", "sugar", "sat_fat",
                        "trans_fat", "cholesterol", "sodium", "fiber")})
            for item in items]


def from_guide(url: str, chain: str, slug: str) -> list[Crawled]:
    """Позиции из PDF-гида сети.

    Раскладка колонок своя у каждой сети и лежит в `pdf_guide.LAYOUTS`:
    прочитать её из шапки нельзя, там текст повёрнут на 90°. Зато
    `pdf_guide.read` проверяет и страну, и раскладку, и отказывается, если
    гид не тот, — молча испорченный каталог хуже, чем несобранный.
    """
    layout = pdf_guide.LAYOUTS.get(slug)
    if layout is None:
        raise SystemExit(
            f"раскладка колонок для {slug} не описана — добавьте её в "
            f"pdf_guide.LAYOUTS, посмотрев файл глазами")

    try:
        import pdfplumber
    except ImportError:
        raise SystemExit("pdfplumber не установлен: pip install -r backend/requirements.txt")

    print(f"  гид: {url}")
    path = DATA / "guides" / f"{slug}.pdf"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(
            ["curl", "-sL", "-m", "120", "-A", GUIDE_AGENT, "-o", str(path), url],
            capture_output=True)
        if blob.returncode != 0 or not path.exists():
            raise SystemExit(f"гид не скачался: {url}")
    print(f"  {path.stat().st_size / 1024:.0f} КБ")

    try:
        with pdfplumber.open(path) as pdf:
            if layout.positioned:
                # Вёрстка рвёт строку блюда — читаем по координатам.
                pages = [[pdf_guide.Line(line["top"], line["x0"], line["text"])
                          for line in page.extract_text_lines()]
                         for page in pdf.pages]
                items = pdf_guide.read_pages(pages, layout=layout)
            else:
                # Колонтитулы снимаем до разбора: они неотличимы от
                # заголовка раздела по виду и становились то категорией,
                # то именем блюда.
                text = pdf_guide.without_furniture(
                    [(page.extract_text() or "") for page in pdf.pages])
                items = pdf_guide.read(text, layout=layout)
    except pdf_guide.WrongGuide as wrong:
        raise SystemExit(f"гид не подходит: {wrong}")

    host = urlparse(url).netloc.removeprefix("www.").removeprefix("media.")
    return [Crawled(chain=chain, ext_key=slugify(item.name), name=item.name,
                    source=host, source_url=url,
                    # Категорией берём внешний раздел гида: он и есть
                    # раздел меню («DRINKS», «SANDWICHES»), а внутренний
                    # заголовок — это подгруппа вроде «Flavored Iced Green
                    # Tea», для меню слишком мелкая.
                    category=(item.section or item.category or "").title() or None,
                    serving=(f"{item.values['serving']:g} g"
                             if item.values.get("serving") else None),
                    **{field: item.values.get(field) for field in
                       ("kcal", "protein", "carbs", "fat", "sugar", "sat_fat",
                        "trans_fat", "cholesterol", "sodium", "fiber")})
            for item in items]


def report(plan: crawl.Plan) -> None:
    broken = len({(p.chain, p.name) for p in validate.errors(plan.problems)})
    print(f"\nСнято со страниц: {plan.crawled}")
    print(f"  сошлись с каталогом: {plan.agreed}")
    print(f"  расходятся:          {len(plan.updates)}")
    print(f"  без пары в каталоге: {len(plan.unmatched)}")
    print(f"  неполная этикетка:   {len(plan.partial)}")
    print(f"  слишком непохоже:    {len(plan.suspicious)}")
    print(f"  не сходятся с собой: {broken}")
    print(f"  каталог не увидел:   {len(plan.unseen)} из {len(plan.unseen) + plan.seen}")
    if plan.adopted or plan.retired:
        print(f"  ЗАВЕСТИ новых:       {len(plan.adopted)}")
        print(f"  УВЕСТИ в архив:      {len(plan.retired)}")

    errors = validate.errors(plan.problems)
    if errors:
        print(f"\n  НЕ СХОДЯТСЯ САМИ С СОБОЙ: {len(errors)} — в базу не поедут")
        for problem in errors[:5]:
            print(f"    {problem.name}: {problem.detail}")

    for update in plan.updates[:20]:
        print(f"  · {update.name}: {update.summary}")
    if len(plan.updates) > 20:
        print(f"  … ещё {len(plan.updates) - 20}")

    if plan.suspicious:
        # При замене меню из структурного источника такие изменения всё
        # равно записываются: ловить там нечего, кроме чужих цифр. Но
        # показать их надо — это самые большие расхождения в прогоне.
        applied = {u.ext_key for u in plan.updates}
        where = ("самые большие расхождения — записываются, но взгляните"
                 if plan.suspicious[0].ext_key in applied
                 else "человеку, не в базу")
        print(f"\n  Слишком непохоже на дрейф рецептуры ({where}):")
        for update in plan.suspicious[:10]:
            print(f"    {update.name}: {update.summary}")

    if plan.adopted:
        print("\n  Новые позиции сети:")
        for adoption in plan.adopted[:10]:
            print(f"    {adoption.name} — {adoption.values.get('kcal', 0):.0f} ккал"
                  f"  [{adoption.category or 'без раздела'}]")
        if len(plan.adopted) > 10:
            print(f"    … ещё {len(plan.adopted) - 10}")

    if plan.unmatched and not plan.adopted:
        print("\n  Без пары (лучшее сходство):")
        for name, score in plan.unmatched[:10]:
            print(f"    {name} — {score}")


def crawl_record(plan: crawl.Plan, chain_id: int) -> str:
    """Строка в `crawls`: сколько нашли, сколько поменяли, чем кончилось."""
    notes = (plan.held or
             f"{plan.agreed} сошлись, {len(plan.unmatched)} без пары, "
             f"{len(plan.suspicious)} слишком непохожи")
    return (
        "insert into crawls (chain_id, finished_at, found, changed, dropped,"
        " status, notes)\n"
        f"values ({chain_id}, now(), {plan.crawled}, {len(plan.updates)},"
        f" {len(plan.unseen)}, {sql_text('held' if plan.held else 'ok')},"
        f" {sql_text(notes)});")


def record_only(plan: crawl.Plan, chain_id: int, observed: str) -> None:
    """Записывает факт кроула, не трогая позиции."""
    path = DATA / "crawls" / f"{plan.chain}-{observed}-record.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(crawl_record(plan, chain_id) + "\n", encoding="utf-8")
    subprocess.run(["supabase", "db", "query", "--linked", "--agent=no",
                    "-f", str(path)], capture_output=True, text=True)


def sql_for(plan: crawl.Plan, chain_id: int, observed: str) -> str:
    """Новая версия позиции: старую закрываем, свежую вставляем.

    Строка не переписывается: `valid_to` у прежней и новая строка рядом.
    Так у позиции остаётся история, а `items_export` берёт текущую.
    """
    lines = [f"-- Кроул {plan.chain}, {observed}. Сгенерировано crawl_chain.py.",
             "begin;", ""]
    # Название, категорию, раздел и пометки несём из закрываемой строки:
    # кроул уточняет числа, а не переписывает позицию. Название вдобавок —
    # ключ, по которому её ищет человек и цепляются варианты.
    CARRIED = ("name", "category", "serving_text", "section", "flags")
    COLUMNS = ("chain_id", "ext_key", *CARRIED, *crawl.NUTRIENTS,
               "source", "source_url", "observed_at", "stale", "confidence")

    for update in plan.updates:
        numbers = ", ".join(sql_number(update.values.get(name))
                            for name in crawl.NUTRIENTS)
        # Закрытие и вставка — одним оператором. Порознь нельзя: на
        # (chain_id, ext_key) при valid_to is null стоит уникальный индекс,
        # и вставка до закрытия упала бы на первой же позиции, а закрытие
        # до вставки оставило бы нечего копировать.
        lines.append(
            f"with closed as (\n"
            f"  update items set valid_to = now()\n"
            f"  where chain_id = {chain_id}"
            f" and ext_key = {sql_text(update.ext_key)} and valid_to is null\n"
            f"  returning chain_id, ext_key, {', '.join(CARRIED)}\n"
            f")\n"
            f"insert into items ({', '.join(COLUMNS)})\n"
            f"select chain_id, ext_key, {', '.join(CARRIED)},\n"
            f"       {numbers},\n"
            f"       {sql_text(plan.source)}, {sql_text(update.source_url)},"
            f" date {sql_text(observed)}, false, 1.00\n"
            f"from closed;\n")

    # Сошедшиеся: цифры те же, но подтверждены сегодня и у сети. Строку
    # не версионируем — значения не менялись, менялось только то, что мы
    # о них знаем. Без этой записи подтверждённая позиция навсегда
    # оставалась бы помеченной как данные 2018 года.
    if plan.confirmed:
        keys = ", ".join(sql_text(key) for key in plan.confirmed)
        lines.append(
            f"update items set source = {sql_text(plan.source)},"
            f" source_url = {sql_text(plan.menu_url)},"
            f" observed_at = date {sql_text(observed)}, stale = false\n"
            f"where chain_id = {chain_id} and valid_to is null"
            f" and ext_key in ({keys});\n")

    # Новые позиции сети. Раздел и вариант им проставит sync_taxonomy по
    # тем же правилам, что и всем остальным: их считает конвейер по
    # названию, а не берёт с источника, — поэтому здесь оставляем пусто.
    if plan.adopted:
        columns = ("chain_id", "ext_key", "name", "category", "serving_text",
                   *crawl.NUTRIENTS,
                   "source", "source_url", "observed_at", "stale", "confidence")
        rows = []
        for adoption in plan.adopted:
            numbers = ", ".join(sql_number(adoption.values.get(name))
                                for name in crawl.NUTRIENTS)
            rows.append(
                f"  ({chain_id}, {sql_text(adoption.ext_key)},"
                f" {sql_text(adoption.name)}, {sql_text(adoption.category)},"
                f" {sql_text(adoption.serving)}, {numbers},"
                f" {sql_text(plan.source)}, {sql_text(adoption.source_url)},"
                f" date {sql_text(observed)}, false, 1.00)")
        lines.append(
            f"insert into items ({', '.join(columns)})\nvalues\n"
            + ",\n".join(rows)
            # Позиция с таким ключом уже есть — значит её завёл прошлый
            # прогон этого же гида. Повтор не ошибка, просто нечего делать.
            + "\non conflict do nothing;\n")

    # Вес порции — только в пустое место. Сеть называет его точнее, чем
    # срез 2018 года, но там, где порция проставлена счётом («1 Cookie»),
    # граммы её не улучшат, а смысл поменяют.
    blanks = {key: value for key, value in plan.servings.items()
              if key not in {a.ext_key for a in plan.adopted}}
    if blanks:
        rows = ", ".join(f"({sql_text(key)}, {sql_text(value)})"
                         for key, value in sorted(blanks.items()))
        lines.append(
            "update items set serving_text = fresh.serving\n"
            f"from (values {rows}) as fresh(key, serving)\n"
            f"where chain_id = {chain_id} and valid_to is null"
            " and ext_key = fresh.key and serving_text is null;\n")

    # Чего сеть не назвала в собственном гиде, того она больше не подаёт.
    # Строку не трогаем: человек мог сохранить блюдо в заказ, и исчезновение
    # выглядело бы поломкой. Приложение уводит такие в раздел «Archive».
    if plan.retired or plan.adopted:
        # «Снято» и «в меню» пишем одинаково явно. Обход бывает неполным —
        # у Firehouse позиции лежат на пятом уровне вложенности, и первый
        # прогон Burger King видел 281 документ там, где их 473. Строка,
        # которую прошлый прогон не дотянулся увидеть и увёл в архив,
        # должна вернуться следующим, а не остаться там навсегда.
        # Заведённая сейчас позиция — в меню по определению: сеть только
        # что назвала её сама. Без этого у Firehouse 97 свежих строк, а у
        # Popeyes 52 оставались без наблюдения вовсе.
        on_menu_keys = sorted(set(plan.seen_keys) | {a.ext_key for a in plan.adopted})
        for on_menu, keys in ((False, plan.retired), (True, on_menu_keys)):
            if not keys:
                continue
            listed = ", ".join(sql_text(key) for key in keys)
            lines.append(
                "insert into menu_presence (chain_id, ext_key, on_menu, source, checked_at)\n"
                f"select {chain_id}, key, {'true' if on_menu else 'false'},"
                f" {sql_text(plan.source)}, now()\n"
                f"from unnest(array[{listed}]::text[]) as key\n"
                "on conflict (chain_id, ext_key) do update set on_menu = excluded.on_menu,"
                " source = excluded.source, checked_at = excluded.checked_at;\n")

    kind = ("pdf" if plan.menu_url.endswith(".pdf")
            else "json_api" if plan.source in {b.domain for b in sanity_rbi.BRANDS.values()}
            else "json_api" if plan.source == mcdonalds.DOMAIN
            else "json_in_html")
    lines.append(f"update chains set last_crawl_at = now(), source_url = "
                 f"{sql_text(plan.menu_url)}, source_kind = {sql_text(kind)}"
                 f" where id = {chain_id};")
    lines.append(crawl_record(plan, chain_id))
    lines.append("commit;")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", help="slug сети в chains")
    parser.add_argument("--menu", help="адрес меню; иначе берётся chains.source_url")
    parser.add_argument("--guide", metavar="URL",
                        help="взять позиции из PDF-гида сети вместо обхода сайта")
    parser.add_argument("--sanity", action="store_true",
                        help="читать контент-базу сети напрямую (бренды RBI)")
    parser.add_argument("--snapshot", action="store_true",
                        help="взять меню из снимка, снятого браузером")
    parser.add_argument("--apply", action="store_true", help="записать в базу")
    parser.add_argument("--replace", action="store_true",
                        help="замена меню: завести новые позиции и увести в "
                             "архив те, которых нет в гиде. Только для --guide "
                             "и только осознанно")
    parser.add_argument("--limit", type=int, help="взять только первые N страниц")
    parser.add_argument("--browser", action="store_true",
                        help="ходить через curl с браузерными заголовками")
    parser.add_argument("--observed", default=date.today().isoformat())
    parser.add_argument("--cache", type=Path, help="снятое класть сюда и брать отсюда")
    args = parser.parse_args()

    row = chain_row(args.chain)
    row_id = row["id"]
    menu_url = args.guide or args.menu or row.get("source_url")
    if args.sanity:
        brand = sanity_rbi.BRANDS.get(args.chain)
        menu_url = f"https://www.{brand.domain}/menu" if brand else None
    if args.snapshot:
        menu_url = mcdonalds.MENU_URL
    if not menu_url:
        raise SystemExit("адрес меню неизвестен: укажите --menu (он запомнится в chains)")

    print(f"── {row['name']} ── {menu_url}")

    if args.sanity:
        live = from_sanity(args.chain)
    elif args.snapshot:
        live = from_snapshot(args.chain)
    elif args.guide:
        live = from_guide(args.guide, row["name"], args.chain)
    elif args.cache and args.cache.exists():
        print(f"  из кэша {args.cache}")
        live = [Crawled(**item) for item in json.loads(args.cache.read_text())]
    else:
        live = walk(menu_url, limit=args.limit, browser=args.browser)
        if args.cache and live:
            args.cache.parent.mkdir(parents=True, exist_ok=True)
            args.cache.write_text(json.dumps([vars(i) for i in live], ensure_ascii=False,
                                             indent=1), encoding="utf-8")

    if not live:
        print("ничего не снято", file=sys.stderr)
        return 1

    live = [Crawled(**{**vars(item), "chain": row["name"]}) for item in live]
    stored = catalog(row["id"])
    print(f"  в каталоге: {len(stored)} позиций")

    if args.replace and not (args.guide or args.sanity or args.snapshot):
        raise SystemExit(
            "--replace только с --guide, --sanity или --snapshot: обход сайта "
            "неполон по природе, и «мы не дошли до страницы» неотличимо от "
            "«блюда нет»")

    plan = crawl.build(row["name"], live, stored,
                       previous=previous_crawl(row_id, live[0].source),
                       adopt=args.replace,
                       structured=bool(args.sanity or args.snapshot),
                       source=live[0].source, menu_url=menu_url)
    report(plan)

    if plan.held:
        print(f"\nДЕРЖИМ: {plan.held}", file=sys.stderr)
        print("Релиз не собирать. Похоже на поломку обхода, а не на новое меню.",
              file=sys.stderr)

    if not args.apply:
        print("\nНичего не записано. Повторите с --apply, если план верен.")
        return 0

    if plan.held and not args.replace:
        # Позиции не трогаем, но запись о кроуле нужна: иначе крон
        # молча уходит ни с чем и следующий запуск ничего не знает.
        record_only(plan, row_id, args.observed)
        print("С held в базу пишем только запись о кроуле.", file=sys.stderr)
        return 1
    if plan.held:
        # Замена меню и должна выглядеть как катастрофа для дифф-проверки:
        # у сети, чей каталог семь лет не трогали, меняется почти всё.
        # Порог существует для обычного обновления, а это не оно — и потому
        # решение принимает человек флагом, а не порог.
        print(f"\nЗамена меню: дифф-проверка сказала «{plan.held}» — "
              f"для замены это ожидаемо, продолжаю по --replace.")
    if not (plan.updates or plan.adopted or plan.retired or plan.confirmed):
        print("\nОбновлять нечего.")
        record_only(plan, row_id, args.observed)
        return 0

    path = DATA / "crawls" / f"{args.chain}-{args.observed}.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql_for(plan, row["id"], args.observed), encoding="utf-8")
    print(f"\nSQL: {path.relative_to(ROOT)}")

    result = subprocess.run(
        ["supabase", "db", "query", "--linked", "--agent=no", "-f", str(path)],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return 1
    done = [f"{len(plan.updates)} обновлено"]
    if plan.confirmed:
        done.append(f"{len(plan.confirmed)} подтверждено")
    if plan.adopted:
        done.append(f"{len(plan.adopted)} заведено")
    if plan.retired:
        done.append(f"{len(plan.retired)} уведено в архив")
    print("Записано: " + ", ".join(done))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
