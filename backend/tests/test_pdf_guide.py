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

# Subway, U.S. NUTRITION INFORMATION, январь 2026. Два уровня заголовков:
# капсом — формат подачи, обычным регистром — группа блюд внутри него.
US = """SANDWICHES
Cheesesteaks
6" Steak Philly 192 510 25 9 1 85 1320 43 2 5 3 28 10 6 90 100
6" Chipotle Philly 198 490 22 9 1 90 1440 44 2 5 4 30 2 6 100 100
6" Grilled Chicken 247 510 24 8 1 85 830 43 3 5 3 31 25 10 100 90
6" Sweet Onion Teriyaki Chicken® 256 430 11 5 0 70 1250 55 4 20 16 29 20 10 10 15
6" Meatball Marinara 239 570 28 12 0 60 1370 53 4 7 4 27 20 15 110 100
Ham & Jack (includes Pepper Jack Cheese)** 71 160 4 2 0 20 550 21 <1 2 2 10 0 0 45 45
WRAPS
Wraps Values include 12" wrap, cheese, select fresh vegetables and footlong meat portions
Cheesesteaks
Steak Philly 253 710 39 12 1 120 1880 55 3 6 4 44 15 8 45 45
Local Favorites **
Turkey & Ham ** 309 620 28 8 1 85 1700 55 3 7 4 37 20 6 20 30
Protein Pockets Values include 9" wrap (pocket), cheese, select fresh vegetables
Turkey & Ham 193 320 11 4 0 50 1260 32 2 4 3 21 10 4 15 20
SALADS
Cheesesteaks
Steak Philly 400 450 33 9 1 65 930 12 4 6 1 21 80 35 20 15
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
        self.assertEqual(len(items), 10)

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


class Ambiguity(unittest.TestCase):
    """Одно название — несколько блюд.

    «Steak Philly» у Subway есть сэндвичем, обёрткой и салатом, с разными
    числами. Ключ позиции считается из имени, поэтому без различения два
    из трёх молча потерялись бы — что и случилось на первом прогоне:
    завести собирались 162 позиции, доехало 114.
    """

    def test_одно_имя_в_разных_форматах_это_разные_блюда(self):
        items = pdf_guide.read(US, layout=pdf_guide.SUBWAY)
        philly = sorted(i.name for i in items if "Steak Philly" in i.name)

        self.assertEqual(philly, ['6" Steak Philly', "Steak Philly, Salads",
                                  "Steak Philly, Wraps"])

    def test_ключи_позиций_уникальны(self):
        from plateful_data.slug import slugify
        items = pdf_guide.read(US, layout=pdf_guide.SUBWAY)
        keys = [slugify(i.name) for i in items]

        self.assertEqual(len(keys), len(set(keys)))

    def test_группа_отделяется_от_пояснения(self):
        """«Protein Pockets Values include 9" wrap…» — имя и пояснение
        в одной строке. Пока строка отбрасывалась за длину, обёртка и
        карман попадали в одну группу и становились неразличимы."""
        items = pdf_guide.read(US, layout=pdf_guide.SUBWAY)
        pockets = [i for i in items if i.category == "Protein Pockets"]

        self.assertEqual(len(pockets), 1)
        self.assertEqual(pockets[0].values["kcal"], 320)

    def test_внешний_раздел_читается_капсом(self):
        items = pdf_guide.parse(US, pdf_guide.SUBWAY)
        self.assertEqual({i.section for i in items}, {"SANDWICHES", "WRAPS", "SALADS"})

    def test_сноска_не_часть_названия(self):
        """«**» значит «не во всех точках» — факт о доступности, не имя."""
        items = pdf_guide.read(US, layout=pdf_guide.SUBWAY)
        self.assertFalse([i.name for i in items if i.name.endswith("*")])

    def test_неразличимое_отвергается_а_не_теряется(self):
        """Две строки, которые нечем развести, — отказ, а не тихая потеря."""
        same = """WRAPS
Cheesesteaks
Steak Philly 253 710 39 12 1 120 1880 55 3 6 4 44 15 8 45 45
Steak Philly 260 720 40 12 1 120 1900 56 3 6 4 45 15 8 45 45
"""
        with self.assertRaises(pdf_guide.WrongGuide) as caught:
            pdf_guide.read(same, layout=pdf_guide.SUBWAY)
        self.assertIn("неразличимые", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
