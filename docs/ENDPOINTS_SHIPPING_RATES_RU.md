# SHIPPING RATES ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/shippingrates/admin`)

### GET /api/shippingrates/admin/

Что: листинг тарифов доставки.
Как: выборка с пагинацией.
Почему: управление тарифной матрицей.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..1000), опционально фильтры `carrier`, `zone_id`, `region` если реализованы. SELECT всех тарифов; возможная сортировка по `min_weight ASC`. Ответ: массив `{id, shipping_zone_id, carrier, min_weight, max_weight, base_rate, currency, warehouse_region}`. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/shippingrates/admin/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50); `carrier` (str optional); `zone_id` (int >0 optional); `region` (str optional).
Steps:

1. Валидация параметров.
2. SELECT \* FROM shipping_rates.
3. Применение фильтров по zone/carrier/region если заданы.
4. (Опционально) ORDER BY min_weight ASC.
5. OFFSET/LIMIT.
   Response: `[ { id:int, shipping_zone_id:int, carrier:str, min_weight:decimal, max_weight:decimal, base_rate:decimal, currency:str(3), warehouse_region:str? } ]`.
   Errors: 422 (невалидные параметры); пустой результат → [].
   Data: `shipping_rates`.

### POST /api/shippingrates/admin/

Что: создание тарифа.
Как: проверка существования зоны и границ веса; вставка.
Почему: добавление правила расчёта стоимости доставки.
Детали:
Тело: схема ShippingRateCreate: `shipping_zone_id` (int >0), `carrier` (строка), `min_weight` (decimal ≥0), `max_weight` (decimal ≥ min_weight), `base_rate` (decimal ≥0), `currency` (строка ISO), `warehouse_region` (строка опционально). Шаги: (1) Проверка существования зоны; (2) Валидация отношений веса (min ≤ max); (3) INSERT + COMMIT + REFRESH. Ответ: созданный тариф. Ошибки: 404 (зона не найдена), 422 (min/max нарушены).
Структурировано:
Request: POST `/api/shippingrates/admin/`.
Body (ShippingRateCreate):
`shipping_zone_id` (int >0 обязательное)
`carrier` (str 1..120 обязательное)
`min_weight` (decimal ≥0 обязательное)
`max_weight` (decimal ≥min_weight обязательное)
`base_rate` (decimal ≥0 обязательное)
`currency` (str 3 ISO обязательное)
`warehouse_region` (str optional)
Steps:

1. Валидация тела.
2. SELECT зона.
3. Проверка min_weight ≤ max_weight.
4. INSERT строки.
5. COMMIT + REFRESH.
   Response: `{ id, shipping_zone_id, carrier, min_weight, max_weight, base_rate, currency, warehouse_region? }`.
   Errors: 404 (нет зоны); 422 (валидация/отношение весов); системные.
   Data: `shipping_zones`, `shipping_rates`.

### POST /api/shippingrates/admin/bulk-create

Что: массовое добавление тарифов.
Как: последовательные проверки зоны и интервала веса; пакетная вставка.
Почему: ускоренное заполнение матрицы.
Детали:
Тело: массив ShippingRateCreate. Итерация: для каждого элемента — проверка зоны, проверка min/max. Валидные добавляются; ошибки фиксируются. Один COMMIT. Ответ: `{total, created, failed, errors[]}`. Ошибки: индивидуальные — не прерывают процесс.
Структурировано:
Request: POST `/api/shippingrates/admin/bulk-create`.
Body: `[ ShippingRateCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждой записи: валидация; SELECT зона; проверка min/max.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,carrier}] }`.
   Errors: Ошибки элементов внутри `errors`; 422 (не массив).
   Data: `shipping_rates`, `shipping_zones`.

### POST /api/shippingrates/admin/bulk-delete?rate_ids=...

Что: массовое удаление тарифов.
Как: удаление по списку ID.
Почему: актуализация набора тарифов.
Детали:
Query: `rate_ids` (список int). Шаги: парсинг → для каждого SELECT → при наличии DELETE → счётчики. Один COMMIT. Ответ: `{total, deleted, failed}`. Ошибки: отсутствующие ID в failed.
Структурировано:
Request: POST `/api/shippingrates/admin/bulk-delete`.
Query: `rate_ids` (CSV список int required).
Steps:

1. Парсинг списка.
2. Для каждого id SELECT.
3. Если найдено → DELETE иначе failed++.
4. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors?:[str] }`.
   Errors: 422 (пустой/неверный список); отсутствующие ID в failed.
   Data: `shipping_rates`.

### GET /api/shippingrates/admin/statistics

Что: сводные показатели (кол-во тарифов, диапазоны цен, уникальные перевозчики/регионы).
Как: агрегаты по таблице.
Почему: обзор структуры тарифной модели.
Детали:
Метрики: COUNT тарифов, MIN/MAX/AVG `base_rate`, количество уникальных `carrier`, количество уникальных `warehouse_region`, распределение по зонам (COUNT GROUP BY shipping_zone_id). Ответ: объект статистики. Ошибки: при отсутствии данных значения null или 0.
Структурировано:
Request: GET `/api/shippingrates/admin/statistics`.
Steps:

1. COUNT тарифов.
2. MIN/MAX/AVG base_rate.
3. COUNT DISTINCT carrier.
4. COUNT DISTINCT warehouse_region.
5. GROUP BY shipping_zone_id.
   Response: `{ total:int, rate:{min:decimal?, max:decimal?, avg:decimal?}, distinct:{carriers:int, regions:int}, by_zone:[{shipping_zone_id:int,count:int}] }`.
   Errors: Пусто → нули/null; системные.
   Data: `shipping_rates`.

### GET /api/shippingrates/admin/by-carrier/{carrier}

Что: статистика тарифов конкретного перевозчика.
Как: выборка ILIKE по `carrier` и вычисление показателей.
Почему: анализ предложения перевозчика.
Детали:
Path: `carrier` (строка). WHERE carrier ILIKE `%carrier%`. Дополнительно: агрегаты по найденным тарифам (COUNT, MIN/MAX/AVG base_rate, суммарное покрытие веса: MIN min_weight, MAX max_weight). Ответ: объект `{carrier_query, count, rate_min, rate_max, rate_avg, weight_min, weight_max}` + массив тарифов. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/shippingrates/admin/by-carrier/{carrier}`.
Path: `carrier` (str 1..120).
Steps:

1. SELECT тарифы WHERE carrier ILIKE '%carrier%'.
2. Агрегация показателей.
   Response: `{ carrier_query:str, count:int, rate_min:decimal?, rate_max:decimal?, rate_avg:decimal?, weight_min:decimal?, weight_max:decimal?, items:[{id,shipping_zone_id,carrier,min_weight,max_weight,base_rate,currency}] }`.
   Errors: Пустой набор → count=0, items=[].
   Data: `shipping_rates`.

### GET /api/shippingrates/admin/by-zone/{zone_id}

Что: тарифы определённой зоны.
Как: фильтр `shipping_zone_id`.
Почему: изучение стоимости для заданной географии.
Детали:
Path: `zone_id` (int >0). WHERE shipping_zone_id = :zone. Ответ: массив. Ошибки: пустой массив если зона существует но тарифов нет; 404 не генерируется при отсутствии тарифов.
Структурировано:
Request: GET `/api/shippingrates/admin/by-zone/{zone_id}`.
Path: `zone_id` (int >0).
Steps: SELECT WHERE shipping_zone_id=:zone.
Response: `[ { id, shipping_zone_id, carrier, min_weight, max_weight, base_rate, currency } ]`.
Errors: 422 (тип ID); пустой массив.
Data: `shipping_rates`.

### GET /api/shippingrates/admin/by-region/{region}

Что: тарифы по региону склада.
Как: фильтр ILIKE по `warehouse_region`.
Почему: сопоставление логистических регионов и стоимости.
Детали:
Path: `region` (строка). WHERE warehouse_region ILIKE `%region%`. Ответ: массив тарифов. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/shippingrates/admin/by-region/{region}`.
Path: `region` (str 1..120).
Steps: SELECT WHERE warehouse_region ILIKE '%region%'.
Response: `[ { id, warehouse_region, carrier, min_weight, max_weight, base_rate } ]`.
Errors: Пустой массив.
Data: `shipping_rates`.

### GET /api/shippingrates/admin/search?carrier=...

Что: поиск тарифов по перевозчику.
Как: фильтр ILIKE по `carrier`.
Почему: быстрый доступ к нужным записям.
Детали:
Query: `carrier` (строка, обязательна). WHERE carrier ILIKE `%carrier%`. Ответ: массив тарифов. Ошибки: 422 при отсутствии параметра, пустой массив при отсутствии совпадений.
Структурировано:
Request: GET `/api/shippingrates/admin/search`.
Query: `carrier` (str 1..120 required).
Steps: SELECT WHERE carrier ILIKE '%carrier%'.
Response: `[ { id, carrier, shipping_zone_id, base_rate } ]`.
Errors: 422 (пустой/нет параметра); пустой массив.
Data: `shipping_rates`.

### GET /api/shippingrates/admin/find-rate?zone_id=...&weight=...&carrier=...

Что: подбор тарифов, покрывающих вес в зоне, с опциональным фильтром перевозчика.
Как: условия по диапазону веса и зоне, дополнительный фильтр по перевозчику.
Почему: определение применимого тарифа для расчёта доставки.
Детали:
Query: `zone_id` (int >0), `weight` (decimal >0), опционально `carrier` (строка). WHERE shipping_zone_id = :zone AND min_weight <= :weight AND max_weight >= :weight; если carrier указан — AND carrier ILIKE `%carrier%`. Ответ: массив подходящих тарифов (обычно 1). Ошибки: 422 при weight ≤0; пустой массив если не найден.
Структурировано:
Request: GET `/api/shippingrates/admin/find-rate`.
Query: `zone_id` (int >0 required); `weight` (decimal >0 required); `carrier` (str optional).
Steps:

1. Валидация параметров.
2. SELECT WHERE shipping_zone_id=:zone AND :weight BETWEEN min_weight AND max_weight.
3. Доп. фильтр carrier ILIKE если задан.
   Response: `[ { id, carrier, shipping_zone_id, min_weight, max_weight, base_rate, currency } ]`.
   Errors: 422 (weight<=0 или zone_id невалиден); [] если нет совпадений.
   Data: `shipping_rates`.

### GET /api/shippingrates/admin/{rate_id}

Что: деталь тарифа.
Как: выборка по ID.
Почему: просмотр параметров интервала.
Детали:
Path: `rate_id` (int). SELECT запись. Ответ: полный объект. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/shippingrates/admin/{rate_id}`.
Path: `rate_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id, shipping_zone_id, carrier, min_weight, max_weight, base_rate, currency, warehouse_region? }`.
Errors: 404 (нет тарифа); 422 (тип ID).
Data: `shipping_rates`.

### PUT /api/shippingrates/admin/{rate_id}

Что: обновление тарифа.
Как: проверка зоны при изменении, контроль границ веса, частичное применение.
Почему: поддержание актуальности стоимости.
Детали:
Path: `rate_id`. Тело: ShippingRateUpdate (опциональные поля). Шаги: (1) SELECT; (2) при изменении `shipping_zone_id` — проверка существования; (3) получение новых min/max значений для проверки min ≤ max; (4) обновление полей; (5) COMMIT+REFRESH. Ответ: обновлённый тариф. Ошибки: 404 (не найден), 422 (min/max нарушены).
Структурировано:
Request: PUT `/api/shippingrates/admin/{rate_id}`.
Path: `rate_id` (int >0).
Body (ShippingRateUpdate): любые из `shipping_zone_id`, `carrier`, `min_weight`, `max_weight`, `base_rate`, `currency`, `warehouse_region`.
Steps:

1. SELECT тариф.
2. Если None → 404.
3. Если меняется `shipping_zone_id` → проверка зоны.
4. Сбор новых min/max → проверка min ≤ max.
5. Обновление значений.
6. COMMIT + REFRESH.
   Response: обновлённый объект тарифа.
   Errors: 404 (нет тарифа); 422 (валидация / отношение весов); системные.
   Data: `shipping_rates`, `shipping_zones`.

### DELETE /api/shippingrates/admin/{rate_id}

Что: удаление тарифа.
Как: удаление по ID.
Почему: управление жизненным циклом интервала стоимости.
Детали:
Path: `rate_id`. Шаги: SELECT → 404 при отсутствии → DELETE → COMMIT. Ответ: 204. Ошибки: 404.
Структурировано:
Request: DELETE `/api/shippingrates/admin/{rate_id}`.
Path: `rate_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.DELETE; 4.COMMIT.
Response: 204 No Content.
Errors: 404 (нет тарифа); 422 (тип ID).
Data: `shipping_rates`.
