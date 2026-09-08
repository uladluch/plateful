"""Пометки позиции: детская порция, на компанию, не во всех точках, сезонное.

Источник держит их нулём и единицей у каждой строки, поэтому «нет пометки»
здесь значит «точно нет», а не «неизвестно».
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import menustat, pack


def row(**over) -> dict:
    base = {"Restaurant": "Applebee's", "Item_Name": "1 Mini Cheeseburger",
            "Food_Category": "Burgers", "Calories": "360", "Protein": "15",
            "Carbohydrates": "22", "Total_Fat": "23",
            "Kids_Meal": "0", "Shareable": "0",
            "Regional": "0", "Limited_Time_Offer": "0", "Combo_Meal": "0"}
    return {**base, **over}


class Flags(unittest.TestCase):

    def test_единица_включает_пометку(self):
        self.assertEqual(menustat._flags(row(Kids_Meal="1")), ("kids",))

    def test_ноль_не_включает(self):
        self.assertEqual(menustat._flags(row()), ())

    def test_порядок_фиксирован_объявлением(self):
        """Пак обязан собираться байт-в-байт, значит порядок не от данных."""
        flags = menustat._flags(row(Limited_Time_Offer="1", Kids_Meal="1",
                                    Regional="1", Shareable="1"))
        self.assertEqual(flags, ("kids", "shareable", "regional", "seasonal"))

    def test_комбо_не_едет(self):
        """166 позиций, и слово «Combo» у большинства уже в названии."""
        self.assertEqual(menustat._flags(row(Combo_Meal="1")), ())

    def test_ограниченное_предложение_становится_сезонным(self):
        # «Действует до» из снимка 2018 года обещало бы закрытое окно.
        self.assertEqual(menustat._flags(row(Limited_Time_Offer="1")), ("seasonal",))

    def test_пустых_пометок_в_паке_нет(self):
        """У 86% блюд пометок нет — ключ с пустым списком раздул бы пак."""
        item = menustat.Item(
            chain="T", ext_key="x", name="X", category=None, serving=None,
            kcal=100.0, protein=1.0, carbs=2.0, fat=3.0, sat_fat=None,
            trans_fat=None, cholesterol=None, sodium=None, sugar=None,
            fiber=None, flags=())
        built = pack.build([item], version=1, source="t", observed="2018-12-31")
        self.assertNotIn("flags", built["items"][0])


if __name__ == "__main__":
    unittest.main()
