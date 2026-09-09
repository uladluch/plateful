"""Точки сетей RBI: разбор часов и адреса.

Без сети: правила разбора — наши, а поход в Sanity сделал бы тест зависимым
от того, что сегодня открыто в Техасе.
"""
import unittest

from plateful_data.adapters import rbi_venues, sanity_rbi


def hours(**kw):
    """Блок часов в том виде, в каком его отдаёт Sanity."""
    return {"_type": "hoursOfOperation", **kw}


class TimeTest(unittest.TestCase):

    def test_takes_clock_from_fake_date(self):
        # Дата в значении фиктивная, время суток настоящее.
        self.assertEqual(rbi_venues._time("1970-01-01 06:00:00"), "06:00")
        self.assertEqual(rbi_venues._time("1970-01-01 23:59:00.0000000"), "23:59")

    def test_rejects_nonsense(self):
        for value in (None, "", "1970-01-01", "не время", 6, "1970-01-01 25:00:00"):
            self.assertIsNone(rbi_venues._time(value), value)


class HoursTest(unittest.TestCase):

    def test_renames_thursday(self):
        # В Sanity четверг — `thr`, у нас `thu`. Разошлись бы — четверга
        # не было бы ни у одного заведения.
        week = rbi_venues.hours_of(hours(thrOpen="1970-01-01 10:00:00",
                                         thrClose="1970-01-01 22:00:00"))
        self.assertEqual(week, {"thu": {"open": "10:00", "close": "22:00"}})

    def test_keeps_closing_after_midnight(self):
        # Открыто с 6 утра до часу ночи. Закрытие раньше открытия — норма,
        # «чинить» перестановкой нельзя: получится ресторан на час в сутки.
        week = rbi_venues.hours_of(hours(monOpen="1970-01-01 06:00:00",
                                         monClose="1970-01-01 01:00:00"))
        self.assertEqual(week["mon"], {"open": "06:00", "close": "01:00"})

    def test_marks_round_the_clock(self):
        week = rbi_venues.hours_of(hours(monOpen="1970-01-01 00:00:00",
                                         monClose="1970-01-01 23:59:00",
                                         monIsOpen24Hours=True))
        self.assertTrue(week["mon"]["h24"])

    def test_day_without_pair_is_closed(self):
        # У ресторана на военной базе в ответе просто нет воскресенья.
        week = rbi_venues.hours_of(hours(monOpen="1970-01-01 06:00:00",
                                         monClose="1970-01-01 22:00:00",
                                         sunOpen="1970-01-01 06:00:00"))
        self.assertEqual(list(week), ["mon"])

    def test_empty_block_is_none(self):
        self.assertIsNone(rbi_venues.hours_of(hours()))
        self.assertIsNone(rbi_venues.hours_of(None))


class VenueTest(unittest.TestCase):

    brand = sanity_rbi.FIREHOUSE

    def doc(self, **kw):
        base = {
            "_id": "abc", "number": "1911",
            "latitude": 31.12, "longitude": -97.42,
            "phoneNumber": "(254) 228-5527",
            "physicalAddress": {"address1": "145 Westfield Blvd.", "city": "Temple",
                                "stateProvince": "Texas", "stateProvinceShort": "TX",
                                "postalCode": "76502", "country": "US"},
        }
        base.update(kw)
        return base

    def test_reads_address_and_number(self):
        v = rbi_venues.venue(self.doc(), self.brand)
        self.assertEqual(v.ext_key, "1911")
        self.assertEqual((v.city, v.state, v.postal_code), ("Temple", "TX", "76502"))
        self.assertEqual(v.chain, "firehouse-subs")

    def test_falls_back_to_long_state(self):
        v = rbi_venues.venue(self.doc(physicalAddress={
            "address1": "1 Main St", "city": "Temple", "stateProvince": "Texas"}),
            self.brand)
        self.assertEqual(v.state, "Texas")

    def test_without_coordinates_is_dropped(self):
        # Булавку некуда ставить — такой строки лучше не заводить вовсе.
        self.assertIsNone(rbi_venues.venue(self.doc(latitude=None), self.brand))
        self.assertIsNone(rbi_venues.venue(self.doc(longitude="—"), self.brand))

    def test_without_street_is_dropped(self):
        self.assertIsNone(rbi_venues.venue(
            self.doc(physicalAddress={"city": "Temple"}), self.brand))

    def test_antarctica_is_dropped(self):
        # Настоящая строка из датасета Firehouse: страна «US», штат «GL»,
        # город в Гренландии и координата посреди Антарктиды. Она доехала
        # до базы и встала бы на карте во льдах.
        self.assertIsNone(rbi_venues.venue(self.doc(
            latitude=-82.862752, longitude=135,
            physicalAddress={"address1": "283P+JVV,", "city": "Narsarmijit",
                             "stateProvinceShort": "GL", "country": "US"}),
            self.brand))

    def test_keeps_the_far_corners_of_the_country(self):
        # Граница не должна отрезать настоящие штаты: Аляска, Гавайи и
        # Пуэрто-Рико лежат далеко от континентальной середины.
        for lat, lng in ((61.2, -149.9), (21.3, -157.8), (18.4, -66.1)):
            self.assertTrue(rbi_venues.in_us(lat, lng), (lat, lng))

    def test_falls_back_to_document_id(self):
        v = rbi_venues.venue(self.doc(number=None), self.brand)
        self.assertEqual(v.ext_key, "abc")

    def test_collects_only_true_amenities(self):
        v = rbi_venues.venue(self.doc(hasDelivery=True, hasWifi=True,
                                      hasDriveThru=False, hasParking=None),
                             self.brand)
        self.assertEqual(v.amenities, ("delivery", "wifi"))


if __name__ == "__main__":
    unittest.main()
