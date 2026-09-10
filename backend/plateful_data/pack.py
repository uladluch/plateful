"""Сборка пака для приложения.

Контракт (его же читает plateful/Menu/MenuPack.swift):

    manifest.json  {format, version, url, sha256, itemCount, releasedAt}
    pack           {format, version, source, observed, stale,
                    sections: [name],            порядок разделов в меню
                    chains: [{name, itemCount}],
                    items:  [{chain, key, name, category, section, serving,
                              kcal, protein, carbs, fat,
                              sugar?, satFat?, transFat?, cholesterol?,
                              sodium?, fiber?, flags?, image,
                              variant?: {group, label, order, kind, base},
                              source?, observed?, stale?}]}

`section` — раздел, в котором приложение покажет позицию: категория
источника, а поверх неё выделенный завтрак. Порядок разделов лежит в паке,
а не в приложении: у источника его нет вовсе, а менять его хочется
публикацией, не релизом.

`variant` — порция или опция одного блюда («Small», «10», «w/ Egg»).
Позиции с одинаковым `group` внутри сети приложение показывает одной
карточкой с переключателем.

Происхождение (`source`, `observed`, `stale`) вынесено на уровень пака, а у
позиции появляется только там, где отличается. В сиде все позиции из одного
среза MenuStat, поэтому у них этих полей нет вовсе; после ручной правки у
конкретной позиции будет свой источник и своя дата. Приложению это нужно:
обещание «показывать дату и источник» — один из трёх дифференциаторов.

Один и тот же формат у сида в бандле и у скачанного обновления, чтобы у
MenuRepository был ровно один декодер.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from collections import Counter
from dataclasses import dataclass

from .archetype import classify, needs_own_photo
from .taxonomy import SECTION_ORDER, section
from .variants import assign_groups
from datetime import date
from pathlib import Path

PACK_FORMAT = 1

DEFAULT_SOURCE = "menustat-2018"
DEFAULT_OBSERVED = "2018-12-31"


def _mode(values, fallback):
    """Самое частое значение — оно и станет умолчанием пака."""
    counted = Counter(values)
    return counted.most_common(1)[0][0] if counted else fallback


# ── Готовность сети ────────────────────────────────────────────────────
#
# Сеть попадает в приложение целиком или не попадает вовсе. Наполовину
# собранная выглядит хуже, чем отсутствующая: человек открывает меню,
# видит блюда без снимков и цифры пятилетней давности вперемешку со
# свежими — и перестаёт верить и тем, и другим. Отсутствие сети он
# объясняет себе сам, а битую карточку объясняет качеством приложения.
#
# **Считаем карточками, а не строками.** Этикетка перечисляет каждое
# сочетание: у Starbucks 3625 строк «напиток × молоко × размер» на 280
# напитков, у Jersey Mike's 1108 строк на 42 блюда. Человек этого не
# видит — приложение схлопывает варианты в одну карточку с
# переключателем. Считать строками значило бы мерить не то, что на
# экране: сеть, снявшая каждое своё блюдо, показывала бы тридцать
# процентов.
#
# **Снимки сеть не держат.** Порог по ним был и снят: карточка без
# фотографии не врёт — она просто беднее, а сеть, спрятанная из-за
# ненайденных снимков, не помогает никому. Держит одна свежесть:
# устаревшая цифра врёт молча, человек считает по ней и не догадывается,
# что она пятилетняя.
#
# Доля снимков по-прежнему считается и показывается — по ней видно, за
# какую сеть браться дальше, — но решения больше не принимает.
#
# **Снимки считаются по блюдам.** Пакетик сахара, помпа сиропа и бутылка
# Pepsi — не блюда: сеть их не снимает и не станет, а человек и так знает,
# как выглядит кола. Им довольно общей картинки по архетипу, поэтому в
# знаменатель порога они не идут (`archetype.needs_own_photo`). Из меню
# они при этом никуда не деваются. Свежесть — наоборот, спрашивается со
# всех: этикетка есть у каждой позиции, включая пакетик сахара.
FRESH_SHARE = 0.90


@dataclass(frozen=True)
class Readiness:
    """Насколько сеть готова показаться человеку."""
    cards: int
    items: int
    photos: float
    fresh: float
    #: Из скольких карточек спрашивается снимок — блюда без добавок и
    #: чужих бутылок. Знаменатель доли `photos`.
    dishes: int = 0

    @property
    def ok(self) -> bool:
        return self.fresh >= FRESH_SHARE

    def __str__(self) -> str:
        return (f"{self.cards:>5} карт. ({self.items:>5} поз.)"
                f"  снимки {self.photos:5.0%} из {self.dishes:>4} блюд"
                f"  свежих {self.fresh:5.0%}")


def readiness(rows) -> dict[str, Readiness]:
    """Готовность каждой сети.

    `rows` — (сеть, ключ карточки, есть снимок, свежая, снята с меню,
    нужен ли ей свой снимок).
    Ключ карточки — группа вариантов, если позиция в ней состоит, иначе
    её собственный ключ: ровно то, что приложение показывает одной
    строкой меню.

    **Снимок у карточки есть, если он есть хоть у одного её варианта** —
    так же выбирает и приложение: `MenuCatalog.representative` ставит
    представителем группы того, у кого фотография, если такой есть.

    **Свежей карточка считается, когда свежи все её варианты**: человек
    переключает размер и видит цифры соседнего, и одна устаревшая строка
    портит карточку целиком.

    Архивные позиции в счёт не идут: у снятого с меню блюда снимка нет и
    не будет, а дата у него старая по определению. Судить по ним
    готовность сети — значит наказывать её за то, что мы честно храним её
    прошлое.
    """
    cards: dict[str, dict[str, list]] = {}
    for chain, card, has_photo, fresh, off_menu, wants_photo in rows:
        if off_menu:
            continue
        state = cards.setdefault(chain, {}).setdefault(card, [0, False, True, False])
        state[0] += 1
        state[1] = state[1] or bool(has_photo)
        state[2] = state[2] and bool(fresh)
        # Карточка — блюдо, если блюдо хоть один её вариант: у «Coke
        # Float» и «Coke Float, Kids» группа общая, и снимок нужен ей.
        state[3] = state[3] or bool(wants_photo)

    out: dict[str, Readiness] = {}
    for chain, by_card in cards.items():
        if not by_card:
            continue
        dishes = [card for card in by_card.values() if card[3]]
        shot = sum(1 for _, has_photo, _, _ in dishes if has_photo)
        fresh = sum(1 for _, _, is_fresh, _ in by_card.values() if is_fresh)
        items = sum(n for n, _, _, _ in by_card.values())
        # Сеть из одних добавок спрашивать не с чего — но и показывать
        # нечего, так что доля единица, а решает свежесть.
        out[chain] = Readiness(len(by_card), items,
                               shot / len(dishes) if dishes else 1.0,
                               fresh / len(by_card), len(dishes))
    return out


def pack_rows(built: dict):
    """Строки готовности из собранного пака — он несёт всё нужное сам."""
    default_stale = bool(built.get("stale", True))
    for item in built["items"]:
        variant = item.get("variant") or {}
        card = variant.get("group") or f'{item["chain"]}:{item["key"]}'
        yield (item["chain"], card, bool(item.get("photo")),
               not bool(item.get("stale", default_stale)),
               bool(item.get("offMenu")),
               needs_own_photo(item["name"]))


def unready(built: dict) -> dict[str, Readiness]:
    """Сети собранного пака, которые показывать нельзя."""
    return {chain: score for chain, score in readiness(pack_rows(built)).items()
            if not score.ok}


def build(items, *, version: int, source: str, observed: str,
          price_tiers: dict[str, int] | None = None) -> dict:
    chains = Counter(i.chain for i in items)
    # Размерные варианты одного блюда склеиваются в группу: приложение
    # покажет их переключателем вместо четырёх карточек колы подряд.
    groups = assign_groups(items)

    sources = [getattr(i, "source", None) or source for i in items]
    observations = [getattr(i, "observed", None) or observed for i in items]
    staleness = [bool(getattr(i, "stale", True)) for i in items]

    pack_source = _mode(sources, source or DEFAULT_SOURCE)
    pack_observed = _mode(observations, observed or DEFAULT_OBSERVED)
    pack_stale = _mode(staleness, True)

    encoded = []
    for item, item_source, item_observed, item_stale in zip(
        items, sources, observations, staleness
    ):
        row = {
            "chain": item.chain,
            "key": item.ext_key,
            "name": item.name,
            "category": item.category,
            # Раздел меню. Считается здесь, а не на клиенте: правило одно на
            # 96 сетей, и ошибку в нём чинит публикация пака.
            "section": section(item.name, item.category),
            "serving": item.serving,
            "kcal": item.kcal,
            "protein": item.protein,
            "carbs": item.carbs,
            "fat": item.fat,
            # Архетип блюда: по нему приложение подбирает снимок. Считается
            # здесь, а не на клиенте, чтобы ошибочно назначенную картинку
            # можно было исправить публикацией пака, без релиза.
            "image": classify(item.name, item.category),
        }
        # Остальная этикетка. Она есть почти везде — источник берёт её из
        # того же обязательного раскрытия, что и калории (21 CFR 101.11), —
        # но приходит не всегда, поэтому только там, где число есть.
        for field, key in (("sugar", "sugar"), ("sat_fat", "satFat"),
                           ("trans_fat", "transFat"),
                           ("cholesterol", "cholesterol"),
                           ("sodium", "sodium"), ("fiber", "fiber")):
            value = getattr(item, field, None)
            if value is not None:
                row[key] = value

        # Пометки позиции: детская порция, на компанию, не во всех точках,
        # сезонное. Едут только там, где есть, — у 86% блюд их нет вовсе.
        if flags := tuple(getattr(item, "flags", ()) or ()):
            row["flags"] = list(flags)

        if variant := groups.get((item.chain, item.ext_key)):
            group, label, order, kind, base = variant
            row["variant"] = {"group": group, "label": label,
                              "order": order, "kind": kind, "base": base}
        # Только отличия от умолчаний пака — иначе пак раздувается втрое.
        if item_source != pack_source:
            row["source"] = item_source
        if item_observed != pack_observed:
            row["observed"] = item_observed
        if item_stale != pack_stale:
            row["stale"] = item_stale
        photo = getattr(item, "photo", None)
        if photo:
            row["photo"] = photo
        if getattr(item, "off_menu", False):
            row["offMenu"] = True
        encoded.append(row)

    # Даты релиза здесь нет намеренно: пак должен байт-в-байт совпадать при
    # пересборке из того же исходника, иначе CI не сможет проверить, что файл
    # в бандле актуален. Дата — свойство манифеста и таблицы releases.
    return {
        "format": PACK_FORMAT,
        "version": version,
        "source": pack_source,
        "observed": pack_observed,
        "stale": pack_stale,
        # Только те разделы, что реально встретились, — в общем порядке.
        "sections": [name for name in SECTION_ORDER
                     if any(row["section"] == name for row in encoded)],
        # Полоса цены — свойство сети, и её проставляют руками: среднего
        # чека по конкретному ресторану нет ни в одном открытом источнике.
        # Сети без полосы едут без поля, а не с нулём: «не знаем» и
        # «бесплатно» — разные вещи.
        "chains": [
            {"name": name, "itemCount": count}
            | ({"priceTier": tier} if (tier := (price_tiers or {}).get(name)) else {})
            for name, count in sorted(chains.items())
        ],
        "items": encoded,
    }


def _raw_deflate(payload: bytes) -> bytes:
    """Сырой DEFLATE, без zlib-обёртки.

    Именно его понимает Data.decompressed(using: .zlib) на стороне iOS:
    у Apple `.zlib` означает raw deflate, а не zlib-контейнер. zlib.compress()
    добавляет двухбайтовый заголовок и adler32 в хвосте — с ними распаковка
    на устройстве падает.
    """
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    return compressor.compress(payload) + compressor.flush()


def write(pack: dict, *, json_path: Path, deflate_path: Path | None = None) -> dict:
    """Пишет пак и возвращает метаданные для манифеста."""
    payload = json.dumps(pack, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_bytes(payload)

    meta = {
        "version": pack["version"],
        "itemCount": len(pack["items"]),
        "releasedAt": date.today().isoformat(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }

    if deflate_path:
        compressed = _raw_deflate(payload)
        deflate_path.parent.mkdir(parents=True, exist_ok=True)
        deflate_path.write_bytes(compressed)
        meta["compressedBytes"] = len(compressed)
        # Манифест проверяет сжатые байты: клиент считает хеш до распаковки.
        meta["compressedSha256"] = hashlib.sha256(compressed).hexdigest()

    return meta


def manifest(meta: dict, *, url: str) -> dict:
    return {
        "format": PACK_FORMAT,
        "version": meta["version"],
        "url": url,
        "sha256": meta.get("compressedSha256", meta["sha256"]),
        "itemCount": meta["itemCount"],
        "releasedAt": meta["releasedAt"],
    }
