"""Архетип блюда — по нему подбирается картинка.

Правила писались под названия MenuStat 2018 года. Гиды сетей называют
блюда иначе, и три правила промахнулись молча: картинка просто становилась
общей «тарелкой с едой», а таких у Subway оказалось 73 из 180.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.archetype import classify


class GuideNames(unittest.TestCase):

    def test_множественное_число_тоже_обёртка(self):
        """«Wraps» — раздел гида, и он попадает в имя позиции. Правило
        писалось как \\bwrap\\b и на множественном числе не срабатывало."""
        self.assertEqual(classify("5 Meat Italian, Wraps"), "wrap")
        self.assertEqual(classify("Steak Philly, Wraps"), "wrap")

    def test_множественное_число_тоже_боул(self):
        self.assertEqual(classify("5 Meat Italian, Protein Bowls"), "bowl")
        self.assertEqual(classify("Market Bowl - Sesame Ginger Chicken"), "bowl")

    def test_дюйм_знаком_это_тот_же_размер(self):
        """Каталог 2018 года писал «6 in», сегодняшний гид пишет «6"»."""
        self.assertEqual(classify('6" Steak Philly'), "sub-sandwich")
        self.assertEqual(classify("Steak Philly, 6 in"), "sub-sandwich")

    def test_обёртка_важнее_размера(self):
        """У «12" Wrap» есть и дюймы, и обёртка. Обёртка определённее."""
        self.assertEqual(classify('12" Wrap'), "wrap")

    def test_прежние_имена_не_сломались(self):
        self.assertEqual(classify("Big Mac"), "cheeseburger")
        self.assertEqual(classify("Footlong Meatball Marinara"), "sub-sandwich")
        self.assertEqual(classify("Waffle Potato Fries"), "fries")
        self.assertEqual(classify("Chick Fil a Nuggets"), "chicken-nuggets")

    def test_картинка_есть_всегда(self):
        """Пустых архетипов не бывает: у любого блюда есть чем его показать."""
        for name in ("", "Нечто неизвестное", "1 Pump Caramel Syrup"):
            self.assertTrue(classify(name))


if __name__ == "__main__":
    unittest.main()


class Accompaniments(unittest.TestCase):
    """«Соус, для рёбрышек» — это соус, а не рёбрышки.

    Позиция названа по блюду, к которому идёт, и классификатор читал имя
    целиком: «Honey BBQ Sauce, for Applebees Riblets Platter» получал
    архетип кофе — от «coffee» внутри «Applebees». Таких в каталоге 2415.
    """

    def test_соус_к_блюду_остаётся_соусом(self):
        self.assertEqual(classify("Classic Buffalo Sauce, for Boneless Wings"), "sauce")
        self.assertEqual(classify("Honey BBQ Sauce, for Applebees Riblets Platter"), "sauce")

    def test_заправка_с_размером_саба_не_саб(self):
        """«12 in» в хвосте — размер саба, к которому идёт заправка."""
        self.assertEqual(classify("Dressing for Baja, 12 in"), "sauce")

    def test_сыр_для_боула_это_сыр(self):
        self.assertEqual(classify("Fontina Cheese for Breakfast Bowls"), "cheese")

    def test_имя_без_for_разбирается_как_прежде(self):
        self.assertEqual(classify("Mesquite, 12 in"), "sub-sandwich")
        self.assertEqual(classify("Big Mac"), "cheeseburger")

    def test_если_начало_ничего_не_говорит_читаем_целиком(self):
        """«Build Your Own, for Sampler» — начало пустое, смысл в хвосте."""
        self.assertEqual(classify("Combo, for Pizza Sampler"), "pizza")
