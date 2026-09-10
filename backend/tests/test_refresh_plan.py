"""Маршрут обновления сети выбирается по строке `chains`, а не по списку в коде."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from refresh_chain import plan_for


class PlanForChain(unittest.TestCase):

    def test_подрядчик_этикетки(self):
        plan = plan_for({"slug": "denny-s", "name": "Denny's", "source_kind": "label_provider",
                         "photo_source_kind": None})
        self.assertEqual(plan.numbers, ["--nutritionix", "--replace"])
        self.assertFalse(plan.photos)
        self.assertIn("снимки: источник не записан", plan.skipped)

    def test_бренд_rbi_идёт_через_sanity(self):
        plan = plan_for({"slug": "burger-king", "name": "Burger King", "source_kind": "json_api",
                         "photo_source_kind": "sanity-rbi"})
        self.assertEqual(plan.numbers, ["--sanity", "--replace"])
        self.assertTrue(plan.photos)

    def test_mcdonalds_снимок_и_присутствие(self):
        plan = plan_for({"slug": "mcdonald-s", "name": "McDonald's", "source_kind": "json_api",
                         "photo_source_kind": "mcdonalds-snapshot"})
        self.assertEqual(plan.numbers, ["--snapshot", "--replace"])
        self.assertEqual(plan.presence, "mcdonalds")

    def test_закрытая_сеть_цифрами_не_обновляется(self):
        plan = plan_for({"slug": "bj-s-restaurant-brewhouse", "name": "BJ's", "source_kind": "blocked",
                         "photo_source_kind": None})
        self.assertIsNone(plan.numbers)
        self.assertTrue(any(s.startswith("цифры") for s in plan.skipped))


if __name__ == "__main__":
    unittest.main()
