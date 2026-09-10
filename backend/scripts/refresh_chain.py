#!/usr/bin/env python3
"""Регулярный контур: обновить сети из очереди и пересчитать готовность.

    python3 backend/scripts/refresh_chain.py                  # показать план
    python3 backend/scripts/refresh_chain.py --due --apply    # кому пора (крон)
    python3 backend/scripts/refresh_chain.py --all --apply    # все сети
    python3 backend/scripts/refresh_chain.py panera-bread --apply
    python3 backend/scripts/refresh_chain.py --due --apply --publish auto

Один вход для крона и для агента. Кого обновлять, решает `crawl_queue`
в базе (ядро — 7 дней, хвост — 30), а не список в этом файле. Как
обновлять — тоже база: `chains.source_kind` говорит, откуда цифры,
`chains.photo_source_kind` — откуда снимки. Этот скрипт только идёт по
шагам, каждый из которых умеет работать сам:

  1. цифры        crawl_chain.py     по source_kind
  2. присутствие  check_menu_presence.py  у кого есть читатель меню
  3. снимки       chain_photos.py    по photo_source_kind
  4. переукладка  relink_photos.py   привязки прежнего правила — прочь
  5. готовность   readiness.py --record   кто готов, в историю
  6. публикация   publish_pack.sh    если просили — и не стало хуже

Строго по одной сети и по одному шагу: два скрипта, заводящие временную
роль в Supabase одновременно, роняют её предохранитель на десять минут.

Сеть, у которой шаг не прошёл, не останавливает обход — она попадает в
сводку. Порог готовности при сборке пака сам не пустит протухшую сеть
к людям; задача обхода — чтобы таких было видно, а не чтобы их не было.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
sys.path.insert(0, str(ROOT / "backend"))

from plateful_data.adapters import sanity_rbi

#: Ключи `check_menu_presence.SOURCES` не совпадают со slug сети в базе.
PRESENCE_READERS = {"mcdonald-s": "mcdonalds", "chick-fil-a": "chick-fil-a"}


@dataclass
class Plan:
    """Что делать с одной сетью — до того, как что-либо запущено."""
    slug: str
    name: str
    numbers: list[str] | None = None      # аргументы crawl_chain.py
    presence: str | None = None           # ключ для check_menu_presence.py
    photos: bool = False
    skipped: list[str] = field(default_factory=list)


def plan_for(row: dict) -> Plan:
    """Маршрут по строке `chains` — без единого запроса наружу.

    Цифры: подрядчик этикетки для `label_provider`, контент-база для
    брендов RBI, снимок калькулятора для McDonald's, обход сайта для
    остальных `json_api`/`html`. Сети `rendered` и `blocked` цифрами не
    обновляются — у них нет источника, и это записано в `source_note`.
    """
    plan = Plan(row["slug"], row["name"])
    kind = row.get("source_kind") or ""
    if kind == "label_provider":
        plan.numbers = ["--nutritionix", "--replace"]
    elif row["slug"] in sanity_rbi.BRANDS:
        plan.numbers = ["--sanity", "--replace"]
    elif row["slug"] == "mcdonald-s":
        plan.numbers = ["--snapshot", "--replace"]
    elif kind in ("rendered", "blocked", ""):
        plan.skipped.append(f"цифры: источника нет ({kind or 'не разведана'})")
    else:
        plan.numbers = []
    plan.presence = PRESENCE_READERS.get(row["slug"])
    plan.photos = bool(row.get("photo_source_kind"))
    if not plan.photos:
        plan.skipped.append("снимки: источник не записан")
    return plan


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


def chains(selection: list[str], *, due: bool, everything: bool) -> list[dict]:
    where = "c.status = 'active'"
    if selection:
        quoted = ", ".join("'" + s.replace("'", "''") + "'" for s in selection)
        where += f" and c.slug in ({quoted})"
    elif due:
        where += " and q.todo = 'кроулить'"
    elif not everything:
        return []
    return query(
        "select c.slug, c.name, c.source_kind, c.photo_source_kind, q.todo"
        " from chains c join crawl_queue q on q.slug = c.slug"
        f" where {where} order by c.item_count desc;")


def run(label: str, command: list[str]) -> bool:
    print(f"\n── {label}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"   не прошло (код {result.returncode})", file=sys.stderr)
    return result.returncode == 0


def refresh(plan: Plan, *, apply: bool) -> list[str]:
    """Выполняет план; возвращает, что не прошло."""
    failed: list[str] = []
    flag = ["--apply"] if apply else []
    if plan.numbers is not None:
        if not run(f"{plan.name}: цифры",
                   [sys.executable, str(SCRIPTS / "crawl_chain.py"), plan.slug,
                    *plan.numbers, *flag]):
            failed.append("цифры")
    if plan.presence and apply:
        if not run(f"{plan.name}: что сегодня в меню",
                   [sys.executable, str(SCRIPTS / "check_menu_presence.py"), plan.presence]):
            failed.append("присутствие")
    if plan.photos:
        if not run(f"{plan.name}: снимки",
                   [sys.executable, str(SCRIPTS / "chain_photos.py"), plan.slug, *flag]):
            failed.append("снимки")
    return failed


def next_version() -> int:
    rows = query("select coalesce(max(version), 0) + 1 as next from releases;")
    return int(rows[0]["next"]) if rows else 1


def ready_now_and_before() -> tuple[int, int | None]:
    rows = query("select ready from readiness_runs order by ran_at desc limit 2;")
    now = int(rows[0]["ready"]) if rows else 0
    before = int(rows[1]["ready"]) if len(rows) > 1 else None
    return now, before


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chains", nargs="*", help="slug сетей; иначе --due или --all")
    parser.add_argument("--due", action="store_true", help="кому пора по crawl_queue")
    parser.add_argument("--all", action="store_true", help="все активные сети")
    parser.add_argument("--apply", action="store_true", help="писать в базу")
    parser.add_argument("--publish", metavar="N|auto",
                        help="собрать пак: номер версии или auto — следующая, "
                             "если готовых сетей не стало меньше")
    args = parser.parse_args()

    rows = chains(args.chains, due=args.due, everything=args.all)
    if not rows:
        print("нечего обновлять: укажите сеть, --due или --all")
        return 0
    plans = [plan_for(row) for row in rows]

    print(f"сетей в обходе: {len(plans)}" + ("" if args.apply else "  (без --apply — только показ)"))
    for plan in plans:
        steps = [s for s, on in (("цифры", plan.numbers is not None),
                                 ("присутствие", plan.presence), ("снимки", plan.photos)) if on]
        print(f"  {plan.slug:26} {', '.join(steps) or '—':30} {'; '.join(plan.skipped)}")

    summary: dict[str, list[str]] = {}
    for plan in plans:
        failed = refresh(plan, apply=args.apply)
        if failed:
            summary[plan.slug] = failed

    if args.apply:
        run("переукладка снимков", [sys.executable, str(SCRIPTS / "relink_photos.py"), "--apply"])
        run("готовность", [sys.executable, str(SCRIPTS / "readiness.py"), "--record"])
    else:
        run("готовность", [sys.executable, str(SCRIPTS / "readiness.py")])

    if summary:
        print("\nне прошло:")
        for slug, steps in summary.items():
            print(f"  {slug}: {', '.join(steps)}")

    if args.publish and args.apply:
        if args.publish == "auto":
            now, before = ready_now_and_before()
            if before is not None and now < before:
                print(f"\nпак не публикуем: готовых сетей {now}, было {before}")
                return 1
            version = next_version()
        else:
            version = int(args.publish)
        run(f"публикация пака v{version}", [str(SCRIPTS / "publish_pack.sh"), str(version)])
    return 1 if summary else 0


if __name__ == "__main__":
    raise SystemExit(main())
