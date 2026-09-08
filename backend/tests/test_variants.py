"""Группировка вариантов блюда: порции и опции.

Ошибки здесь тихие: пак собирается, приложение запускается, просто у колы
переключатель показывает «Small» дважды. Поэтому проверяем не только счастливый
путь, но и то, что склейка НЕ трогает похожие на размер хвосты названий.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.variants import (OPTION, SIZE, assign_groups,
                                    count_label, learn_size_words,
                                    option_label, size_label)
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


class CountTests(unittest.TestCase):
    """Счёт перед названием: «10 Chicken McNuggets»."""

    def test_reads_a_leading_count(self):
        self.assertEqual(count_label("10 Chicken McNuggets"), ("Chicken McNuggets", "10"))
        self.assertEqual(count_label("3 Piece McCrispy Strips"), ("McCrispy Strips", "3 Piece"))

    def test_keeps_the_unit(self):
        # «12 oz» — размер стейка; голое «12» рядом с «16» прочтётся так же,
        # но потеряет, в чём меряют.
        self.assertEqual(count_label("12 oz Top Sirloin"), ("Top Sirloin", "12 oz"))

    def test_leaves_percentages_alone(self):
        self.assertIsNone(count_label("1% Low Fat Milk Jug"))

    def test_groups_singular_and_plural(self):
        # «1 Mini Cheeseburger» и «2 Mini Cheeseburgers» — одно блюдо.
        items = [Item("A", "1 Mini Cheeseburger"), Item("A", "2 Mini Cheeseburgers")]
        groups = assign_groups(items)
        self.assertEqual(len({g[0] for g in groups.values()}), 1)
        self.assertEqual([g[1] for g in sorted(groups.values(), key=lambda g: g[2])],
                         ["1", "2"])


class OptionTests(unittest.TestCase):
    """Исполнения одного блюда: «Big Breakfast w/ Hotcakes»."""

    def test_splits_at_the_connector(self):
        self.assertEqual(option_label("Big Breakfast w/ Hotcakes"),
                         ("Big Breakfast", "Hotcakes"))
        self.assertEqual(option_label("Meatballs with Marinara"),
                         ("Meatballs", "Marinara"))

    def test_plain_dish_joins_its_own_group(self):
        items = [Item("A", "Big Breakfast"), Item("A", "Big Breakfast w/ Hotcakes")]
        groups = assign_groups(items)
        self.assertEqual(len(groups), 2)
        labels = [g[1] for g in sorted(groups.values(), key=lambda g: g[2])]
        self.assertEqual(labels, ["Plain", "Hotcakes"])
        self.assertTrue(all(g[3] == OPTION for g in groups.values()))

    def test_a_lonely_variant_is_not_a_group(self):
        # Простого «Quarter Pounder» в меню нет — склеивать не с чем.
        self.assertEqual(assign_groups([Item("A", "Quarter Pounder w/ Cheese")]), {})


class LearnedSizeTests(unittest.TestCase):
    """Словарь размеров выводится из данных, а не пишется по сетям."""

    def test_learns_a_word_the_chain_reuses(self):
        # «Shorti» у Wawa — размер, но ни в одном словаре его нет.
        items = [Item("Wawa", f"{dish}, Shorti") for dish in ("Turkey", "Ham", "Italian")]
        items += [Item("Wawa", f"{dish}, Classic") for dish in ("Turkey", "Ham", "Italian")]
        self.assertIn("shorti", learn_size_words(items)["Wawa"])

    def test_ignores_an_ingredient_list(self):
        # У хвоста «Egg & Cheese Biscuit» тоже три разных начала — бекон,
        # сосиска и стейк, — и без ограничений они склеились бы в одно блюдо.
        items = [Item("A", f"{meat}, Egg & Cheese Biscuit")
                 for meat in ("Bacon", "Sausage", "Steak")]
        self.assertEqual(learn_size_words(items), {})
        self.assertEqual(assign_groups(items), {})

    def test_a_rare_tail_is_not_a_size(self):
        items = [Item("A", "Soup, Chunky"), Item("A", "Stew, Chunky")]
        self.assertEqual(learn_size_words(items), {})


class BaseTests(unittest.TestCase):
    """База едет в паке: правило отрезания знает только тот, кто отрезал."""

    def test_base_is_the_name_without_the_variant(self):
        items = [Item("A", "4 Chicken McNuggets"), Item("A", "10 Chicken McNuggets"),
                 Item("A", "Coca Cola, Small"), Item("A", "Coca Cola, Large"),
                 Item("A", "Big Breakfast"), Item("A", "Big Breakfast w/ Hotcakes")]
        bases = {g[0]: g[4] for g in assign_groups(items).values()}
        self.assertEqual(bases, {"chicken-mcnugget": "Chicken McNuggets",
                                 "coca-cola": "Coca Cola",
                                 "big-breakfast": "Big Breakfast"})

    def test_label_is_cut_from_the_name_verbatim(self):
        # Иначе клиент не сможет собрать имя обратно из базы и подписи.
        pairs = [("3 Piece McCrispy Strips", "5 Piece McCrispy Strips"),
                 ("12 oz Top Sirloin", "16 oz Top Sirloin"),
                 ("Latte, Venti", "Latte, Grande")]
        for first, second in pairs:
            groups = assign_groups([Item("A", first), Item("A", second)])
            for name in (first, second):
                _, label, _, _, base = groups[("A", slugify(name))]
                self.assertIn(label, name)
                self.assertIn(base, name)


class KindTests(unittest.TestCase):
    def test_mixed_group_counts_as_portions(self):
        # Порция важнее: из неё складываются калории.
        items = [Item("A", "Fries, Small"), Item("A", "Fries, Large"),
                 Item("A", "Fries w/ Cheese")]
        kinds = {g[3] for g in assign_groups(items).values()}
        self.assertEqual(kinds, {SIZE})


if __name__ == "__main__":
    unittest.main()
