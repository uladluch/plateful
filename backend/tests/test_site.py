"""Общий извлекатель страницы блюда.

Ошибки здесь тихие и дорогие: со страницы уезжает не то число, и его никто
не заметит, пока человек не увидит блюдо на 6 700 205 ккал. Поэтому каждое
правило закреплено, включая то, на котором извлекатель уже ошибся.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.site import (MIN_NUTRIENTS_PER_BLOCK, from_open_graph,
                                         item_links, read_page)


class JsonLdTests(unittest.TestCase):
    """Schema.org сеть кладёт ради поисковиков и потому держит в порядке."""

    PAGE = '''<html><head>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Big Mac",
     "image":"https://example.com/big-mac.png",
     "nutrition":{"@type":"NutritionInformation","calories":"540 cal",
       "proteinContent":"25 g","carbohydrateContent":"46 g","fatContent":"28 g",
       "sugarContent":"9 g","sodiumContent":"950 mg"}}
    </script></head><body></body></html>'''

    def test_reads_name_photo_and_label(self):
        facts = read_page(self.PAGE)
        self.assertEqual(facts.name, "Big Mac")
        self.assertEqual(facts.photo, "https://example.com/big-mac.png")
        self.assertEqual((facts.kcal, facts.protein, facts.carbs, facts.fat),
                         (540.0, 25.0, 46.0, 28.0))
        self.assertEqual((facts.sugar, facts.sodium), (9.0, 950.0))
        self.assertIn("json-ld", facts.shapes)


class EmbeddedJsonTests(unittest.TestCase):
    """Данные для гидратации фронта: у Chick-fil-A это data-wp-context."""

    PAGE = """<div data-wp-context='{"allergens":"Milk, Egg, Soy, Wheat and Sesame",
      "ingredients":"Chicken, peanut oil, malted barley flour",
      "nutrition":[{"key":"calories","label":"Calories","value":420},
                   {"key":"protein","label":"Protein","value":"29g"},
                   {"key":"sugar","label":"Sugars","value":"6g"}]}'></div>"""

    def test_reads_label_allergens_and_ingredients(self):
        facts = read_page(self.PAGE)
        self.assertEqual((facts.kcal, facts.protein, facts.sugar), (420.0, 29.0, 6.0))
        self.assertEqual(facts.allergens, "Milk, Egg, Soy, Wheat and Sesame")
        self.assertIn("malted barley", facts.ingredients)

    def test_ignores_a_lone_nutrient_key(self):
        # На этом извлекатель уже ошибся: во вшитом JSON лежит всё состояние
        # страницы, «calories» встречается не только у еды, и чужой
        # идентификатор проехал как блюдо на 6 700 205 ккал.
        page = """<script id="__NEXT_DATA__" type="application/json">
          {"props":{"tracking":{"calories":"6700205"}}}</script>"""
        self.assertIsNone(read_page(page).kcal)

    def test_rejects_impossible_numbers_and_keeps_the_rest(self):
        page = """<div data-wp-context='{"nutrition":[
            {"key":"calories","value":6700205},{"key":"protein","value":29},
            {"key":"carbs","value":41}]}'></div>"""
        facts = read_page(page)
        self.assertIsNone(facts.kcal)
        self.assertEqual((facts.protein, facts.carbs), (29.0, 41.0))

    def test_a_block_left_with_one_field_is_not_trusted(self):
        # Выбросили невозможное число — и от блока осталось одно поле.
        # Одного мало: настоящая этикетка так не выглядит.
        page = """<div data-wp-context='{"nutrition":[
            {"key":"calories","value":6700205},{"key":"protein","value":29}]}'></div>"""
        self.assertIsNone(read_page(page).protein)

    def test_a_real_block_needs_more_than_one_field(self):
        self.assertGreaterEqual(MIN_NUTRIENTS_PER_BLOCK, 2)


class OpenGraphTests(unittest.TestCase):
    """Имени и снимка хватает, чтобы сверить меню и забрать графику."""

    def test_reads_name_and_photo(self):
        page = ('<meta property="og:title" content="Waffle Fries | Chick-fil-A">'
                '<meta property="og:image" content="https://example.com/fries.png">')
        facts = read_page(page)
        self.assertEqual(facts.name, "Waffle Fries")
        self.assertEqual(facts.photo, "https://example.com/fries.png")

    def test_unescapes_entities(self):
        page = '<meta property="og:title" content="Mac &amp; Cheese">'
        self.assertEqual(read_page(page).name, "Mac & Cheese")


class LadderTests(unittest.TestCase):
    def test_later_extractors_only_fill_gaps(self):
        # JSON-LD надёжнее Open Graph, поэтому имя должно остаться от него.
        page = (JsonLdTests.PAGE
                + '<meta property="og:title" content="Big Mac Meal Deal">'
                + '<meta property="og:image" content="https://example.com/promo.jpg">')
        facts = read_page(page)
        self.assertEqual(facts.name, "Big Mac")
        self.assertEqual(facts.photo, "https://example.com/big-mac.png")

    def test_says_nothing_when_nothing_works(self):
        facts = read_page("<html><body><h1>Menu</h1></body></html>")
        self.assertEqual(facts.shapes, ())
        self.assertFalse(facts.has_nutrition)


class LinkTests(unittest.TestCase):
    def test_keeps_only_menu_links_of_the_same_host(self):
        html = ('<a href="/menu/entrees/sandwich">a</a>'
                '<a href="https://www.example.com/menu/sides/fries">b</a>'
                '<a href="https://twitter.com/example">c</a>'
                '<a href="/careers">d</a>'
                '<a href="/menu">e</a>')
        links = item_links(html, "https://www.example.com/menu")
        self.assertEqual(links, ["https://www.example.com/menu/entrees/sandwich",
                                 "https://www.example.com/menu/sides/fries"])

    def test_drops_duplicates_and_fragments(self):
        html = '<a href="/menu/a">1</a><a href="/menu/a#nutrition">2</a>'
        self.assertEqual(item_links(html, "https://www.example.com/menu"),
                         ["https://www.example.com/menu/a"])



class TitleTail(unittest.TestCase):
    """Хвост заголовка страницы — не часть названия блюда, а дефис в бренде — часть."""

    def test_хвост_после_палки_отрезается(self):
        facts = from_open_graph(
            '<meta property="og:title" content="Mac &amp; Cheese | Chick-fil-A">')
        self.assertEqual(facts.name, "Mac & Cheese")

    def test_дефис_внутри_бренда_не_разделитель(self):
        """«Chick-fil-A® Nuggets» превращалось в «Chick»."""
        facts = from_open_graph(
            '<meta property="og:title" content="Chick-fil-A Nuggets">')
        self.assertEqual(facts.name, "Chick-fil-A Nuggets")

    def test_тире_с_пробелами_отрезается(self):
        facts = from_open_graph(
            '<meta property="og:title" content="Waffle Fries - Chick-fil-A">')
        self.assertEqual(facts.name, "Waffle Fries")


if __name__ == "__main__":
    unittest.main()