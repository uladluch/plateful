"""Разделы меню.

Правило одно на 96 сетей, поэтому ошибка в нём стоит дорого: записать обед
в завтрак — значит спрятать блюдо там, где его не ищут. Пропустить завтрак
дешевле: он останется в своей категории.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.taxonomy import BREAKFAST, SECTION_ORDER, section


class BreakfastTests(unittest.TestCase):
    def test_explicit_words(self):
        for name in ("Big Breakfast", "Egg McMuffin", "Sausage McGriddles",
                     "Hotcakes", "Fruit & Maple Oatmeal", "Hash Browns",
                     "French Toast Sticks", "Eggs Benedict"):
            self.assertEqual(section(name, "Entrees"), BREAKFAST, name)

    def test_carrier_plus_filling(self):
        self.assertEqual(section("Sausage Biscuit", "Sandwiches"), BREAKFAST)
        self.assertEqual(section("Bacon, Egg & Cheese Bagel", "Sandwiches"), BREAKFAST)

    def test_carrier_alone_is_not_breakfast(self):
        # «Bagel» — это и завтрак, и просто выпечка.
        self.assertEqual(section("Blueberry Bagel", "Baked Goods"), "Baked Goods")
        self.assertEqual(section("Bean & Cheese Burrito", "Sandwiches"), "Sandwiches")
        self.assertEqual(section("Biscuit", "Appetizers & Sides"), "Appetizers & Sides")

    def test_generic_carrier_needs_an_egg(self):
        # Мясо на общем носителе — это обед.
        self.assertEqual(section("Bacon Ranch Sandwich", "Sandwiches"), "Sandwiches")
        self.assertEqual(section("Bacon, Egg & Cheese Sandwich", "Sandwiches"), BREAKFAST)

    def test_never_moves_drinks_desserts_or_toppings(self):
        for category in ("Beverages", "Desserts", "Pizza", "Burgers",
                         "Salads", "Soup", "Toppings & Ingredients"):
            self.assertEqual(section("Breakfast Blend Coffee", category), category)

    def test_waffle_is_too_busy_a_word(self):
        # Вафельный рожок, вафельная картошка, вафельный крендель.
        self.assertEqual(section("Waffle Potato Fries", "Fried Potatoes"), "Fried Potatoes")
        self.assertEqual(section("Fresh Baked Waffle Cone", "Desserts"), "Desserts")

    def test_keeps_the_source_category_otherwise(self):
        self.assertEqual(section("Big Mac", "Burgers"), "Burgers")
        self.assertIsNone(section("Mystery Item", None))


class OrderTests(unittest.TestCase):
    def test_mains_first_extras_last(self):
        self.assertEqual(SECTION_ORDER[0], BREAKFAST)
        self.assertLess(SECTION_ORDER.index("Burgers"), SECTION_ORDER.index("Beverages"))
        self.assertEqual(SECTION_ORDER[-1], "Toppings & Ingredients")

    def test_every_source_category_has_a_place(self):
        # Раздел без места в порядке уедет в конец молча.
        source = {"Beverages", "Toppings & Ingredients", "Entrees", "Sandwiches",
                  "Appetizers & Sides", "Pizza", "Desserts", "Baked Goods",
                  "Salads", "Burgers", "Soup", "Fried Potatoes"}
        self.assertTrue(source <= set(SECTION_ORDER), source - set(SECTION_ORDER))


if __name__ == "__main__":
    unittest.main()
