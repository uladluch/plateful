"""Архетип блюда — то, что видно на фотографии.

Двадцать пять тысяч позиций сфотографировать нельзя, да и незачем: чизбургер
выглядит чизбургером у любой сети. Поэтому каждой позиции присваивается
архетип, а снимков нужно около полусотни.

Классификация живёт здесь, а не в приложении, намеренно: ошибочно назначенная
картинка чинится публикацией нового пака, без релиза в App Store.

Порядок правил важен — от частного к общему. «Chicken Sandwich» обязан
поймать `chicken-sandwich` раньше, чем общий `sandwich`.
"""

from __future__ import annotations

import re

# (архетип, регулярка). Проверяются по порядку, побеждает первое совпадение.
RULES: list[tuple[str, str]] = [
    # Напитки узнаются по названию надёжнее всего, поэтому идут первыми:
    # «Frosted Lemonade» — не лимонад в стакане, а молочный коктейль.
    ("milkshake",         r"milkshake|\bshake\b|\bmalt\b|frosted lemonade|frosted coffee"),
    ("ice-cream",         r"ice cream|icedream|sundae|\bcone\b|blizzard|frosty|mcflurry|soft serve|float\b"),
    ("iced-coffee",       r"frappuccino|frappe|iced coffee|cold brew|iced latte|iced mocha"),
    ("coffee",            r"coffee|latte|cappuccino|americano|espresso|macchiato|mocha|\bbrew\b"),
    ("tea",               r"\btea\b|chai|matcha"),
    ("slush",             r"slurpee|slush|icee|freeze\b|frozen (drink|carbonated)"),
    ("smoothie",          r"smoothie|refresher"),
    ("juice",             r"juice|lemonade|orange drink|apple drink"),
    ("soda",              r"coca[- ]cola|coke\b|pepsi|sprite|dr pepper|root beer|mountain dew|"
                          r"fanta|soda\b|fountain|barq|mello yello|sierra mist|soft drink"),
    ("water",             r"\bwater\b|dasani|aquafina|smartwater"),
    ("milk",              r"\bmilk\b(?! ?shake)|chocolate milk"),
    ("beer",              r"\bbeer\b|\bale\b|lager|\bipa\b"),
    ("cocktail",          r"margarita|sangria|mojito|martini|cocktail|daiquiri|long island"),
    ("wine",              r"\bwine\b|chardonnay|merlot|cabernet"),

    # Основные блюда
    ("cheeseburger",      r"cheeseburger|quarter pounder|big mac|whopper|baconator|"
                          r"double cheese|bacon burger"),
    ("hamburger",         r"\bburger\b|hamburger|patty melt|slider"),
    ("chicken-sandwich",  r"chicken sandwich|chicken deluxe|spicy (deluxe|sandwich)|"
                          r"chicken filet|mcchicken|chicken club|grilled chicken sandwich"),
    ("chicken-nuggets",   r"nugget|popcorn chicken|chicken bite"),
    ("chicken-strips",    r"\bstrip\b|strips\b|tender|chick n strips"),
    ("chicken-wings",     r"\bwing\b|wings\b|boneless wing"),
    ("fried-chicken",     r"fried chicken|drumstick|chicken thigh|chicken breast|"
                          r"crispy chicken|original recipe"),
    ("taco",              r"\btaco\b|tostada|chalupa|gordita"),
    ("burrito",           r"burrito|chimichanga|quesadilla|enchilada"),
    ("bowl",              r"\bbowls?\b"),
    ("pizza",             r"pizza|calzone|stromboli|flatbread"),
    ("wrap",              r"\bwraps?\b|cool wrap"),
    # Размер сабвея сеть пишет и словом, и знаком дюйма: «6 in» в
    # каталоге 2018 года, «6"» в сегодняшнем гиде.
    ("sub-sandwich",      r"\bsub\b|hoagie|footlong|\d+\s*(?:in\b|\")|"
                          r"b\.?m\.?t\.?|cheesesteak"),
    ("breakfast-sandwich", r"biscuit|mcmuffin|croissan|egg white grill|breakfast sandwich|"
                           r"english muffin|breakfast burrito"),
    ("sandwich",          r"sandwich|panini|\bmelt\b|\bb\.?l\.?t\.?\b|\bclub\b|reuben"),
    ("salad",             r"salad|\bgreens\b|slaw"),
    ("soup",              r"soup|chili\b|bisque|chowder"),
    ("pasta",             r"pasta|spaghetti|alfredo|lasagna|macaroni|mac & cheese|"
                          r"mac and cheese|fettuccine|ravioli|penne"),
    ("steak",             r"steak|sirloin|ribeye|brisket|prime rib"),
    ("seafood",           r"shrimp|salmon|\bfish\b|crab|lobster|tilapia|scallop|calamari"),
    ("ribs",              r"\brib\b|ribs\b|riblet"),
    ("hot-dog",           r"hot dog|corn dog|frank\b"),

    # Гарниры и добавки
    ("fries",             r"\bfries\b|waffle potato|tater|potato wedge|onion ring|curly fries"),
    ("hash-browns",       r"hash brown|hashbrown"),
    ("baked-potato",      r"baked potato|mashed potato"),
    ("chips",             r"chips|crisps|nacho"),
    ("side-vegetables",   r"broccoli|\bcorn\b|green bean|\bbeans\b|carrot|vegetable|"
                          r"\brice\b|asparagus"),
    ("bread",             r"bagel|\btoast\b|\bbread\b|\broll\b|pretzel|breadstick|biscuit only"),
    ("egg",               r"\begg\b|omelet|scramble"),
    ("bacon",             r"bacon|sausage|\bham\b"),
    ("cheese",            r"\bcheese\b|queso"),
    ("sauce",             r"sauce|dressing|\bdip\b|syrup|mayo|ketchup|mustard|vinaigrette|"
                          r"guacamole|salsa|sour cream"),

    # Сладкое
    ("cookie",            r"cookie|brownie"),
    ("donut",             r"donut|doughnut"),
    ("cake",              r"cake|\bpie\b|cheesecake|cinnamon roll|danish|muffin|"
                          r"pastry|churro|cobbler"),
    ("yogurt",            r"yogurt|parfait"),
    ("fruit",             r"fruit|apple slice|banana|berries|grapes|orange\b|melon"),
]

# Если ни одно правило не сработало, берём общий снимок по категории MenuStat.
# Так покрытие становится полным без выдумывания архетипа.
CATEGORY_FALLBACK = {
    "Beverages": "drink",
    "Toppings & Ingredients": "ingredients",
    "Entrees": "plated-meal",
    "Sandwiches": "sandwich",
    "Appetizers & Sides": "side-dish",
    "Pizza": "pizza",
    "Desserts": "dessert",
    "Baked Goods": "bread",
    "Salads": "salad",
    "Burgers": "hamburger",
    "Soup": "soup",
    "Fried Potatoes": "fries",
}

DEFAULT = "plated-meal"

_COMPILED = [(name, re.compile(pattern)) for name, pattern in RULES]


#: «Соус, для рёбрышек», «Сыр для боулов», «Заправка для Baja, 12 in» —
#: позиция названа по блюду, к которому идёт, а не по себе. Классификатор
#: же читает имя целиком и выдаёт архетип сопровождаемого блюда: «Honey BBQ
#: Sauce, for Applebees Riblets Platter» получал кофе (от «coffee» в
#: «Applebees»), а «Dressing for Baja, 12 in» — саб, потому что «12 in».
#: Таких позиций в каталоге 2415, и у 1565 картинка была чужой.
_ACCOMPANIES = re.compile(r",?\s+for\s+")


def classify(name: str, category: str | None = None) -> str:
    """Архетип позиции. Всегда возвращает значение — пустых не бывает."""
    # Сначала по тому, чем позиция является, и лишь потом — по имени целиком.
    head = _ACCOMPANIES.split(name, maxsplit=1)[0]
    for candidate in (head, name) if head != name else (name,):
        text = candidate.lower()
        for archetype, pattern in _COMPILED:
            if pattern.search(text):
                return archetype
    return CATEGORY_FALLBACK.get(category or "", DEFAULT)


def all_archetypes() -> list[str]:
    """Полный список — по нему заказывается набор изображений."""
    names = {archetype for archetype, _ in RULES}
    names.update(CATEGORY_FALLBACK.values())
    names.add(DEFAULT)
    return sorted(names)


# ── Кому своя фотография не нужна ───────────────────────────────────────
#
# Снимок нужен блюду. Пакетик сахара, помпа сиропа, бустер шпината и
# бутылка Pepsi — не блюда: сеть их не фотографирует и никогда не будет,
# а человек и так знает, как выглядит кола. Им хватит общей картинки по
# архетипу — ровно того, ради чего этот модуль и написан.
#
# Правило нужно не для показа, а для счёта: такие карточки не идут в
# знаменатель порога снимков (`pack.readiness`). В меню они остаются.
#
# Мерили: у Panera из 117 карточек без снимка 30 — соусы и сиропы, 20 —
# бутылки чужих брендов; у Jamba из 65 почти все — бустеры и топпинги.

#: Чужой бренд в бутылке или банке. Сеть его перепродаёт, а не готовит,
#: и снимать чужую этикетку ей незачем — да и права на неё не её.
_PACKAGED_BRANDS = re.compile(
    r"\b(?:coca[- ]?cola|coke|pepsi|starry|sprite|fanta|crush|"
    r"dr\.? pepper|pibb|mtn dew|mountain dew|sierra mist|mello yello|barq|"
    r"7\s*up|mug root beer|schweppes|canada dry|"
    r"dasani|aquafina|smartwater|vitaminwater|perrier|san pellegrino|"
    r"gatorade|powerade|body ?armor|red bull|celsius|amp energy|"
    r"(?<!cookie )monster|"
    r"tropicana|minute maid|simply (?:orange|lemonade|apple)|dole|"
    r"ocean spray|naked juice|izze|snapple|honest tea|gold peak|"
    r"pure leaf|lipton|sobe|bubly|core power|hi-?c|nestea|"
    r"bai|essentia|life ?wtr|propel)\b", re.I)

#: Добавка, а не блюдо. Слово обязано стоять **в конце** имени: позиция
#: должна добавкой быть, а не упоминать её. «Yellow Mustard» — горчица,
#: «Honey Mustard Chicken Wrap» — врап, и разница между ними ровно в
#: том, чем имя кончается.
_ADD_ON_TAIL = re.compile(
    r"\b(?:sauce|dressing|spread|aioli|mayo|mayonnaise|mustard|ketchup|"
    r"vinaigrette|syrup|jam|jelly|preserves|creamer|sweetener|splenda|"
    r"stevia|seasoning|boost|booster|topping|toppings|sugar|butter|"
    r"half\s*(?:&|and)\s*half)\s*$", re.I)

#: Мера подачи в хвосте: «BBQ Sauce Dipping **Cup**», «Hummus **Portion**».
#: Снимаем её, чтобы добраться до слова, которым позиция названа.
_PORTION_TAIL = re.compile(
    r"[\s\-–]+(?:cups?|packets?|portions?|sides?|containers?|tubs?|pats?|"
    r"dipping|small|large|medium|kids?)\s*$", re.I)

#: Сегмент, который сам по себе говорит, что это добавка: «Agave,
#: **Topping**», «Banana, Fresh, **Topping**». Голова тут — название
#: продукта, а вид позиции стоит в хвосте, поэтому смотрим и туда.
_ALONE = {"topping", "toppings", "add-on", "add on", "addon", "packet"}

#: Позиция, названная одним словом-приправой: «Sugar», «Butter». Отдельно
#: от хвостового правила: тут слово и есть всё имя целиком.
_PLAIN = {"sugar", "honey", "butter", "salt", "pepper", "ice", "sweetener",
          "creamer", "sour cream", "salsa", "ranch"}

#: То, что сеть делает сама из чужого напитка: «Coke Float», «Coke
#: Freezee», молочный коктейль. Это уже её блюдо, она его снимает,
#: и чужой бренд в имени ничего не отменяет.
_MADE_BY_CHAIN = re.compile(
    r"\b(?:float|freeze|freezee|slush|slushie|icee|shakes?|frappe|"
    r"frosty|blizzard|sundae|cake|pie)\b", re.I)

#: Где кончается сама позиция и начинается уточнение: «Hollandaise
#: Sauce**, for** Build Your Own Omelet», «Big Fish Sandwich **With**
#: Tartar Sauce», «Spread **-** Hummus **-** Sandwich Portion».
_QUALIFIER = re.compile(r",|\bfor\b|\bwith\b|\bw/|\(|\s-\s|\s–\s", re.I)
#: Счёт в начале имени: «(30) Classic Bone-In Wings».
_LEADING_COUNT = re.compile(r"^\s*\(?\d+\)?\s*")
#: Канал подачи впереди имени: «**Drive Thru,** Fanta Orange, 20 fl oz».
#: Это не позиция, а откуда её берут, — и если принять её за голову, то
#: чужая бутылка станет блюдом Panera.
_CHANNEL = re.compile(r"^\s*drive[\s-]*thru\s*,\s*", re.I)


def _head(name: str) -> str:
    """Начало имени — то, чем позиция является.

    Без него правило читает упоминание соуса в составе блюда как сам
    соус, и «Cheese Ravioli with Meat Sauce» перестаёт быть едой.
    """
    text = _CHANNEL.sub("", " ".join(name.split()))
    text = _LEADING_COUNT.sub("", text)
    head = _QUALIFIER.split(text, maxsplit=1)[0].strip(" -–")
    return head or text


def needs_own_photo(name: str) -> bool:
    """Нужна ли позиции своя фотография.

    Ложь — место в меню у карточки есть, а собственного снимка не будет
    и не требуется: довольно общей картинки по архетипу. Так решено про
    добавки и про бутылки чужих брендов: сеть их не снимает и не станет.
    """
    if any(part.strip().lower() in _ALONE for part in name.split(",")):
        return False
    if " ".join(name.split()).lower() in _PLAIN:
        return False
    head = _head(name)
    if _MADE_BY_CHAIN.search(head):
        return True
    if _PACKAGED_BRANDS.search(head):
        return False
    # Мера подачи может стоять в несколько слоёв: «Sauce Dipping Cup».
    while (trimmed := _PORTION_TAIL.sub("", head)) != head:
        head = trimmed
    return not _ADD_ON_TAIL.search(head)
