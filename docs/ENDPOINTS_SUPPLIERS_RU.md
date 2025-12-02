# SUPPLIERS ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/suppliers/admin`)

### GET /api/suppliers/admin/search?name=...

Что: поиск поставщиков по имени.
Как: `Supplier.name ILIKE %name%` + пагинация.
Почему: быстрый выбор конкретного поставщика.
Детали:
Query: `name` (строка), `skip` (int ≥0), `limit` (int 1..1000). WHERE name ILIKE `%name%`; OFFSET/LIMIT. Ответ: массив `{id, name}`. Ошибки: пустой массив при отсутствии совпадений; 422 если нет обязательного параметра name или тип не строка.
Структурировано:
Request: GET `/api/suppliers/admin/search`.
Query: `name` (str 1..120 required); `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50).
Steps:

1. Валидация обязательного `name`.
2. SELECT WHERE name ILIKE '%name%'.
3. OFFSET/LIMIT.
   Response: `[ { id:int, name:str } ]`.
   Errors: 422 (пустой/отсутствует name); пустой массив при отсутствии совпадений.
   Data: `suppliers`.

### GET /api/suppliers/admin/all

Что: листинг поставщиков.
Как: выборка с расширенным лимитом.
Почему: управление реестром поставщиков.
Детали:
Query: `skip`, `limit`. SELECT всех поставщиков. Возможная сортировка по имени. Ответ: массив `{id, name}`. Ошибки: пустой массив если нет записей.
Структурировано:
Request: GET `/api/suppliers/admin/all`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 100).
Steps:

1. Валидация параметров.
2. SELECT \* FROM suppliers.
3. (Опционально) ORDER BY name.
4. OFFSET/LIMIT.
   Response: `[ { id:int, name:str } ]`.
   Errors: 422 (невалидные числовые параметры); пустой массив.
   Data: `suppliers`.

### GET /api/suppliers/admin/statistics

Что: агрегаты по наличию связанных сущностей (склады, цены, правила).
Как: подсчёт distinct по джойнам.
Почему: обзор степени интеграции поставщиков.
Детали:
Метрики: общее число поставщиков; количество поставщиков со складами (JOIN warehouses); со ценами (JOIN supplier_price); с правилами (JOIN pricing_rules); распределение по количеству складов (GROUP BY supplier_id COUNT warehouses). Ответ: объект `{suppliers_total, suppliers_with_warehouses, suppliers_with_prices, suppliers_with_rules, warehouse_distribution: [{supplier_id, warehouses_count}]}`. Ошибки: при отсутствии данных значения 0 или пустые массивы.
Структурировано:
Request: GET `/api/suppliers/admin/statistics`.
Steps:

1. COUNT всех поставщиков.
2. COUNT DISTINCT поставщиков с складами.
3. COUNT DISTINCT поставщиков с прайсами.
4. COUNT DISTINCT поставщиков с правилами.
5. GROUP BY supplier_id для складов.
   Response: `{ suppliers_total:int, suppliers_with_warehouses:int, suppliers_with_prices:int, suppliers_with_rules:int, warehouse_distribution:[{supplier_id:int, warehouses_count:int}] }`.
   Errors: Пусто → нули/[]; системные.
   Data: `suppliers`, `warehouses`, `supplier_price`, `pricing_rules`.

### POST /api/suppliers/admin/bulk-create

Что: массовое создание поставщиков.
Как: проверка уникальности имени, пакетная вставка.
Почему: ускоренное пополнение справочника.
Детали:
Тело: массив объектов `{name}`. Итерация: проверка отсутствия поставщика с тем же именем; валидные добавляются в сессию; ошибки (дубликаты) копятся. Один COMMIT. Ответ: `{total, created, failed, errors[]}`. Ошибки: индивидуальные — не прерывают вставку остальных.
Структурировано:
Request: POST `/api/suppliers/admin/bulk-create`.
Body: `[ { name:str }, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: валидация имени; проверка уникальности.
3. Добавление валидных.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,name}] }`.
   Errors: Ошибки элементов внутри списка; 422 (не массив / пустое имя).
   Data: `suppliers`.

### POST /api/suppliers/admin/bulk-delete?supplier_ids=...&force=bool

Что: массовое удаление поставщиков.
Как: проверка зависимостей (склады, цены, правила) и условное удаление.
Почему: реорганизация базы поставщиков.
Детали:
Query: `supplier_ids` (список int), `force` (bool, default=false). Для каждого: SELECT → COUNT складов → COUNT цен → COUNT правил. Если есть зависимости и force=false → ошибка в список. Иначе DELETE. Один COMMIT. Ответ: `{total, deleted, failed, errors[]}`. Ошибки: отсутствующие ID и зависимые без force.
Структурировано:
Request: POST `/api/suppliers/admin/bulk-delete`.
Query: `supplier_ids` (CSV список int required); `force` (bool default=false).
Steps:

1. Парсинг списка.
2. Для каждого id SELECT поставщик.
3. Если отсутствует → failed++.
4. Если есть → COUNT warehouses, supplier_price, pricing_rules.
5. Если зависимости>0 и force=false → errors.add(); failed++.
6. Иначе DELETE.
7. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors:[str] }`.
   Errors: 422 (неверный список); логические ошибки в errors.
   Data: `suppliers`, `warehouses`, `supplier_price`, `pricing_rules`.

### GET /api/suppliers/admin/{supplier_id}/warehouses

Что: склады данного поставщика.
Как: проверка существования поставщика; выборка `Warehouse` по FK.
Почему: просмотр логистической инфраструктуры поставщика.
Детали:
Path: `supplier_id` (int >0). Шаги: (1) SELECT поставщика; (2) SELECT складов WHERE supplier_id=:id. Ответ: массив складов `{id, name, shipping_zone_id, country, region}`. Ошибки: 404 если поставщик отсутствует.
Структурировано:
Request: GET `/api/suppliers/admin/{supplier_id}/warehouses`.
Path: `supplier_id` (int >0).
Steps:

1. SELECT поставщик.
2. Если None → 404.
3. SELECT склады поставщика.
   Response: `[ { id:int, name:str, shipping_zone_id:int?, country:str, region:str? } ]`.
   Errors: 404 (нет поставщика); 422 (тип ID); пустой массив.
   Data: `suppliers`, `warehouses`.

### GET /api/suppliers/admin/{supplier_id}/parts-count

Что: число частей (в текущей схеме всегда 0).
Как: возврат фиксированного значения.
Почему: зарезервировано для потенциального расширения связей.
Детали:
Path: `supplier_id`. Шаги: проверка существования поставщика; возврат `{supplier_id, parts_count:0}`. Ошибки: 404 если не найден.
Структурировано:
Request: GET `/api/suppliers/admin/{supplier_id}/parts-count`.
Path: `supplier_id` (int >0).
Steps:

1. SELECT поставщик.
2. Если None → 404.
3. Формирование ответа с parts_count:0.
   Response: `{ supplier_id:int, parts_count:int }`.
   Errors: 404 (нет поставщика); 422 (тип ID).
   Data: `suppliers`.

### POST /api/suppliers/admin/

Что: создание поставщика.
Как: проверка уникальности имени, вставка.
Почему: добавление нового источника закупок.
Детали:
Тело: SupplierCreate `{name}`. Шаги: (1) SELECT по имени — при наличии 409; (2) INSERT + COMMIT + REFRESH. Ответ: созданный `{id, name}`. Ошибки: 409 (дубликат).
Структурировано:
Request: POST `/api/suppliers/admin/`.
Body (SupplierCreate): `name` (str 1..120 обязательное).
Steps:

1. Валидация тела.
2. SELECT поставщик WHERE name=:name.
3. Если найден → 409.
4. INSERT.
5. COMMIT + REFRESH.
   Response: `{ id:int, name:str }`.
   Errors: 409 (дубликат имени); 422 (валидация); системные.
   Data: `suppliers`.

### GET /api/suppliers/admin/{supplier_id}

Что: деталь поставщика.
Как: выборка по ID.
Почему: отображение профиля для редактирования.
Детали:
Path: `supplier_id`. SELECT запись. Ответ: `{id, name}`. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/suppliers/admin/{supplier_id}`.
Path: `supplier_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id:int, name:str }`.
Errors: 404 (нет поставщика); 422 (тип ID).
Data: `suppliers`.

### PUT /api/suppliers/admin/{supplier_id}

Что: обновление имени.
Как: проверка конфликта с другим поставщиком; применение.
Почему: поддержание актуальной информации.
Детали:
Path: `supplier_id`. Тело: SupplierUpdate `{name?}`. Шаги: (1) SELECT; (2) при изменении name — проверка отсутствия другого поставщика с тем же именем; (3) обновление; (4) COMMIT + REFRESH. Ответ: обновлённый `{id,name}`. Ошибки: 404 (не найден), 409 (имя занято).
Структурировано:
Request: PUT `/api/suppliers/admin/{supplier_id}`.
Path: `supplier_id` (int >0).
Body (SupplierUpdate): `name` (str 1..120 optional).
Steps:

1. SELECT поставщик.
2. Если None → 404.
3. Если новое имя → проверка уникальности.
4. Обновление значения.
5. COMMIT + REFRESH.
   Response: `{ id:int, name:str }`.
   Errors: 404 (нет поставщика); 409 (дубликат имени); 422 (валидация); системные.
   Data: `suppliers`.

### DELETE /api/suppliers/admin/{supplier_id}?force=bool

Что: удаление поставщика.
Как: проверка наличия зависимостей; условное удаление.
Почему: управление жизненным циклом источника.
Детали:
Path: `supplier_id`; Query: `force` (bool default=false). Шаги: (1) SELECT поставщика; (2) COUNT складов; (3) COUNT supplier_price; (4) COUNT pricing_rules; (5) если любая зависимость>0 и force=false → 409; (6) DELETE + COMMIT. Ответ: 204. Ошибки: 404, 409.
Структурировано:
Request: DELETE `/api/suppliers/admin/{supplier_id}`.
Path: `supplier_id` (int >0).
Query: `force` (bool default=false).
Steps:

1. SELECT поставщик.
2. Если None → 404.
3. COUNT warehouses, supplier_price, pricing_rules.
4. Если любая зависимость>0 и force=false → 409.
5. DELETE + COMMIT.
   Response: 204 No Content.
   Errors: 404 (нет поставщика); 409 (зависимости); 422 (тип ID).
   Data: `suppliers`, `warehouses`, `supplier_price`, `pricing_rules`.
