#!/usr/bin/env python3
"""Сверяет каталог с тем, что сеть публикует сегодня.

    python3 backend/scripts/audit_chain.py chick-fil-a
    python3 backend/scripts/audit_chain.py chick-fil-a --apply

Без `--apply` только отчёт. С `--apply` пишет SQL правок в
`backend/data/overrides/<сеть>.sql` — его применяет `supabase db query`.

Сопоставление имён нестрогое: MenuStat 2018 писал «Chick Fil a Nuggets», сайт
пишет «Chick-fil-A® Nuggets». Уверенные совпадения берём автоматически,
сомнительные выносим в отчёт — выдумывать соответствия хуже, чем признать,
что позиция не сматчилась.
"""
from __future__ import annotations

import argparse
import dataclasses
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import chick_fil_a
from plateful_data.adapters.base import Fetcher, LiveItem
from plateful_data.slug import slugify

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"
DATA = ROOT / "backend" / "data"

ADAPTERS = {"chick-fil-a": chick_fil_a}

# Ниже этого сходства имён считаем, что позиция не найдена.
MATCH_THRESHOLD = 0.82
# Расхождение меньше этого — округление сети, а не изменение рецептуры.
NOISE_KCAL = 5.0
NOISE_GRAMS = 1.0

# Расхождение больше этой доли — почти наверняка не дрейф рецептуры, а разный
# смысл строки. Проверено на Side Salad: страница сети показывает салат
# с заправкой (470 ккал), в каталоге он без неё (160). Матч при этом верный,
# сравнивать нечего — такие строки уходят человеку, а не в правки.
SUSPICIOUS_SHARE = 0.30

# Хвост со страниц сети: «… Nutrition and Ingredients».
_PAGE_SUFFIX = re.compile(r"\s*nutrition and ingredients\s*$")
_BRAND_WORDS = re.compile(r"\b(chick fil a|chickfila|mcdonalds)\b")

# Размер и количество — не украшение названия, а другая позиция. «Milkshake»
# и «Milkshake, Large» отличаются на сотни калорий, а по строке почти
# совпадают, поэтому сравниваем их отдельно и строго.
_SIZE_WORDS = {"small", "medium", "large", "kids", "kid", "ct", "count", "jr"}


def normalized(name: str) -> str:
    text = name.lower().replace("®", " ").replace("™", " ").replace("’", "'")
    text = _PAGE_SUFFIX.sub("", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(_BRAND_WORDS.sub(" ", text).split())


def portion(name: str) -> frozenset[str]:
    """Числа и слова размера из названия.

    Совпадать обязаны точно: «4 Grilled Nuggets» и «8 Grilled Nuggets» —
    разные блюда, и подменить одно другим значит выдумать расхождение.
    """
    words = normalized(name).split()
    return frozenset(w for w in words if w.isdigit() or w in _SIZE_WORDS)


def comparable(name: str) -> str:
    """Имя без бренда, размеров и порядка слов — для нестрогого сравнения."""
    words = [w for w in normalized(name).split()
             if not w.isdigit() and w not in _SIZE_WORDS]
    return " ".join(sorted(words))


def load_catalog(chain: str) -> dict[str, dict]:
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    return {item["key"]: item for item in pack["items"] if item["chain"] == chain}


def match_all(live: list[LiveItem],
              catalog: dict[str, dict]) -> tuple[dict[str, dict], dict[str, float]]:
    """Сопоставляет позиции один к одному.

    Раньше несколько живых позиций могли указать на одну запись каталога, и
    отчёт показывал её дважды с разными числами. Теперь запись занимается
    первым же самым похожим кандидатом, остальные остаются несопоставленными —
    это честнее, чем выдать выдуманную пару за расхождение.
    """
    pairs: list[tuple[float, str, str]] = []
    for item in live:
        target, size = comparable(item.name), portion(item.name)
        for key, stored in catalog.items():
            if portion(stored["name"]) != size:
                continue
            ratio = difflib.SequenceMatcher(None, target, comparable(stored["name"])).ratio()
            if ratio >= MATCH_THRESHOLD:
                pairs.append((ratio, item.ext_key, key))

    pairs.sort(reverse=True)
    matched: dict[str, dict] = {}
    best_score: dict[str, float] = {}
    used: set[str] = set()

    for ratio, live_key, catalog_key in pairs:
        best_score[live_key] = max(best_score.get(live_key, 0.0), ratio)
        if live_key in matched or catalog_key in used:
            continue
        matched[live_key] = catalog[catalog_key]
        used.add(catalog_key)

    return matched, best_score


def differences(live: LiveItem, stored: dict) -> dict[str, tuple[float, float]]:
    """Что реально разошлось, за вычетом округлений."""
    checks = (("kcal", live.kcal, stored["kcal"], NOISE_KCAL),
              ("protein", live.protein, stored["protein"], NOISE_GRAMS),
              ("carbs", live.carbs, stored["carbs"], NOISE_GRAMS),
              ("fat", live.fat, stored["fat"], NOISE_GRAMS))
    return {field: (was, now)
            for field, now, was, noise in checks
            if now is not None and abs(now - was) > noise}


def suspicious(diff: dict[str, tuple[float, float]]) -> bool:
    return any(was > 0 and abs(now - was) / was > SUSPICIOUS_SHARE
               for was, now in diff.values())


def sql_for(chain: str, rows: list[tuple[dict, LiveItem, dict]], observed: str) -> str:
    lines = [f"-- Сверка {chain} с сайтом сети, {observed}.",
             "-- Сгенерировано audit_chain.py. Правки живут отдельно от данных",
             "-- кроула и переживают его.", ""]
    for stored, live, diff in rows:
        patch = {field: live_value for field, (_, live_value) in diff.items()}
        patch |= {"source": live.source, "observed": observed, "stale": False}
        reason = ", ".join(f"{f}: {was:g}→{now:g}" for f, (was, now) in diff.items())
        lines.append(
            "insert into overrides (chain_id, ext_key, patch, reason, author)\n"
            f"select c.id, {sql_text(stored['key'])}, {sql_text(json.dumps(patch))}::jsonb,\n"
            f"       {sql_text(f'Сверено с {live.source} {observed}: {reason}')}, 'audit'\n"
            f"from chains c where c.name = {sql_text(chain)}\n"
            "on conflict (chain_id, ext_key) do update\n"
            "  set patch = excluded.patch, reason = excluded.reason, updated_at = now();\n")
    return "\n".join(lines)


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", choices=sorted(ADAPTERS))
    parser.add_argument("--apply", action="store_true", help="записать SQL правок")
    parser.add_argument("--cache", type=Path, help="взять снятые данные из файла")
    parser.add_argument("--observed", default="2026-09-08")
    args = parser.parse_args()

    adapter = ADAPTERS[args.chain]

    if args.cache and args.cache.exists():
        live = [LiveItem(**row) for row in json.loads(args.cache.read_text())]
        print(f"Из кэша: {len(live)} позиций")
    else:
        live = adapter.fetch(Fetcher())
        # Пустую выдачу не кэшируем: иначе следующий запуск прочитает её как
        # «сеть ничего не публикует» и сверка молча покажет ноль расхождений.
        if args.cache and live:
            args.cache.parent.mkdir(parents=True, exist_ok=True)
            args.cache.write_text(json.dumps([dataclasses.asdict(i) for i in live],
                                             ensure_ascii=False, indent=1))

    if not live:
        print("Сеть не отдала ни одной позиции — сверять нечего.", file=sys.stderr)
        return 1

    catalog = load_catalog(adapter.CHAIN)
    print(f"В каталоге {adapter.CHAIN}: {len(catalog)} позиций\n")

    matched, scores = match_all(live, catalog)

    changed, same, unmatched = [], 0, []
    for item in live:
        stored = matched.get(item.ext_key)
        if stored is None:
            unmatched.append((item, scores.get(item.ext_key, 0.0)))
            continue
        diff = differences(item, stored)
        if diff:
            changed.append((stored, item, diff))
        else:
            same += 1

    confident = [row for row in changed if not suspicious(row[2])]
    review = [row for row in changed if suspicious(row[2])]

    print(f"Совпало без изменений:      {same}")
    print(f"Уверенные правки:           {len(confident)}")
    print(f"На глаза (расхождение >30%): {len(review)}")
    print(f"Не сопоставлено:            {len(unmatched)}\n")

    def report(title: str, rows: list) -> None:
        if not rows:
            return
        print(title)
        for stored, _, diff in sorted(rows, key=lambda r: -max(
                abs(now - was) / was if was else 0 for was, now in r[2].values())):
            detail = "  ".join(f"{f} {was:g}→{now:g}" for f, (was, now) in diff.items())
            print(f"  {stored['name'][:36]:<36} {detail}")
        print()

    report("УВЕРЕННЫЕ ПРАВКИ", confident)
    report("НА ПРОВЕРКУ ЧЕЛОВЕКУ — вероятно разный смысл строки, а не дрейф", review)

    if unmatched:
        print("НЕ СОПОСТАВЛЕНО")
        for item, score in unmatched[:15]:
            print(f"  {item.name[:46]:<46} лучшее сходство {score:.2f}")
        print()

    if args.apply and confident:
        out = DATA / "overrides" / f"{args.chain}.sql"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sql_for(adapter.CHAIN, confident, args.observed), encoding="utf-8")
        print(f"SQL уверенных правок: {out.relative_to(ROOT)}")
        print(f"Применить:  supabase db query --linked -f {out.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
