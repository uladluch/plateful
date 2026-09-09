"""Точки сетей RBI: Burger King, Popeyes, Firehouse Subs, Tim Hortons.

Тот же публичный датасет Sanity, из которого берётся меню (`sanity_rbi`), —
в нём рядом с позициями лежит тип `restaurant`: координаты, адрес, телефон,
часы зала и драйв-тру по дням недели и признаки вроде доставки и завтрака.
Одна реализация закрывает четыре сети из пяти, что сегодня едут в паке.

Чего в этом датасете нет — цен. Тип `restaurantPosData` с ценами в центах
существует, но во всём датасете он один и тот пустой: настоящие цены RBI
отдаёт только заказным API по конкретному магазину. Поэтому среднего чека
по точке здесь не будет, и выдумывать его нельзя.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sanity_rbi import Brand, query

#: Дни недели в Sanity: четверг сокращён как `thr`, у нас — `thu`.
DAYS = {"mon": "mon", "tue": "tue", "wed": "wed", "thr": "thu",
        "fri": "fri", "sat": "sat", "sun": "sun"}

#: Признаки заведения: ключ в Sanity → наше имя.
AMENITIES = {
    "hasDriveThru": "drive_thru",
    "hasDelivery": "delivery",
    "hasBreakfast": "breakfast",
    "hasWifi": "wifi",
    "hasMobileOrdering": "mobile_ordering",
    "hasParking": "parking",
    "hasPlayground": "playground",
}

#: Как сети пишут США. Firehouse — «US», Burger King и Popeyes — «USA».
US = ("US", "USA", "United States")

#: Сколько документов забирать за один запрос. Sanity отдаёт и больше, но
#: ответ на шесть тысяч ресторанов — это мегабайты в одной строке.
PAGE = 500


@dataclass(frozen=True)
class Venue:
    """Заведение сети — уже в наших терминах."""
    chain: str
    ext_key: str
    latitude: float
    longitude: float
    address1: str
    city: str
    state: str | None
    postal_code: str | None
    country: str
    phone: str | None
    #: {"mon": {"open": "06:00", "close": "00:00"}} — закрытие раньше
    #: открытия значит «за полночь», это норма, а не ошибка.
    hours: dict | None
    drive_thru_hours: dict | None
    amenities: tuple[str, ...]
    source: str


FIELDS = """{
  _id, number, latitude, longitude, phoneNumber, physicalAddress,
  "dining": diningRoomHours, "drive": driveThruHours,
  hasDriveThru, hasDelivery, hasBreakfast, hasWifi, hasMobileOrdering,
  hasParking, hasPlayground
}"""


def _time(value: object) -> str | None:
    """`1970-01-01 06:00:00` → `06:00`.

    Дата в значении фиктивная — Sanity хранит время суток отдельным полем
    такого вида. Берём часы и минуты, остальное отбрасываем.
    """
    if not isinstance(value, str):
        return None
    parts = value.split(" ")
    if len(parts) != 2 or len(parts[1]) < 5:
        return None
    clock = parts[1][:5]
    hh, _, mm = clock.partition(":")
    if not (hh.isdigit() and mm.isdigit()):
        return None
    if not (0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
        return None
    return clock


def hours_of(block: object) -> dict | None:
    """Часы одной формы: день → открытие, закрытие и круглые сутки.

    Дня без пары «открыто/закрыто» в ответе просто нет — значит в этот день
    заведение закрыто. Так у ресторана на военной базе нет воскресенья.
    """
    if not isinstance(block, dict):
        return None
    week: dict[str, dict] = {}
    for source_day, day in DAYS.items():
        opens = _time(block.get(f"{source_day}Open"))
        closes = _time(block.get(f"{source_day}Close"))
        if opens is None or closes is None:
            continue
        entry = {"open": opens, "close": closes}
        if block.get(f"{source_day}IsOpen24Hours") is True:
            entry["h24"] = True
        week[day] = entry
    return week or None


def venue(doc: dict, brand: Brand) -> Venue | None:
    """Документ Sanity → наше значение, или `None`, если он бесполезен.

    Без координат точку некуда поставить, без адреса — некуда идти; такую
    строку лучше не заводить вовсе, чем показать булавку в океане.
    """
    address = doc.get("physicalAddress") or {}
    lat, lng = doc.get("latitude"), doc.get("longitude")
    street, city = address.get("address1"), address.get("city")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return None
    if not street or not city:
        return None

    key = doc.get("number") or doc.get("_id")
    if not key:
        return None

    amenities = tuple(sorted(name for field, name in AMENITIES.items()
                             if doc.get(field) is True))

    return Venue(
        chain=brand.slug,
        ext_key=str(key),
        latitude=float(lat),
        longitude=float(lng),
        address1=str(street).strip(),
        city=str(city).strip(),
        state=(address.get("stateProvinceShort") or address.get("stateProvince")) or None,
        postal_code=address.get("postalCode") or None,
        country="US",
        phone=str(doc["phoneNumber"]).strip() if doc.get("phoneNumber") else None,
        hours=hours_of(doc.get("dining")),
        drive_thru_hours=hours_of(doc.get("drive")),
        amenities=amenities,
        source=f"sanity:{brand.project}/{brand.dataset}",
    )


def fetch(brand: Brand) -> list[Venue]:
    """Все открытые точки сети в США.

    Страницами по `_id`, а не по смещению: смещение на шести тысячах
    документов Sanity уже не отдаёт, а курсор по идентификатору отдаёт
    всегда и не теряет строк, если во время обхода что-то поменялось.
    """
    countries = ", ".join(f'"{c}"' for c in US)
    where = ('_type == "restaurant" && environment == "prod" && '
             'status == "Open" && physicalAddress.country in [%s]' % countries)

    found: list[Venue] = []
    last = ""
    while True:
        groq = (f'*[{where} && _id > $last] | order(_id asc) '
                f'[0...{PAGE}] {FIELDS}')
        page = query(brand, groq, {"last": last})
        if not isinstance(page, list) or not page:
            break
        for doc in page:
            if isinstance(doc, dict) and (row := venue(doc, brand)):
                found.append(row)
        last = page[-1].get("_id", "")
        if len(page) < PAGE or not last:
            break
    return found
