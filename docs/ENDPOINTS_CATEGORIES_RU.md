# CATEGORIES ROUTER — Функциональное описание эндпоинтов

## 1. Публичные эндпоинты (`/api/categories`)

### GET /api/categories/

Что: список категорий с пагинацией.
Как: выборка `Category` с ограничением и смещением.
Почему: базовая таксономия каталога для интерфейса и фильтров.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..500). SELECT категорий без сортировки либо по имени. Ответ: массив `{id, name}`. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/categories/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..500 default 50).
Steps:

1. Валидация параметров.
2. SELECT \* FROM categories.
3. (Опционально) ORDER BY name.
4. OFFSET/LIMIT.
   Response: `[ { id:int, name:str } ]`.
   Errors: 422 (невалидные параметры); пустой массив.
   Data: `categories`.

### GET /api/categories/search?name=...

Что: поиск категорий по фрагменту имени.
Как: фильтр `Category.name ILIKE %name%` + пагинация.
Почему: облегчает навигацию при неизвестном точном названии.
Детали:
Query: `name` (строка), `skip`, `limit`. WHERE name ILIKE `%name%`. Ответ: массив категорий. Ошибки: пустой массив если нет совпадений, 422 при отсутствии параметра `name`.
Структурировано:
Request: GET `/api/categories/search`.
Query: `name` (str 1..120 required); `skip` (int ≥0 default 0); `limit` (int 1..500 default 50).
Steps:

1. Проверка обязательного `name`.
2. SELECT WHERE name ILIKE '%name%'.
3. OFFSET/LIMIT.
   Response: `[ { id, name } ]`.
   Errors: 422 (отсутствует/пустой name); пустой массив.
   Data: `categories`.

### GET /api/categories/{category_id}

Что: получение одной категории.
Как: выборка по ID; при отсутствии 404.
Почему: отображение детальной записи и связанных данных.
Детали:
Path: `category_id` (int >0). SELECT категория. Ответ: `{id, name}`. Ошибки: 404 если не существует.
Структурировано:
Request: GET `/api/categories/{category_id}`.
Path: `category_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id:int, name:str }`.
Errors: 404 (нет категории); 422 (тип ID).
Data: `categories`.

### GET /api/categories/{category_id}/subcategories

Что: подкатегории конкретной категории.
Как: проверка существования родителя; выборка `Subcategory.parent_id = category_id`.
Почему: раскрытие иерархии для построения дерева навигации.
Детали:
Path: `category_id`. Шаги: (1) SELECT категория; (2) SELECT подкатегорий WHERE parent_id=:id. Ответ: массив `{id, name, parent_id}`. Ошибки: 404 если категория отсутствует; пустой массив если нет подкатегорий.
Структурировано:
Request: GET `/api/categories/{category_id}/subcategories`.
Path: `category_id` (int >0).
Steps:

1. SELECT категория.
2. Если None → 404.
3. SELECT подкатегории WHERE parent_id=:id.
   Response: `[ { id:int, name:str, parent_id:int } ]`.
   Errors: 404 (нет категории); пустой массив.
   Data: `categories`, `subcategories`.

### GET /api/categories/{category_id}/parts-count

Что: количественные показатели по частям и подкатегориям.
Как: два агрегата COUNT по `parts` и `subcategories`.
Почему: отображение наполненности категории для UI и аналитики.
Детали:
Path: `category_id`. Шаги: (1) Проверка категории; (2) COUNT частей WHERE category_id=:id; (3) COUNT подкатегорий WHERE parent_id=:id. Ответ: `{category_id, parts_count, subcategories_count}`. Ошибки: 404 если категория не найдена.
Структурировано:
Request: GET `/api/categories/{category_id}/parts-count`.
Path: `category_id` (int >0).
Steps:

1. SELECT категория.
2. Если None → 404.
3. COUNT parts по category_id.
4. COUNT subcategories по parent_id.
   Response: `{ category_id:int, parts_count:int, subcategories_count:int }`.
   Errors: 404 (нет категории); 422 (тип ID).
   Data: `categories`, `parts`, `subcategories`.

## 2. Админские эндпоинты (`/api/categories/admin`)

### GET /api/categories/admin/

Что: расширенный листинг категорий.
Как: выборка с лимитом до 1000.
Почему: массовое администрирование таксономии.
Детали:
Query: `skip` (≥0), `limit` (1..1000). SELECT категорий. Ответ: массив `{id,name}`. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/categories/admin/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 100).
Steps:

1. Валидация параметров.
2. SELECT \* FROM categories.
3. OFFSET/LIMIT.
   Response: `[ { id:int, name:str } ]`.
   Errors: 422 (невалидные параметры); пустой массив.
   Data: `categories`.

### POST /api/categories/admin/

Что: создание категории.
Как: проверка на совпадение имени; вставка.
Почему: расширение структуры каталога.
Детали:
Тело: CategoryCreate `{name}`. Шаги: (1) SELECT по имени; (2) при наличии — 409; (3) INSERT + COMMIT + REFRESH. Ответ: созданная категория. Ошибки: 409 (дубликат).
Структурировано:
Request: POST `/api/categories/admin/`.
Body (CategoryCreate): `name` (str 1..120 обязательное).
Steps:

1. Валидация тела.
2. SELECT WHERE name=:name.
3. Если найдено → 409.
4. INSERT.
5. COMMIT + REFRESH.
   Response: `{ id:int, name:str }`.
   Errors: 409 (имя занято); 422 (валидация); системные.
   Data: `categories`.

### GET /api/categories/admin/{category_id}

Что: просмотр категории.
Как: выборка по первичному ключу.
Почему: точечное редактирование и контроль.
Детали:
Path: `category_id`. SELECT категория. Ответ: `{id,name}`. Ошибки: 404.
Структурировано:
Request: GET `/api/categories/admin/{category_id}`.
Path: `category_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.Возврат.
Response: `{ id:int, name:str }`.
Errors: 404 (нет категории); 422 (тип ID).
Data: `categories`.

### PUT /api/categories/admin/{category_id}

Что: обновление названия.
Как: загрузка, проверка конфликта имени, применение изменений.
Почему: поддержание актуальности терминологии.
Детали:
Path: `category_id`. Тело: CategoryUpdate `{name?}`. Шаги: (1) SELECT; (2) если новое имя и отличается — проверка отсутствия другой категории с этим именем; (3) обновление; (4) COMMIT+REFRESH. Ответ: обновлённая категория. Ошибки: 404, 409.
Структурировано:
Request: PUT `/api/categories/admin/{category_id}`.
Path: `category_id` (int >0).
Body (CategoryUpdate): `name` (str 1..120 optional).
Steps:

1. SELECT категория.
2. Если None → 404.
3. Если новое имя → проверка уникальности.
4. Обновление значения.
5. COMMIT + REFRESH.
   Response: `{ id:int, name:str }`.
   Errors: 404 (нет категории); 409 (имя занято); 422 (валидация).
   Data: `categories`.

### DELETE /api/categories/admin/{category_id}?force=bool

Что: удаление категории.
Как: подсчёт связанных частей и подкатегорий; условная блокировка без force.
Почему: управление жизненным циклом узлов таксономии.
Детали:
Path: `category_id`; Query: `force` (bool default=false). Шаги: (1) SELECT категория; (2) COUNT частей; (3) COUNT подкатегорий; (4) если (parts_count>0 или subcategories_count>0) и force=false → 409; (5) DELETE + COMMIT. Ответ: 204. Ошибки: 404, 409.
Структурировано:
Request: DELETE `/api/categories/admin/{category_id}`.
Path: `category_id` (int >0).
Query: `force` (bool default=false).
Steps:

1. SELECT категория.
2. Если None → 404.
3. COUNT parts.
4. COUNT subcategories.
5. Если зависимости и force=false → 409.
6. DELETE + COMMIT.
   Response: 204 No Content.
   Errors: 404 (нет категории); 409 (зависимости); 422 (тип ID).
   Data: `categories`, `parts`, `subcategories`.

### POST /api/categories/admin/bulk-create

Что: пакетное добавление категорий.
Как: проверка уникальности каждой; вставка допустимых.
Почему: ускорение первоначального наполнения.
Детали:
Тело: массив CategoryCreate. Для каждой: проверка уникальности имени. Валидные создаются; ошибки фиксируются. Один COMMIT. Ответ: `{total, created, failed, errors[]}`.
Структурировано:
Request: POST `/api/categories/admin/bulk-create`.
Body: `[ CategoryCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого: валидация; SELECT имя; проверка уникальности.
3. Добавление валидных.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[{id,name}] }`.
   Errors: Ошибки элементов; 422 (не массив).
   Data: `categories`.

### GET /api/categories/admin/bulk-delete?ids=...&force=bool

Что: пакетное удаление категорий.
Как: проверка зависимостей по каждой; выборочное удаление.
Почему: реорганизация структуры за один проход.
Детали:
Query: `ids` (список int), `force` (bool). Итерация: SELECT → COUNT parts/subcategories → при наличии и force=false → ошибка; иначе DELETE. Один COMMIT. Ответ: `{total, deleted, failed, errors[]}`.
Структурировано:
Request: GET `/api/categories/admin/bulk-delete` (метод может быть POST/DELETE в иной реализации; здесь отражено исходное описание).
Query: `ids` (CSV список int required); `force` (bool default=false).
Steps:

1. Парсинг списка.
2. Для каждого id SELECT категория.
3. Если отсутствует → failed++.
4. Если присутствует → COUNT parts и COUNT subcategories.
5. Если зависимости и force=false → errors.add(); failed++.
6. Иначе DELETE.
7. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors:[str] }`.
   Errors: 422 (неверный список); логические в errors.
   Data: `categories`, `parts`, `subcategories`.

### GET /api/categories/admin/stats

Что: статистика по категориям (кол-во частей, подкатегорий, топовые).
Как: агрегирующие запросы + группировки с подсчётами.
Почему: обзор распределения ассортимента по верхнему уровню.
Детали:
Метрики: общее число категорий; суммарное количество частей; среднее частей на категорию; количество пустых категорий; топ-5 по числу частей (ORDER BY parts_count DESC LIMIT 5); аналогично топ-5 по числу подкатегорий. Ответ: объект статистики с массивами `{category_id, name, parts_count}` и `{category_id, name, subcategories_count}`. Ошибки: при отсутствии данных массивы пустые.
Структурировано:
Request: GET `/api/categories/admin/stats`.
Steps:

1. COUNT категорий.
2. LEFT JOIN parts для подсчёта parts_count по категории.
3. SUM общего количества частей.
4. Расчёт среднего (parts_total/categories_total при categories_total>0).
5. Подсчёт пустых категорий (parts_count=0).
6. LEFT JOIN subcategories для подсчёта subcategories_count.
7. Формирование топ-5 по частям и топ-5 по подкатегориям.
   Response: `{ categories_total:int, parts_total:int, avg_parts_per_category:float?, empty_categories:int, top_parts:[{category_id:int,name:str,parts_count:int}], top_subcategories:[{category_id:int,name:str,subcategories_count:int}] }`.
   Errors: Пустая таблица → нули/[]; системные.
   Data: `categories`, `parts`, `subcategories`.
