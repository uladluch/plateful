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
MATCH_THRESHOLD = 0.72
# Расхождение меньше этого — округление сети, а не изменение рецептуры.
NOISE_KCAL = 5.0
NOISE_GRAMS = 1.0

_NOISE_WORDS = re.compile(
    r"\b(chick fil a|chickfila|mcdonalds|nutrition|and ingredients|meal|entree)\b")


def comparable(name: str) -> str:
    """Имя без бренда, значков и пунктуации — только для сопоставления."""
    text = name.lower().replace("®", " ").replace("™", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = _NOISE_WORDS.sub(" ", text)
    return " ".join(sorted(text.split()))


def load_catalog(chain: str) -> dict[str, dict]:
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    return {item["key"]: item for item in pack["items"] if item["chain"] == chain}


def match(live: LiveItem, catalog: dict[str, dict]) -> tuple[dict | None, float]:
    if live.ext_key in catalog:
        return catalog[live.ext_key], 1.0

    target = comparable(live.name)
    best, score = None, 0.0
    for item in catalog.values():
        ratio = difflib.SequenceMatcher(None, target, comparable(item["name"])).ratio()
        if ratio > score:
            best, score = item, ratio
    return (best, score) if score >= MATCH_THRESHOLD else (None, score)


def differences(live: LiveItem, stored: dict) -> dict[str, tuple[float, float]]:
    """Что реально разошлось, за вычетом округлений."""
    checks = (("kcal", live.kcal, stored["kcal"], NOISE_KCAL),
              ("protein", live.protein, stored["protein"], NOISE_GRAMS),
              ("carbs", live.carbs, stored["carbs"], NOISE_GRAMS),
              ("fat", live.fat, stored["fat"], NOISE_GRAMS))
    return {field: (was, now)
            for field, now, was, noise in checks
            if now is not None and abs(now - was) > noise}


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

    changed, same, unmatched = [], 0, []
    for item in live:
        stored, score = match(item, catalog)
        if stored is None:
            unmatched.append((item, score))
            continue
        diff = differences(item, stored)
        if diff:
            changed.append((stored, item, diff))
        else:
            same += 1

    print(f"Совпало без изменений: {same}")
    print(f"Разошлось:             {len(changed)}")
    print(f"Не сопоставлено:       {len(unmatched)}\n")

    if changed:
        print("РАСХОЖДЕНИЯ")
        for stored, item, diff in sorted(changed, key=lambda r: -abs(
                r[2].get("kcal", (0, 0))[1] - r[2].get("kcal", (0, 0))[0])):
            detail = "  ".join(f"{f} {was:g}→{now:g}" for f, (was, now) in diff.items())
            print(f"  {stored['name'][:36]:<36} {detail}")

    if unmatched:
        print("\nНЕ СОПОСТАВЛЕНО (нужны глаза)")
        for item, score in unmatched[:15]:
            print(f"  {item.name[:44]:<44} лучшее сходство {score:.2f}")

    if args.apply and changed:
        out = DATA / "overrides" / f"{args.chain}.sql"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sql_for(adapter.CHAIN, changed, args.observed), encoding="utf-8")
        print(f"\nSQL правок: {out.relative_to(ROOT)}")
        print(f"Применить:  supabase db query --linked -f {out.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
