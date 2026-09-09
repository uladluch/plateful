"""Точки McDonald's: локатор сети отдаёт координаты, адрес и часы по дням.

Тот же приём, что и с меню (`adapters/mcdonalds`): обычный запрос сеть
отвергает обрывом TLS — смотрят на отпечаток рукопожатия, — а `curl` с
полным набором браузерных заголовков проходит. Playwright не нужен.

Локатор отвечает на вопрос «что рядом с точкой», а не «покажи всё», и
отдаёт не больше трёхсот заведений за раз. Поэтому обход — сеткой, которая
дробится только там, где упёрлась в потолок: над пустой Невадой хватает
одной клетки, над Лос-Анджелесом их набирается несколько десятков.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass

from .base import BROWSER_HEADERS, Robots, curl_get
from .rbi_venues import Venue, in_us

LOCATOR = "https://www.mcdonalds.com/googleappsv2/geolocation"

#: Сколько заведений локатор отдаёт за один запрос. Больше не отдаёт при
#: любом `maxResults`: на радиусе 100 км вокруг Таймс-сквер приходит ровно
#: триста, и самое дальнее из них — в 36 км, то есть список обрезан по
#: количеству, а не по расстоянию.
CAP = 300

#: Радиус локатора — в километрах: на `radius=25` самое дальнее заведение
#: оказалось ровно в 25.0 км.
KM_PER_DEGREE = 111.32

#: Дальше этого локатор не смотрит, сколько ни проси. Измерено: в Салине
#: (Канзас) запросы с радиусом 50, 100 и 150 возвращают одни и те же пять
#: точек, дальняя из них в 36.0 км, хотя следующий ресторан стоит в сотне.
#:
#: Из-за этого первый обход и недобрал: клетки были по два градуса, то есть
#: по 220 км, а накрывал запрос круг в 36 км вокруг центра — пятую часть
#: клетки. Вышло 2795 точек вместо примерно тринадцати тысяч.
REACH_KM = 35.0

#: Шаг сетки. Круги радиуса R, расставленные по квадратной сетке, покрывают
#: плоскость без дыр, пока шаг не больше R·√2 — иначе остаются просветы
#: между четырьмя соседними кругами.
STEP_KM = REACH_KM * math.sqrt(2)

#: Пауза между запросами — ровно правило проекта, не быстрее секунды.
#: Сетка на семь тысяч клеток идёт около двух часов; полторы секунды
#: растянули бы её за три, а месячный крон и так ходит по ночам.
DELAY = 1.0

#: Клетка мельче этого не дробится. Пять сотых градуса — около пяти
#: километров; если и там триста заведений, лишние потеряются, но такой
#: плотности McDonald's нигде не даёт.
MIN_SPAN = 0.05

DAYS = {"hoursMonday": "mon", "hoursTuesday": "tue", "hoursWednesday": "wed",
        "hoursThursday": "thu", "hoursFriday": "fri", "hoursSaturday": "sat",
        "hoursSunday": "sun"}

#: Признаки берём из `filterType`, а не из полей `driveThru`/`wifi`/
#: `breakFast`: те приходят строкой «0» даже там, где признак заведомо есть
#: — у ресторанов на Таймс-сквер `wifi` равен «0», а в `filterType` у них
#: же стоит WIFI. Одно из двух полей врёт, и это не список.
#:
#: Завтрака в `filterType` нет вовсе, и выводить его из «это McDonald's»
#: мы не будем: признак, который никто не подтверждал, — выдумка.
FILTERS = {"WIFI": "wifi", "DRIVETHRU": "drive_thru", "MCDELIVERY": "delivery",
           "MOBILEORDERS": "mobile_ordering", "INDOORPLAYGROUND": "playground",
           "OUTDOORPLAYGROUND": "playground", "PlayPlacePresence": "playground"}

#: Штаты США вместе с Аляской, Гавайями и Пуэрто-Рико.
#:
#: Аляска обрезана до обжитой южной части: рестораны там стоят в Анкоридже,
#: Фэрбенксе, Джуно, Кетчикане и на трассе между ними, а сетка по всему
#: штату — это тысячи запросов над тундрой ради трёх десятков точек.
BOXES = (
    (24.4, -125.0, 49.4, -66.9),    # континентальные штаты
    (55.0, -166.0, 65.5, -130.0),   # Аляска, обжитая часть
    (18.8, -160.4, 22.4, -154.7),   # Гавайи
    (17.8, -67.4, 18.6, -65.2),     # Пуэрто-Рико
)


@dataclass(frozen=True)
class Cell:
    south: float
    west: float
    north: float
    east: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.south + self.north) / 2, (self.west + self.east) / 2)

    @property
    def radius_km(self) -> float:
        """Радиус круга, накрывающего клетку целиком, — по её диагонали.

        Ширина берётся по тому краю клетки, что ближе к экватору: там
        градус долготы длиннее всего, и клетка шире всего. Взять ширину по
        середине или по дальнему краю значит посчитать круг меньше клетки
        и оставить её углы неопрошенными.
        """
        equatorward = min(abs(self.south), abs(self.north))
        height = (self.north - self.south) * KM_PER_DEGREE
        width = ((self.east - self.west) * KM_PER_DEGREE
                 * math.cos(math.radians(equatorward)))
        return math.hypot(height, width) / 2

    def quarters(self) -> list["Cell"]:
        lat, lng = self.center
        return [Cell(self.south, self.west, lat, lng),
                Cell(self.south, lng, lat, self.east),
                Cell(lat, self.west, self.north, lng),
                Cell(lat, lng, self.north, self.east)]

    @property
    def span(self) -> float:
        return max(self.north - self.south, self.east - self.west)


def hours_of(block: object) -> dict | None:
    """`{"hoursMonday": "06:00 - 04:00"}` → наша форма.

    `00:00 - 00:00` значит круглые сутки, а не «нисколько»: у заведения с
    таким понедельником в тот же день стоит признак TWENTYFOURHOURS, и по
    пятницам оно же пишет `00:00 - 04:00`, когда закрывается.
    """
    if not isinstance(block, dict):
        return None
    week: dict[str, dict] = {}
    for field, day in DAYS.items():
        value = block.get(field)
        if not isinstance(value, str) or "-" not in value:
            continue
        opens, _, closes = (part.strip() for part in value.partition("-"))
        if not (_clock(opens) and _clock(closes)):
            continue
        entry = {"open": opens, "close": closes}
        if opens == closes == "00:00":
            entry["h24"] = True
        week[day] = entry
    return week or None


def _clock(value: str) -> bool:
    parts = value.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return False
    return 0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59


def _store_number(props: dict) -> str | None:
    """Национальный номер магазина — он же ключ обновления.

    Идентификаторов у McDonald's полдюжины (регион, кооператив, телевизионный
    рынок); нужен `NATLSTRNUMBER`, остальные не про конкретную дверь.
    """
    holder = props.get("identifiers") or {}
    for entry in holder.get("storeIdentifier") or []:
        if entry.get("identifierType") == "NATLSTRNUMBER":
            value = str(entry.get("identifierValue") or "").strip()
            if value:
                return value
    return None


def venue(feature: dict) -> Venue | None:
    """Одна точка локатора → наше значение, или `None`, если она бесполезна."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    if len(coords) != 2:
        return None
    lng, lat = coords
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return None
    if not in_us(float(lat), float(lng)):
        return None

    street, city = props.get("addressLine1"), props.get("addressLine3")
    number = _store_number(props)
    if not street or not city or not number:
        return None
    # Закрытая точка хуже ненайденной: человек до неё дойдёт.
    if str(props.get("openstatus", "OPEN")).upper() not in ("OPEN", ""):
        return None

    filters = props.get("filterType") or []
    amenities = {name for flag, name in FILTERS.items() if flag in filters}

    return Venue(
        chain="mcdonald-s",
        ext_key=number,
        latitude=float(lat),
        longitude=float(lng),
        address1=str(street).strip(),
        city=str(city).strip(),
        state=props.get("subDivision") or None,
        postal_code=props.get("postcode") or None,
        country="US",
        phone=str(props["telephone"]).strip() if props.get("telephone") else None,
        hours=hours_of(props.get("restauranthours")),
        # Часы драйв-тру локатор даёт только на сегодня («driveTodayHours»),
        # а неделей — нет. Один день недели в поле, которое читается как
        # расписание, хуже пустого поля.
        drive_thru_hours=None,
        amenities=tuple(sorted(amenities)),
        source="mcdonalds.com/googleappsv2",
    )


def ask(cell: Cell, robots: Robots | None = None) -> list[dict] | None:
    """Один запрос локатора по центру клетки. `None` — сеть не ответила.

    `robots` передаётся всегда, кроме тестов: обход бот-защиты по отпечатку
    TLS не отменяет правил сайта, а проверять их глазами один раз — ровно
    та привычка, из-за которой правило и переехало в код.
    """
    lat, lng = cell.center
    # Просим предел локатора, а не диагональ клетки: больший радиус он
    # молча урезает, а меньший оставил бы углы клетки неопрошенными.
    url = (f"{LOCATOR}?latitude={lat:.4f}&longitude={lng:.4f}"
           f"&radius={int(REACH_KM)}&maxResults={CAP}"
           f"&country=us&language=en-us")
    body = curl_get(url, BROWSER_HEADERS, robots=robots)
    if not body:
        return None
    try:
        return json.loads(body).get("features") or []
    except json.JSONDecodeError:
        return None


def grid(boxes=BOXES) -> list[Cell]:
    """Клетки, каждая из которых целиком помещается в круг запроса.

    Шаг считается в километрах, а не в градусах: градус долготы в Техасе
    короче, чем в Монтане, и одинаковый шаг в градусах оставил бы на севере
    просветы между кругами.
    """
    cells: list[Cell] = []
    for south, west, north, east in boxes:
        lat = south
        while lat < north:
            top = min(lat + STEP_KM / KM_PER_DEGREE, north)
            # Долготный шаг — по тому краю полосы, где градус длиннее, то
            # есть ближе к экватору: иначе клетка окажется шире шага в
            # километрах у противоположного края, и круг её не накроет.
            equatorward = min(abs(lat), abs(top))
            step_lng = STEP_KM / (KM_PER_DEGREE
                                  * max(math.cos(math.radians(equatorward)), 0.05))
            lng = west
            while lng < east:
                cells.append(Cell(lat, lng, top, min(lng + step_lng, east)))
                lng += step_lng
            lat = top
    return cells


def sweep(boxes=BOXES, *, log=print) -> list[Venue]:
    """Все точки сети в США: сетка, которая дробится там, где упёрлась.

    Клетка, вернувшая ровно потолок, почти наверняка обрезана — её делим
    на четыре и спрашиваем заново. Клетка, вернувшая меньше, показала всё,
    что в ней есть.
    """
    found: dict[str, Venue] = {}
    robots = Robots()
    queue: list[Cell] = list(grid(boxes))

    asked = 0
    while queue:
        cell = queue.pop()
        features = ask(cell, robots)
        asked += 1
        time.sleep(DELAY)
        if features is None:
            log(f"  клетка {cell.center} не ответила — пропускаю")
            continue
        for feature in features:
            if row := venue(feature):
                found[row.ext_key] = row
        if len(features) >= CAP and cell.span > MIN_SPAN:
            queue.extend(cell.quarters())
        if asked % 25 == 0:
            log(f"  запросов {asked}, очередь {len(queue)}, точек {len(found)}")

    log(f"  всего запросов {asked}")
    return sorted(found.values(), key=lambda v: v.ext_key)
