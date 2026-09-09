"""Этикетка со страницы поставщика: разбор без сети.

Разметка настоящая — снята со страницы Jersey Mike's 2026-09-09 и урезана
до строк, которые мы читаем.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters import nutritionix as nx

HEADERS = """
<th id="inmGrid_c0"></th>
<th id="inmGrid_c1">Calories <span>Sort by Calories</span></th>
<th id="inmGrid_c2">Total Fat (g) <span>Sort by Total Fat (grams)</span></th>
<th id="inmGrid_c3">Calories from Fat <span>Sort by Calories from Fat</span></th>
<th id="inmGrid_c4">Sodium (mg) <span>Sort by Sodium (milligrams)</span></th>
<th id="inmGrid_c5">Total Carbohydrates (g) <span>Sort by Total Carbs</span></th>
<th id="inmGrid_c6">Protein (g) <span>Sort by Protein (grams)</span></th>
"""

ROW = """
<tr class="odd"><td class="al" headers="inmGrid_c0">
<a class="nmItem" title="#1 BLT, Bowl" href="viewLabel">#1 BLT, Bowl</a></td>
<td class="col" title="470 Calories" headers="inmGrid_c1">470</td>
<td class="col" title="45g Total Fat" headers="inmGrid_c2">45</td>
<td class="col" title="405 Calories from Fat" headers="inmGrid_c3">405</td>
<td class="col" title="1,050mg Sodium" headers="inmGrid_c4">1,050</td>
<td class="col" title="&lt;1g Total Carbohydrates" headers="inmGrid_c5">&lt;1</td>
<td class="col" title="15g Protein" headers="inmGrid_c6">15</td></tr>
"""

PAGE = HEADERS + """
<tr class="subCategory"><td colspan="7"><h3>Cold Subs</h3></td></tr>
""" + ROW + """
<tr class="subCategory"><td colspan="7"><h3>Hot Subs</h3></td></tr>
<tr class="even"><td class="al" headers="inmGrid_c0">
<a class="nmItem" title="#1 BLT, Bowl" href="viewLabel">#1 BLT, Bowl</a></td>
<td class="col" title="470 Calories" headers="inmGrid_c1">470</td></tr>
"""


class Columns(unittest.TestCase):

    def test_шапка_читается_со_страницы(self):
        """Набор колонок у брендов разный: у одних «Calories from Fat»,
        у других «Added Sugars». Раскладку тут не зашить."""
        found = nx.columns(HEADERS)
        self.assertEqual(found["inmGrid_c1"], "kcal")
        self.assertEqual(found["inmGrid_c4"], "sodium")
        self.assertEqual(found["inmGrid_c6"], "protein")

    def test_чужие_колонки_пропускаются(self):
        """«Calories from Fat» мы не ведём."""
        self.assertNotIn("inmGrid_c3", nx.columns(HEADERS))


class Number(unittest.TestCase):

    def test_разделитель_тысяч(self):
        self.assertEqual(nx.number("1,050mg Sodium"), 1050.0)

    def test_меньше_единицы_читается_границей(self):
        """Сеть говорит «меньше грамма». Взять названную границу —
        единственное чтение, которое ничего не выдумывает."""
        self.assertEqual(nx.number("&lt;1g Total Carbohydrates"), 1.0)

    def test_пусто_это_не_ноль(self):
        self.assertIsNone(nx.number(""))
        self.assertIsNone(nx.number("n/a"))


class Parse(unittest.TestCase):

    def items(self):
        return nx.parse(PAGE, "Jersey Mike's Subs", "https://example.test")

    def test_позиция_с_этикеткой(self):
        [item] = self.items()
        self.assertEqual(item.name, "#1 BLT, Bowl")
        self.assertEqual((item.kcal, item.fat, item.sodium), (470.0, 45.0, 1050.0))
        self.assertEqual(item.protein, 15.0)

    def test_раздел_меню_берётся_из_заголовка(self):
        [item] = self.items()
        self.assertEqual(item.category, "Cold Subs")

    def test_повтор_в_другом_разделе_не_дублируется(self):
        """Блюдо стоит и в своём разделе, и в «Избранном». Берём первое:
        у него раздел настоящий."""
        self.assertEqual(len(self.items()), 1)

    def test_шапка_не_разобралась_значит_страница_не_та(self):
        with self.assertRaises(SystemExit):
            nx.parse(ROW, "X", "https://example.test")


class Slugs(unittest.TestCase):

    def test_сеть_без_страницы_у_поставщика_отвергается(self):
        with self.assertRaises(SystemExit) as caught:
            nx.fetch("boston-market", "Boston Market")
        self.assertIn("SLUGS", str(caught.exception))

    def test_карта_покрывает_каталог(self):
        """Девяносто сетей из девяноста шести; у шести страницы нет."""
        self.assertGreater(len(nx.SLUGS), 85)
        self.assertEqual(nx.SLUGS["dunkin-donuts"], "dunkin")


if __name__ == "__main__":
    unittest.main()
