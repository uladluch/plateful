"""Точки McDonald's: разбор ответа локатора и сетка обхода.

Без сети: правила разбора наши, а поход в локатор сделал бы тест зависимым
от того, сколько ресторанов сегодня открыто в Нью-Джерси.
"""
import unittest

from plateful_data.adapters import mcdonalds_venues as mv


def feature(**props):
    base = {
        "addressLine1": "428 Grand St", "addressLine3": "Jersey City",
        "subDivision": "NJ", "postcode": "07303", "telephone": "(551) 529-4053",
        "openstatus": "OPEN",
        "filterType": ["WIFI", "MOBILEORDERS", "MCDELIVERY"],
        "identifiers": {"storeIdentifier": [
            {"identifierType": "Region ID", "identifierValue": "30"},
            {"identifierType": "NATLSTRNUMBER", "identifierValue": "10074"},
        ]},
        "restauranthours": {"hoursMonday": "05:00 - 00:00"},
    }
    base.update(props)
    return {"geometry": {"coordinates": [-74.05, 40.71]}, "properties": base}


class HoursTest(unittest.TestCase):

    def test_reads_range(self):
        week = mv.hours_of({"hoursMonday": "05:00 - 00:00"})
        self.assertEqual(week, {"mon": {"open": "05:00", "close": "00:00"}})

    def test_keeps_closing_after_midnight(self):
        # Закрывается в четыре утра следующего дня — так и записываем.
        week = mv.hours_of({"hoursThursday": "06:00 - 04:00"})
        self.assertEqual(week["thu"], {"open": "06:00", "close": "04:00"})

    def test_midnight_to_midnight_is_round_the_clock(self):
        # У того же заведения по пятницам стоит «00:00 - 04:00», значит
        # «00:00 - 00:00» — это сутки напролёт, а не нисколько.
        week = mv.hours_of({"hoursFriday": "00:00 - 00:00"})
        self.assertTrue(week["fri"]["h24"])

    def test_drops_unreadable_day(self):
        week = mv.hours_of({"hoursMonday": "Closed",
                            "hoursTuesday": "25:00 - 03:00",
                            "hoursWednesday": "08:00 - 20:00"})
        self.assertEqual(list(week), ["wed"])

    def test_no_hours_at_all(self):
        self.assertIsNone(mv.hours_of({}))
        self.assertIsNone(mv.hours_of(None))


class VenueTest(unittest.TestCase):

    def test_takes_national_store_number(self):
        # Идентификаторов полдюжины: регион, кооператив, телевизионный
        # рынок. Дверь различает только NATLSTRNUMBER.
        v = mv.venue(feature())
        self.assertEqual(v.ext_key, "10074")
        self.assertEqual(v.chain, "mcdonald-s")
        self.assertEqual((v.latitude, v.longitude), (40.71, -74.05))

    def test_amenities_come_from_filters(self):
        # Поля `wifi`/`driveThru` приходят строкой «0» даже там, где
        # признак есть; верим списку.
        v = mv.venue(feature(wifi="0", driveThru="0"))
        self.assertEqual(v.amenities, ("delivery", "mobile_ordering", "wifi"))

    def test_closed_restaurant_is_dropped(self):
        self.assertIsNone(mv.venue(feature(openstatus="CLOSED")))

    def test_without_store_number_is_dropped(self):
        self.assertIsNone(mv.venue(feature(identifiers={})))

    def test_without_coordinates_is_dropped(self):
        broken = feature()
        broken["geometry"] = {"coordinates": []}
        self.assertIsNone(mv.venue(broken))

    def test_drive_thru_hours_stay_empty(self):
        # Локатор даёт часы драйв-тру только на сегодня; один день в поле,
        # которое читается как расписание, хуже пустого поля.
        self.assertIsNone(mv.venue(feature(driveTodayHours="06:00 - 23:00"))
                          .drive_thru_hours)


class CellTest(unittest.TestCase):

    def test_quarters_cover_the_cell(self):
        cell = mv.Cell(40.0, -74.0, 42.0, -72.0)
        quarters = cell.quarters()
        self.assertEqual(len(quarters), 4)
        self.assertEqual(min(q.south for q in quarters), 40.0)
        self.assertEqual(max(q.north for q in quarters), 42.0)
        self.assertEqual(min(q.west for q in quarters), -74.0)
        self.assertEqual(max(q.east for q in quarters), -72.0)

    def test_radius_covers_the_corner(self):
        # Радиус берётся по диагонали: круг меньше клетки оставил бы углы
        # неопрошенными, и точки в них потерялись бы молча.
        cell = mv.Cell(40.0, -74.0, 42.0, -72.0)
        height_km = 2 * mv.KM_PER_DEGREE
        self.assertGreater(cell.radius_km, height_km / 2)

    def test_quarters_shrink(self):
        cell = mv.Cell(40.0, -74.0, 42.0, -72.0)
        self.assertEqual(cell.span, 2.0)
        self.assertEqual(cell.quarters()[0].span, 1.0)


if __name__ == "__main__":
    unittest.main()
