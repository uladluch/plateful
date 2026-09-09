"""Sanity-адаптер RBI: разбор без сети.

Сеть подменяется целиком: `fetch` и `on_menu_ids` ходят через `query`,
а `query` здесь возвращает заготовленные документы. Ответы настоящие —
сняты с `prod_bk_us` 2026-09-09 и урезаны до полей, которые мы читаем.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import sanity_rbi as s

COOKIE = {
    "_id": "604676c0", "name": "Two Chocolate Chip Cookies", "region": "US",
    "dummy": None, "L2": "DESSERTS", "L3": "COOKIES",
    "image": "image-9532a9347bdd321b0f4ef1d2a08ca68c9ac2eceb-1333x1333-png",
    "nutrition": {"calories": 320, "carbohydrates": 46, "cholesterol": 20,
                  "fat": 15, "fiber": 2, "proteins": 4, "saturatedFat": 8,
                  "sodium": 220, "sugar": 28, "transFat": 0, "salt": None},
    "allergens": {"milk": 1, "wheat": 1, "eggs": 0, "soy": 1, "gluten": 0},
}
TEST_ITEM = {**COOKIE, "_id": "t1", "name": "16 Pc. Chicken Nuggets - PDP Test"}
DUMMY = {**COOKIE, "_id": "d1", "name": "Dummy Item for Coupon", "dummy": True}
CANADA = {**COOKIE, "_id": "c1", "name": "Poutine", "region": "CA"}
TWIN = {**COOKIE, "_id": "twin", "name": "Two Chocolate Chip Cookies"}
APOSTROPHE = {**COOKIE, "_id": "ap1", "name": "Small Barq's Root Beer"}
NO_APOSTROPHE = {**COOKIE, "_id": "ap2", "name": "Small Barqs Root Beer"}
RETIRED = {**COOKIE, "_id": "old1", "name": "Ch'King Sandwich"}

# Ответ обхода: на каждом уровне только `t`/`id` — прямая ссылка или через
# `option`, GROQ это уже склеил. У Firehouse позиция лежит на пятом уровне:
# раздел → пикер → комбо → слот комбо → позиция.
MENU = {"sections": [
    {"name": "Sweets", "opts": [
        {"t": "item", "id": "604676c0"},
        {"t": "item", "id": "ap1"},
        {"t": "item", "id": "ap2"},
        {"t": "picker", "id": "p1", "opts": [
            {"t": "item", "id": "twin"},
            {"t": "combo", "id": "combo1", "opts": [
                {"t": "comboSlot", "id": "slot1", "opts": [
                    {"t": "item", "id": "t1"}]}]}]}]},
    {"name": "Empty", "opts": None},
]}


def fake_query(brand, groq, params=None):
    if "_id == $menu" in groq:
        return MENU
    return [COOKIE, TEST_ITEM, DUMMY, CANADA, TWIN, RETIRED, APOSTROPHE, NO_APOSTROPHE]


class ImageUrl(unittest.TestCase):

    def test_ссылка_на_ассет_превращается_в_адрес_cdn(self):
        url = s.image_url("kjfd81ul", "prod_bk_us", COOKIE["image"])
        self.assertTrue(url.startswith(
            "https://cdn.sanity.io/images/kjfd81ul/prod_bk_us/"
            "9532a9347bdd321b0f4ef1d2a08ca68c9ac2eceb-1333x1333.png"))
        # CDN режет под нас: исходный PNG весит 400 КБ, webp — 30.
        self.assertIn("fm=webp", url)

    def test_нет_ссылки_нет_адреса(self):
        self.assertIsNone(s.image_url("p", "d", None))
        self.assertIsNone(s.image_url("p", "d", "garbage"))


@mock.patch.object(s, "query", side_effect=fake_query)
class Fetch(unittest.TestCase):

    def test_живое_меню_обходится_на_всю_глубину(self, _):
        """Раздел → пикер → комбо → слот комбо → позиция. Пока уровень
        понимал только прямую ссылку, слоты комбо обрывали обход, и живое
        меню Firehouse выглядело как 72 позиции при 753 настоящих."""
        self.assertEqual(s.on_menu_ids(s.BURGER_KING), {"604676c0", "twin", "t1", "ap1", "ap2"})

    def test_запрос_принимает_оба_вида_ссылки_на_каждом_уровне(self, _):
        """Прямая `->` и завёрнутая `option->` — одним `coalesce`."""
        self.assertIn("coalesce(@->_id, option->_id)", s.MENU_QUERY)
        self.assertGreaterEqual(s.MENU_QUERY.count('"opts"'), 5)

    def test_берётся_только_то_что_в_меню(self, _):
        names = {i.name for i in s.fetch(s.BURGER_KING)}
        self.assertNotIn("Ch'King Sandwich", names)

    def test_тест_и_заглушка_отсеиваются(self, _):
        """Датасет хранит всё, что сеть когда-либо вводила."""
        names = {i.name for i in s.fetch(s.BURGER_KING)}
        self.assertNotIn("16 Pc. Chicken Nuggets - PDP Test", names)
        self.assertNotIn("Dummy Item for Coupon", names)

    def test_чужой_регион_отсеивается(self, _):
        names = {i.name for i in s.fetch(s.BURGER_KING, only_on_menu=False)}
        self.assertNotIn("Poutine", names)

    def test_двойник_для_другой_кассы_не_дублируется(self, _):
        """Один бургер лежит под двумя документами — для разных касс."""
        names = [i.name for i in s.fetch(s.BURGER_KING)]
        self.assertEqual(names.count("Two Chocolate Chip Cookies"), 1)

    def test_двойники_с_апострофом_и_без_это_одно_имя(self, _):
        """«Barq's» и «Barqs» — один напиток. Для slug апостроф значим,
        и двойники расходились ключами: один занимал строку каталога,
        второй шёл заводиться под занятый ключ, и кроул отказывался."""
        names = [i.name for i in s.fetch(s.BURGER_KING) if "barq" in i.name.lower()]
        self.assertEqual(len(names), 1)

    @staticmethod
    def _cookie():
        [cookie] = [i for i in s.fetch(s.BURGER_KING) if "Cookie" in i.name]
        return cookie

    def test_этикетка_в_наших_терминах(self, _):
        cookie = self._cookie()
        self.assertEqual(cookie.kcal, 320)
        self.assertEqual(cookie.protein, 4)
        self.assertEqual(cookie.sat_fat, 8)
        self.assertEqual(cookie.trans_fat, 0)
        self.assertEqual(cookie.cholesterol, 20)

    def test_аллергены_только_отмеченные(self, _):
        cookie = self._cookie()
        self.assertEqual(cookie.allergens, ("milk", "wheat", "soy"))

    def test_категория_из_иерархии_продукта(self, _):
        cookie = self._cookie()
        self.assertEqual(cookie.category, "Desserts")
        self.assertEqual(cookie.ext_key, "two-chocolate-chip-cookies")


if __name__ == "__main__":
    unittest.main()
