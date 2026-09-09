#!/usr/bin/env python3
"""Собирает каталог конвейера из MenuStat 2018.

  python3 scripts/build_seed.py [--cache PATH]

На выходе:
  backend/data/catalog.json           — полный каталог: из него живёт
                                        конвейер (load_seed, аудит, поиск
                                        снимков) и его сверяет CI
  backend/data/seed-pack-v1.deflate   — то же, сжатое
  backend/data/problems.csv           — что не прошло валидацию

**В бандл приложения этот файл не едет.** Там лежит опубликованный пак,
и кладёт его туда `publish_pack.sh`: приложение показывает только сети,
собранные целиком, а конвейеру нужны все девяносто шесть — иначе
`load_seed.py` затрёт базу тем, что осталось после отбора.

Детерминирован: пересборка из того же исходника даёт тот же байт, и на
этом держится проверка «каталог не устарел» в CI и в pre-push.
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
CATALOG_JSON = ROOT / "backend" / "data" / "catalog.json"
DATA = ROOT / "backend" / "data"


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
    meta = pack.write(built, json_path=CATALOG_JSON,
                      deflate_path=DATA / f"seed-pack-v{args.version}.deflate")

    print(f"\nКаталог конвейера v{meta['version']}: {meta['itemCount']:,} позиций")
    print(f"  {meta['bytes']/1e6:.2f} MB → deflate {meta['compressedBytes']/1e6:.2f} MB")
    print(f"  {CATALOG_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
