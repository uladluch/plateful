---
name: plateful-data
description: Данные и бэкенд Plateful — MenuStat как seed, источники сетей, валидация, схема Supabase, контракт пака для приложения. Использовать при работе с датасетом, адаптерами-парсерами сетей, Supabase-схемой, экспортом пака, MenuRepository и любыми цифрами калорий/макросов.
---

# Plateful — данные и бэкенд

Полный план: `agent/backend-plan.md`. Разбор источников: `agent/data-source.md`,
`agent/research-2026-09-07.md`. Здесь — то, что нужно держать в голове.

## Supabase

Проект **`tnlmtyhuuqpjwuhzximh`** — `https://supabase.com/dashboard/project/tnlmtyhuuqpjwuhzximh`.
Подключён по MCP (`mcp__7f803660-…__*`) **и по CLI**: `supabase link --project-ref tnlmtyhuuqpjwuhzximh`
работает без пароля базы — CLI поднимает временную роль по access-токену. Отсюда:
`supabase db push`, `supabase db query --linked -f file.sql`, `supabase migration list --linked`.
Это основной рабочий путь, паролей и service-ключей не требует.

Состояние: 7 миграций, **96 сетей и 25 366 позиций загружены**, бакет Storage `packs`
публичный на чтение.

**Производные значения материализуются в базу.** `items.section`,
`items.variant_*` заполняет `sync_taxonomy.py` по тем же правилам, что и пак, —
чтобы их видел SQL («сколько у сети завтраков», «все размеры блюда»), а база и
пак говорили одно и то же. Гонять его после каждой правки правил и до
`export_pack.py`.
**Миграции — в `supabase/migrations/` (конвенция Supabase CLI), версии совпадают с удалёнными.**
Новая миграция = файл там + `apply_migration` с тем же именем; не расходить.
Service key — только в GitHub Secrets / локальном `.env`, никогда в клиент.

## Архитектура: конвейер, не сервер

```
сайты сетей → адаптеры → нормализация → валидация → Postgres (истина)
                                                      ↓ экспорт
приложение ← Storage: packs/v{N}.deflate (0.56 MB) + manifest.json
```
Клиент читает только `manifest.json` и пак. Пишет только `search_events` (anon key, RLS INSERT-only).
Seed-пак зашит в бандл — без сети и при лежащем Supabase приложение работает.

## Seed: MenuStat 2018, CC0

- Harvard Dataverse `doi:10.7910/DVN/K4NYTR`, файл 2018: `https://dataverse.harvard.edu/api/access/datafile/6191167`
  (расширение `.tab`, на деле CSV с кавычками, 71 172 строки, 50 колонок).
- Очистка: выбросить `Customizable_Builds == 'Accompanying Item'` (41 052 combo-перестановки),
  дедуп по `(Restaurant, lower(Item_Name))`, оставить строки с числовыми
  `Calories, Protein, Carbohydrates, Total_Fat` → 25 836; минус 470 с противоречивыми числами
  (ошибки Атуотера) → **25 366 позиций в паке, 96 сетей**, 4.94 MB JSON / 0.56 MB deflate.
- Все 8 сетей из keywords есть. Нет Shake Shack и Sweetgreen.
- Помечать `stale=true`, `source='menustat-2018'`. Дрейф: Big Mac 540→580 ккал (жир +21%),
  Crunchy Taco совпадает. Топ-20 у 8 ключевых сетей сверить руками до релиза.

## Этикетка целиком, а не только БЖУ

В паке едут `sugar`, `satFat`, `sodium`, `fiber` — покрытие 98–100%. Они лежали
в MenuStat с самого начала (`Sugar`, `Saturated_Fat`, `Sodium`, `Dietary_Fiber`),
`menustat.Item` их парсил, но `pack.py` не отдавал, а `load_seed.py` не заливал —
данные терялись на первом шаге. Пак вырос с 0.70 до 0.86 MB deflate.

Причина, по которой они есть почти везде: **21 CFR 101.11** обязывает сети от 20
точек раскрывать по запросу всю этикетку, а не только калории — сахар, клетчатку,
насыщенные и трансжиры, холестерин, натрий. Именно из этого раскрытия и собран
MenuStat, отсюда совпадение колонок.

Не парсим `Trans_Fat` (83%) и `Cholesterol` (86%) — доступны, если понадобятся.
`Potassium` — 1%, бесполезен.

**Аллергенов в MenuStat нет вовсе** и быть не может: 21 CFR 101.11 их не требует,
а FALCPA распространяется на упаковку, не на рестораны. Раскрытие добровольное,
у каждой сети своё. Что публикуют те две сети, у которых есть адаптеры:

| Сеть | Где | Что |
|---|---|---|
| Chick-fil-A | тот же `data-wp-context`, что и калории | `allergens` («Milk, Egg, Soy, Wheat and Sesame»), полный `ingredients`, дисклеймер |
| McDonald's | `/dnaapp/itemDetails?item=<itemId>` | `item_allergen` («Contains»), `item_additional_allergen` («May Contain»), `item_ingredient_statement` |

Обе покрывают девять аллергенов FDA: яйца, молоко, пшеница, соя, арахис, орехи,
рыба, моллюски, кунжут.

**Глютен по этому полю определять нельзя.** У Chick-fil-A в составе курицы есть
`malted barley flour`, а в списке аллергенов ячменя нет — он не входит в девятку.
Фильтр «без глютена», построенный на аллергенах, назвал бы это блюдо безопасным.
McDonald's говорит прямо: «We do not promote any of our US menu items as
vegetarian, vegan or gluten-free».

## USDA не использовать

`dataType=Branded` — упакованные товары с UPC, позиций меню нет. `totalHits` — OR по словам.
`DEMO_KEY` = 10 запросов/час. Nutritionix — $299/мес, не берём и не парсим (ToS, конкурент).

## Подключение новой сети — с разведки, не с адаптера

```bash
python3 backend/scripts/probe_chain.py --menu https://www.example.com/menu
python3 backend/scripts/probe_chain.py https://www.example.com/menu/burger   # одна страница
```

`adapters/site.py` — общий извлекатель. Лесенка из трёх видов разметки, каждый
дополняет предыдущий: **JSON-LD** (schema.org `Product`/`NutritionInformation`,
сеть кладёт ради поисковиков и потому держит в порядке) → **вшитый JSON**
(`__NEXT_DATA__`, `data-wp-context`, голое `"nutrition":[...]`) → **Open Graph**
(имя и снимок). Сработал любой — сеть подключается **без своего кода**.

Два предохранителя, оба заработаны на живых данных:
- **потолки правдоподобия** — во вшитом JSON лежит всё состояние страницы, ключ
  `calories` встречается не только у еды; разведка по Taco Bell принесла блюдо
  на 6 700 205 ккал (чужой идентификатор, из которого `to_number` выкусил цифры);
- **минимум два поля в блоке** — одинокий `calories` посреди чужого JSON почти
  наверняка совпадение.

**Что показала разведка 2026-09-08.** Chick-fil-A отдаёт общим извлекателем всё
сразу: имя, снимок, восемь полей этикетки, аллергены, полный состав. Wendy's,
Burger King, Popeyes, KFC, Dunkin', Panera, Sonic, Jack in the Box, Subway,
Starbucks, Taco Bell — ничего: индексы меню пустые оболочки под JS, часть отвечает
403/404/308. **Лёгких сетей почти не осталось**, дальше PDF-гайды или браузер.

## Рецепт McDonald's: страница есть, а данных в ней нет

Единственный отработанный обход, `adapters/mcdonalds.py`:

1. Страница позиции — пустая оболочка. Данные брать со **страницы калькулятора
   питания**: она отдаёт разом все плитки блюд.
2. Обычный запрос сеть отвергает обрывом TLS — смотрят на отпечаток рукопожатия.
   Помогает `curl` с полным набором браузерных заголовков (`BROWSER_HEADERS`).
   **Playwright для этого не нужен.**
3. Снимки на Adobe Scene7. **Пресет в конце пути срезать обязательно**:
   `:nutrition-calculator-tile` режет кадр в 1000×600, без пресета отдаётся
   исходный квадрат 1564×1564.
4. Название зашито в имя файла CamelCase вперемешку с датами и артикулами:
   `DC_202201_0007-005_QuarterPounderwithCheese_1564x1564-1`.
5. Аллергены и состав — `/dnaapp/itemDetails?...&item=<itemId>`: `item_allergen`
   («Contains»), `item_additional_allergen` («May Contain»),
   `item_ingredient_statement`. itemId лежат на странице калькулятора.

Сопоставление снимка с позицией — самое хрупкое место конвейера. Все правила, на
которых матчер уже ошибался, закреплены в `backend/tests/test_photo_match.py`;
трогать матчер только через них.

## Источники сетей (проверено 2026-09-07)

| Сеть | Источник | Статус |
|---|---|---|
| Chick-fil-A | страница позиции `/menu/<slug>`, в HTML JSON `"nutrition":[{"key":"calories","value":420},…]` | ✅ работает curl'ом |
| Taco Bell | `/food` → `__NEXT_DATA__`, 589 позиций с `calories`; макросы на лейбле позиции (хостится на nutritionix.com — использовать в крайнем случае) | ✅ |
| Panera | 403 Akamai | Playwright или PDF-гайд |
| McDonald's | TLS-обрыв (бот-защита); есть `dnaapp/itemDetails` JSON | Playwright с браузерными заголовками |
| Subway, BK, Wendy's, хвост | PDF nutrition guide | pdfplumber → при кривой таблице LLM-экстракция в схему |

Вежливость: 1 req/s, честный UA с контактом, robots.txt, без обхода CAPTCHA и логинов.
Только с домена сети. Пищевые факты не защищены копирайтом (Feist), публикация обязательна (21 CFR 101.11).

## Валидация — обязательна для каждого кроула

1. **Атуотер асимметричный**: макросы дают больше ккал, чем заявлено (>25%) — **ошибка**, так не бывает;
   заявлено больше, чем объясняют макросы — **предупреждение** (алкоголь, 7 ккал/г, не в макросах).
   Ошибки в пак не едут, лежат в `backend/data/problems.csv`, чинятся через `overrides`.
2. Диапазоны: до 5000 ккал (целые пироги бывают), >2000 — предупреждение; макросы ≥ 0.
3. Дифф с прошлым кроулом: >30% изменилось или >20% пропало → `crawls.status='held'`, релиз не собирать.
4. Диапазоны комбо «730-1010» → `kcal_min/kcal_max`, не усреднять.

## Схема Postgres (целевая)

`chains` · `items` (версии через `valid_from/valid_to`, `stale`, `source`, `confidence`,
`kcal_min/max`) · `overrides` (ручные правки, живут отдельно и переживают кроулы) ·
`crawls` · `releases` (version, pack_url, sha256) · `search_events`.

## Контракт пака для приложения (реализован в `backend/plateful_data/pack.py`)

```json
// manifest.json — единственное место с датой релиза
{"format":1,"version":1,"url":".../object/public/packs/v1.deflate","sha256":"<sha256 deflate>","itemCount":25366,"releasedAt":"2026-09-07"}
// пак (JSON; для Storage — raw deflate/zlib, читается Data.decompressed(using: .zlib) без зависимостей)
{"format":1,"version":1,"source":"menustat-2018","observed":"2018-12-31",
 "chains":[{"name":"McDonald's","itemCount":223}],
 "items":[{"chain":"McDonald's","key":"big-mac","name":"Big Mac","category":"Burgers","serving":null,
           "kcal":540.0,"protein":25.0,"carbs":46.0,"fat":28.0,
           "section":"Beverages",
           "variant":{"group":"coca-cola","label":"Large","order":3,"kind":"size","base":"Coca Cola"}}]}
```
Пак детерминирован (без даты внутри) — CI сверяет `plateful/Resources/seed-pack.json` с пересборкой.
Версии immutable.

Сжатие для Storage — **сырой DEFLATE** (`zlib.compressobj(..., -zlib.MAX_WBITS)`), а не
zlib-контейнер: у Apple `Data.decompressed(using: .zlib)` понимает именно его, и с обычным
`zlib.compress()` клиент бы не распаковал. Хеш в манифесте — по сжатым байтам.

## Разделы меню — `taxonomy.py`

Источник даёт 12 категорий, единых для всех сетей. Не хватало двух вещей:

- **Порядка.** Его не было вовсе — разделы шли по алфавиту первого блюда, и меню
  McDonald's открывалось напитками, а соусы стояли выше картошки. `SECTION_ORDER`
  задаёт один порядок на каталог, он едет в паке (`pack["sections"]`) — значит
  меняется публикацией. Пак без этого поля (v1–v12) клиент раскладывает по порядку
  первого появления, как раньше.
- **Завтрака.** Это время дня, а не категория: в источнике он размазан по
  `Sandwiches` (193) и `Entrees` (123), у McDonald's из 14 «сэндвичей» 11 завтраки.
  Правило осторожное — либо слово, которое само значит завтрак (`McMuffin`,
  `Hotcakes`, `Oatmeal`), либо носитель плюс начинка (`Biscuit` + `Sausage`).
  Одного «Bagel» мало: это и `Bacon, Egg & Cheese Bagel`, и `Blueberry Bagel`.
  Пропустить завтрак дешевле, чем записать в него обед. **1124 позиции у 57 сетей.**

## Варианты одного блюда — `variants.py`

Три правила, по убыванию надёжности:

    Coca Cola, Large          порция в хвосте после запятой
    10 Chicken McNuggets      счёт или вес перед названием
    Big Breakfast w/ Hotcakes опция после «w/»

Позиция получает `variant: {group, label, order, kind, base}`, где `kind` — `size`
или `option`, а `base` — название без варианта («Chicken McNuggets»). База едет
в паке, а не режется на клиенте: правило отрезания знает только тот, кто
отрезал, и первая же попытка повторить его в Swift разошлась с конвейером в
регистре единицы («3 piece» против «3 Piece»). 25 366 позиций → 3 573 группы → **18 680 карточек**; у McDonald's
102 живые позиции складываются в 58 карточек.

**Словарь размеров выводится из данных, а не пишется по сетям.** «Shorti» у Wawa,
«RT 44» у Sonic, «6 in» у Subway, «Venti Iced» у Starbucks — перечислять это
руками значит перебирать рестораны по очереди, и каждая новая сеть потребует
того же. Размер узнаётся по поведению: сеть повторяет слово у многих разных блюд
(`MIN_SHARED_BASES = 3`). От ингредиентов защищает длина хвоста — у
«Egg & Cheese Biscuit» тоже три разных начала (Bacon, Sausage, Steak), и без
`MAX_LEARNED_WORDS = 2` бекон, сосиска и стейк склеились бы в одно блюдо.

Ключ соответствия — **`(chain, ext_key)`, не `ext_key`**: он уникален только
внутри сети, и «Coca Cola, Small» есть у половины каталога. Пока ключом был
один `ext_key`, сети затирали друг другу позиции — у McDonald's кола получала
0, 0, 1, 2. Тесты: `backend/tests/`, `python3 -m unittest discover -s backend/tests`.

На клиенте: `MenuItem.variant`, `MenuCatalog.variants(of:)`, свёртка списка —
`collapsingVariants(_:)`. Порядок шагов **выборка → фильтр → свёртка**:
свёртка последней, иначе цель «до 500 ккал» вычеркнет группу из-за среднего
размера, хотя маленький в цель укладывается. Представитель группы — средний
вариант, а если снят только один — снятый (у «Waffle Potato Fries» сеть сняла
только Large). Свёртки нет там, где выбирают порцию: `ItemPickerView`
(сравнение и сборка заказа) и «Recent» показывают конкретный вариант.
Сегменты до шести подписей, дальше системный список; порции сокращаются
до буквы (`XS S M L XL`), исполнения — нет.

Происхождение (`source`, `observed`, `stale`) лежит на уровне пака, а у позиции появляется
только если отличается — то есть после правки в `overrides`. В сиде таких нет, в паке из базы
одна (Big Mac).

## Клиент: слой данных готов (`plateful/Menu/`)

| Файл | Что делает |
|---|---|
| `MenuPack.swift` | Контракт пака, отвергает чужой `format` и пустой пак |
| `MenuItem.swift` | Позиция; `persistentID` (chain+key) переживает обновление пака |
| `TextIndex.swift` | Нормализация и байтовый поиск, один плоский буфер вместо 50 тысяч строк |
| `MenuCatalog.swift` | Каталог целиком в памяти, поиск 1–2 мс по 25 тысячам позиций |
| `PackStore.swift` | Выбор пака (бандл/скачанный), sha256, распаковка, атомарная подмена |
| `MenuRepository.swift` | `@MainActor @Observable` фасад; разбор пака вне главного потока |

Типы данных помечены `nonisolated`: проект собран с `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`,
что верно для SwiftUI, но не для каталога.

Апостроф при нормализации **выпадает**, а не становится пробелом: иначе «McDonald's» → `mcdonald s`
и запрос «mcdonalds» не находит ничего. Это поймал живой прогон, тест закреплён.

148 тестов в `platefulTests/` (Swift Testing), гоняет `.github/workflows/ios-ci.yml`.
Загрузка сида на симуляторе — около 260 мс, вне главного потока.

## Оркестрация

- `.github/workflows/backend-ci.yml` — на каждый пуш в `backend/`: собрать пак, проверить, что бандл актуален.
- `.github/workflows/publish-pack.yml` — вручную: seed → Postgres (`load_seed.py`), пак → Storage через
  Storage REST API (curl, без своего клиента). Секреты: `SUPABASE_DB_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- Кроулы (позже): cron, 8 ключевых сетей еженедельно, хвост ежемесячно (`chains.crawl_every`);
  добавится `ANTHROPIC_API_KEY` для PDF-экстракции. Стоимость ≈ $3–30/мес.
- Приоритет новых адаптеров — по `search_events` с `matched=false`.

## Два пака

- `build_seed.py`: MenuStat → `plateful/Resources/seed-pack.json`. Детерминирован, в бандле, CI сверяет.
- `export_pack.py --version N`: `items_export` (с overrides) → `pack-vN.deflate` для Storage.

Проверка, что overrides доезжают: Big Mac — 540 ккал в сиде, 580 в паке из базы,
сырая строка кроула не изменена.

**`items_export` — самое хрупкое место конвейера.** Пак собирается из неё, и
достаточно пересоздать вью по устаревшему определению, чтобы молча отвалились
снимки блюд и пометки о снятых с меню: так v12 потерял 150 фотографий и 121
архивную позицию. Полное определение вью лежит в миграции `menu_taxonomy` —
только там оно записано целиком. `export_pack.py` сравнивает новый пак с
предыдущим — с диска, а в CI из Storage — и отказывается собирать пак, который
беднее больше чем на 5%. `publish_pack.sh` перед сборкой гоняет `sync_taxonomy.py`,
чтобы база несла те же разделы и варианты, что и пак.

## Что клиент берёт у Supabase — и чего нет

Клиент ходит только за публичными файлами Storage (`manifest.json`, `vN.deflate`)
обычным `URLSession`. SDK там нечего делать: это GET публичного объекта, и лишняя
зависимость с Auth и Realtime внутри ничего не добавит. Единственное, что клиенту
разрешено писать, — `search_events` (policy `search_events_insert_anon`), и это
**не реализовано**: продуктовое решение о телеметрии поиска не принято. Если
принимать — брать `supabase-swift` только с продуктом `PostgREST`, слать лишь
`matched=false` и без текста запроса целиком.

Бэкенд ходит через `supabase` CLI по access-токену, без service-ключа и пароля
базы; `supabase-py` потребовал бы service-ключ в локальном окружении — не надо.
Советники (`get_advisors`) чистые: 7 таблиц с RLS без политик — так и задумано,
клиент их не читает.

## Правило одного slug
`backend/plateful_data/slug.py` — единственная реализация `slugify`; `chains.slug` и `items.ext_key`
считаются им же; SQL-эквивалент `regexp_replace(lower(name), '[^a-z0-9]+', '-', 'g')`. Не дублировать.
