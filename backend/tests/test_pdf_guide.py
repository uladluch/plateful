"""Гид по питанию в PDF: разбор и два отказа.

Выдержки настоящие — из `us-nutrition-en.pdf` Subway (январь 2026) и
`Core Menu.pdf` Wendy's с их собственных доменов. Второй оказался
британским, и именно на нём проверяется отказ по стране.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import pdf_guide

# Subway, U.S. NUTRITION INFORMATION, январь 2026.
US = """SANDWICHES
Cheesesteaks
6" Steak Philly 192 510 25 9 1 85 1320 43 2 5 3 28 10 6 90 100
6" Chipotle Philly 198 490 22 9 1 90 1440 44 2 5 4 30 2 6 100 100
6" Grilled Chicken 247 510 24 8 1 85 830 43 3 5 3 31 25 10 100 90
6" Sweet Onion Teriyaki Chicken® 256 430 11 5 0 70 1250 55 4 20 16 29 20 10 10 15
6" Meatball Marinara 239 570 28 12 0 60 1370 53 4 7 4 27 20 15 110 100
Ham & Jack (includes Pepper Jack Cheese)** 71 160 4 2 0 20 550 21 <1 2 2 10 0 0 45 45
"""

# Wendy's, тот же собственный домен — но гид британский: соль в граммах.
UK = """HAMBURGERS & CHICKEN
Dave's Single 524 29 10 37 8.2 1.7 28 2.2
Dave's Double 879 56 22 39 9.7 1.7 54 4.4
Curry Bean Burger 535 25 7 57 9 7 17 2.8
Spicy Chicken 400 15 2.4 45 6.3 2.4 20 2.2
Pain au Chocolat 206 10 6.2 24 7.3 1.6 4.1 0.32
"""

UK_LAYOUT = pdf_guide.Layout(
    columns=("kcal", "fat", "sat_fat", "carbs", "sugar", "fiber", "protein", "sodium"),
    count=8)

# Та же раскладка Subway, но белок и клетчатка поменяны местами.
SHUFFLED = pdf_guide.Layout(
    columns=("serving", "kcal", "fat", "sat_fat", "trans_fat", "cholesterol",
             "sodium", "carbs", "protein", "sugar", None, "fiber",
             None, None, None, None),
    count=16)


class Parsing(unittest.TestCase):

    def test_строка_блюда_разбирается_целиком(self):
        [item] = [i for i in pdf_guide.parse(US, pdf_guide.SUBWAY)
                  if i.name == '6" Steak Philly']
        self.assertEqual(item.values["kcal"], 510)
        self.assertEqual(item.values["trans_fat"], 1)
        self.assertEqual(item.values["cholesterol"], 85)
        self.assertEqual(item.values["sodium"], 1320)
        self.assertEqual(item.values["protein"], 28)

    def test_заголовки_разделов_не_блюда(self):
        names = [i.name for i in pdf_guide.parse(US, pdf_guide.SUBWAY)]
        self.assertNotIn("SANDWICHES", names)
        self.assertNotIn("Cheesesteaks", names)

    def test_проценты_дневной_нормы_не_едут(self):
        """После белка идут витамины и кальций — они не наши."""
        [item] = [i for i in pdf_guide.parse(US, pdf_guide.SUBWAY)
                  if i.name.startswith('6" Sweet Onion')]
        self.assertEqual(set(item.values) & {"vitamin_d", "calcium"}, set())
        self.assertEqual(item.values["protein"], 29)

    def test_меньше_единицы_это_не_ноль_и_не_единица(self):
        """«<1 г клетчатки» схема не хранит, а выдумать середину — соврать."""
        [item] = [i for i in pdf_guide.parse(US, pdf_guide.SUBWAY)
                  if i.name.startswith("Ham & Jack")]
        self.assertIsNone(item.values["fiber"])
        self.assertEqual(item.values["kcal"], 160)

    def test_имя_с_цифрой_и_значком_не_ломает_разбор(self):
        names = [i.name for i in pdf_guide.parse(US, pdf_guide.SUBWAY)]
        self.assertIn('6" Sweet Onion Teriyaki Chicken®', names)


class Refusals(unittest.TestCase):
    """Гид с чужого рынка и съехавшие колонки портят каталог молча."""

    def test_американский_гид_принимается(self):
        items = pdf_guide.read(US, layout=pdf_guide.SUBWAY)
        self.assertEqual(len(items), 6)

    def test_британский_гид_отвергается(self):
        """У Wendy's на своём домене лежит гид с солью в граммах."""
        with self.assertRaises(pdf_guide.WrongGuide) as caught:
            pdf_guide.read(UK, layout=UK_LAYOUT)
        self.assertIn("натрий", str(caught.exception))

    def test_съехавшие_колонки_отвергаются(self):
        with self.assertRaises(pdf_guide.WrongGuide) as caught:
            pdf_guide.read(US, layout=SHUFFLED)
        self.assertIn("колонки", str(caught.exception))

    def test_верная_раскладка_сходится_почти_точно(self):
        """Гид считает калории из тех же макросов, что публикует."""
        import statistics
        drift = pdf_guide.atwater_drift(pdf_guide.parse(US, pdf_guide.SUBWAY))
        self.assertLess(statistics.median(drift), 0.05)


if __name__ == "__main__":
    unittest.main()
