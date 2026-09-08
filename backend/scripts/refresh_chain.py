#!/usr/bin/env python3
"""Полный цикл обновления одной сети.

    python3 backend/scripts/refresh_chain.py mcdonalds
    python3 backend/scripts/refresh_chain.py --all --publish 9

Три шага подряд, каждый уже умеет работать сам по себе:
  1. присутствие в меню — что сеть продаёт сегодня, а что сняла;
  2. снимки — официальная съёмка для тех блюд, у которых её ещё нет;
  3. публикация пака — если попросили.

Сделано одним входом, чтобы крон запускал одну команду, а не три, и чтобы
порядок шагов не приходилось помнить.

Область — национальное меню США. Регионы и языки будут отдельным измерением:
у позиции появится регион, а у пака — локаль. Пока всё US/en.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"

# Условия использования снимков у каждой сети свои и хранятся рядом с ними.
CHAINS = {
    "mcdonalds": "© McDonald's Corporation. Used with permission. Source: mcdonalds.com",
    "chick-fil-a": "© Chick-fil-A, Inc. Used with permission. Source: chick-fil-a.com",
}


def run(step: str, command: list[str]) -> bool:
    print(f"\n── {step}")
    result = subprocess.run([sys.executable, *command], cwd=ROOT)
    if result.returncode != 0:
        print(f"   шаг не прошёл (код {result.returncode})", file=sys.stderr)
        return False
    return True


def refresh(chain: str) -> bool:
    ok = run(f"{chain}: что сегодня в меню",
             [str(SCRIPTS / "check_menu_presence.py"), chain])
    # Снимки берём даже если проверка меню сорвалась: это независимые данные,
    # и половина результата лучше, чем ничего.
    ok &= run(f"{chain}: официальные снимки",
              [str(SCRIPTS / "fetch_chain_photos.py"), chain, "--rights", CHAINS[chain]])
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", nargs="?", choices=sorted(CHAINS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--publish", type=int, metavar="VERSION",
                        help="собрать и выложить пак этой версии")
    args = parser.parse_args()

    if not args.chain and not args.all:
        parser.error("укажите сеть или --all")

    chains = sorted(CHAINS) if args.all else [args.chain]
    failures = [chain for chain in chains if not refresh(chain)]

    if args.publish:
        print(f"\n── публикация пака v{args.publish}")
        result = subprocess.run([str(SCRIPTS / "publish_pack.sh"), str(args.publish)],
                                cwd=ROOT)
        if result.returncode != 0:
            failures.append("публикация")

    if failures:
        print(f"\nс ошибками: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nготово")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
