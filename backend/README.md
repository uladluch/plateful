# Plateful — конвейер данных

Не сервер, а batch-конвейер. Ничего не работает 24/7.

```
источники сетей → адаптеры → валидация → Postgres (истина)
                                            ↓ экспорт
                    приложение ← Storage: pack.deflate + manifest.json
```

Приложение никогда не ходит в Postgres. Оно качает пак и держит копию в бандле.

## Что уже есть

| Файл | Что делает |
|---|---|
| `plateful_data/menustat.py` | Скачивает MenuStat 2018 с Harvard Dataverse (CC0), чистит |
| `plateful_data/validate.py` | Атуотер, диапазоны, дифф-проверка кроула |
| `plateful_data/pack.py` | Собирает пак и манифест, считает sha256 |
| `scripts/build_seed.py` | MenuStat → `plateful/Resources/seed-pack.json` |
| `scripts/load_seed.py` | Пак → Postgres |

## Быстрый старт

```bash
python3 backend/scripts/build_seed.py          # собрать пак (сеть нужна один раз)
cp backend/.env.example backend/.env           # вписать SUPABASE_DB_URL
pip install -r backend/requirements.txt
python3 backend/scripts/load_seed.py           # залить в Postgres
```

## Очистка MenuStat — три шага, каждый обязателен

1. Выбросить строки `Customizable_Builds = 'Accompanying Item'` — это перестановки
   комбо (напиток × гарнир × основное), 41 052 из 71 172.
2. Выбросить строки, где хоть один из четырёх макросов не парсится в число.
3. Дедуп по `(сеть, нормализованное имя)`.

Итог: **25 366 позиций, 96 сетей**, 4.94 МБ JSON / 0.56 МБ deflate.

## Валидация

Главная проверка — Атуотер, и она **асимметрична**:

- макросы дают больше энергии, чем заявлено калорий → **ошибка**, так не бывает;
- калорий больше, чем объясняют макросы → **предупреждение**: это алкоголь
  (7 ккал/г, не входит ни в один макрос). В сиде таких 873, все — Beverages.

Позиции с ошибками в пак не едут: 470 штук, среди них сэндвич с 368 г жира.
Они лежат в `data/problems.csv` и чинятся через таблицу `overrides`.

Дифф-проверка кроула: пропало >20% позиций или изменилось >30% → `crawls.status='held'`,
релиз не собирается. Это единственное, что стоит между редизайном сайта сети
и стёртой из приложения сетью.

## Дальше — адаптеры сетей

Интерфейс один:

```python
class Adapter(Protocol):
    chain: str
    def fetch(self) -> list[RawItem]: ...
```

Проверенные источники (2026-09-07):

| Сеть | Источник | Статус |
|---|---|---|
| Chick-fil-A | JSON в HTML страницы позиции | работает curl'ом |
| Taco Bell | `__NEXT_DATA__` на `/food`, 589 позиций | работает |
| Panera | 403 Akamai | Playwright или PDF |
| McDonald's | обрыв TLS, есть `dnaapp/itemDetails` | Playwright |
| Хвост | PDF nutrition guide | pdfplumber, кривые таблицы — через LLM |

Вежливость обязательна: 1 запрос/сек, честный User-Agent с контактом, robots.txt,
без обхода CAPTCHA и логинов, только с домена самой сети.

## Секреты

`.env` и GitHub Secrets. `SUPABASE_DB_URL` — строка подключения с паролем базы.
В клиент не попадает ничего: приложение знает только публичный URL пака.
