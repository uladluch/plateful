"""Этикетка: что доезжает до пака и чему нельзя верить.

Правило одно — доля не бывает больше целого. Насыщенные и трансжиры входят
в общий жир, сахар и клетчатка — в углеводы. Нарушение значит сломанное
число, а не необычное блюдо, и в источнике таких 109.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import pack, validate
from plateful_data.menustat import Item


def item(**over) -> Item:
    base = dict(chain="Test", ext_key="x", name="X", category=None, serving=None,
                kcal=200.0, protein=10.0, carbs=20.0, fat=10.0,
                sat_fat=3.0, trans_fat=0.0, cholesterol=30.0,
                sodium=400.0, sugar=5.0, fiber=2.0)
    return Item(**{**base, **over})


class BrokenLabel(unittest.TestCase):

    def test_clean_item_has_no_complaints(self):
        self.assertEqual(validate.broken_label_fields(item()), [])

    def test_sugar_above_carbs_is_broken(self):
        # «Diet Dr Pepper, Large»: ноль углеводов и 96 г сахара.
        broken = validate.broken_label_fields(item(carbs=0.0, sugar=96.0, fiber=0.0))
        self.assertEqual([field for field, _ in broken], ["sugar"])

    def test_trans_fat_above_total_fat_is_broken(self):
        # У TGI Friday's трансжиры в 1470 г при 26 г жира целиком.
        broken = validate.broken_label_fields(item(fat=26.0, trans_fat=1470.0))
        self.assertEqual([field for field, _ in broken], ["trans_fat"])

    def test_rounding_is_not_broken(self):
        """Источник округляет до целых — грамм расхождения законен."""
        self.assertEqual(validate.broken_label_fields(item(carbs=20.0, sugar=21.0)), [])
        self.assertEqual([f for f, _ in validate.broken_label_fields(
            item(carbs=20.0, sugar=22.0))], ["sugar"])

    def test_stripping_keeps_the_item(self):
        """Гасится поле, а не позиция: калории и макросы у неё в порядке."""
        [cleaned] = validate.strip_broken_label([item(carbs=0.0, sugar=96.0, fiber=0.0)])
        self.assertIsNone(cleaned.sugar)
        self.assertEqual(cleaned.kcal, 200.0)
        self.assertEqual(cleaned.fat, 10.0)
        self.assertEqual(cleaned.sat_fat, 3.0)

    def test_label_problem_never_drops_an_item(self):
        problems = validate.check_item(item(carbs=0.0, sugar=96.0, fiber=0.0))
        self.assertEqual([p.severity for p in problems if p.kind == "label"], ["warning"])
        self.assertEqual(validate.errors(problems), [])


class LabelInPack(unittest.TestCase):

    def test_all_six_fields_reach_the_pack(self):
        built = pack.build([item()], version=1, source="test", observed="2018-12-31")
        row = built["items"][0]
        self.assertEqual(row["satFat"], 3.0)
        self.assertEqual(row["transFat"], 0.0)
        self.assertEqual(row["cholesterol"], 30.0)
        self.assertEqual(row["sodium"], 400.0)
        self.assertEqual(row["sugar"], 5.0)
        self.assertEqual(row["fiber"], 2.0)

    def test_missing_values_are_absent_not_zero(self):
        """«Нет числа» и «ноль» — разное: ноль сахара это обещание."""
        built = pack.build([item(sugar=None, cholesterol=None)],
                           version=1, source="test", observed="2018-12-31")
        row = built["items"][0]
        self.assertNotIn("sugar", row)
        self.assertNotIn("cholesterol", row)
        self.assertIn("transFat", row)


if __name__ == "__main__":
    unittest.main()
