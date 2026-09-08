#!/usr/bin/env python3
"""Принимает официальные снимки блюд от сетей.

Раскладка папок — сеть/позиция:

    backend/data/official-photos/
      mcdonalds/
        big-mac.png
        quarter-pounder-w-cheese.jpg
      burger-king/
        whopper-sandwich.png

Имя папки — слаг сети, имя файла — ext_key позиции (тот же, что в базе).

    python3 backend/scripts/import_official_photos.py --check          # что найдено
    python3 backend/scripts/import_official_photos.py --rights "Used with permission from McDonald's"

Прозрачный фон сохраняется: студийная предметная съёмка обычно приходит
PNG с альфой, и её нельзя кадрировать в квадрат — обрежутся края тарелки.
Такие файлы вписываются целиком, а в паке помечаются `fit: contain`,
чтобы приложение показало их без обрезки.

Условия использования пишутся в поле license: они у каждой сети свои,
и через полгода никто не вспомнит, что было разрешено.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "data" / "official-photos"
BUCKET_URL = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/photos"
PACK = ROOT / "plateful" / "Resources" / "seed-pack.json"
SIDE = 1000
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def slug_to_chain() -> dict[str, str]:
    """Слаг папки → название сети, как оно записано в базе."""
    import re
    chains = json.loads(PACK.read_text())["chains"]
    return {re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-"): c["name"]
            for c in chains}


def item_keys(chain: str) -> set[str]:
    return {i["key"] for i in json.loads(PACK.read_text())["items"] if i["chain"] == chain}


def prepare(path: Path) -> tuple[Image.Image, bool]:
    """Готовит файл. Возвращает изображение и признак прозрачности."""
    image = Image.open(path)
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info

    if has_alpha:
        # Вписываем в квадрат, не обрезая: у предметной съёмки края значимы.
        image = image.convert("RGBA")
        canvas = Image.new("RGBA", (SIDE, SIDE), (0, 0, 0, 0))
        image.thumbnail((SIDE, SIDE), Image.LANCZOS)
        canvas.paste(image, ((SIDE - image.width) // 2, (SIDE - image.height) // 2))
        return canvas, True

    image = image.convert("RGB")
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS), False


def sql_text(value) -> str:
    return "null" if value in (None, "") else "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="только показать, что найдено")
    parser.add_argument("--rights", help="условия, на которых сеть разрешила использование")
    args = parser.parse_args()

    if not SOURCE.exists():
        SOURCE.mkdir(parents=True, exist_ok=True)
        print(f"Положите файлы в {SOURCE.relative_to(ROOT)}/<слаг-сети>/<ключ-позиции>.png")
        return 0

    chains = slug_to_chain()
    found, unknown, statements = [], [], []

    for folder in sorted(p for p in SOURCE.iterdir() if p.is_dir()):
        chain = chains.get(folder.name)
        if not chain:
            unknown.append(f"папка {folder.name}: такой сети нет в каталоге")
            continue
        keys = item_keys(chain)
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in SUFFIXES:
                continue
            key = path.stem
            if key not in keys:
                unknown.append(f"{folder.name}/{path.name}: нет позиции «{key}» у {chain}")
                continue
            found.append((chain, key, path))

    for message in unknown:
        print(f"  ! {message}")
    if not found:
        print("Файлов для импорта не найдено.")
        return 0 if args.check else 1

    if args.check:
        for chain, key, path in found:
            image = Image.open(path)
            print(f"  {chain[:14]:<14} {key:<32} {image.size[0]}x{image.size[1]} {image.mode}")
        print(f"\nвсего {len(found)}")
        return 0

    if not args.rights:
        print("Укажите --rights: на каких условиях сеть разрешила использование.",
              file=sys.stderr)
        return 2

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for chain, key, path in found:
            image, transparent = prepare(path)
            slug = next(s for s, name in chains.items() if name == chain)
            name = f"{slug}--{key}." + ("png" if transparent else "jpg")
            out = Path(tmp) / name
            if transparent:
                image.save(out, "PNG", optimize=True)
            else:
                image.save(out, "JPEG", quality=88, optimize=True)

            upload = subprocess.run(
                ["supabase", "storage", "cp", str(out), f"ss:///photos/{name}",
                 "--linked", "--experimental",
                 "--content-type", "image/png" if transparent else "image/jpeg",
                 "--cache-control", "max-age=31536000, immutable"],
                capture_output=True, text=True)
            if upload.returncode != 0 and "Duplicate" not in upload.stderr:
                print(f"  ! {key}: {upload.stderr.strip()[:80]}")
                continue

            statements.append(
                "insert into item_photos (chain_id, ext_key, url, license, creator, title)\n"
                f"select c.id, {sql_text(key)}, {sql_text(f'{BUCKET_URL}/{name}')},"
                f" {sql_text(args.rights)}, {sql_text(chain)}, {sql_text(path.name)}\n"
                f"from chains c where c.name = {sql_text(chain)}\n"
                "on conflict (chain_id, ext_key) do update set url = excluded.url,"
                " license = excluded.license, creator = excluded.creator,"
                " title = excluded.title;")
            print(f"  ✓ {chain[:14]:<14} {key:<32} {'прозрачный' if transparent else 'фото'}")

    if statements:
        out = ROOT / "backend" / "data" / "official-photos.sql"
        out.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
        applied = subprocess.run(["supabase", "db", "query", "--linked", "-f", str(out)],
                                 capture_output=True, text=True)
        print(f"\nв базу записано {len(statements)}" if applied.returncode == 0
              else f"\nSQL не применился: {applied.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
