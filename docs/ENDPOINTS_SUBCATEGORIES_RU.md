# SUBCATEGORIES ROUTER — Функциональное описание эндпоинтов

## 1. Публичные эндпоинты (`/api/subcategories`)

### GET /api/subcategories/

Что: список подкатегорий.
Как: выборка с пагинацией.
Почему: отображение второй ступени таксономии.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..500). SELECT всех подкатегорий. Ответ: массив `{id, name, parent_id}`. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/subcategories/`.
Query: `skip` (int ≥0 default 0), `limit` (int 1..500 default 50).
Steps:

1. Валидация параметров.
2. SELECT \* FROM subcategories.
3. (Опционально) ORDER BY name.
4. OFFSET/LIMIT.
   Response: `[ { id:int, name:str, parent_id:int } ]`.
   Errors: 422 (невалидные параметры); пустой массив.
   Data: `subcategories`.

### GET /api/subcategories/search?name=...

Что: поиск подкатегории по имени.
Как: фильтр ILIKE по имени.
Почему: упрощение навигации внутри родительской категории.
Детали:
Query: `name` (строка), `skip`, `limit`. WHERE name ILIKE `%name%`. Ответ: массив. Ошибки: пустой массив если нет совпадений, 422 при отсутствии name.
Структурировано:
Request: GET `/api/subcategories/search`.
Query: `name` (str 1..120 required), `skip` (int ≥0 default 0), `limit` (int 1..500 default 50).
Steps:

1. Проверка обязательного `name`.
2. SELECT WHERE name ILIKE '%name%'.
3. OFFSET/LIMIT.
   Response: `[ { id:int, name:str, parent_id:int } ]`.
   Errors: 422 (отсутствует/пустой name); пустой массив.
   Data: `subcategories`.

### GET /api/subcategories/by-parent/{parent_id}

Что: подкатегории конкретной категории.
Как: проверка категории и выборка по `parent_id`.
Почему: построение дерева категории → подкатегории.
Детали:
Path: `parent_id` (int >0). Шаги: (1) SELECT категория; (2) SELECT подкатегорий WHERE parent_id=:id. Ответ: массив `{id,name,parent_id}`. Ошибки: 404 если категория отсутствует.
Структурировано:
Request: GET `/api/subcategories/by-parent/{parent_id}`.
Path: `parent_id` (int >0).
Steps:

1. SELECT категория.
2. Если None → 404.
3. SELECT subcategories WHERE parent_id=:id.
   Response: `[ { id:int, name:str, parent_id:int } ]`.
   Errors: 404 (нет категории); пустой массив.
   Data: `categories`, `subcategories`.

### GET /api/subcategories/{subcategory_id}

Что: детальная запись подкатегории.
Как: поиск по ID; 404 при отсутствии.
Почему: отображение свойств узла.
Детали:
Path: `subcategory_id` (int >0). SELECT. Ответ: `{id,name,parent_id}`. Ошибки: 404 при отсутствии.
Структурировано:
Request: GET `/api/subcategories/{subcategory_id}`.
Path: `subcategory_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id:int, name:str, parent_id:int }`.
Errors: 404 (нет подкатегории); 422 (тип ID).
Data: `subcategories`.

### GET /api/subcategories/{subcategory_id}/parts-count

Что: число частей в подкатегории.
Как: COUNT по `parts.subcategory_id`.
Почему: информирование о наполненности сегмента.
Детали:
Path: `subcategory_id`. Шаги: (1) Проверка подкатегории; (2) COUNT частей WHERE subcategory_id=:id. Ответ: `{subcategory_id, parts_count}`. Ошибки: 404 если подкатегория не найдена.
Структурировано:
Request: GET `/api/subcategories/{subcategory_id}/parts-count`.
Path: `subcategory_id` (int >0).
Steps:

1. SELECT подкатегория.
2. Если None → 404.
3. COUNT parts WHERE subcategory_id=:id.
   Response: `{ subcategory_id:int, parts_count:int }`.
   Errors: 404 (нет подкатегории); 422 (тип ID).
   Data: `subcategories`, `parts`.

## 2. Админские эндпоинты (`/api/subcategories/admin`)

### GET /api/subcategories/admin/all

Что: листинг админский.
Как: выборка всех с пагинацией.
Почему: управление множеством подкатегорий.
Детали:
Query: `skip` (≥0), `limit` (1..1000). SELECT всех подкатегорий. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/subcategories/admin/all`.
Query: `skip` (int ≥0 default 0), `limit` (int 1..1000 default 100).
Steps:

1. Валидация.
2. SELECT \* FROM subcategories.
3. OFFSET/LIMIT.
   Response: `[ { id:int, name:str, parent_id:int } ]`.
   Errors: 422 (невалидные параметры); пустой массив.
   Data: `subcategories`.

### POST /api/subcategories/admin/

Что: создание подкатегории.
Как: проверка родительской категории и отсутствия дубликата имени под тем же родителем; вставка.
Почему: расширение структуры классификации.
Детали:
Тело: SubcategoryCreate `{name, parent_id}`. Шаги: (1) Проверка родителя; (2) SELECT по имени+parent_id для уникальности; (3) при конфликте 409; (4) INSERT + COMMIT + REFRESH. Ответ: созданная `{id,name,parent_id}`. Ошибки: 404 (родитель не найден), 409 (дубликат имени).
Структурировано:
Request: POST `/api/subcategories/admin/`.
Body (SubcategoryCreate): `name` (str 1..120 required), `parent_id` (int >0 required).
Steps:

1. Валидация тела.
2. SELECT категория по parent_id.
3. Если None → 404.
4. SELECT subcategory WHERE name=:name AND parent_id=:parent_id.
5. Если найдено → 409.
6. INSERT.
7. COMMIT + REFRESH.
   Response: `{ id:int, name:str, parent_id:int }`.
   Errors: 404 (нет родителя); 409 (имя занято в рамках родителя); 422 (валидация).
   Data: `categories`, `subcategories`.

### GET /api/subcategories/admin/{id}

Что: просмотр подкатегории.
Как: выборка по ID.
Почему: точечное редактирование.
Детали:
Path: `id`. SELECT. Ответ: `{id,name,parent_id}`. Ошибки: 404.
Структурировано:
Request: GET `/api/subcategories/admin/{id}`.
Path: `id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id:int, name:str, parent_id:int }`.
Errors: 404 (нет подкатегории); 422 (тип ID).
Data: `subcategories`.

### PUT /api/subcategories/admin/{id}

Что: частичное обновление имени или родителя.
Как: проверки существования нового родителя и конфликтов имен.
Почему: перенос и переименование узлов.
Детали:
Path: `id`. Тело: SubcategoryUpdate `{name?, parent_id?}`. Шаги: (1) SELECT подкатегория; (2) если изменяется parent_id — проверка родителя; (3) формирование потенциальной пары (new_parent_id, new_name) и проверка уникальности; (4) обновление; (5) COMMIT+REFRESH. Ответ: обновлённая запись. Ошибки: 404 (не найдена/родитель отсутствует), 409 (дубликат).
Структурировано:
Request: PUT `/api/subcategories/admin/{id}`.
Path: `id` (int >0).
Body (SubcategoryUpdate): `name` (str 1..120 optional), `parent_id` (int >0 optional).
Steps:

1. SELECT подкатегория.
2. Если None → 404.
3. Если изменяется parent_id → SELECT новый родитель (404 если нет).
4. Определение целевых значений (target_parent_id, target_name).
5. SELECT подкатегория WHERE parent_id=target_parent_id AND name=target_name (исключая текущую).
6. Если найдено → 409.
7. Применение изменений.
8. COMMIT + REFRESH.
   Response: `{ id:int, name:str, parent_id:int }`.
   Errors: 404 (нет подкатегории/родителя); 409 (конфликт имени); 422 (валидация).
   Data: `categories`, `subcategories`.

### DELETE /api/subcategories/admin/{id}?force=bool

Что: удаление подкатегории.
Как: подсчёт связанных частей; удаление при отсутствии или при force.
Почему: управление жизненным циклом сегмента.
Детали:
Path: `id`; Query: `force` (bool default=false). Шаги: (1) SELECT; (2) COUNT частей; (3) если count>0 и force=false → 409; (4) DELETE + COMMIT. Ответ: 204. Ошибки: 404, 409.
Структурировано:
Request: DELETE `/api/subcategories/admin/{id}`.
Path: `id` (int >0).
Query: `force` (bool default=false).
Steps:

1. SELECT подкатегория.
2. Если None → 404.
3. COUNT parts WHERE subcategory_id=:id.
4. Если count>0 и force=false → 409.
5. DELETE + COMMIT.
   Response: 204 No Content.
   Errors: 404 (нет подкатегории); 409 (есть связанные parts); 422 (тип ID).
   Data: `subcategories`, `parts`.

### POST /api/subcategories/admin/bulk-create

Что: пакетное добавление.
Как: итерация с проверками родителя и уникальности имени.
Почему: ускорение массового ввода классификации.
Детали:
Тело: массив SubcategoryCreate. Для каждой: проверка родителя, проверка уникальности имени в пределах родителя. Успешные добавляются; ошибки фиксируются. Один COMMIT. Ответ: `{total, created, failed, errors[]}`.
Структурировано:
Request: POST `/api/subcategories/admin/bulk-create`.
Body: `[ SubcategoryCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого элемента: валидация; SELECT родитель; если отсутствует → errors.add(); failed++.
3. SELECT подкатегория WHERE parent_id AND name.
4. Если конфликт → errors.add(); failed++.
5. Иначе добавление.
6. Один COMMIT.
7. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id:int,name:str,parent_id:int}] }`.
   Errors: Ошибки элементов; 422 (не массив/структура); системные.
   Data: `categories`, `subcategories`.

### POST /api/subcategories/admin/bulk-delete?subcategory_ids=...&force=bool

Что: массовое удаление.
Как: проверка наличия частей и условное удаление.
Почему: быстрая реорганизация.
Детали:
Query: `subcategory_ids` (список int), `force` (bool). Итерация: SELECT → COUNT parts → при наличии и force=false → ошибка; иначе DELETE. COMMIT. Ответ: `{total, deleted, failed, errors[]}`.
Структурировано:
Request: POST `/api/subcategories/admin/bulk-delete`.
Query: `subcategory_ids` (CSV список int required), `force` (bool default=false).
Steps:

1. Парсинг списка.
2. Для каждого id: SELECT подкатегория.
3. Если отсутствует → failed++ / errors.add().
4. COUNT parts.
5. Если parts>0 и force=false → failed++ / errors.add().
6. Иначе DELETE.
7. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors:[str] }`.
   Errors: 422 (неверный список); логические в errors.
   Data: `subcategories`, `parts`.

### PUT /api/subcategories/admin/{id}/move-to-parent?new_parent_id=...

Что: перенос подкатегории к новому родителю.
Как: проверки существования категории и отсутствия конфликта имени.
Почему: изменение структуры без пересоздания.
Детали:
Path: `id`; Query: `new_parent_id` (int >0). Шаги: (1) SELECT подкатегория; (2) SELECT новый родитель; (3) проверка, что нет другой подкатегории с тем же именем под новым родителем; (4) обновление parent_id; (5) COMMIT+REFRESH. Ответ: обновлённая запись. Ошибки: 404 (подкатегория/новый родитель), 409 (конфликт имени).
Структурировано:
Request: PUT `/api/subcategories/admin/{id}/move-to-parent`.
Path: `id` (int >0).
Query: `new_parent_id` (int >0 required).
Steps:

1. SELECT подкатегория.
2. Если None → 404.
3. SELECT категория по new_parent_id.
4. Если None → 404.
5. SELECT подкатегория WHERE parent_id=new_parent_id AND name=текущее имя.
6. Если найдено → 409.
7. Обновление parent_id.
8. COMMIT + REFRESH.
   Response: `{ id:int, name:str, parent_id:int }`.
   Errors: 404 (нет подкатегории/родителя); 409 (конфликт имени); 422 (валидация параметров).
   Data: `categories`, `subcategories`.

### GET /api/subcategories/admin/statistics

Что: сводные показатели по количеству подкатегорий, частей.
Как: агрегаты по таблицам.
Почему: обзор распределения ассортимента по второму уровню.
Детали:
Метрики: COUNT подкатегорий; COUNT частей в сумме; среднее частей на подкатегорию; количество пустых подкатегорий (parts_count=0); топ-5 по количеству частей. Ответ: объект статистики с массивом топовых `{subcategory_id,name,parts_count}`. Ошибки: при отсутствии данных массивы пустые.
Структурировано:
Request: GET `/api/subcategories/admin/statistics`.
Steps:

1. COUNT subcategories.
2. LEFT JOIN parts для подсчёта parts_count по subcategory.
3. SUM общего количества частей.
4. Расчёт среднего (parts_total/subcategories_total при subcategories_total>0).
5. Подсчёт пустых подкатегорий (parts_count=0).
6. Формирование топ-5 по частям (ORDER BY parts_count DESC LIMIT 5).
   Response: `{ subcategories_total:int, parts_total:int, avg_parts_per_subcategory:float?, empty_subcategories:int, top_parts:[{ subcategory_id:int, name:str, parts_count:int }] }`.
   Errors: Пустая таблица → нули/[]; системные.
   Data: `subcategories`, `parts`.
