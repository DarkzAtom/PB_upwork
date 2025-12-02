# SUPPLIER PRICE ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/supplierprice/admin`)

### GET /api/supplierprice/admin/all

Что: листинг цен поставщиков.
Как: выборка `SupplierPrice` с пагинацией.
Почему: обзор доступных офферов.
Детали:
Query: `skip` (≥0), `limit` (1..1000), опционально `part_id`, `supplier_id`, `warehouse_id` (если реализованы дополнительные фильтры). Порядок: базовый SELECT без сортировки либо по ID. Ответ: массив объектов `{id, part_id, supplier_id, warehouse_id, base_price, currency, available_qty, stock_status, lead_time_days}`. Ошибки: пустой результат → пустой массив.
Структурировано:
Request: GET `/api/supplierprice/admin/all`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50); `part_id` (int >0 optional); `supplier_id` (int >0 optional); `warehouse_id` (int >0 optional).
Path: отсутствует.
Body: отсутствует.
Steps:

1. Валидация параметров.
2. Базовый SELECT из `supplier_price`.
3. Применение фильтров по заданным FK.
4. OFFSET/LIMIT.
   Response: `[ { id:int, part_id:int, supplier_id:int, warehouse_id:int?, base_price:float, currency:str, available_qty:int?, stock_status:str?, lead_time_days:int? } ]`.
   Errors: 422 (невалидные параметры); пустой результат → `[]`.
   Data: `supplier_price`.

### POST /api/supplierprice/admin/

Что: создание записи цены.
Как: проверки существования части, поставщика, склада; вставка.
Почему: добавление нового оффера для расчёта стоимости.
Детали:
Тело: схема SupplierPriceCreate — включает `part_id`, `supplier_id`, `warehouse_id`, `base_price`, `currency`, `available_qty`, `stock_status`, `lead_time_days` (или диапазон). Шаги: (1) Проверка части; (2) Проверка поставщика; (3) Проверка склада; (4) INSERT + COMMIT; (5) REFRESH. Ответ: созданный объект. Ошибки: 404 если любой FK не найден.
Структурировано:
Request: POST `/api/supplierprice/admin/`.
Body (SupplierPriceCreate):
`part_id` (int >0) обязательное; `supplier_id` (int >0) обязательное; `warehouse_id` (int >0) обязательное; `base_price` (float >0); `currency` (str ISO код, длина 3); `available_qty` (int ≥0 optional); `stock_status` (str?); `lead_time_days` (int ≥0 или пара min/max если предусмотрено).
Steps:

1. Валидация тела.
2. SELECT часть.
3. SELECT поставщика.
4. SELECT склада.
5. INSERT строки.
6. COMMIT + REFRESH.
   Response: `{ id:int, part_id:int, supplier_id:int, warehouse_id:int, base_price:float, currency:str, available_qty:int?, stock_status:str?, lead_time_days:int? }`.
   Errors: 404 (отсутствует любой FK); 422 (валидация); прочие системные.
   Data: `parts`, `suppliers`, `warehouses`, `supplier_price`.

### GET /api/supplierprice/admin/statistics

Что: агрегированные показатели (количество, диапазоны цен, суммарная доступность).
Как: агрегаты MIN/MAX/AVG/SUM по полям.
Почему: обзор структуры цен и запасов.
Детали:
Расчёт: COUNT записей, MIN/MAX/AVG по `base_price`, SUM по `available_qty`, распределение по валютам (если реализовано) через группировку. Ответ: JSON `{total_offers, price_min, price_max, price_avg, total_available_qty}` + дополнительные поля. Ошибки: при отсутствии записей значения могут быть null либо 0.
Структурировано:
Request: GET `/api/supplierprice/admin/statistics`.
Steps:

1. COUNT(\*) из `supplier_price`.
2. MIN/MAX/AVG `base_price`.
3. SUM `available_qty`.
4. GROUP BY currency (если реализовано) → массив распределения.
   Response: `{ total_offers:int, price_min:float?, price_max:float?, price_avg:float?, total_available_qty:int?, currency_breakdown?:[ { currency:str, count:int } ] }`.
   Errors: Пустая таблица → численные поля могут быть 0 или null; системные.
   Data: `supplier_price`.

### GET /api/supplierprice/admin/low-stock?threshold=...

Что: цены с количеством ≤ порога.
Как: фильтр по `available_qty`.
Почему: выявление позиций на минимуме наличия.
Детали:
Query: `threshold` (int ≥0, по умолчанию значение может быть 0 или заданное). Логика: WHERE `available_qty <= threshold`. Ответ: массив записей ограниченных порогом. Ошибки: некорректный тип порога → 422.
Структурировано:
Request: GET `/api/supplierprice/admin/low-stock`.
Query: `threshold` (int ≥0 default=0).
Steps:

1. Валидация параметра.
2. SELECT WHERE available_qty <= :threshold.
3. Формирование массива.
   Response: `[ { id, part_id, supplier_id, available_qty, stock_status } ]`.
   Errors: 422 (отрицательное значение/не число).
   Data: `supplier_price`.

### GET /api/supplierprice/admin/upcoming-lead-time

Что: анализ показателей lead time.
Как: сбор всех записей и вычисление min/max/average.
Почему: понимание сроков поставки.
Детали:
Логика: агрегаты MIN/MAX/AVG по `lead_time_days` (либо min/max пар если диапазон). Ответ: `{lead_time_min, lead_time_max, lead_time_avg}`. Ошибки: при отсутствии данных значения null.
Структурировано:
Request: GET `/api/supplierprice/admin/upcoming-lead-time`.
Steps:

1. Агрегация MIN/MAX/AVG lead_time_days.
2. Формирование объекта.
   Response: `{ lead_time_min:int?, lead_time_max:int?, lead_time_avg:float? }`.
   Errors: Пусто → все поля null; системные.
   Data: `supplier_price`.

### GET /api/supplierprice/admin/find-best-price?part_id=...

Что: минимальная базовая цена для части.
Как: сортировка/поиск по `base_price` данного `part_id`.
Почему: определение выгодного источника закупки.
Детали:
Query: `part_id` (int >0). Шаги: фильтр по части → ORDER BY `base_price` ASC LIMIT 1. Ответ: запись предложения с минимальной ценой. Ошибки: 404 если ни одна цена не найдена для части.
Структурировано:
Request: GET `/api/supplierprice/admin/find-best-price`.
Query: `part_id` (int >0 required).
Steps:

1. Валидация `part_id`.
2. SELECT WHERE part_id=:part_id ORDER BY base_price ASC LIMIT 1.
3. Если нет строки → 404.
   Response: `{ id, part_id, supplier_id, warehouse_id, base_price, currency }`.
   Errors: 404 (нет цен для части); 422 (невалидный ID).
   Data: `supplier_price`.

### GET /api/supplierprice/admin/{price_id}

Что: деталь конкретной записи.
Как: выборка по ID.
Почему: просмотр параметров оффера.
Детали:
Path: `price_id`. SELECT по первичному ключу, возврат полного объекта. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/supplierprice/admin/{price_id}`.
Path: `price_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: полный объект записи.
Errors: 404 (не найдено); 422 (тип ID).
Data: `supplier_price`.

### PUT /api/supplierprice/admin/{price_id}

Что: обновление полей цены.
Как: проверки FK при изменении; применение данных.
Почему: актуализация условий поставки.
Детали:
Тело: SupplierPriceUpdate (все поля опциональны). Шаги: (1) SELECT запись; (2) при изменении part/supplier/warehouse — валидация существования; (3) обновление каждого изменяемого поля; (4) COMMIT + REFRESH. Ответ: обновлённая запись. Ошибки: 404 (не найдена), 422 (невалидные типы).
Структурировано:
Request: PUT `/api/supplierprice/admin/{price_id}`.
Path: `price_id` (int >0).
Body: любые из `part_id`, `supplier_id`, `warehouse_id`, `base_price`, `currency`, `available_qty`, `stock_status`, `lead_time_days`.
Steps:

1. SELECT запись.
2. Если None → 404.
3. При наличии изменений FK → проверка их существования.
4. Обновление значений.
5. COMMIT + REFRESH.
   Response: обновлённый объект.
   Errors: 404 (нет записи); 422 (валидация); системные.
   Data: `supplier_price`, `parts`, `suppliers`, `warehouses`.

### DELETE /api/supplierprice/admin/{price_id}

Что: удаление записи.
Как: удаление по ID.
Почему: выведение оффера из использования.
Детали:
Path: `price_id`. Шаги: SELECT → 404 при отсутствии → DELETE → COMMIT. Ответ: 204. Ошибки: 404.
Структурировано:
Request: DELETE `/api/supplierprice/admin/{price_id}`.
Path: `price_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.DELETE; 4.COMMIT.
Response: 204 No Content.
Errors: 404 (нет записи); 422 (тип ID).
Data: `supplier_price`.

### POST /api/supplierprice/admin/bulk-create

Что: массовое добавление цен.
Как: поэлементные проверки FK и сбор к вставке.
Почему: ускорение ввода большого количества предложений.
Детали:
Тело: массив SupplierPriceCreate. Итерация: на каждую запись проверки частей/поставщиков/складов; валидные добавляются в сессию; ошибки сохраняются в список. После цикла единый COMMIT. Ответ: `{total, created, failed, errors}`. Ошибки: дубликаты не проверяются если нет уникальных ограничений – проблемные FK в errors.
Структурировано:
Request: POST `/api/supplierprice/admin/bulk-create`.
Body: `[ SupplierPriceCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: валидация; проверка FK.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[ {id,...} ] }`.
   Errors: Ошибки элементов внутри списка; 422 если тело не массив.
   Data: `supplier_price`, `parts`, `suppliers`, `warehouses`.

### POST /api/supplierprice/admin/bulk-delete?price_ids=...

Что: массовое удаление выбранных цен.
Как: итерация по ID и удаление найденных.
Почему: пакетная очистка устаревших офферов.
Детали:
Query: `price_ids` (список int). Шаги: разбор списка → для каждого SELECT → при наличии DELETE → счётчик deleted / failed. Один COMMIT. Ответ: `{total, deleted, failed}`. Ошибки: отсутствующие ID заносятся в failed.
Структурировано:
Request: POST `/api/supplierprice/admin/bulk-delete`.
Query: `price_ids` (CSV список int, обязательный).
Steps:

1. Парсинг CSV.
2. Для каждого id SELECT.
3. Если запись найдена → DELETE иначе failed++.
4. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors?:[str] }`.
   Errors: 422 (пустой или неверный формат списка); отсутствующие ID отражаются в failed.
   Data: `supplier_price`.

### GET /api/supplierprice/admin/by-stock-status/{status}

Что: выборка по статусу наличия.
Как: фильтр ILIKE по `stock_status`.
Почему: сегментация предложений по состоянию запасов.
Детали:
Path: `status` (строка). WHERE stock_status ILIKE `%status%`. Ответ: массив записей. Ошибки: пустой массив если нет совпадений.
Структурировано:
Request: GET `/api/supplierprice/admin/by-stock-status/{status}`.
Path: `status` (str length 1..50?).
Steps: SELECT WHERE stock_status ILIKE '%status%'.
Response: `[ { id, stock_status, available_qty, part_id, supplier_id } ]`.
Errors: Пустой результат → []; 422 (пустая строка).
Data: `supplier_price`.

### GET /api/supplierprice/admin/by-part/{part_id}

Что: все цены для части.
Как: фильтр по `part_id`.
Почему: сравнение доступных источников для одного артикула.
Детали:
Path: `part_id`. WHERE part_id = :id. Ответ: массив всех цен. Ошибки: отсутствие цен → пустой массив (часть может существовать). 404 не генерируется.
Структурировано:
Request: GET `/api/supplierprice/admin/by-part/{part_id}`.
Path: `part_id` (int >0).
Steps: SELECT WHERE part_id=:id.
Response: `[ { id, part_id, supplier_id, base_price, currency } ]`.
Errors: 422 (тип ID); пустой массив если нет записей.
Data: `supplier_price`.

### GET /api/supplierprice/admin/by-supplier/{supplier_id}

Что: все цены данного поставщика.
Как: фильтр по `supplier_id`.
Почему: анализ ассортимента поставщика.
Детали:
Path: `supplier_id`. WHERE supplier_id = :id. Ответ: массив. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/supplierprice/admin/by-supplier/{supplier_id}`.
Path: `supplier_id` (int >0).
Steps: SELECT WHERE supplier_id=:id.
Response: `[ { id, supplier_id, part_id, base_price } ]`.
Errors: 422 (тип ID); пустой массив если нет.
Data: `supplier_price`.

### GET /api/supplierprice/admin/by-warehouse/{warehouse_id}

Что: цены по складу.
Как: фильтр `warehouse_id`.
Почему: оценка предложения конкретного склада.
Детали:
Path: `warehouse_id`. WHERE warehouse_id = :id. Ответ: массив. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/supplierprice/admin/by-warehouse/{warehouse_id}`.
Path: `warehouse_id` (int >0).
Steps: SELECT WHERE warehouse_id=:id.
Response: `[ { id, warehouse_id, part_id, supplier_id, base_price } ]`.
Errors: 422 (тип ID); пустой массив.
Data: `supplier_price`.

### GET /api/supplierprice/admin/filter/by-part-and-supplier?part_id=...&supplier_id=...

Что: цены пересечения части и поставщика.
Как: двойной фильтр по двум FK.
Почему: точечная выборка для анализа конкретной связки.
Детали:
Query: `part_id`, `supplier_id` (оба обязательны). WHERE part_id = :part AND supplier_id = :supplier. Ответ: массив (часто небольшой). Ошибки: отсутствие результатов → пустой массив; отсутствие одного из параметров → 422.
Структурировано:
Request: GET `/api/supplierprice/admin/filter/by-part-and-supplier`.
Query: `part_id` (int >0 required); `supplier_id` (int >0 required).
Steps:

1. Валидация обязательных параметров.
2. SELECT WHERE part_id=:part AND supplier_id=:supplier.
3. Формирование массива.
   Response: `[ { id, part_id, supplier_id, base_price, currency } ]`.
   Errors: 422 (отсутствует любой параметр или неверный тип); пустой массив если нет записей.
   Data: `supplier_price`.
