"""Группировка размерных вариантов.

Ошибки здесь тихие: пак собирается, приложение запускается, просто у колы
переключатель показывает «Small» дважды. Поэтому проверяем не только счастливый
путь, но и то, что склейка НЕ трогает похожие на размер хвосты названий.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.sizes import assign_groups, size_label
from plateful_data.slug import slugify


class Item:
    """Утиный двойник menustat.Item: assign_groups читает три поля."""

    def __init__(self, chain: str, name: str):
        self.chain = chain
        self.name = name
        self.ext_key = slugify(name)


class SizeLabelTests(unittest.TestCase):
    def test_known_words(self):
        self.assertEqual(size_label("Coca Cola, Large"), ("Coca Cola", "Large"))
        self.assertEqual(size_label("Latte, Venti"), ("Latte", "Venti"))

    def test_volumes_and_portions(self):
        self.assertEqual(size_label("Orange Juice, 12 fl oz"),
                         ("Orange Juice", "12 fl oz"))
        self.assertEqual(size_label("Cheese Pizza, 2 Slices"),
                         ("Cheese Pizza", "2 Slices"))

    def test_leaves_names_alone(self):
        # Хвост после запятой — часть названия блюда, а не размер.
        self.assertIsNone(size_label("Cobb Salad, w/ Nuggets"))
        self.assertIsNone(size_label("Biscuit, Sausage and Egg"))
        self.assertIsNone(size_label("Big Mac"))
        self.assertIsNone(size_label("Fries,"))

    def test_only_last_segment(self):
        # Режем по последней запятой, иначе «Sandwich, Grilled» съест «Grilled».
        self.assertEqual(size_label("Iced Coffee, Vanilla, Medium"),
                         ("Iced Coffee, Vanilla", "Medium"))


class AssignGroupsTests(unittest.TestCase):
    def test_orders_by_vocabulary(self):
        items = [Item("A", f"Coca Cola, {s}")
                 for s in ("Large", "Small", "Medium", "Extra Small")]
        groups = assign_groups(items)
        order = {name: groups[("A", slugify(f"Coca Cola, {name}"))][2]
                 for name in ("Extra Small", "Small", "Medium", "Large")}
        self.assertEqual(list(order.values()), [0, 1, 2, 3])

    def test_orders_volumes_numerically(self):
        items = [Item("A", f"Juice, {n} fl oz") for n in (32, 12, 16)]
        groups = assign_groups(items)
        labels = sorted(groups.values(), key=lambda g: g[2])
        self.assertEqual([g[1] for g in labels], ["12 fl oz", "16 fl oz", "32 fl oz"])

    def test_chains_do_not_overwrite_each_other(self):
        # ext_key уникален только внутри сети. Пока ключом был он один,
        # сеть с тремя размерами затирала позиции сети с четырьмя.
        items = [Item("A", f"Coca Cola, {s}")
                 for s in ("Extra Small", "Small", "Medium", "Large")]
        items += [Item("B", f"Coca Cola, {s}") for s in ("Small", "Medium", "Large")]
        groups = assign_groups(items)

        a = sorted(v[2] for k, v in groups.items() if k[0] == "A")
        b = sorted(v[2] for k, v in groups.items() if k[0] == "B")
        self.assertEqual(a, [0, 1, 2, 3])
        self.assertEqual(b, [0, 1, 2])

    def test_singleton_is_not_a_group(self):
        groups = assign_groups([Item("A", "Apple Slices, 1 Package")])
        self.assertEqual(groups, {})

    def test_group_key_is_the_base_slug(self):
        items = [Item("A", "Diet Coke, Small"), Item("A", "Diet Coke, Large")]
        groups = assign_groups(items)
        self.assertEqual({g[0] for g in groups.values()}, {"diet-coke"})


if __name__ == "__main__":
    unittest.main()
