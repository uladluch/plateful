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

from plateful_data import pack


def rows(chain: str, n: int, *, photos: int, fresh: int, archived: int = 0,
         card=None):
    """n живых карточек сети плюс `archived` снятых с меню."""
    live = [(chain, card or f"{chain}:{i}", i < photos, i < fresh, False)
            for i in range(n)]
    return live + [(chain, f"{chain}:old{i}", False, False, True)
                   for i in range(archived)]


class ByCard(unittest.TestCase):

    def test_варианты_одного_блюда_это_одна_карточка(self):
        """Двадцать строк «латте × молоко × размер» — одна строка меню."""
        variants = [("Starbucks", "latte", False, True, False) for _ in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.cards, 1)
        self.assertEqual(score.items, 20)

    def test_снимок_у_одного_варианта_красит_всю_карточку(self):
        """Приложение ставит представителем группы того, у кого есть
        фотография, — значит карточка со снимком."""
        variants = [("Starbucks", "latte", i == 7, True, False) for i in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.photos, 1.0)
        self.assertTrue(score.ok)

    def test_одна_устаревшая_строка_портит_карточку(self):
        """Человек переключает размер и видит цифры соседнего варианта."""
        variants = [("Starbucks", "latte", True, i != 3, False) for i in range(20)]
        [score] = pack.readiness(variants).values()
        self.assertEqual(score.fresh, 0.0)
        self.assertFalse(score.ok)


class Threshold(unittest.TestCase):

    def test_сеть_целиком_собранная_проходит(self):
        [score] = pack.readiness(rows("McDonald's", 100, photos=100, fresh=100)).values()
        self.assertTrue(score.ok)

    def test_десятая_часть_без_снимка_допустима(self):
        """У сети всегда найдётся напиток, который она не сфотографировала."""
        [score] = pack.readiness(rows("Popeyes", 100, photos=91, fresh=100)).values()
        self.assertTrue(score.ok)

    def test_каждая_пятая_без_снимка_уже_нет(self):
        [score] = pack.readiness(rows("Firehouse", 100, photos=80, fresh=100)).values()
        self.assertFalse(score.ok)

    def test_устаревшие_цифры_держат_так_же_как_снимки(self):
        [score] = pack.readiness(rows("Chick-Fil-A", 100, photos=100, fresh=20)).values()
        self.assertFalse(score.ok)

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
            {"chain": "McDonald's", "key": "big-mac", "photo": {"url": "a.png"}},
            {"chain": "Panera Bread", "key": "bagel"},
        ], **kwargs}

    def test_неготовую_сеть_видно_в_собранном_паке(self):
        self.assertEqual(list(pack.unready(self.built())), ["Panera Bread"])

    def test_свежесть_читается_с_умолчанием_пака(self):
        """Позиция несёт `stale` только если отличается от умолчания."""
        self.assertEqual(sorted(pack.unready(self.built(stale=True))),
                         ["McDonald's", "Panera Bread"])

    def test_группа_вариантов_склеивает_строки_пака(self):
        built = {"stale": False, "items": [
            {"chain": "Starbucks", "key": "latte-tall",
             "variant": {"group": "starbucks:latte"}},
            {"chain": "Starbucks", "key": "latte-venti", "photo": {"url": "l.png"},
             "variant": {"group": "starbucks:latte"}},
        ]}
        [score] = pack.readiness(pack.pack_rows(built)).values()
        self.assertEqual((score.cards, score.items), (1, 2))
        self.assertEqual(score.photos, 1.0)


if __name__ == "__main__":
    unittest.main()
