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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from plateful_data import matching
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


class PhotoPairs(unittest.TestCase):
    """Снимку правила мягче, чем цифрам: одна фотография на все размеры."""

    CATALOG = {
        "coffee-16": {"ext_key": "coffee-16",
                      "name": "Cafe Blend Light Roast Coffee - 16 fl oz 16 fl oz (473 mL)"},
        "coffee-20": {"ext_key": "coffee-20",
                      "name": "Cafe Blend Light Roast Coffee - 20 fl oz (591 mL)"},
        "roll": {"ext_key": "roll",
                 "name": "Italian Style Roll 2 oz (about 2.5 inch slice / 57g)"},
        "tea": {"ext_key": "tea", "name": "Unsweetened Iced Tea - Serves 4 - Group"},
        "stranger": {"ext_key": "stranger", "name": "Broccoli Cheddar Soup, Bowl"},
    }

    class Shot:
        def __init__(self, slug):
            self.ext_key = slug
            self.name = slug.replace("-", " ")

    def pairs(self, *slugs):
        return matching.photo_pairs([self.Shot(s) for s in slugs], self.CATALOG)

    def test_мера_порции_из_имени_не_мешает(self):
        """«Cafe Blend Light Roast Coffee - 16 fl oz 16 fl oz (473 mL)» —
        это кофе, а не отдельное блюдо с мерой в названии."""
        found = self.pairs("cafe-blend-light-roast-coffee")
        self.assertIn("coffee-16", found)

    def test_один_снимок_достаётся_всем_размерам(self):
        """У блюда четыре строки каталога и одна фотография."""
        found = self.pairs("cafe-blend-light-roast-coffee")
        self.assertEqual({found["coffee-16"].ext_key, found["coffee-20"].ext_key},
                         {"cafe-blend-light-roast-coffee"})

    def test_подача_отбрасывается(self):
        found = self.pairs("unsweetened-iced-tea", "italian-style-roll")
        self.assertIn("tea", found)
        self.assertIn("roll", found)

    def test_чужому_блюду_снимок_не_достаётся(self):
        found = self.pairs("cafe-blend-light-roast-coffee")
        self.assertNotIn("stranger", found)




class NearMiss(unittest.TestCase):
    """Промах на волосок принимается, только если слова укладываются."""

    CATALOG = {
        "muffin": {"ext_key": "muffin", "name": "Muffin - Blueberry"},
        "croissant": {"ext_key": "croissant",
                      "name": "Bacon, Egg & Cheese on Croissant"},
    }

    class Shot:
        def __init__(self, name):
            self.ext_key = name.lower().replace(" ", "-")
            self.name = name

    def test_лишнее_слово_у_сети_не_мешает(self):
        """«Muffin — Blueberry» против «Blueberry Muffin Paradise» — 0.78,
        ниже порога, но все слова каталога лежат в имени сети."""
        found = matching.photo_pairs([self.Shot("Blueberry Muffin Paradise")],
                                     self.CATALOG)
        self.assertIn("muffin", found)

    def test_чужое_блюдо_не_проходит_даже_рядом(self):
        """Одного вхождения мало: «banana» лежит и в хлебе, и в смузи."""
        found = matching.photo_pairs([self.Shot("Banana")], self.CATALOG)
        self.assertEqual(found, {})




class WordsMustAgree(unittest.TestCase):
    """Буквенное сходство пропускает подмену слова — слова её ловят."""

    class Shot:
        def __init__(self, name):
            self.ext_key = name.lower().replace(" ", "-")
            self.name = name

    def pairs(self, catalog_name, *shots):
        return matching.photo_pairs([self.Shot(s) for s in shots],
                                    {"x": {"ext_key": "x", "name": catalog_name}})

    def test_подмена_одного_слова_не_проходит(self):
        """«Farmhouse Egg Sandwich» и «Maplehouse Egg Sandwich» набирают
        0.82 по буквам — и это разные блюда."""
        self.assertEqual(self.pairs("Farmhouse Egg Sandwich", "Maplehouse Egg Sandwich"), {})
        self.assertEqual(self.pairs("Steamed Broccoli", "Seasoned Broccoli"), {})

    def test_форма_слова_проходит(self):
        """Множественное число, ударение, «steak/steakhouse» — одно слово."""
        self.assertIn("x", self.pairs("Nacho Cheese Doritos Locos Taco",
                                      "Nacho Cheese Doritos Locos Tacos"))
        self.assertIn("x", self.pairs("Iced Caffe Americano, Venti", "Iced Caffè Americano"))

    def test_сначала_согласие_по_словам_потом_буквы(self):
        """«Pastry - Chocolate Croissant»: по буквам ближе «chocolate
        croissant straight», но это чужое; годится «chocolate croissant»."""
        found = self.pairs("Pastry - Chocolate Croissant",
                           "Chocolate Croissant Straight", "Chocolate Croissant")
        self.assertEqual(found["x"].name, "Chocolate Croissant")

    def test_двойной_чизбургер_не_одинарный(self):
        """«Double» — не форма подачи, а другое блюдо: при двух снимках
        «Whopper» получает свой, а не «Double Whopper». (Когда у сети
        есть только одинарный, двойной его всё же берёт — лишнее слово
        в каталоге правило прощает намеренно, см. NearMiss.)"""
        found = self.pairs("Whopper", "Double Whopper", "Whopper")
        self.assertEqual(found["x"].name, "Whopper")
        found = self.pairs("Double Whopper", "Double Whopper", "Whopper")
        self.assertEqual(found["x"].name, "Double Whopper")

    def test_из_снимков_с_одним_ключом_берётся_ближайший_по_имени(self):
        """«Brownie» и «Kids Brownie» делят ключ — размер вычищен, — и
        брауни для взрослых должен получить свой снимок, а не детский."""
        found = self.pairs("Brownie", "Kids Brownie", "Brownie")
        self.assertEqual(found["x"].name, "Brownie")

    def test_мера_в_начале_не_съедает_имя(self):
        """От «20oz Bottle Coca-Cola» после вычистки меры должно остаться
        блюдо, а не пустая строка."""
        self.assertEqual(matching.dish("20oz Bottle Coca-Cola®"), "coca cola")
        self.assertEqual(matching.dish("Chocolate Shake (Large)"), "chocolate shake")



class Shortenings(unittest.TestCase):
    """Этикетка перечисляет хлеб и размер, снимок — нет."""

    def test_имя_укорачивается_от_полного_к_блюду(self):
        forms = matching.shortenings("#1 BLT, Seeded Italian Bread, Giant")
        self.assertEqual(forms[0], "blt bread italian seeded")
        self.assertIn("blt", forms)

    def test_хлеб_после_on_отбрасывается(self):
        """MenuStat писал «#1 BLT on White Regular» — хлеб в имени."""
        self.assertIn("blt", matching.shortenings("#1 BLT on White Regular"))

    def test_снимок_блюда_годится_всем_его_размерам(self):
        catalog = {
            "giant": {"ext_key": "giant", "name": "#1 BLT, Wheat Bread, Giant"},
            "mini": {"ext_key": "mini", "name": "#1 BLT, White Bread, Mini"},
            "other": {"ext_key": "other", "name": "Chicken Salad, Regular"},
        }
        class Shot:
            ext_key, name = "blt", "BLT, Giant"
        found = matching.photo_pairs([Shot()], catalog)
        self.assertEqual(set(found), {"giant", "mini"})

    def test_чужому_блюду_укороченное_имя_не_помогает(self):
        catalog = {"club": {"ext_key": "club", "name": "California Club on Wheat Giant"}}
        class Shot:
            ext_key, name = "blt", "BLT, Giant"
        self.assertEqual(matching.photo_pairs([Shot()], catalog), {})




class StarbucksNames(unittest.TestCase):
    """Этикетка называет напиток с молоком и размером, снимок — без."""

    CATALOG = {
        "green": {"ext_key": "green", "name": "Green Tea Latte w/ 2% Milk, Grande"},
        "macch": {"ext_key": "macch", "name": "Latte Macchiato w/ Whole Milk, Tall"},
    }

    class Shot:
        def __init__(self, name):
            self.ext_key, self.name = name.lower(), name

    def test_молоко_и_размер_снимку_не_важны(self):
        found = matching.photo_pairs([self.Shot("Green Tea Latte")], self.CATALOG)
        self.assertIn("green", found)
        self.assertNotIn("macch", found)

    def test_размеры_starbucks_различают_позиции_для_цифр(self):
        """Для этикетки Tall и Venti — разные строки с разными калориями."""
        self.assertNotEqual(matching.portion("Latte, Tall"),
                            matching.portion("Latte, Venti"))


if __name__ == "__main__":
    unittest.main()
