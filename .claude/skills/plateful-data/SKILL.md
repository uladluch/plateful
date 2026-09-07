---
name: plateful-data
description: Данные и бэкенд Plateful — MenuStat как seed, источники сетей, валидация, схема Supabase, контракт пака для приложения. Использовать при работе с датасетом, адаптерами-парсерами сетей, Supabase-схемой, экспортом пака, MenuRepository и любыми цифрами калорий/макросов.
---

# Plateful — данные и бэкенд

Полный план: `agent/backend-plan.md`. Разбор источников: `agent/data-source.md`,
`agent/research-2026-09-07.md`. Здесь — то, что нужно держать в голове.

## Supabase

Проект **`tnlmtyhuuqpjwuhzximh`** — `https://supabase.com/dashboard/project/tnlmtyhuuqpjwuhzximh`.
Подключён по MCP (`mcp__7f803660-…__*`). На 2026-09-07 схема `public` пустая.
DDL — только через `apply_migration`, данные — `execute_sql`.
Service key — только в GitHub Secrets / локальном `.env`, никогда в клиент.

## Архитектура: конвейер, не сервер

```
сайты сетей → адаптеры → нормализация → валидация → Postgres (истина)
                                                      ↓ экспорт
приложение ← Storage: packs/v{N}.json.gz (≈0.4 MB) + manifest.json
```
Клиент читает только `manifest.json` и пак. Пишет только `search_events` (anon key, RLS INSERT-only).
Seed-пак зашит в бандл — без сети и при лежащем Supabase приложение работает.

## Seed: MenuStat 2018, CC0

- Harvard Dataverse `doi:10.7910/DVN/K4NYTR`, файл 2018: `https://dataverse.harvard.edu/api/access/datafile/6191167`
  (расширение `.tab`, на деле CSV с кавычками, 71 172 строки, 50 колонок).
- Очистка: выбросить `Customizable_Builds == 'Accompanying Item'` (41 052 combo-перестановки),
  дедуп по `(Restaurant, lower(Item_Name))`, оставить строки с числовыми
  `Calories, Protein, Carbohydrates, Total_Fat` → **25 838 позиций, 96 сетей**, 2.1 MB / 0.37 MB gz.
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

1. **Атуотер**: `kcal ≈ 4·P + 4·C + 9·F` ±20% (шире для алкоголя/клетчатки). Ловит съехавшие колонки и галлюцинации LLM.
2. Диапазоны: 0–3000 ккал на позицию, макросы ≥ 0.
3. Дифф с прошлым кроулом: >30% изменилось или >20% пропало → `crawls.status='held'`, релиз не собирать.
4. Диапазоны комбо «730-1010» → `kcal_min/kcal_max`, не усреднять.

## Схема Postgres (целевая)

`chains` · `items` (версии через `valid_from/valid_to`, `stale`, `source`, `confidence`,
`kcal_min/max`) · `overrides` (ручные правки, живут отдельно и переживают кроулы) ·
`crawls` · `releases` (version, pack_url, sha256) · `search_events`.

## Контракт пака для приложения

```json
// manifest.json
{"version": 7, "url": ".../packs/v7.json.gz", "sha256": "…", "item_count": 25838, "released_at": "…"}
// pack: массив позиций
[{"chain":"McDonald's","name":"Big Mac","category":"Burgers","serving":"1 sandwich",
  "kcal":580,"protein":25,"carbs":45,"fat":34,"source":"mcdonalds.com","observed":"2026-09-07","stale":false}]
```
Версии пака immutable. В приложении `MenuRepository` — единственная граница; реализация
«бандл или скачанный пак, что новее», проверка sha256, атомарная подмена.

## Оркестрация

GitHub Actions cron: 8 ключевых сетей еженедельно, хвост ежемесячно (`chains.crawl_every`).
Секреты `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY` в GitHub Secrets. Стоимость ≈ $3–30/мес.
Приоритет новых адаптеров — по `search_events` с `matched=false`.
