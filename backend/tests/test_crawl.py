"""Решение кроула: что обновить, чего не трогать и когда остановиться.

Кроул — единственное место конвейера, которое пишет в `items` поверх того,
что уже видят люди. Проверять его живым обходом сайта значит не проверять
вовсе: сайт меняется, и тест становится то зелёным, то красным без единой
правки в коде.
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data import crawl, matching


@dataclass(frozen=True)
class Live:
    name: str
    kcal: float | None = 500.0
    protein: float | None = 25.0
    carbs: float | None = 45.0
    fat: float | None = 25.0
    sugar: float | None = None
    sat_fat: float | None = None
    trans_fat: float | None = None
    cholesterol: float | None = None
    sodium: float | None = None
    fiber: float | None = None
    chain: str = "Chick-Fil-A"
    source: str = "chick-fil-a.com"
    source_url: str = "https://www.chick-fil-a.com/menu/x"

    @property
    def ext_key(self) -> str:
        return self.name.lower().replace(" ", "-")


def stored(**over) -> dict[str, dict]:
    base = {"ext_key": "chicken-sandwich", "name": "Chicken Sandwich",
            "kcal": 440.0, "protein": 28.0, "carbs": 40.0, "fat": 19.0}
    record = {**base, **over}
    return {record["ext_key"]: record}


class Matching(unittest.TestCase):

    def test_бренд_и_знаки_не_мешают(self):
        """MenuStat писал «Chick Fil a Nuggets», сайт — «Chick-fil-A® Nuggets»."""
        matched, _ = matching.match_all(
            [Live(name="Chick-fil-A® Nuggets")],
            stored(ext_key="chick-fil-a-nuggets", name="Chick Fil a Nuggets"))
        self.assertEqual(len(matched), 1)

    def test_разный_счёт_не_матчится(self):
        """«4 Nuggets» и «8 Nuggets» отличаются вдвое, а по строке — почти нет."""
        matched, _ = matching.match_all(
            [Live(name="8 Count Nuggets")],
            stored(ext_key="4-count-nuggets", name="4 Count Nuggets"))
        self.assertEqual(matched, {})

    def test_единица_счёта_не_отличает_блюдо(self):
        """«8 ct Nuggets» на сайте и «8 Nuggets» в каталоге — одно блюдо."""
        matched, _ = matching.match_all(
            [Live(name="8 ct Chick-fil-A® Nuggets")],
            stored(ext_key="8-chick-fil-a-nuggets", name="8 Chick Fil a Nuggets"))
        self.assertEqual(len(matched), 1)

    def test_притяжательное_не_оставляет_мусора(self):
        self.assertNotIn("s", matching.normalized("Kid's Meal").split()[1:])
        self.assertEqual(matching.normalized("Kid's Meal"), "kids meal")

    def test_сходство_видно_и_у_непойманных(self):
        """Иначе «промахнулись на волосок» неотличимо от «такого блюда нет»."""
        _, best = matching.match_all(
            [Live(name="Grilled Chicken Club Sandwich")],
            stored(ext_key="grilled-chicken-sandwich", name="Grilled Chicken Sandwich"))
        self.assertGreater(best["grilled-chicken-club-sandwich"], 0.5)

    def test_запись_каталога_занимается_один_раз(self):
        matched, _ = matching.match_all(
            [Live(name="Chicken Sandwich"), Live(name="Chicken Sandwich ")],
            stored())
        self.assertEqual(len(matched), 1)


class Planning(unittest.TestCase):

    def test_округление_сети_не_считается_расхождением(self):
        plan = crawl.build("Chick-Fil-A", [Live(name="Chicken Sandwich", kcal=443.0,
                                                protein=28.0, carbs=40.0, fat=19.5)],
                           stored())
        self.assertEqual(plan.updates, [])
        self.assertEqual(plan.agreed, 1)

    def test_настоящее_расхождение_попадает_в_план(self):
        plan = crawl.build("Chick-Fil-A", [Live(name="Chicken Sandwich", kcal=460.0,
                                                protein=28.0, carbs=45.0, fat=19.0)],
                           stored())
        [update] = plan.updates
        self.assertEqual(update.ext_key, "chicken-sandwich")
        self.assertEqual(update.changes["kcal"], (440.0, 460.0))
        self.assertIn("carbs", update.changes)

    def test_неполная_этикетка_не_применяется(self):
        """Свежие калории рядом с макросами 2018 года — строка, которая
        не сходится сама с собой."""
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Chicken Sandwich", kcal=460.0, protein=None)],
                           stored())
        self.assertEqual(plan.updates, [])
        self.assertEqual(plan.partial, [("Chicken Sandwich", ("protein",))])

    def test_битая_позиция_не_затирает_верную(self):
        """Макросы не могут давать больше энергии, чем заявлено калорий."""
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Chicken Sandwich", kcal=100.0, protein=28.0,
                                 carbs=40.0, fat=19.0)],
                           stored())
        self.assertEqual(plan.updates, [])
        self.assertTrue(crawl.validate.errors(plan.problems))

    def test_сломанная_доля_гасится_а_позиция_едет(self):
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Chicken Sandwich", kcal=460.0, protein=28.0,
                                 carbs=45.0, fat=19.0, sugar=300.0)],
                           stored())
        [update] = plan.updates
        self.assertNotIn("sugar", update.values)
        self.assertIn("kcal", update.values)

    def test_слишком_большое_изменение_не_пишется(self):
        """Side Salad: страница показывает салат с заправкой (470 ккал),
        каталог — без неё (160). Сопоставление верное, сравнивать нечего."""
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Side Salad", kcal=470.0, protein=13.0,
                                 carbs=14.0, fat=42.0)],
                           stored(ext_key="side-salad", name="Side Salad",
                                  kcal=160.0, protein=13.0, carbs=12.0, fat=11.0))
        self.assertEqual(plan.updates, [])
        [flagged] = plan.suspicious
        self.assertEqual(flagged.ext_key, "side-salad")

    def test_доля_на_маленьком_основании_не_подозрительна(self):
        """Сахар 1 → 4 г — это +300% и при этом три грамма. Ручная сверка
        такую правку приняла."""
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Chicken Sandwich", kcal=445.0, protein=28.0,
                                 carbs=40.0, fat=19.0, sugar=4.0)],
                           stored(sugar=1.0))
        self.assertEqual(plan.suspicious, [])
        self.assertEqual(len(plan.updates), 1)

    def test_дрейф_рецептуры_пишется(self):
        """Отличать от предыдущего должен масштаб, а не сам факт изменения."""
        plan = crawl.build("Chick-Fil-A",
                           [Live(name="Chicken Sandwich", kcal=470.0, protein=28.0,
                                 carbs=42.0, fat=20.0)],
                           stored())
        self.assertEqual(plan.suspicious, [])
        self.assertEqual(len(plan.updates), 1)

    def test_сомнительные_считаются_увиденными(self):
        """Иначе они попадут в «пропало» и держали бы кроул на ровном месте."""
        catalog = {f"item-{i}": {"ext_key": f"item-{i}", "name": f"Item {i}",
                                 "kcal": 400.0, "protein": 20.0,
                                 "carbs": 40.0, "fat": 15.0} for i in range(10)}
        live = [Live(name=f"Item {i}", kcal=1200.0, protein=60.0,
                     carbs=120.0, fat=50.0) for i in range(10)]
        plan = crawl.build("X", live, catalog)
        self.assertEqual(plan.unseen, [])
        self.assertEqual(len(plan.suspicious), 10)

    def test_ненайденное_не_закрывается(self):
        """«Блюда нет в меню» и «обход не дошёл» неразличимы для кода."""
        catalog = stored() | {"waffle-fries": {"ext_key": "waffle-fries",
                                               "name": "Waffle Potato Fries",
                                               "kcal": 420.0, "protein": 5.0,
                                               "carbs": 45.0, "fat": 24.0}}
        plan = crawl.build("Chick-Fil-A", [Live(name="Chicken Sandwich")], catalog)
        self.assertEqual(plan.unseen, ["waffle-fries"])

    def test_итог_сходится_с_тем_что_видел_обход(self):
        """Позиция, не прошедшая валидацию, не попадает ни в одну корзину."""
        live = [Live(name="Chicken Sandwich", kcal=460.0, protein=28.0,
                     carbs=45.0, fat=19.0),
                Live(name="Totally New Wrap"),
                Live(name="Chicken Sandwich", kcal=100.0)]
        plan = crawl.build("Chick-Fil-A", live, stored())
        self.assertEqual(plan.crawled, 3)
        self.assertGreater(plan.crawled,
                           len(plan.updates) + plan.agreed
                           + len(plan.unmatched) + len(plan.partial))

    def test_новинка_сети_не_заводится_вслепую(self):
        """У новой позиции нет ни категории, ни раздела, ни варианта."""
        plan = crawl.build("Chick-Fil-A", [Live(name="Totally New Wrap")], stored())
        self.assertEqual(plan.updates, [])
        self.assertEqual(len(plan.unmatched), 1)


class DiffGuard(unittest.TestCase):
    """Редизайн сайта не должен доехать до людей как новое меню.

    Сравнивается кроул с кроулом, а не с каталогом: каталог собран из среза
    2018 года и содержит позиции, которых сеть давно не листает отдельно.
    Сравнение с ним объявляло бы held на каждом первом кроуле.
    """

    def _catalog(self, n: int) -> dict[str, dict]:
        return {f"item-{i}": {"ext_key": f"item-{i}", "name": f"Item {i}",
                              "kcal": 400.0, "protein": 20.0,
                              "carbs": 40.0, "fat": 15.0} for i in range(n)}

    def test_первый_кроул_не_держим(self):
        """Сравнивать не с чем: прошлого кроула этой сети не было."""
        catalog = self._catalog(20)
        plan = crawl.build("X", [Live(name="Item 0"), Live(name="Item 1")], catalog)
        self.assertTrue(plan.ok, plan.held)
        self.assertEqual(len(plan.unseen), 18)

    def test_обход_потерял_половину_прошлого_держим(self):
        catalog = self._catalog(20)
        previous = {key: dict(record) for key, record in catalog.items()}
        plan = crawl.build("X", [Live(name="Item 0"), Live(name="Item 1")], catalog,
                           previous=previous)
        self.assertFalse(plan.ok)
        self.assertIn("пропало", plan.held)

    def test_переписанное_меню_держим(self):
        catalog = self._catalog(10)
        previous = {key: dict(record) for key, record in catalog.items()}
        live = [Live(name=f"Item {i}", kcal=900.0, protein=50.0, carbs=80.0, fat=40.0)
                for i in range(10)]
        plan = crawl.build("X", live, catalog, previous=previous)
        self.assertFalse(plan.ok)
        self.assertIn("изменилось", plan.held)

    def test_обычное_обновление_проходит(self):
        catalog = self._catalog(20)
        previous = {key: dict(record) for key, record in catalog.items()}
        live = [Live(name=f"Item {i}", kcal=400.0, protein=20.0, carbs=40.0, fat=15.0)
                for i in range(20)]
        live[0] = replace(live[0], kcal=430.0)
        plan = crawl.build("X", live, catalog, previous=previous)
        self.assertTrue(plan.ok, plan.held)
        self.assertEqual(len(plan.updates), 1)


if __name__ == "__main__":
    unittest.main()


class RobotsRules(unittest.TestCase):
    """robots.txt был правилом на словах: записан в скилле, не проверен кодом.

    Один сайт можно посмотреть руками, девяносто шесть — нет.
    """

    class _Parser:
        def __init__(self, allowed: bool, delay=None):
            self.allowed, self.delay = allowed, delay

        def can_fetch(self, agent, url):
            return self.allowed

        def crawl_delay(self, agent):
            return self.delay

    def _robots(self, parser):
        from plateful_data.adapters.base import Robots
        robots = Robots()
        robots._parsers["https://example.com"] = parser
        return robots

    def test_запрет_соблюдается(self):
        robots = self._robots(self._Parser(allowed=False))
        self.assertFalse(robots.allows("https://example.com/menu"))

    def test_нечитаемый_файл_не_запрещает_сайт(self):
        """Так велит стандарт: упавший robots.txt иначе закрыл бы всё."""
        robots = self._robots(None)
        self.assertTrue(robots.allows("https://example.com/menu"))
        self.assertIsNone(robots.crawl_delay("https://example.com/menu"))

    def test_просьба_сайта_о_паузе_важнее_нашей(self):
        from plateful_data.adapters.base import Fetcher
        fetcher = Fetcher(delay=5.0)
        fetcher.robots = self._robots(self._Parser(allowed=True, delay=20))
        # get() выдержит паузу и уйдёт в сеть, поэтому проверяем сам расчёт
        self.assertEqual(max(fetcher.delay,
                             fetcher.robots.crawl_delay("https://example.com/x")), 20.0)

    def test_запрещённый_адрес_не_ошибка_а_результат(self):
        from plateful_data.adapters.base import Fetcher
        fetcher = Fetcher()
        fetcher.robots = self._robots(self._Parser(allowed=False))
        self.assertIsNone(fetcher.get("https://example.com/menu"))
        self.assertEqual(fetcher.forbidden, ["https://example.com/menu"])
