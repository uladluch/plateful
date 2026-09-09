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


# Panera Bread® Nutrition Guide: порция стоит словами в названии, а имя
# блюда порой переносится на предыдущую строку.
PANERA_TEXT = """SOUPS
Broccoli Cheddar - Cup 1 Cup 280 180 20 13 1.5 60 1010 17 1 6 8 0
Broccoli Cheddar - Cup 1 Cup 280 180 20 13 1.5 60 1010 17 1 6 8 0
Sesame Ginger Chicken Market Bowl
1 Bowl 930 280 38 8 0 105 3200 96 12 22 38 0
1/2 Bowl 470 140 19 4 0 55 1600 48 6 11 19 0
"""


class TextualServing(unittest.TestCase):
    """Гид Panera устроен иначе, чем Subway, и на нём ломались две вещи."""

    def test_порция_словами_отделяется_от_имени(self):
        items = pdf_guide.parse(PANERA_TEXT, pdf_guide.PANERA)
        cup = next(i for i in items if i.name.startswith("Broccoli"))

        self.assertEqual(cup.name, "Broccoli Cheddar - Cup")
        self.assertEqual(cup.serving, "1 Cup")

    def test_перенесённое_имя_берётся_со_строки_выше(self):
        """В строке осталась одна порция — «1 Bowl». Половинка и целый
        боул назывались бы «1/2 Bowl» и «1 Bowl» вместо своих имён."""
        items = pdf_guide.parse(PANERA_TEXT, pdf_guide.PANERA)
        bowls = [i for i in items if "Sesame Ginger" in i.name]

        self.assertEqual(len(bowls), 2)
        self.assertEqual({i.serving for i in bowls}, {"1 Bowl", "1/2 Bowl"})

    def test_точный_повтор_строки_снимается(self):
        """Страница 30 гида печатает часть таблицы дважды, символ в символ."""
        items = pdf_guide.dedupe(pdf_guide.parse(PANERA_TEXT, pdf_guide.PANERA))
        cups = [i for i in items if i.name == "Broccoli Cheddar - Cup"]

        self.assertEqual(len(cups), 1)

    def test_повтор_с_разными_числами_не_снимается(self):
        """Одинаковое имя при разных числах — два блюда, а не дубль."""
        text = """SOUPS
Broccoli Cheddar - Cup 1 Cup 280 180 20 13 1.5 60 1010 17 1 6 8 0
Broccoli Cheddar - Cup 1 Cup 420 280 31 19 2.5 90 1520 25 1 9 12 0
"""
        items = pdf_guide.dedupe(pdf_guide.parse(text, pdf_guide.PANERA))

        self.assertEqual(len(items), 2)



class Description(unittest.TestCase):
    """Состав блюда в хвосте названия — не часть названия."""

    def test_состав_после_тире_отрезается(self):
        """Quiznos пишет «Classic Italian - with capicola, salami, ham…»,
        и без этого в имя уезжала половина состава: позиция становилась
        неузнаваемой, и весь каталог сети уходил в архив как непойманный."""
        self.assertEqual(
            pdf_guide.without_description(
                "Classic Italian - with capicola, salami, ham, provolone cheese."),
            "Classic Italian")

    def test_имя_с_тире_целое(self):
        """Отличаем состав от имени по регистру: имя сеть пишет с
        прописной. Иначе «Bacon - Egg & Cheese» теряет половину."""
        for name in ("Bacon - Egg & Cheese", "Chick-fil-A® Nuggets",
                     "Turkey Ranch & Swiss"):
            self.assertEqual(pdf_guide.without_description(name), name)

    def test_скобка_со_строчной_тоже_состав(self):
        self.assertEqual(
            pdf_guide.without_description(
                "Broccoli Cheese - (not available at all locations)"),
            "Broccoli Cheese")

if __name__ == "__main__":
    unittest.main()


class PageFurniture(unittest.TestCase):
    """Колонтитул неотличим от заголовка по виду — только по повторяемости."""

    def _pages(self, n: int) -> list[str]:
        # Заголовок раздела у каждой страницы свой — как в настоящем гиде,
        # где содержание не повторяется, а колонтитул повторяется всегда.
        return [f"© 2026 Panera Bread. All Rights Reserved.\n"
                f"Effective: 6/17/2026 Edition: 1\n"
                f"Page {i}\n"
                f"Section {i}\n"
                f"Soup {i} 1 Cup {200 + i} 100 10 5 0 30 800 20 2 5 8 0\n"
                for i in range(n)]

    def test_повторяющаяся_строка_не_заголовок(self):
        text = pdf_guide.without_furniture(self._pages(10))
        self.assertNotIn("Panera Bread. All Rights", text)
        self.assertNotIn("Effective:", text)
        self.assertIn("Section 3", text)

    def test_на_коротком_гиде_ничего_не_режется(self):
        """У Subway три страницы, и «Cheesesteaks» стоит на двух из них."""
        text = pdf_guide.without_furniture(self._pages(3))
        self.assertIn("Panera Bread. All Rights", text)

    def test_номер_страницы_не_становится_категорией(self):
        items = pdf_guide.parse(
            "SOUPS\nCreamy soups\nPage 31\n"
            "Broccoli 1 Cup 280 180 20 13 1.5 60 1010 17 1 6 8 0\n",
            pdf_guide.PANERA)
        self.assertEqual(items[0].category, "Creamy soups")
        self.assertEqual(items[0].name, "Broccoli")


class Positioned(unittest.TestCase):
    """Разбор по координатам — для гидов, где строка разорвана.

    У Panera имя занимает две строки левой колонки, а числа стоят правее и
    вертикально между ними. Построчное чтение видит строку без чисел,
    строку без имени и ещё одну без чисел; по координатам же правило
    простое — строка имени принадлежит ближайшей по вертикали строке чисел.
    """

    def _page(self) -> list[pdf_guide.Line]:
        L = pdf_guide.Line
        return [
            L(150, 22, "SALADS"),
            L(171, 22, "Catering Asian Sesame Chicken Salad -"),
            L(180, 253, "1 Container 1260 640 71 9 0 175 4540 86 17 23 74 0"),
            L(186, 22, "serves 5"),
            L(198, 22, "Catering Asian Sesame Chicken Salad -"),
            L(207, 253, "1 Container 1050 470 52 8 0 175 4540 79 13 21 67 0"),
            L(213, 22, "serves 5 (no nuts)"),
        ]

    def test_имя_собирается_из_строк_вокруг_чисел(self):
        items = pdf_guide.parse_positioned([self._page()], pdf_guide.PANERA)
        names = sorted(i.name for i in items)

        # Дефис — часть стиля Panera: в цельной строке она пишет так же,
        # «Catering Asian Sesame Salad - serves 10».
        self.assertEqual(names, [
            "Catering Asian Sesame Chicken Salad - serves 5",
            "Catering Asian Sesame Chicken Salad - serves 5 (no nuts)",
        ])

    def test_числа_достаются_своему_блюду(self):
        items = pdf_guide.parse_positioned([self._page()], pdf_guide.PANERA)
        plain = next(i for i in items if "no nuts" not in i.name)

        self.assertEqual(plain.values["kcal"], 1260)
        self.assertEqual(plain.serving, "1 Container")

    def test_строка_с_именем_и_числами_не_идёт_в_геометрию(self):
        """Обычная строка сама себе имя, и соседи ей не нужны."""
        L = pdf_guide.Line
        page = [L(150, 22, "SALADS"),
                L(171, 22, "Asiago Cheese Bagel 1 Bagel 350 80 9 4 0 20 500 60 2 6 12 0"),
                L(180, 22, "Blueberry Bagel 1 Bagel 290 30 3 1 0 0 450 59 2 12 10 0")]
        items = pdf_guide.parse_positioned([page], pdf_guide.PANERA)

        self.assertEqual([i.name for i in items],
                         ["Asiago Cheese Bagel", "Blueberry Bagel"])
        self.assertEqual([i.values["kcal"] for i in items], [350, 290])

    def test_строка_чисел_узнаётся_по_отступу_а_не_по_доле_ширины(self):
        """У Panera имена стоят на 22 пунктах, числа на 257. Доля от
        ширины страницы давала границу 332 — числа оказывались левее неё,
        разбирались как целая строка, и именем блюда становилась порция."""
        L = pdf_guide.Line
        page = [L(150, 22, "MARKET BOWLS"),
                L(330, 22, "Market Bowl - Sesame Ginger Chicken -"),
                L(339, 257, "1/2 Bowl 470 200 22 3 0 35 1600 47 5 14 19 0"),
                L(345, 22, "Half")]
        [item] = pdf_guide.parse_positioned([page], pdf_guide.PANERA)

        self.assertEqual(item.name, "Market Bowl - Sesame Ginger Chicken - Half")
        self.assertEqual(item.serving, "1/2 Bowl")
