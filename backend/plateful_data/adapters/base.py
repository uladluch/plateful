"""Общее для всех адаптеров сетей.

Правила вежливости обязательны и одинаковы для всех:
  * один запрос в секунду, не быстрее;
  * честный User-Agent с адресом проекта;
  * только домен самой сети;
  * никакого обхода CAPTCHA и логинов.

Пищевые факты не защищены копирайтом (Feist v. Rural), а публиковать их сети
обязаны по 21 CFR 101.11 — но это не повод вести себя как бот-пылесос.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "plateful-data/1.0 (+https://github.com/uladluch/plateful)"

# Chick-fil-A отвечает 429 уже на третьем десятке запросов при паузе в
# секунду, и после такого бурста держит в пенальти минутами. Пять секунд
# проходят; обход сети из сотни позиций занимает восемь минут, что для
# еженедельного крона несущественно.
DELAY_SECONDS = 5.0
MAX_RETRIES = 4
# После 429 ждём заметно дольше обычной паузы: сайт просит не «чуть
# помедленнее», а «отойди».
PENALTY_SECONDS = 60.0


@dataclass(frozen=True)
class LiveItem:
    """Позиция, снятая с сайта сети."""
    chain: str
    ext_key: str
    name: str
    kcal: float
    protein: float | None
    carbs: float | None
    fat: float | None
    source: str
    source_url: str


class Fetcher:
    """HTTP с выдержкой паузы между запросами."""

    def __init__(self, delay: float = DELAY_SECONDS):
        self.delay = delay
        self._last = 0.0

    def get(self, url: str, timeout: int = 30) -> str | None:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        for attempt in range(MAX_RETRIES):
            elapsed = time.monotonic() - self._last
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self._last = time.monotonic()

            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return response.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as error:
                # 429 — просьба притормозить, а не отказ. Отступаем и ждём
                # дольше с каждой попыткой.
                if error.code == 429 and attempt < MAX_RETRIES - 1:
                    pause = PENALTY_SECONDS * (2 ** attempt)
                    print(f"  · 429, жду {pause:.0f} с")
                    time.sleep(pause)
                    continue
                print(f"  ! {url}: {error}")
                return None
            except (urllib.error.URLError, TimeoutError) as error:
                print(f"  ! {url}: {error}")
                return None
        return None


def to_number(value) -> float | None:
    """«29g» → 29.0, «420» → 420.0, мусор → None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    digits = "".join(c for c in str(value) if c.isdigit() or c == ".")
    try:
        return float(digits)
    except ValueError:
        return None
