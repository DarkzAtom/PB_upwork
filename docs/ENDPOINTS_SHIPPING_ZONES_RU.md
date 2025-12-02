# SHIPPING ZONES ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/shippingzones/admin`)

### GET /api/shippingzones/admin/

Что: листинг зон доставки.
Как: выборка с пагинацией.
Почему: управление географическими сегментами.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..1000). Базовый SELECT по таблице зон, опциональная сортировка по имени. Ответ: массив `{id, name, description?}`. Ошибки: пустой массив при отсутствии зон.
Структурировано:
Request: GET `/api/shippingzones/admin/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50).
Steps:

1. Валидация параметров.
2. SELECT \* FROM shipping_zones.
3. (Опционально) ORDER BY name.
4. OFFSET/LIMIT.
   Response: `[ { id:int, name:str, description:str? } ]`.
   Errors: 422 (параметры вне диапазона); пустой результат → [].
   Data: `shipping_zones`.

### GET /api/shippingzones/admin/search?name=...

Что: поиск зоны по имени.
Как: фильтр ILIKE.
Почему: быстрый доступ к конкретной зоне.
Детали:
Query: `name` (строка). WHERE name ILIKE `%name%`. Ответ: массив зон. Ошибки: пустой массив при отсутствии совпадений; 422 при отсутствии параметра.
Структурировано:
Request: GET `/api/shippingzones/admin/search`.
Query: `name` (str 1..120 required).
Steps:

1. Проверка обязательного параметра.
2. SELECT WHERE name ILIKE '%name%'.
   Response: `[ { id, name, description? } ]`.
   Errors: 422 (пустой или отсутствующий параметр); пустой массив.
   Data: `shipping_zones`.

### GET /api/shippingzones/admin/statistics

Что: глобальные показатели (кол-во зон, наличие тарифов и складов).
Как: агрегаты и подсчёт связей.
Почему: обзор покрытия логистической сети.
Детали:
Метрики: COUNT зон; число зон с хотя бы одним тарифом (JOIN shipping_rates GROUP BY zone_id WHERE COUNT>0); количество тарифов всего; количество складов привязанных к зонам (JOIN warehouses). Ответ: объект `{zones_total, zones_with_rates, zones_with_warehouses, rates_total, warehouses_total}`. Ошибки: при отсутствии данных значения 0.
Структурировано:
Request: GET `/api/shippingzones/admin/statistics`.
Steps:

1. COUNT зон.
2. Подсчёт зон с тарифами (JOIN shipping_rates GROUP BY zone_id HAVING COUNT>0).
3. COUNT всех тарифов.
4. COUNT складов JOIN warehouses.
   Response: `{ zones_total:int, zones_with_rates:int, zones_with_warehouses:int, rates_total:int, warehouses_total:int }`.
   Errors: Пусто → нули; системные.
   Data: `shipping_zones`, `shipping_rates`, `warehouses`.

### GET /api/shippingzones/admin/{zone_id}

Что: детальная информация о зоне.
Как: выборка по ID.
Почему: просмотр единицы справочника.
Детали:
Path: `zone_id` (int >0). SELECT по первичному ключу. Ответ: `{id, name, description?}`. Ошибки: 404 если зона отсутствует.
Структурировано:
Request: GET `/api/shippingzones/admin/{zone_id}`.
Path: `zone_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id, name, description? }`.
Errors: 404 (нет зоны); 422 (тип ID).
Data: `shipping_zones`.

### GET /api/shippingzones/admin/{zone_id}/statistics

Что: статистика по одной зоне (тарифы, склады).
Как: COUNT связанных записей по FK.
Почему: оценка насыщенности зоны ресурсами.
Детали:
Path: `zone_id`. Шаги: (1) Проверка существования зоны; (2) COUNT тарифов WHERE shipping_zone_id = :zone; (3) COUNT складов WHERE shipping_zone_id = :zone. Ответ: `{zone_id, rates_count, warehouses_count}`. Ошибки: 404 (зона не найдена).
Структурировано:
Request: GET `/api/shippingzones/admin/{zone_id}/statistics`.
Path: `zone_id` (int >0).
Steps:

1. SELECT зона.
2. Если None → 404.
3. COUNT тарифов по зоне.
4. COUNT складов по зоне.
   Response: `{ zone_id:int, rates_count:int, warehouses_count:int }`.
   Errors: 404 (нет зоны); 422 (тип ID).
   Data: `shipping_zones`, `shipping_rates`, `warehouses`.

### POST /api/shippingzones/admin/

Что: создание зоны.
Как: проверка отсутствия имени; вставка.
Почему: расширение географии доставки.
Детали:
Тело: ShippingZoneCreate (`name`, `description?`). Шаги: (1) Проверка уникальности имени; (2) INSERT + COMMIT + REFRESH. Ответ: созданная зона. Ошибки: 409 (имя занято).
Структурировано:
Request: POST `/api/shippingzones/admin/`.
Body (ShippingZoneCreate): `name` (str 1..120 обязательное), `description` (str? optional).
Steps:

1. Валидация тела.
2. SELECT по имени.
3. Если существует → 409.
4. INSERT новой зоны.
5. COMMIT + REFRESH.
   Response: `{ id:int, name:str, description:str? }`.
   Errors: 409 (дубликат имени); 422 (валидация); системные.
   Data: `shipping_zones`.

### PUT /api/shippingzones/admin/{zone_id}

Что: обновление названия зоны.
Как: проверка конфликта имени; применение изменения.
Почему: поддержание корректной номенклатуры.
Детали:
Path: `zone_id`. Тело: ShippingZoneUpdate (`name?`, `description?`). Шаги: (1) SELECT зона; (2) при изменении name — проверка уникальности; (3) обновление полей; (4) COMMIT+REFRESH. Ответ: обновлённая зона. Ошибки: 404 (не найдена), 409 (имя занято).
Структурировано:
Request: PUT `/api/shippingzones/admin/{zone_id}`.
Path: `zone_id` (int >0).
Body: `name` (str?), `description` (str?).
Steps:

1. SELECT зона.
2. Если None → 404.
3. Если новое имя → проверка уникальности.
4. Обновление значений.
5. COMMIT + REFRESH.
   Response: `{ id, name, description? }`.
   Errors: 404 (нет зоны); 409 (дубликат имени); 422 (валидация).
   Data: `shipping_zones`.

### DELETE /api/shippingzones/admin/{zone_id}?force=bool

Что: удаление зоны.
Как: проверка наличия тарифов и складов; условное удаление.
Почему: управление актуальностью логистических сегментов.
Детали:
Path: `zone_id`; Query: `force` (bool, по умолчанию false). Шаги: (1) SELECT зона; (2) COUNT тарифов; (3) COUNT складов; (4) если (rates_count>0 или warehouses_count>0) и force=false → 409; (5) DELETE + COMMIT. Ответ: 204. Ошибки: 404 (нет зоны), 409 (зависимости присутствуют без force).
Структурировано:
Request: DELETE `/api/shippingzones/admin/{zone_id}`.
Query: `force` (bool default=false).
Path: `zone_id` (int >0).
Steps:

1. SELECT зона.
2. Если None → 404.
3. COUNT связанных тарифов.
4. COUNT связанных складов.
5. Если зависимости и force=false → 409.
6. DELETE + COMMIT.
   Response: 204 No Content.
   Errors: 404 (нет зоны); 409 (зависимости); 422 (тип ID).
   Data: `shipping_zones`, `shipping_rates`, `warehouses`.

### POST /api/shippingzones/admin/bulk-create

Что: массовое создание зон.
Как: итерация и проверка уникальности имён.
Почему: быстрое первичное заполнение.
Детали:
Тело: массив ShippingZoneCreate. Для каждой записи проверка уникальности имени. Валидные добавляются; ошибки фиксируются (дубликаты). Один COMMIT. Ответ: `{total, created, failed, errors[]}`. Ошибки: индивидуальные, не прерывают процесс.
Структурировано:
Request: POST `/api/shippingzones/admin/bulk-create`.
Body: `[ ShippingZoneCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: валидация; проверка имени.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,name}] }`.
   Errors: Ошибки внутри `errors`; 422 (не массив).
   Data: `shipping_zones`.

### POST /api/shippingzones/admin/bulk-delete?zone_ids=...&force=bool

Что: массовое удаление зон.
Как: проверка зависимостей каждой; выборочное удаление.
Почему: оперативная реорганизация.
Детали:
Query: `zone_ids` (список int), `force` (bool). Итерация: SELECT для каждой; подсчёт зависимостей (тарифы, склады); если есть и force=false → ошибка в список; иначе DELETE. Итоговый COMMIT. Ответ: `{total, deleted, failed, errors[]}`. Ошибки: перечислены в errors.
Структурировано:
Request: POST `/api/shippingzones/admin/bulk-delete`.
Query: `zone_ids` (CSV список int required), `force` (bool default=false).
Steps:

1. Парсинг списка.
2. Для каждого id SELECT зона.
3. Если нет → failed++.
4. Если есть → COUNT зависимостей тарифов и складов.
5. Если зависимости и force=false → errors.add(); failed++.
6. Иначе DELETE.
7. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors:[str] }`.
   Errors: 422 (пустой/неверный список); логические в errors.
   Data: `shipping_zones`, `shipping_rates`, `warehouses`.

### GET /api/shippingzones/admin/{zone_id}/warehouses

Что: склады внутри зоны.
Как: выборка `Warehouse.shipping_zone_id`.
Почему: просмотр логистической инфраструктуры зоны.
Детали:
Path: `zone_id`. Шаги: (1) Проверка существования зоны; (2) SELECT всех складов WHERE shipping_zone_id = :zone. Ответ: массив `{id, supplier_id?, shipping_zone_id, region, name}` (фактические поля склада). Ошибки: 404 при отсутствии зоны; если складов нет → пустой массив.
Структурировано:
Request: GET `/api/shippingzones/admin/{zone_id}/warehouses`.
Path: `zone_id` (int >0).
Steps:

1. SELECT зона.
2. Если None → 404.
3. SELECT склады WHERE shipping_zone_id=:zone.
   Response: `[ { id:int, supplier_id:int?, shipping_zone_id:int, region:str?, name:str } ]`.
   Errors: 404 (нет зоны); пустой массив.
   Data: `shipping_zones`, `warehouses`.
