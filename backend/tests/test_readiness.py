"""Порог готовности сети: кого пак берёт в приложение, а кого нет.

Считаем **карточками**, а не строками этикетки: человек видит одну
строку меню с переключателем размера, а не двадцать строк «напиток ×
молоко × размер».
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import archetype, pack


def rows(chain: str, n: int, *, photos: int, fresh: int, archived: int = 0,
         card=None, dish: bool = True):
    """n живых карточек сети плюс `archived` снятых с меню."""
    live = [(chain, card or f"{chain}:{i}", i < photos, i < fresh, False, dish)
            for i in range(n)]
    return live + [(chain, f"{chain}:old{i}", False, False, True, True)
                   for i in range(archived)]


class ByCard(unittest.TestCase):

    def test_варианты_одного_блюда_это_одна_карточка(self):
        """Двадцать строк «латте × молоко × размер» — одна строка меню."""
        variants = [("Starbucks", "latte", False, True, False, True) for _ in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.cards, 1)
        self.assertEqual(score.items, 20)

    def test_снимок_у_одного_варианта_красит_всю_карточку(self):
        """Приложение ставит представителем группы того, у кого есть
        фотография, — значит карточка со снимком."""
        variants = [("Starbucks", "latte", i == 7, True, False, True) for i in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.photos, 1.0)
        self.assertTrue(score.ok)

    def test_одна_устаревшая_строка_портит_карточку(self):
        """Человек переключает размер и видит цифры соседнего варианта."""
        variants = [("Starbucks", "latte", True, i != 3, False, True) for i in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.fresh, 0.0)
        self.assertFalse(score.ok)


class Threshold(unittest.TestCase):

    def test_сеть_целиком_собранная_проходит(self):
        [score] = pack.readiness(rows("McDonald's", 100, photos=100, fresh=100)).values()
        self.assertTrue(score.ok)

    def test_снимки_сеть_не_держат(self):
        """Порог по снимкам снят: карточка без фотографии не врёт."""
        [score] = pack.readiness(rows("Popeyes", 100, photos=0, fresh=100)).values()
        self.assertTrue(score.ok)
        self.assertEqual(score.photos, 0.0)

    def test_держит_одна_свежесть(self):
        """Устаревшая цифра врёт молча — человек считает по ней."""
        [score] = pack.readiness(rows("Chick-Fil-A", 100, photos=100, fresh=85)).values()
        self.assertFalse(score.ok)
        [score] = pack.readiness(rows("Chick-Fil-A", 100, photos=100, fresh=90)).values()
        self.assertTrue(score.ok)

    def test_архив_не_учитывается(self):
        """У снятого с меню блюда снимка нет и не будет, а дата у него
        старая по определению."""
        [score] = pack.readiness(
            rows("McDonald's", 100, photos=100, fresh=100, archived=200)).values()
        self.assertEqual(score.cards, 100)
        self.assertTrue(score.ok)

    def test_сеть_из_одного_архива_в_счёт_не_идёт(self):
        self.assertEqual(pack.readiness(rows("X", 0, photos=0, fresh=0, archived=5)), {})


class InPack(unittest.TestCase):
    """Собранный пак несёт всё нужное сам — по нему же и проверяется."""

    @staticmethod
    def built(**kwargs):
        return {"stale": False, "items": [
            {"chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
             "photo": {"url": "a.png"}},
            # Снимка нет и цифры протухли: держит второе, не первое.
            {"chain": "Panera Bread", "key": "bagel", "name": "Plain Bagel",
             "stale": True},
        ], **kwargs}

    def test_неготовую_сеть_видно_в_собранном_паке(self):
        self.assertEqual(list(pack.unready(self.built())), ["Panera Bread"])

    def test_свежесть_читается_с_умолчанием_пака(self):
        """Позиция несёт `stale` только если отличается от умолчания."""
        self.assertEqual(sorted(pack.unready(self.built(stale=True))),
                         ["McDonald's", "Panera Bread"])

    def test_отсутствие_снимка_сеть_не_держит(self):
        """У бейгла снимка нет, но цифры свежие — сеть едет."""
        self.assertEqual(list(pack.unready(self.built(items=[
            {"chain": "Panera Bread", "key": "bagel", "name": "Plain Bagel"}]))), [])

    def test_группа_вариантов_склеивает_строки_пака(self):
        built = {"stale": False, "items": [
            {"chain": "Starbucks", "key": "latte-tall", "name": "Latte, Tall",
             "variant": {"group": "starbucks:latte"}},
            {"chain": "Starbucks", "key": "latte-venti", "name": "Latte, Venti",
             "photo": {"url": "l.png"}, "variant": {"group": "starbucks:latte"}},
        ]}
        [score] = pack.readiness(pack.pack_rows(built)).values()
        self.assertEqual((score.cards, score.items), (1, 2))
        self.assertEqual(score.photos, 1.0)


class WhoNeedsAPhoto(unittest.TestCase):
    """Снимок спрашивается с блюда, а не с пакетика сахара."""

    def test_добавка_и_чужая_бутылка_не_идут_в_знаменатель(self):
        """Сеть сняла все свои блюда — она готова, хоть у соусов
        фотографий и нет."""
        dishes = [("Panera", f"d{i}", True, True, False, True) for i in range(90)]
        extras = [("Panera", f"s{i}", False, True, False, False) for i in range(60)]
        [score] = pack.readiness(dishes + extras).values()
        self.assertEqual((score.cards, score.dishes), (150, 90))
        self.assertEqual(score.photos, 1.0)
        self.assertTrue(score.ok)

    def test_свежесть_спрашивается_со_всех(self):
        """Этикетка есть и у пакетика сахара — тут поблажки нет."""
        dishes = [("Panera", f"d{i}", True, True, False, True) for i in range(90)]
        extras = [("Panera", f"s{i}", False, False, False, False) for i in range(60)]
        [score] = pack.readiness(dishes + extras).values()
        self.assertEqual(score.fresh, 0.6)
        self.assertFalse(score.ok)

    def test_блюдо_в_группе_красит_всю_карточку(self):
        """«Coke Float» и «Coke Float, Kids» — одна карточка, и она блюдо."""
        group = [("Chili's", "float", False, True, False, False),
                 ("Chili's", "float", False, True, False, True)]
        [score] = pack.readiness(group).values()
        self.assertEqual(score.dishes, 1)
        self.assertEqual(score.photos, 0.0)


class WhatCountsAsADish(unittest.TestCase):
    """Правило само по себе: что считается блюдом, а что добавкой."""

    def test_добавки_и_бутылки_освобождены(self):
        for name in ("Blue Packet Sweetener", "Agave, Topping", "Sugar",
                     "Hollandaise Sauce, for Build Your Own Omelet",
                     "Spread - Hummus - Sandwich Portion", "Spinach Boost",
                     "Diet Coke", "Pepsi, 20 oz", "1 pump of Cane Sugar Syrup"):
            with self.subTest(name):
                self.assertFalse(archetype.needs_own_photo(name))

    def test_упоминание_соуса_не_делает_блюдо_соусом(self):
        """«Honey Mustard Chicken Wrap» — врап, а не горчица."""
        for name in ("Value Honey Mustard Chicken Wrap",
                     "Big Fish Sandwich With Tartar Sauce, Grilled",
                     "Lighter Portions, Cheese Ravioli with Meat Sauce",
                     "(30) Classic Bone-In Wings (no flavor or dipping sauce)",
                     "Mexican Casserole Add-On - Chips & Salsa - Large"):
            with self.subTest(name):
                self.assertTrue(archetype.needs_own_photo(name))

    def test_напиток_из_чужого_бренда_сеть_делает_сама(self):
        """«Coke Float» — десерт сети, она его снимает."""
        for name in ("Coke Float, Kids", "Medium Coke Freezee King",
                     "Cookie Monster, 2.5 oz Scoop"):
            with self.subTest(name):
                self.assertTrue(archetype.needs_own_photo(name))


class BeerIsNotADish(unittest.TestCase):
    """Пиво чужих пивоварен снимка не требует — но пиво в составе блюда
    не делает блюдо пивом."""

    def test_пиво_и_сидр_освобождены(self):
        for name in ("Bell's Oberon Ale, 14 fl oz", "Angel Island IPA (12 oz)",
                     "Blue Moon (Grande)", "Angry Orchard Hard Cider, 12 oz",
                     "Beer, 6% ABV & Up, 23 oz", "Modelo Especial", "Barqs Root Beer"):
            with self.subTest(name):
                self.assertFalse(archetype.needs_own_photo(name))

    def test_пиво_в_составе_блюда_не_освобождает(self):
        for name in ("2 Beer Battered Fish Tacos Plato", "Beer Cheese & Pretzels",
                     "A La Carte, Beer-Battered Onion Rings",
                     "3 Rib Combo, Choose One Side and One Beverage, Beverage Choice Barq's Root Beer",
                     "Barq's Root Beer Float, 16 oz", "Add On Warm Pretzels w/ Craft Beer Cheese Dipping Sauce"):
            with self.subTest(name):
                self.assertTrue(archetype.needs_own_photo(name))

if __name__ == "__main__":
    unittest.main()
