"""Общее для всех адаптеров сетей.

Правила вежливости обязательны и одинаковы для всех:
  * `robots.txt` спрашивается до первого запроса и соблюдается;
  * один запрос в секунду, не быстрее;
  * честный User-Agent с адресом проекта;
  * только домен самой сети;
  * никакого обхода CAPTCHA и логинов.

Пищевые факты не защищены копирайтом (Feist v. Rural), а публиковать их сети
обязаны по 21 CFR 101.11 — но это не повод вести себя как бот-пылесос.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

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


class Robots:
    """`robots.txt` каждого хоста: спрашивается один раз, помнится до конца.

    Правило было записано в скилле и в комментариях, но кодом не
    проверялось: у Chick-fil-A файл смотрели руками. Один сайт так
    проверить можно, девяносто шесть — нет, и обход, нарушающий
    собственное правило, отличается от бота-пылесоса только намерением.

    Недоступный `robots.txt` считаем разрешением: так велит стандарт и так
    делают поисковики — иначе упавший файл запрещал бы весь сайт. А вот
    сам запрет соблюдаем молча и до конца, без «ну один раз можно».
    """

    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _parser(self, url: str):
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._parsers:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(urlunsplit((parts.scheme, parts.netloc,
                                       "/robots.txt", "", "")))
            try:
                parser.read()
            except Exception:
                # Не отдался — читаем как разрешение, но говорим об этом.
                print(f"  · robots.txt не прочитан у {parts.netloc}")
                parser = None
            self._parsers[host] = parser
        return self._parsers[host]

    def allows(self, url: str) -> bool:
        parser = self._parser(url)
        return True if parser is None else parser.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        """Пауза, которую сайт просит сам. Его просьба важнее нашей ставки."""
        parser = self._parser(url)
        if parser is None:
            return None
        try:
            delay = parser.crawl_delay(self.user_agent)
        except Exception:
            return None
        return float(delay) if delay else None


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
    """HTTP с выдержкой паузы между запросами и с оглядкой на robots.txt."""

    def __init__(self, delay: float = DELAY_SECONDS, *, obey_robots: bool = True):
        self.delay = delay
        self._last = 0.0
        self.robots = Robots() if obey_robots else None
        #: Адреса, которые сайт запретил. Не ошибка обхода, а его результат.
        self.forbidden: list[str] = []

    def get(self, url: str, timeout: int = 60,
            headers: dict[str, str] | None = None) -> str | None:
        if self.robots and not self.robots.allows(url):
            self.forbidden.append(url)
            print(f"  · robots.txt запрещает {url}")
            return None

        # Сайт может попросить паузу длиннее нашей — его просьба важнее.
        if self.robots and (asked := self.robots.crawl_delay(url)):
            self.delay = max(self.delay, asked)

        # Часть сетей смотрит на полный набор браузерных заголовков, а не
        # только на User-Agent, поэтому адаптер может передать свои.
        request = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})

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
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                # Таймаут у сетей за Akamai — обычное дело на первом запросе,
                # поэтому пробуем ещё раз, а не сдаёмся сразу.
                if attempt < MAX_RETRIES - 1:
                    print(f"  · {type(error).__name__}, повтор")
                    time.sleep(self.delay * 2)
                    continue
                print(f"  ! {url}: {error}")
                return None
        return None


def curl_get(url: str, headers: dict[str, str], timeout: int = 45,
             robots: "Robots | None" = None) -> str | None:
    """Забирает страницу через curl.

    Часть сетей за Akamai не отвечает Python-у вовсе: там смотрят на отпечаток
    TLS-рукопожатия, а он у стандартной библиотеки другой, чем у браузера.
    Тот же адрес curl отдаёт нормально, и это дешевле, чем поднимать браузер.
    """
    # Обход бот-защиты по отпечатку TLS — не повод обойти и robots.txt:
    # первое про то, чем мы стучимся, второе про то, куда нас пускают.
    if robots and not robots.allows(url):
        print(f"  · robots.txt запрещает {url}")
        return None
    if not shutil.which("curl"):
        return None
    command = ["curl", "-sL", "--compressed", "-m", str(timeout)]
    for key, value in headers.items():
        command += ["-H", f"{key}: {value}"]
    command.append(url)
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 and result.stdout else None


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
