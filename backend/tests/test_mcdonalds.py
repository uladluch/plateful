"""Снимок McDonald's: разбор без сети и без файла на диске.

Записи настоящие — сняты с калькулятора питания 2026-09-09 и урезаны до
полей, которые мы читаем.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import mcdonalds as m

BIG_MAC = {"id": "200463", "n": "Big Mac", "cat": "Burgers", "g": 217,
           "img": "https://s7d1.scene7.com/is/image/mcdonalds/BigMac_1564x1564",
           "alg": ["wheat", "sesame"], "kcal": 580, "protein": 26, "carbs": 45,
           "fat": 33, "sat_fat": 11, "trans_fat": 1, "cholesterol": 85,
           "sodium": 1050, "sugar": 9, "fiber": 3}
FRIES = {**BIG_MAC, "id": "200066", "n": "Small French Fries", "cat": "McValue®",
         "g": 78, "alg": ["wheat", "milk"], "kcal": 230}
NUGGETS = {**BIG_MAC, "id": "203841", "n": "Spicy Chicken McNuggets (6 piece)",
           "cat": "Spicy Chicken McNuggets®", "g": 108, "alg": [], "kcal": 300}
MEAL = {**BIG_MAC, "id": "200739", "n": "Egg McMuffin Meal", "cat": None,
        "g": None, "kcal": None}
NAMELESS = {**BIG_MAC, "id": "999999", "n": "  ", "kcal": 100}

SECTIONS = {
    "Spicy Chicken McNuggets®": ["203841"],
    "McValue®": ["200066", "200463"],
    "Burgers": ["200463"],
    "McNuggets® & McCrispy® Strips": ["203841"],
    "Fries & Sides": ["200066"],
}


class Load(unittest.TestCase):

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.snapshot = self.dir / "snap.json"
        self.sections = self.dir / "sections.json"
        self.snapshot.write_text(json.dumps(
            [BIG_MAC, FRIES, NUGGETS, MEAL, NAMELESS]), encoding="utf-8")
        self.sections.write_text(json.dumps(SECTIONS), encoding="utf-8")

    def load(self):
        return m.load(self.snapshot, self.sections)

    def test_комбо_без_этикетки_не_заводится(self):
        """У набора этикетка зависит от выбранных стороны и напитка, и
        сеть отдаёт пустой список нутриентов. Позиция без цифр — не позиция."""
        self.assertNotIn("Egg McMuffin Meal", [i.name for i in self.load()])

    def test_безымянное_пропускается(self):
        self.assertEqual(len(self.load()), 3)

    def test_витрина_не_становится_категорией(self):
        """Разделы идут не по важности: «McValue®» и «Spicy Chicken
        McNuggets®» лежат первыми, и по первому попавшемуся у Big Mac
        категорией оказалась бы акция."""
        by = {i.ext_key: i for i in self.load()}
        self.assertEqual(by["big-mac"].category, "Burgers")
        self.assertEqual(by["small-french-fries"].category, "Appetizers & Sides")

    def test_витрина_не_проходит_и_запасным_путём(self):
        """У этой позиции витрина названа главным разделом самой сетью."""
        by = {i.ext_key: i for i in self.load()}
        self.assertEqual(by["spicy-chicken-mcnuggets-6-piece"].category, "Entrees")

    def test_порция_в_граммах(self):
        """Веса сеть не публикует — он считается из значения на сто грамм."""
        by = {i.ext_key: i for i in self.load()}
        self.assertEqual(by["big-mac"].serving, "217 g")

    def test_аллергены_в_девятке_fda(self):
        by = {i.ext_key: i for i in self.load()}
        self.assertEqual(by["big-mac"].allergens, ("wheat", "sesame"))
        self.assertEqual(by["spicy-chicken-mcnuggets-6-piece"].allergens, ())

    def test_этикетка_в_наших_терминах(self):
        by = {i.ext_key: i for i in self.load()}
        big = by["big-mac"]
        self.assertEqual((big.kcal, big.protein, big.carbs, big.fat), (580, 26, 45, 33))
        self.assertEqual((big.trans_fat, big.cholesterol, big.fiber), (1, 85, 3))

    def test_без_разделов_остаётся_то_что_назвала_сеть(self):
        """Файл разделов необязателен: без него берётся главный раздел
        позиции — кроме витрин, которые и там не годятся."""
        by = {i.ext_key: i for i in m.load(self.snapshot, self.dir / "нет.json")}
        self.assertEqual(by["big-mac"].category, "Burgers")
        self.assertIsNone(by["spicy-chicken-mcnuggets-6-piece"].category)

    def test_без_снимка_объясняет_как_его_снять(self):
        with self.assertRaises(SystemExit) as caught:
            m.load(self.dir / "нет.json", self.sections)
        self.assertIn("collect/mcdonalds.js", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
