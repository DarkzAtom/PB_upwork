# FX RATES ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/fxrates/admin`)

### GET /api/fxrates/admin/

Что: список курсов валют.
Как: выборка с пагинацией.
Почему: обзор доступных пар для конвертации.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..1000). SELECT всех записей, опциональная сортировка по времени обновления (`updated_at DESC`) если реализовано. Ответ: массив `{id, from_currency, to_currency, rate, updated_at}`. Ошибки: пустой массив при отсутствии данных; 422 при неверных типах параметров.
Структурировано:
Request: GET `/api/fxrates/admin/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50).
Steps:

1. Валидация параметров.
2. SELECT \* FROM fx_rates.
3. (Опционально) ORDER BY updated_at DESC.
4. OFFSET/LIMIT.
   Response: `[ { id:int, from_currency:str(3), to_currency:str(3), rate:decimal, updated_at:datetime } ]`.
   Errors: 422 (тип/диапазон параметров); пустой результат → [].
   Data: `fx_rates`.

### POST /api/fxrates/admin/

Что: создание нового курса.
Как: нормализация кодов валют, проверка отсутствия пары, сохранение.
Почему: добавление базовой информации для пересчёта цен.
Детали:
Тело: схема FxRateCreate — поля `from_currency`, `to_currency` (строки ISO 3), `rate` (decimal >0). Шаги: (1) Приведение кодов (upper-case); (2) Проверка, что пара (from,to) не существует (или уникальность направленной пары); (3) Валидация `rate > 0`; (4) INSERT с текущим `updated_at`; (5) COMMIT + REFRESH. Ответ: созданный курс. Ошибки: 409 при конфликте пары, 422 при rate ≤0.
Структурировано:
Request: POST `/api/fxrates/admin/`.
Body (FxRateCreate): `from_currency` (str 3, ISO), `to_currency` (str 3, ISO), `rate` (decimal >0).
Steps:

1. Нормализация валют to upper-case.
2. SELECT для проверки уникальной пары.
3. Проверка `rate>0`.
4. INSERT новой строки с timestamp.
5. COMMIT + REFRESH.
   Response: `{ id, from_currency, to_currency, rate, updated_at }`.
   Errors: 409 (пара существует); 422 (rate<=0 или неверная длина кодов); системные.
   Data: `fx_rates`.

### GET /api/fxrates/admin/{fxrate_id}

Что: деталь записи курса.
Как: выборка по ID.
Почему: просмотр параметров для проверки актуальности.
Детали:
Path: `fxrate_id` (int >0). SELECT по первичному ключу. Ответ: `{id, from_currency, to_currency, rate, updated_at}`. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/fxrates/admin/{fxrate_id}`.
Path: `fxrate_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: полный объект курса.
Errors: 404 (не найден); 422 (тип ID); системные.
Data: `fx_rates`.

### PUT /api/fxrates/admin/{fxrate_id}

Что: обновление полей курса.
Как: возможная смена кодов валют с проверкой уникальности пары; обновление значения и временной метки.
Почему: отражение свежих рыночных значений.
Детали:
Path: `fxrate_id`. Тело: FxRateUpdate (опциональные поля). Шаги: (1) SELECT курс; (2) если изменяются `from_currency`/`to_currency` — нормализация и проверка отсутствия уже существующей пары; (3) при изменении rate — валидация >0; (4) обновление полей; (5) обновление `updated_at` (текущее время); (6) COMMIT+REFRESH. Ответ: обновлённый объект. Ошибки: 404 (курс не найден), 409 (пара занята), 422 (rate ≤0).
Структурировано:
Request: PUT `/api/fxrates/admin/{fxrate_id}`.
Path: `fxrate_id` (int >0).
Body (FxRateUpdate): опциональные `from_currency`, `to_currency`, `rate`.
Steps:

1. SELECT запись.
2. Если None → 404.
3. При изменении валют нормализация и проверка уникальности пары.
4. Проверка `rate>0` при изменении.
5. Присвоение новых значений.
6. Обновление `updated_at`.
7. COMMIT + REFRESH.
   Response: обновлённый объект.
   Errors: 404 (нет записи); 409 (пара конфликт); 422 (rate<=0 / неверные коды).
   Data: `fx_rates`.

### DELETE /api/fxrates/admin/{fxrate_id}

Что: удаление курса.
Как: удаление по ID.
Почему: исключение неиспользуемой пары.
Детали:
Path: `fxrate_id`. Шаги: SELECT → 404 при отсутствии → DELETE → COMMIT. Ответ: статус 204. Ошибки: 404.
Структурировано:
Request: DELETE `/api/fxrates/admin/{fxrate_id}`.
Path: `fxrate_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.DELETE; 4.COMMIT.
Response: 204 No Content.
Errors: 404 (не найдено); 422 (тип ID); системные.
Data: `fx_rates`.

### POST /api/fxrates/admin/bulk-create

Что: массовое добавление курсов.
Как: итерация по входным данным и проверка каждой пары.
Почему: быстрое заполнение набора валют.
Детали:
Тело: массив FxRateCreate. Для каждого элемента: нормализация, проверка уникальности пары, валидация rate>0. Валидные добавляются; ошибки накапливаются в список. Один COMMIT. Ответ: `{total, created, failed, errors[]}`. Ошибки: индивидуальные — не прерывают процесс.
Структурировано:
Request: POST `/api/fxrates/admin/bulk-create`.
Body: `[ FxRateCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: нормализация валют; проверка пары; проверка rate>0.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,from_currency,to_currency}] }`.
   Errors: Ошибки элементов внутри списка; 422 (не массив / неверные данные).
   Data: `fx_rates`.

### POST /api/fxrates/admin/bulk-delete?fxrate_ids=...

Что: массовое удаление выбранных курсов.
Как: удаление записей по списку ID.
Почему: пакетное управление набором пар.
Детали:
Query: `fxrate_ids` (список int). Шаги: парсинг → для каждого SELECT → при наличии DELETE → счётчики. Один COMMIT. Ответ: `{total, deleted, failed}`. Ошибки: отсутствующие ID в failed.
Структурировано:
Request: POST `/api/fxrates/admin/bulk-delete`.
Query: `fxrate_ids` (CSV список int required).
Steps:

1. Парсинг CSV.
2. Для каждого id SELECT.
3. Если запись найдена → DELETE иначе failed++.
4. COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors?:[str] }`.
   Errors: 422 (пустой/неверный список); отсутствующие ID отражаются в failed.
   Data: `fx_rates`.

### PUT /api/fxrates/admin/update-rate?from_currency=...&to_currency=...&new_rate=...

Что: обновление значения курса по паре.
Как: поиск по комбинации валют, изменение `rate`, обновление времени.
Почему: оперативное изменение без идентификатора.
Детали:
Query: `from_currency`, `to_currency`, `new_rate` (decimal >0). Шаги: (1) Нормализация кодов; (2) SELECT по паре; (3) при отсутствии 404; (4) проверка `new_rate>0`; (5) обновление `rate` и `updated_at`; (6) COMMIT+REFRESH. Ответ: обновлённый объект. Ошибки: 404 (пара не найдена), 422 (new_rate ≤0).
Структурировано:
Request: PUT `/api/fxrates/admin/update-rate`.
Query: `from_currency` (str 3 required), `to_currency` (str 3 required), `new_rate` (decimal >0 required).
Steps:

1. Нормализация валют.
2. SELECT WHERE from_currency=:from AND to_currency=:to.
3. Если None → 404.
4. Проверка `new_rate>0`.
5. Обновление rate и updated_at.
6. COMMIT + REFRESH.
   Response: `{ id, from_currency, to_currency, rate, updated_at }`.
   Errors: 404 (нет пары); 422 (new_rate<=0 или неверные коды); системные.
   Data: `fx_rates`.

### GET /api/fxrates/admin/statistics

Что: сводные метрики (количество пар, min/max/avg).
Как: агрегаты по таблице.
Почему: обзор диапазона значений и разнообразия источников.
Детали:
Метрики: COUNT всех пар, MIN/MAX/AVG `rate`, распределение по базовой валюте (COUNT GROUP BY from_currency) и по целевой (GROUP BY to_currency) если включено. Ответ: `{total_pairs, rate_min, rate_max, rate_avg, base_currency_counts[], quote_currency_counts[]}`. Ошибки: при отсутствии данных значения null или 0.
Структурировано:
Request: GET `/api/fxrates/admin/statistics`.
Steps:

1. COUNT пар.
2. MIN/MAX/AVG rate.
3. GROUP BY from_currency.
4. GROUP BY to_currency.
   Response: `{ total_pairs:int, rate_min:decimal?, rate_max:decimal?, rate_avg:decimal?, base_currency_counts:[{currency:str,count:int}], quote_currency_counts:[{currency:str,count:int}] }`.
   Errors: Пусто → списки []; численные поля null/0.
   Data: `fx_rates`.

### GET /api/fxrates/admin/rate-pairs

Что: сводный перечень всех пар с текущими значениями.
Как: выборка всех строк, формирование словаря пар.
Почему: единый снимок состояния для интерфейса.
Детали:
Логика: SELECT всех курсов → преобразование в список или map вида `{from_currency_to_currency: rate}` или массив объектов. Ответ: структура текущих пар с rate и updated_at. Ошибки: пустой массив/объект при отсутствии.
Структурировано:
Request: GET `/api/fxrates/admin/rate-pairs`.
Steps:

1. SELECT всех курсов.
2. Формирование массива объектов или словаря.
   Response: `[ { from_currency:str, to_currency:str, rate:decimal, updated_at:datetime } ]` или `{ "USD_EUR":rate, ... }` (зависит от реализации).
   Errors: Пустой результат → [] / пустой объект.
   Data: `fx_rates`.
