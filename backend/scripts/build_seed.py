#!/usr/bin/env python3
"""Собирает seed-пак из MenuStat 2018.

  python3 scripts/build_seed.py [--cache PATH]

На выходе:
  plateful/Resources/seed-pack.json   — едет в бандле приложения
  backend/data/seed-pack.deflate      — то же, сжатое (для Storage)
  backend/data/manifest.json
  backend/data/problems.csv           — что не прошло валидацию
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import menustat, pack, validate

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_JSON = ROOT / "plateful" / "Resources" / "seed-pack.json"
DATA = ROOT / "backend" / "data"
STORAGE_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs/v{v}.deflate"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=DATA / "raw" / "menustat-2018.tab")
    ap.add_argument("--version", type=int, default=1)
    args = ap.parse_args()

    print("Скачиваю MenuStat 2018…" if not args.cache.exists() else f"Читаю кэш {args.cache}")
    raw = menustat.download(cache=args.cache)
    print(f"  {len(raw):,} байт")

    items = menustat.parse(raw)
    chains = {i.chain for i in items}
    print(f"Очищено: {len(items):,} позиций, {len(chains)} сетей")

    problems = validate.check_catalog(items)
    errors = validate.errors(problems)
    by_kind = {}
    for p in problems:
        by_kind.setdefault(p.severity, {}).setdefault(p.kind, 0)
        by_kind[p.severity][p.kind] += 1
    print(f"Валидация: {len(errors):,} ошибок, {len(problems) - len(errors):,} предупреждений")
    for sev in ("error", "warning"):
        if by_kind.get(sev):
            print(f"  {sev}: {by_kind[sev]}")
    if errors:
        print("  ПЕРВЫЕ ОШИБКИ:")
        for p in errors[:5]:
            print(f"    {p.chain} / {p.name}: {p.detail}")

    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "problems.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["severity", "chain", "name", "kind", "detail"])
        for p in problems:
            w.writerow([p.severity, p.chain, p.name, p.kind, p.detail])

    # Позиции с ошибками в пак не едут: лучше 2% пробелов, чем сэндвич
    # с 368 г жира. Все они лежат в problems.csv и чинятся через overrides.
    broken = {(p.chain, p.name) for p in errors}
    shipped = [i for i in items if (i.chain, i.name) not in broken]
    if broken:
        print(f"Исключено из пака: {len(items) - len(shipped):,} позиций с ошибками")

    # Сломанные доли этикетки гасим, а позицию оставляем: сахар больше
    # углеводов не отменяет калорий блюда. В отчёте они уже посчитаны
    # предупреждениями kind=label.
    cleaned = validate.strip_broken_label(shipped)
    nulled = sum(len(validate.broken_label_fields(i)) for i in shipped)
    if nulled:
        print(f"Погашено полей этикетки: {nulled}")

    built = pack.build(cleaned, version=args.version,
                       source=menustat.SOURCE, observed=menustat.OBSERVED_AT)
    meta = pack.write(built, json_path=BUNDLE_JSON,
                      deflate_path=DATA / f"seed-pack-v{args.version}.deflate")

    (DATA / "manifest.json").write_text(
        json.dumps(pack.manifest(meta, url=STORAGE_URL.format(v=args.version)),
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nПак v{meta['version']}: {meta['itemCount']:,} позиций")
    print(f"  bundle {meta['bytes']/1e6:.2f} MB → deflate {meta['compressedBytes']/1e6:.2f} MB")
    print(f"  {BUNDLE_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
