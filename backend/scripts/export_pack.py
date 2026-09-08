#!/usr/bin/env python3
"""Собирает пак из базы — с наложенными overrides.

    python3 backend/scripts/export_pack.py --version 2

Отличие от build_seed.py: тот делает bootstrap-пак напрямую из MenuStat и
детерминирован, поэтому CI может сверить его с файлом в бандле. Этот берёт
текущее состояние базы, то есть данные кроулов плюс ручные правки, — именно
он готовит паки для Storage начиная с v2.

Данные тянет через `supabase db query --linked`, которому хватает access-токена
CLI: пароль базы не нужен.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import pack

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
STORAGE_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs/v{v}.deflate"
PAGE = 5000


class Row:
    """Утиный двойник menustat.Item — pack.build читает только эти поля."""
    __slots__ = ("chain", "ext_key", "name", "category", "serving",
                 "kcal", "protein", "carbs", "fat",
                 "sugar", "sat_fat", "trans_fat", "cholesterol",
                 "sodium", "fiber", "flags",
                 "source", "observed", "stale", "photo", "off_menu")

    def __init__(self, item: dict, key: str):
        self.chain = item["chain"]
        self.ext_key = key
        self.name = item["name"]
        self.category = item.get("category")
        self.serving = item.get("serving")
        self.kcal = float(item["kcal"])
        self.protein = float(item["protein"])
        self.carbs = float(item["carbs"])
        self.fat = float(item["fat"])
        # Остальная этикетка: сахар, жиры, холестерин, натрий, клетчатка.
        # Есть не у всех позиций, поэтому None проходит насквозь.
        for field, key in (("sugar", "sugar"), ("sat_fat", "satFat"),
                           ("trans_fat", "transFat"),
                           ("cholesterol", "cholesterol"),
                           ("sodium", "sodium"), ("fiber", "fiber")):
            value = item.get(key)
            setattr(self, field, float(value) if value is not None else None)
        # Пометки позиции: детская порция, на компанию, не во всех точках,
        # сезонное. Термины закрыты словарём в базе.
        self.flags = tuple(item.get("flags") or ())
        # После override у позиции может быть свой источник и дата — пак их несёт.
        self.source = item.get("source")
        self.observed = item.get("observed")
        self.stale = bool(item.get("stale", False))
        # Снимок именно этого блюда, если он есть; иначе приложение покажет
        # картинку по архетипу.
        photo = item.get("photo")
        # Прозрачная предметная съёмка вписывается целиком: обрезка съест
        # края тарелки и стакан рядом с бургером.
        if photo and str(photo.get("url", "")).endswith(".png"):
            photo = {**photo, "fit": "contain"}
        self.photo = photo
        # Позиции больше нет в меню сети. Скрывать нельзя — человек мог
        # сохранить её в заказ; но и молчать нельзя.
        self.off_menu = bool(item.get("offMenu"))


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

    start = proc.stdout.index("[")
    return json.loads(proc.stdout[start:])


def fetch_all() -> list[Row]:
    rows: list[Row] = []
    offset = 0
    while True:
        page = query(
            "select ext_key, item from items_export "
            f"order by item_id limit {PAGE} offset {offset};")
        if not page:
            break
        rows.extend(Row(r["item"], r["ext_key"]) for r in page)
        print(f"  получено {len(rows):,}")
        offset += PAGE
    return rows


# Насколько пак может обеднеть по сравнению с прошлым, прежде чем это
# перестанет быть обновлением и станет поломкой.
MAX_LOSS = 0.05


def previous_items(version: int) -> list[dict] | None:
    """Позиции прошлого пака — с диска, а если его там нет, из Storage.

    В CI диска нет: паки не в репозитории. А сравнивать надо с тем, что
    реально опубликовано, — это и есть то, чего не должен лишиться человек
    с установленным приложением.
    """
    local = DATA / f"pack-v{version}.json"
    if local.exists():
        return json.loads(local.read_text())["items"]
    try:
        with urllib.request.urlopen(STORAGE_URL.format(v=version), timeout=120) as response:
            raw = zlib.decompress(response.read(), -zlib.MAX_WBITS)
    except urllib.error.HTTPError as error:
        # Storage отвечает на отсутствующий объект 400 с телом «not_found»,
        # а не 404. Оба значат одно: сравнивать не с чем.
        if error.code in (400, 404):
            return None
        raise
    return json.loads(raw)["items"]


def check_against_previous(pack: dict, version: int) -> list[str]:
    """Не потерял ли новый пак того, что было в прошлом.

    Ловит поломки не в цифрах, а в выборке: пак собирается из вью
    `items_export`, и достаточно пересоздать её по устаревшему определению,
    чтобы молча отвалились снимки блюд и пометки о снятых с меню. Так и
    случилось с v12 — 150 фотографий и 121 архивная позиция исчезли, и
    заметить это можно было только глазами.
    """
    was = previous_items(version - 1)
    if was is None:
        return []

    now = pack["items"]
    problems = []
    for field, label in (("photo", "снимков блюд"), ("offMenu", "снятых с меню"),
                         ("variant", "вариантов"), ("sugar", "сахара")):
        before = sum(1 for i in was if i.get(field))
        after = sum(1 for i in now if i.get(field))
        if before and after < before * (1 - MAX_LOSS):
            problems.append(f"{label}: было {before:,}, стало {after:,}")
    if len(now) < len(was) * (1 - MAX_LOSS):
        problems.append(f"позиций: было {len(was):,}, стало {len(now):,}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--allow-loss", action="store_true",
                    help="пак беднее прошлого намеренно")
    args = ap.parse_args()

    rows = fetch_all()
    if not rows:
        print("База пуста — сначала load_seed.py", file=sys.stderr)
        return 1
    rows.sort(key=lambda r: (r.chain, r.name))

    built = pack.build(rows, version=args.version, source="", observed="")

    if losses := check_against_previous(built, args.version):
        print("\nПак беднее прошлого:", file=sys.stderr)
        for loss in losses:
            print(f"  {loss}", file=sys.stderr)
        if not args.allow_loss:
            print("Публиковать нельзя. Проверьте items_export — обычно дело в ней."
                  " Если потеря намеренная, --allow-loss.", file=sys.stderr)
            return 1

    meta = pack.write(built,
                      json_path=DATA / f"pack-v{args.version}.json",
                      deflate_path=DATA / f"pack-v{args.version}.deflate")
    (DATA / "manifest.json").write_text(
        json.dumps(pack.manifest(meta, url=STORAGE_URL.format(v=args.version)),
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nПак v{meta['version']}: {meta['itemCount']:,} позиций")
    print(f"  {meta['bytes']/1e6:.2f} MB → deflate {meta['compressedBytes']/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
