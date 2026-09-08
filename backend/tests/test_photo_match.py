"""Сопоставление снимков сети с позициями каталога.

Ошибка здесь тихая и дорогая: у блюда появляется чужая фотография, и
заметить это можно только глазами. Поэтому каждое правило закреплено на
настоящих названиях с сайта McDonald's, включая те, на которых матчер
уже ошибался.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_chain_photos import (PHOTO_THRESHOLD, containment, ingredients_agree,
                                photo_score, photo_words)


def matches(catalog: str, tile: str) -> bool:
    return photo_score(catalog, tile) > 0


class PhotoWordsTests(unittest.TestCase):
    def test_strips_framing_from_tiles(self):
        # Ракурс и подача — свойства кадра, а не блюда.
        self.assertEqual(photo_words("Filet O Fish Half Slice Protein", True),
                         ["filet", "fish"])
        self.assertEqual(photo_words("Small French Fries Standing", True),
                         ["french", "fries"])

    def test_keeps_framing_words_in_catalog_names(self):
        # Мусорный список — про имена файлов на сайте; каталог им не чистим.
        self.assertIn("half", photo_words("Half Rack Ribs"))

    def test_drops_one_letter_scraps(self):
        # «w» из «w/ Cheese» — не слово, а обломок пунктуации, и в проверке
        # вхождения он находится в любой строке.
        self.assertEqual(photo_words("Sausage Biscuit w/ Egg"),
                         ["sausage", "biscuit", "egg"])


class IngredientsTests(unittest.TestCase):
    def test_separates_different_sandwiches(self):
        self.assertFalse(ingredients_agree("Steak, Egg & Cheese Biscuit",
                                           "Egg Cheese Biscuit"))
        self.assertFalse(ingredients_agree("Sausage McMuffin", "Sausage Egg Mc Muffin"))
        self.assertFalse(ingredients_agree("Hamburger", "Cheeseburger Alt Protein"))

    def test_nuggets_imply_chicken(self):
        # Сайт подписывает плитку «10 Mc Nuggets», каталог — «10 Chicken
        # McNuggets»; наггетсы куриные, различитель не должен их разводить.
        self.assertTrue(ingredients_agree("10 Chicken McNuggets", "4 Mc Nuggets Stacked"))
        self.assertFalse(ingredients_agree("10 Chicken McNuggets", "10 Spicy Mc Nuggets"))


class ContainmentTests(unittest.TestCase):
    def test_matches_longer_and_shorter_names(self):
        self.assertTrue(matches("Dasani Water", "Dasani Bottled Water"))
        self.assertTrue(matches("1% Low Fat Milk Jug", "Milk Jug"))
        self.assertTrue(matches("10 Chicken McNuggets", "4 Mc Nuggets Stacked"))

    def test_word_order_is_required(self):
        # На этом матчер уже ошибся: «mc» и «chicken» лежат в названии
        # наггетсов оба, но в другом порядке, и «McChicken» забирал их плитку.
        self.assertEqual(containment("10 Chicken McNuggets", "Mc Chicken"), 0.0)

    def test_ignores_a_name_swallowed_by_a_longer_one(self):
        # «Sprite» целиком лежит внутри «Sprite Berry Blast», но это другой
        # напиток: слишком мало общего, чтобы считать вхождение совпадением.
        self.assertEqual(containment("Sprite", "Medium Sprite Berry Blast"), 0.0)


class ScoreTests(unittest.TestCase):
    def test_exact_name_beats_containment(self):
        # «Sweet Tea» лежит внутри «Unsweet Tea», но своя плитка у неё есть,
        # и выиграть должна она.
        own = photo_score("Sweet Tea, Large", "Sweet Tea")
        other = photo_score("Sweet Tea, Large", "Unsweet Tea")
        self.assertGreaterEqual(own, PHOTO_THRESHOLD)
        self.assertGreater(own, other)

    def test_refuses_a_dish_the_site_does_not_show(self):
        tiles = ["Double Cheeseburgerv 2", "Cheeseburger Alt Protein", "Hamburger"]
        self.assertTrue(all(not matches("Triple Cheeseburger", t) for t in tiles))

    def test_refuses_a_lookalike_sandwich(self):
        self.assertFalse(matches("Steak, Egg & Cheese Biscuit", "Steak Egg Cheese Bagel"))

    def test_matches_camel_case_from_a_filename(self):
        # «McDouble» в каталоге слитно, из имени файла разбор даёт «Mc Double».
        self.assertTrue(matches("McDouble", "Mc Double Protein"))


if __name__ == "__main__":
    unittest.main()
