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
