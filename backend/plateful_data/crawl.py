"""Кроул одной сети: что сняли с сайта и что с этим делать.

Здесь нет ни HTTP, ни SQL — только решение. Ходит по сайту `scripts/
crawl_chain.py`, пишет в базу он же; сюда приходят уже снятые позиции и
текущий каталог, а отсюда уходит план: что обновить, чего мы не нашли и
можно ли вообще это применять.

Разделение не ради красоты. Кроул — самое опасное место конвейера: он
единственный пишет в `items` поверх того, что уже видят люди. Проверять
такое решение живым обходом сайта значит не проверять его вовсе.

**Позиции, которых кроул не увидел, не закрываются.** «Блюда нет в меню» и
«наш обход не дошёл до его страницы» с точки зрения кода неразличимы, а
последствия разные: первое — факт, второе — наша поломка. Снятием с меню
занимается `check_menu_presence.py`, у него для этого есть отдельная
таблица. Кроул же молча оставляет ненайденное как было и выносит их число
в отчёт — если оно вдруг велико, сработает диff-проверка.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import validate
from .matching import match_all
from .validate import check_item, errors, strip_broken_label

# Расхождение меньше этого — округление сети, а не изменение рецептуры.
NOISE_KCAL = 5.0
NOISE_GRAMS = 1.0

# Расхождение больше этой доли — почти наверняка не дрейф рецептуры, а разный
# смысл строки. Проверено на Side Salad: страница сети показывает салат
# с заправкой (470 ккал), в каталоге он без неё (160). Сопоставление при этом
# верное, спорить не с чем — просто сравнивать нечего. Такие уходят человеку.
#
# Кроул без этого правила записал бы Cobb Salad как 830 ккал вместо 250 и был
# бы формально прав: сеть действительно публикует такое число, но про другое
# блюдо.
SUSPICIOUS_SHARE = 0.30

# Одной доли мало: на маленьком основании она срабатывает от округления.
# Сахар 1 → 4 г — это плюс триста процентов и при этом три грамма; ручная
# сверка такую правку приняла, а доля отправила бы позицию человеку. Поэтому
# подозрительным считаем только то, что вышло за долю И за абсолютный порог.
SUSPICIOUS_FLOOR = {"kcal": 50.0, "sodium": 100.0, "cholesterol": 100.0}
SUSPICIOUS_FLOOR_GRAMS = 5.0

# Поля этикетки, которые кроул обновляет. Имя и категория не трогаются:
# название позиции — ключ, по которому её ищет человек и цепляются правки.
NUTRIENTS = ("kcal", "protein", "carbs", "fat",
             "sugar", "sat_fat", "trans_fat", "cholesterol", "sodium", "fiber")


@dataclass(frozen=True)
class Adoption:
    """Позиция, которой в каталоге нет, — завести как новую.

    Заводим только из гида и только с разрешения человека. Обход сайта на
    это права не имеет: он неполон по природе, и «мы не дошли до страницы»
    неотличимо от «блюда нет». Гид же — полное заявление сети о своём меню,
    один документ; чего в нём нет, того сеть не публикует.
    """
    ext_key: str
    name: str
    category: str | None
    serving: str | None
    source_url: str
    values: dict[str, float]


@dataclass(frozen=True)
class Update:
    """Позиция каталога, для которой сеть сегодня даёт другие числа."""
    ext_key: str
    name: str
    live_name: str
    source_url: str
    values: dict[str, float]
    changes: dict[str, tuple[float, float]]

    @property
    def summary(self) -> str:
        return ", ".join(f"{field}: {was:g}→{now:g}"
                         for field, (was, now) in sorted(self.changes.items()))


@dataclass
class Plan:
    """Что кроул предлагает сделать."""
    chain: str
    #: Домен, с которого сняли, и адрес меню — они едут в items и chains.
    source: str = ""
    menu_url: str = ""
    updates: list[Update] = field(default_factory=list)
    #: Позиции сайта, которым не нашлось пары в каталоге: новинки сети либо
    #: слишком непохожее название. Заводить их вслепую нельзя — у новой
    #: позиции нет ни категории, ни раздела, ни варианта.
    unmatched: list[tuple[str, float]] = field(default_factory=list)
    #: Позиции каталога, до которых обход не дошёл.
    unseen: list[str] = field(default_factory=list)
    #: Расхождение слишком велико, чтобы быть новой рецептурой. Не пишем:
    #: скорее всего сайт и каталог говорят о разных вещах — салат с
    #: заправкой и без, чашка супа и миска.
    suspicious: list[Update] = field(default_factory=list)
    #: Сеть отдала не все четыре макроса. Такие не применяем: свежие
    #: калории рядом с макросами 2018 года дали бы строку, которая не
    #: сходится сама с собой, а проверка Атуотера — единственное, чем мы
    #: ловим съехавшую колонку.
    partial: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)
    #: Новые позиции сети. Пусто, пока не разрешили заводить.
    adopted: list[Adoption] = field(default_factory=list)
    #: Позиции каталога, которых в гиде нет: сеть их больше не подаёт.
    #: Не удаляем — уводим в архив, чтобы сохранённые заказы не сломались.
    retired: list[str] = field(default_factory=list)
    #: Позиции каталога, которые источник назвал — сматчились, с
    #: обновлением или без. Замена меню пишет по ним «в меню» так же
    #: явно, как «снято»: обход бывает неполным, и позиция, которую
    #: прошлый прогон не дотянулся увидеть, должна вернуться из архива
    #: следующим — а не остаться там навсегда.
    seen_keys: list[str] = field(default_factory=list)
    #: Сошлись с сайтом до округления — их большинство, и это норма.
    agreed: int = 0
    #: Сколько позиций сняли со страниц. Отдельным числом, а не суммой
    #: остальных: позиция, не прошедшая валидацию, не попадает ни в одну
    #: из корзин, и итог без неё не сходился бы с тем, что видел обход.
    crawled: int = 0
    problems: list[validate.Problem] = field(default_factory=list)
    held: str | None = None

    @property
    def ok(self) -> bool:
        return self.held is None

    @property
    def seen(self) -> int:
        return len(self.updates) + self.agreed


#: По чему сравниваются кроулы между собой. Этикетка сюда не входит:
#: сеть может уточнить натрий, не тронув блюдо, и это не повод держать релиз.
DIFF_FIELDS = ("kcal", "protein", "carbs", "fat")


def _macros(records: dict[str, dict]) -> dict[str, tuple]:
    """Одна форма для обеих сторон сравнения."""
    return {key: tuple(record.get(field) for field in DIFF_FIELDS)
            for key, record in records.items()}


def _adoptions(plan: Plan, live, matched: dict[str, dict]) -> list[Adoption]:
    """Несматченные позиции, годные для заведения.

    Через ту же валидацию, что и обновления: блюдо, которое не сходится
    само с собой, не станет лучше оттого, что оно новое. Разница лишь в
    том, что здесь нечего портить — поэтому непрошедшее просто не заводим.
    """
    unmatched = {name for name, _ in plan.unmatched}
    adopted: list[Adoption] = []

    for item in live:
        if item.name not in unmatched or item.ext_key in matched:
            continue
        if any(getattr(item, field, None) is None
               for field in ("kcal", "protein", "carbs", "fat")):
            continue

        problems = check_item(item)
        plan.problems.extend(problems)
        if errors(problems):
            continue

        [clean] = strip_broken_label([item])
        values = {name: value for name in NUTRIENTS
                  if (value := getattr(clean, name, None)) is not None}
        adopted.append(Adoption(
            ext_key=item.ext_key, name=item.name,
            category=getattr(item, "category", None),
            serving=getattr(item, "serving", None),
            source_url=getattr(item, "source_url", "") or "",
            values=values))

    return adopted


def _changes(live: dict[str, float], stored: dict) -> dict[str, tuple[float, float]]:
    """Что реально разошлось, за вычетом округлений."""
    out: dict[str, tuple[float, float]] = {}
    for name in NUTRIENTS:
        now = live.get(name)
        was = stored.get(name)
        if now is None or was is None:
            continue
        noise = NOISE_KCAL if name == "kcal" else NOISE_GRAMS
        # Натрий и холестерин в миллиграммах — грамм допуска там бессмыслен,
        # поэтому им допуск в процентах от собственной величины.
        if name in ("sodium", "cholesterol"):
            noise = max(NOISE_GRAMS, abs(was) * 0.02)
        if abs(now - was) > noise:
            out[name] = (float(was), float(now))
    return out


def is_suspicious(changes: dict[str, tuple[float, float]]) -> bool:
    """Изменение слишком велико, чтобы быть новой рецептурой."""
    for name, (was, now) in changes.items():
        floor = SUSPICIOUS_FLOOR.get(name, SUSPICIOUS_FLOOR_GRAMS)
        if (was > 0 and abs(now - was) / was > SUSPICIOUS_SHARE
                and abs(now - was) > floor):
            return True
    return False


def build(chain: str, live, stored: dict[str, dict], *,
          previous: dict[str, dict] | None = None,
          adopt: bool = False,
          source: str = "", menu_url: str = "") -> Plan:
    """Живые позиции + текущий каталог → план.

    `live` — объекты с `ext_key`, `name`, `source_url` и числами этикетки;
    `stored` — записи каталога по `ext_key`; `previous` — что видел прошлый
    кроул этой же сети.

    Дифф-проверка сравнивает **кроул с кроулом**, а не с каталогом. Разница
    принципиальная: каталог собран из среза 2018 года и содержит позиции,
    которых сеть давно не листает по отдельности, — у Chick-fil-A обход
    покрывает 23 строки из 101, и это норма, а не поломка. Сравнение с
    каталогом объявляло бы held на каждом первом кроуле, то есть проверка
    срабатывала бы всегда и потому не значила бы ничего.
    """
    live = list(live)
    plan = Plan(chain=chain, source=source, menu_url=menu_url, crawled=len(live))
    matched, best = match_all(live, stored)
    taken: set[str] = set()

    for item in live:
        record = matched.get(item.ext_key)
        if record is None:
            plan.unmatched.append((item.name, round(best.get(item.ext_key, 0.0), 2)))
            continue

        missing = tuple(name for name in ("kcal", "protein", "carbs", "fat")
                        if getattr(item, name, None) is None)
        if missing:
            plan.partial.append((item.name, missing))
            continue

        taken.add(record["ext_key"])
        problems = validate.check_item(item)
        plan.problems.extend(problems)
        if validate.errors(problems):
            # Позиция не сходится сама с собой — в каталог она не поедет,
            # старые числа остаются. Молчать об этом нельзя, но и
            # заменять верное на битое тем более.
            continue

        [clean] = validate.strip_broken_label([item])
        values = {name: value for name in NUTRIENTS
                  if (value := getattr(clean, name, None)) is not None}
        changes = _changes(values, record)
        if not changes:
            plan.agreed += 1
            continue

        update = Update(
            ext_key=record["ext_key"], name=record["name"], live_name=item.name,
            source_url=getattr(item, "source_url", "") or "",
            values=values, changes=changes)
        bucket = plan.suspicious if is_suspicious(changes) else plan.updates
        bucket.append(update)

    plan.unseen = sorted(set(stored) - taken)
    plan.seen_keys = sorted(taken)

    if adopt:
        plan.adopted = _adoptions(plan, live, matched)
        # Ключ позиции считается из имени, и два одинаковых имени дают один
        # ключ: второе молча затрёт первое. На первом прогоне Subway так
        # потерялись 48 позиций из 162 — гид перечисляет «Steak Philly»
        # трижды, обёрткой, салатом и боулом. Разводить их — дело
        # `pdf_guide.qualify`; здесь мы только отказываемся, если не развели.
        taken_keys = {a.ext_key for a in plan.adopted}
        if len(taken_keys) != len(plan.adopted) or taken_keys & set(stored):
            plan.held = ("новые позиции сталкиваются ключами с каталогом или "
                         "друг с другом — заводить нельзя, потеряем часть")
            plan.adopted = []
            return plan
        # Чего сеть не назвала в своём же гиде, того она больше не подаёт.
        plan.retired = plan.unseen

    # Что этот кроул увидел — против того, что видел прошлый. На первом
    # кроуле `previous` пуст, и check_diff честно говорит: сравнивать не с чем.
    #
    # Обе стороны приводим к четырём макросам. Без этого сравнивались
    # словари разной формы — запись каталога со всеми полями против
    # четырёх чисел прошлого кроула, — и «изменилось» получалось у всего
    # подряд: повторный кроул той же сети показывал 100% на неизменных
    # данных. Проверка, срабатывающая всегда, не значит ничего.
    seen_now = {key: record for key, record in stored.items() if key in taken}
    seen_now |= {u.ext_key: u.values for u in plan.updates + plan.suspicious}
    ok, why = validate.check_diff(_macros(previous or {}), _macros(seen_now))
    if not ok:
        plan.held = why

    return plan
