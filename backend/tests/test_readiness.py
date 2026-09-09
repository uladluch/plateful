"""Порог готовности сети: кого пак берёт в приложение, а кого нет."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import pack


def rows(chain: str, n: int, *, photos: int, fresh: int, archived: int = 0):
    """n живых позиций сети плюс `archived` снятых с меню."""
    live = [(chain, i < photos, i < fresh, False) for i in range(n)]
    return live + [(chain, False, False, True) for _ in range(archived)]


class Readiness(unittest.TestCase):

    def test_сеть_целиком_собранная_проходит(self):
        [score] = pack.readiness(rows("McDonald's", 100, photos=100, fresh=100)).values()
        self.assertTrue(score.ok)

    def test_десятая_часть_без_снимка_допустима(self):
        """У сети всегда найдётся напиток, который она сама нигде не
        сфотографировала. Порог не «всё до последней позиции»."""
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
        старая по определению. Судить по ним готовность сети — значит
        наказывать её за то, что мы честно храним её прошлое."""
        [score] = pack.readiness(
            rows("McDonald's", 100, photos=100, fresh=100, archived=200)).values()
        self.assertEqual(score.items, 100)
        self.assertTrue(score.ok)

    def test_сеть_из_одного_архива_в_счёт_не_идёт(self):
        self.assertEqual(pack.readiness(rows("X", 0, photos=0, fresh=0, archived=5)), {})


class InPack(unittest.TestCase):
    """Собранный пак несёт всё нужное сам — по нему же и проверяется."""

    @staticmethod
    def built(**kwargs):
        return {"stale": False, "items": [
            {"chain": "McDonald's", "photo": {"url": "a.png"}},
            {"chain": "Panera Bread"},
        ], **kwargs}

    def test_неготовую_сеть_видно_в_собранном_паке(self):
        bad = pack.unready(self.built())
        self.assertEqual(list(bad), ["Panera Bread"])

    def test_свежесть_читается_с_умолчанием_пака(self):
        """Позиция несёт `stale` только если отличается от умолчания."""
        bad = pack.unready(self.built(stale=True))
        self.assertEqual(sorted(bad), ["McDonald's", "Panera Bread"])
