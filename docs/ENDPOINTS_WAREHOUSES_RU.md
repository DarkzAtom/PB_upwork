# WAREHOUSES ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/warehouses/admin`)

### GET /api/warehouses/admin/all

Что: постраничный список складов.
Как: выборка `Warehouse` с лимитом.
Почему: обзор логистической инфраструктуры.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..1000), опционально `supplier_id`, `shipping_zone_id`, `country` если реализованы встроенные фильтры. SELECT всех складов; возможная сортировка по имени. Ответ: массив `{id, name, supplier_id, shipping_zone_id, country, region, address?, lead_time_days?}`. Ошибки: пустой массив при отсутствии; 422 при неверных типах.
Структурировано:
Request: GET `/api/warehouses/admin/all`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50); `supplier_id` (int >0 optional); `shipping_zone_id` (int >0 optional); `country` (str optional).
Steps:

1. Валидация параметров.
2. SELECT \* FROM warehouses.
3. Применение фильтров по supplier/zone/country.
4. (Опционально) ORDER BY name.
5. OFFSET/LIMIT.
   Response: `[ { id:int, name:str, supplier_id:int, shipping_zone_id:int?, country:str, region:str?, address:str?, lead_time_days:int? } ]`.
   Errors: 422 (невалидные параметры); пустой массив.
   Data: `warehouses`.

### GET /api/warehouses/admin/search?name=...

Что: поиск склада по имени.
Как: фильтр ILIKE по `name`.
Почему: точное нахождение склада для операций.
Детали:
Query: `name` (строка). WHERE name ILIKE `%name%`. Ответ: массив складов. Ошибки: пустой массив при отсутствии совпадений; 422 при отсутствующем параметре.
Структурировано:
Request: GET `/api/warehouses/admin/search`.
Query: `name` (str 1..120 required).
Steps: SELECT WHERE name ILIKE '%name%'.
Response: `[ { id, name, supplier_id, shipping_zone_id } ]`.
Errors: 422 (пустой параметр); пустой массив.
Data: `warehouses`.

### GET /api/warehouses/admin/by-supplier/{supplier_id}

Что: склады конкретного поставщика.
Как: проверка поставщика; выборка по FK.
Почему: анализ распределения складов по поставщику.
Детали:
Path: `supplier_id` (int >0). Шаги: (1) Проверка существования поставщика; (2) SELECT всех складов WHERE supplier_id = :id. Ответ: массив складов. Ошибки: 404 (поставщик не найден), пустой массив если складов нет.
Структурировано:
Request: GET `/api/warehouses/admin/by-supplier/{supplier_id}`.
Path: `supplier_id` (int >0).
Steps:

1. SELECT поставщик.
2. Если None → 404.
3. SELECT склады WHERE supplier_id=:id.
   Response: `[ { id, name, supplier_id, country } ]`.
   Errors: 404 (нет поставщика); пустой массив.
   Data: `suppliers`, `warehouses`.

### GET /api/warehouses/admin/by-zone/{shipping_zone_id}

Что: склады внутри зоны.
Как: проверка зоны; выборка `shipping_zone_id`.
Почему: просмотр логистического покрытия зоны.
Детали:
Path: `shipping_zone_id` (int >0). Шаги: (1) Проверка зоны; (2) SELECT складов WHERE shipping_zone_id = :zone. Ответ: массив. Ошибки: 404 (зона не найдена) или пустой массив.
Структурировано:
Request: GET `/api/warehouses/admin/by-zone/{shipping_zone_id}`.
Path: `shipping_zone_id` (int >0).
Steps:

1. SELECT зона.
2. Если None → 404.
3. SELECT склады WHERE shipping_zone_id=:zone.
   Response: `[ { id, name, shipping_zone_id, supplier_id } ]`.
   Errors: 404 (нет зоны); пустой массив.
   Data: `shipping_zones`, `warehouses`.

### GET /api/warehouses/admin/by-country/{country}

Что: склады указанной страны.
Как: фильтр по полю `country` (регистронезависимый).
Почему: географическая навигация.
Детали:
Path: `country` (строка ISO2/ISO3 или произвольная). WHERE LOWER(country) = LOWER(:country). Ответ: массив. Ошибки: пустой массив если нет совпадений.
Структурировано:
Request: GET `/api/warehouses/admin/by-country/{country}`.
Path: `country` (str 1..60).
Steps: SELECT WHERE LOWER(country)=LOWER(:country).
Response: `[ { id, name, country, region?, supplier_id } ]`.
Errors: пустой массив.
Data: `warehouses`.

### GET /api/warehouses/admin/statistics

Что: агрегаты по складам (количество, средний lead time, привязки).
Как: COUNT и AVG по соответствующим таблицам.
Почему: аналитика эффективности и покрытия.
Детали:
Метрики: COUNT складов, AVG `lead_time_days` (если поле присутствует), распределение по странам (COUNT GROUP BY country), распределение по зонам (COUNT GROUP BY shipping_zone_id), количество поставщиков (COUNT DISTINCT supplier_id). Ответ: JSON объект статистики. Ошибки: при отсутствии данных — значения 0 или null.
Структурировано:
Request: GET `/api/warehouses/admin/statistics`.
Steps:

1. COUNT складов.
2. AVG lead_time_days.
3. GROUP BY country.
4. GROUP BY shipping_zone_id.
5. COUNT DISTINCT supplier_id.
   Response: `{ total:int, lead_time_avg:float?, by_country:[{country:str,count:int}], by_zone:[{shipping_zone_id:int,count:int}], distinct_suppliers:int }`.
   Errors: Пусто → нули/null; системные.
   Data: `warehouses`.

### GET /api/warehouses/admin/{warehouse_id}

Что: деталь склада.
Как: выборка по ID.
Почему: просмотр параметров для редактирования.
Детали:
Path: `warehouse_id` (int >0). SELECT по PK. Ответ: полный объект `{id, name, supplier_id, shipping_zone_id, country, region, address?, lead_time_days?}`. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/warehouses/admin/{warehouse_id}`.
Path: `warehouse_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: полный объект склада.
Errors: 404 (нет склада); 422 (тип ID).
Data: `warehouses`.

### GET /api/warehouses/admin/{warehouse_id}/inventory-count

Что: количество записей цен поставщика для склада.
Как: COUNT по `SupplierPrice.warehouse_id`.
Почему: отражение насыщенности склада ассортиментом.
Детали:
Path: `warehouse_id`. Шаги: (1) Проверка склада; (2) COUNT записей supplier_price WHERE warehouse_id = :id. Ответ: `{warehouse_id, inventory_count}`. Ошибки: 404 если склад отсутствует.
Структурировано:
Request: GET `/api/warehouses/admin/{warehouse_id}/inventory-count`.
Path: `warehouse_id` (int >0).
Steps:

1. SELECT склад.
2. Если None → 404.
3. COUNT supplier_price по warehouse_id.
   Response: `{ warehouse_id:int, inventory_count:int }`.
   Errors: 404 (нет склада); 422 (тип ID).
   Data: `warehouses`, `supplier_price`.

### POST /api/warehouses/admin/

Что: создание склада.
Как: проверки существования поставщика и зоны; проверка конфликта имени внутри поставщика; вставка.
Почему: добавление нового логистического узла.
Детали:
Тело: WarehouseCreate: `name`, `supplier_id`, `shipping_zone_id?`, `country`, `region?`, `address?`, `lead_time_days?`. Шаги: (1) Проверка поставщика; (2) если указана зона — проверка зоны; (3) проверка уникальности имени среди складов того же `supplier_id`; (4) INSERT + COMMIT + REFRESH. Ответ: созданный склад. Ошибки: 404 (поставщик/зона не найдены), 409 (имя конфликт).
Структурировано:
Request: POST `/api/warehouses/admin/`.
Body (WarehouseCreate):
`name` (str 1..120 обязательное)
`supplier_id` (int >0 обязательное)
`shipping_zone_id` (int >0 optional)
`country` (str 2..60 обязательное)
`region` (str optional)
`address` (str optional)
`lead_time_days` (int ≥0 optional)
Steps:

1. Валидация тела.
2. SELECT поставщик.
3. (Опционально) SELECT зона.
4. Проверка уникальности имени среди складов поставщика.
5. INSERT.
6. COMMIT + REFRESH.
   Response: `{ id, name, supplier_id, shipping_zone_id?, country, region?, address?, lead_time_days? }`.
   Errors: 404 (нет поставщика/зоны); 409 (дубликат имени); 422 (валидация); системные.
   Data: `suppliers`, `shipping_zones`, `warehouses`.

### PUT /api/warehouses/admin/{warehouse_id}

Что: обновление параметров.
Как: проверки изменений FK и уникальности имени; применение данных.
Почему: поддержание точности логистической информации.
Детали:
Path: `warehouse_id`. Тело: WarehouseUpdate (все поля опциональны). Шаги: (1) SELECT склад; (2) если меняется supplier_id — проверка поставщика и уникальности имени в контексте нового поставщика; (3) если меняется shipping_zone_id — проверка зоны; (4) обновление полей; (5) COMMIT+REFRESH. Ответ: обновлённый склад. Ошибки: 404 (не найден/ FK не найдены), 409 (конфликт имени).
Структурировано:
Request: PUT `/api/warehouses/admin/{warehouse_id}`.
Path: `warehouse_id` (int >0).
Body (WarehouseUpdate): любые из `name`, `supplier_id`, `shipping_zone_id`, `country`, `region`, `address`, `lead_time_days`.
Steps:

1. SELECT склад.
2. Если None → 404.
3. При изменении supplier_id → проверка поставщика + уникальность имени.
4. При изменении shipping_zone_id → проверка зоны.
5. Обновление значений.
6. COMMIT + REFRESH.
   Response: обновлённый объект склада.
   Errors: 404 (нет склада/нет FK); 409 (имя занято); 422 (валидация); системные.
   Data: `warehouses`, `suppliers`, `shipping_zones`.

### DELETE /api/warehouses/admin/{warehouse_id}?force=bool

Что: удаление склада.
Как: проверка наличия связанных записей цен; условное удаление.
Почему: управление жизненным циклом узла.
Детали:
Path: `warehouse_id`; Query: `force` (bool, default=false). Шаги: (1) SELECT склад; (2) COUNT supplier_price WHERE warehouse_id=:id; (3) если count>0 и force=false → 409; (4) DELETE + COMMIT. Ответ: 204. Ошибки: 404, 409.
Структурировано:
Request: DELETE `/api/warehouses/admin/{warehouse_id}`.
Path: `warehouse_id` (int >0).
Query: `force` (bool default=false).
Steps:

1. SELECT склад.
2. Если None → 404.
3. COUNT связанного инвентаря.
4. Если count>0 и force=false → 409.
5. DELETE + COMMIT.
   Response: 204 No Content.
   Errors: 404 (нет склада); 409 (есть инвентарь); 422 (тип ID).
   Data: `warehouses`, `supplier_price`.

### POST /api/warehouses/admin/bulk-create

Что: массовое добавление складов.
Как: циклические проверки FK и уникальности имени; пакетная вставка.
Почему: ускорение первоначального наполнения.
Детали:
Тело: массив WarehouseCreate. Для каждого: проверки поставщика/зоны, уникальность имени у данного поставщика. Валидные добавляются; ошибки фиксируются. Один COMMIT. Ответ: `{total, created, failed, errors[]}`.
Структурировано:
Request: POST `/api/warehouses/admin/bulk-create`.
Body: `[ WarehouseCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: валидация; SELECT поставщик; SELECT зона (если указана); проверка уникальности имени.
3. Добавление валидных.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,name}] }`.
   Errors: Логические внутри `errors`; 422 (не массив).
   Data: `warehouses`, `suppliers`, `shipping_zones`.

### POST /api/warehouses/admin/bulk-delete?warehouse_ids=...&force=bool

Что: массовое удаление складов.
Как: проверка наличия инвентаря; условное удаление.
Почему: реорганизация логистической сети.
Детали:
Query: `warehouse_ids` (список int), `force` (bool). Итерация: SELECT → COUNT inventory → если count>0 и force=false → ошибка; иначе DELETE. Финальный COMMIT. Ответ: `{total, deleted, failed, errors[]}`.
Структурировано:
Request: POST `/api/warehouses/admin/bulk-delete`.
Query: `warehouse_ids` (CSV список int required); `force` (bool default=false).
Steps:

1. Парсинг списка.
2. Для каждого id SELECT склад.
3. Если отсутствует → failed++.
4. Если присутствует → COUNT inventory.
5. Если inventory>0 и force=false → errors.add(); failed++.
6. Иначе DELETE.
7. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors:[str] }`.
   Errors: 422 (неверный список); логические в errors.
   Data: `warehouses`, `supplier_price`.

### GET /api/warehouses/admin/filter/by-supplier-and-zone?supplier_id=...&shipping_zone_id=...

Что: фильтр складов по поставщику и зоне одновременно.
Как: проверка обеих сущностей; выборка с двумя условиями.
Почему: получение пересечения для анализа покрытия.
Детали:
Query: `supplier_id` (int >0), `shipping_zone_id` (int >0). Шаги: (1) Проверка поставщика; (2) Проверка зоны; (3) SELECT складов WHERE supplier_id=:s AND shipping_zone_id=:z. Ответ: массив складов. Ошибки: 404 (поставщик/зона не найдены), пустой массив при отсутствии складов.
Структурировано:
Request: GET `/api/warehouses/admin/filter/by-supplier-and-zone`.
Query: `supplier_id` (int >0 required); `shipping_zone_id` (int >0 required).
Steps:

1. SELECT поставщик.
2. SELECT зона.
3. Если любой отсутствует → 404.
4. SELECT склады WHERE supplier_id=:s AND shipping_zone_id=:z.
   Response: `[ { id, name, supplier_id, shipping_zone_id } ]`.
   Errors: 404 (нет поставщика или зоны); 422 (тип параметров); пустой массив.
   Data: `suppliers`, `shipping_zones`, `warehouses`.
