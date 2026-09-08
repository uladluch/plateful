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

Состояние: 4 миграции, **96 сетей и 25 366 позиций загружены**, бакет Storage `packs`
публичный на чтение.
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

## USDA не использовать

`dataType=Branded` — упакованные товары с UPC, позиций меню нет. `totalHits` — OR по словам.
`DEMO_KEY` = 10 запросов/час. Nutritionix — $299/мес, не берём и не парсим (ToS, конкурент).

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
           "group":"coca-cola","size":"Large","sizeOrder":3}]}
```
Пак детерминирован (без даты внутри) — CI сверяет `plateful/Resources/seed-pack.json` с пересборкой.
Версии immutable.

Сжатие для Storage — **сырой DEFLATE** (`zlib.compressobj(..., -zlib.MAX_WBITS)`), а не
zlib-контейнер: у Apple `Data.decompressed(using: .zlib)` понимает именно его, и с обычным
`zlib.compress()` клиент бы не распаковал. Хеш в манифесте — по сжатым байтам.

## Размеры одного блюда

`sizes.py` склеивает «Coca Cola, Small/Medium/Large» в группу: позиция получает
`group` (slug базового имени), `size` (подпись сегмента) и `sizeOrder`. Три поля
приходят вместе или не приходят вовсе; одиночный размер группой не считается.
25 366 позиций → 2 296 групп → **20 986 карточек** в списках.

Ключ соответствия — **`(chain, ext_key)`, не `ext_key`**: он уникален только
внутри сети, и «Coca Cola, Small» есть у половины каталога. Пока ключом был
один `ext_key`, сети затирали друг другу позиции — у McDonald's кола получала
0, 0, 1, 2. Тесты: `backend/tests/`, `python3 -m unittest discover -s backend/tests`.

На клиенте: `MenuItem.size`, `MenuCatalog.sizeVariants(of:)`, свёртка списка —
`collapsingSizeVariants(_:)`. Порядок шагов **выборка → фильтр → свёртка**:
свёртка последней, иначе цель «до 500 ккал» вычеркнет группу из-за среднего
размера, хотя маленький в цель укладывается. Представитель группы — средний
размер, а если снят только один — снятый (у «Waffle Potato Fries» сеть сняла
только Large). Свёртки нет там, где выбирают порцию: `ItemPickerView`
(сравнение и сборка заказа) и «Recent» показывают конкретный размер.

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

136 тестов в `platefulTests/` (Swift Testing), гоняет `.github/workflows/ios-ci.yml`.
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

## Правило одного slug
`backend/plateful_data/slug.py` — единственная реализация `slugify`; `chains.slug` и `items.ext_key`
считаются им же; SQL-эквивалент `regexp_replace(lower(name), '[^a-z0-9]+', '-', 'g')`. Не дублировать.
