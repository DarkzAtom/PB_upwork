# PRICING RULES ROUTER — Функциональное описание эндпоинтов

## Админские эндпоинты (`/api/pricingrules/admin`)

### GET /api/pricingrules/admin/

Что: листинг правил ценообразования.
Как: выборка с пагинацией.
Почему: просмотр действующих конфигураций.
Детали:
Query: `skip` (int ≥0), `limit` (int 1..1000). Базовый SELECT всех правил без сортировки либо сортировка по `priority DESC` (если реализовано). Ответ: массив `{id, rule_name, min_cost, max_cost, margin_percent, markup_fixed, priority, is_active, supplier_id?, brand_id?, category_id?, region?}`. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/pricingrules/admin/`.
Query: `skip` (int ≥0 default 0); `limit` (int 1..1000 default 50).
Steps:

1. Валидация параметров.
2. SELECT \* FROM pricing_rules.
3. (Опционально) ORDER BY priority DESC.
4. OFFSET/LIMIT.
   Response: `[ { id:int, rule_name:str, min_cost:decimal?, max_cost:decimal?, margin_percent:decimal?, markup_fixed:decimal?, priority:int, is_active:bool, supplier_id:int?, brand_id:int?, category_id:int?, region:str? } ]`.
   Errors: 422 (невалидные параметры); пустой результат → [].
   Data: `pricing_rules`.

### POST /api/pricingrules/admin/

Что: создание правила.
Как: проверки существования указанных FK, отношений границ стоимости, уникальности имени; сохранение.
Почему: добавление новой логики расчёта цены.
Детали:
Тело: схема PricingRuleCreate. Поля: `rule_name` (строка уник.), `min_cost` (decimal ≥0), `max_cost` (decimal ≥ min_cost или null), `margin_percent` (decimal ≥0), `markup_fixed` (decimal ≥0), `priority` (int ≥0), `is_active` (bool), опциональные FK `supplier_id`, `brand_id`, `category_id`, `region`. Шаги: (1) Проверка уникальности `rule_name`; (2) Валидация min/max (если оба заданы: min ≤ max); (3) Проверка существования связанных FK при их присутствии; (4) INSERT + COMMIT + REFRESH. Ответ: созданное правило. Ошибки: 409 при конфликте имени, 422 при нарушении отношения min/max, 404 если FK не существует.
Структурировано:
Request: POST `/api/pricingrules/admin/`.
Body (PricingRuleCreate):
`rule_name` (str 1..120 уник.) обязательное.
`min_cost` (decimal ≥0 optional).
`max_cost` (decimal ≥0 optional, если задано ≥ min_cost).
`margin_percent` (decimal ≥0 optional).
`markup_fixed` (decimal ≥0 optional).
`priority` (int ≥0 обязательное).
`is_active` (bool обязательное).
FK: `supplier_id` (int >0 optional), `brand_id` (int >0 optional), `category_id` (int >0 optional), `region` (str ≤50 optional).
Steps:

1. Валидация схемы.
2. SELECT rule_name для проверки уникальности.
3. Проверка min/max соотношения.
4. Проверка существования каждого указанного FK.
5. INSERT строки.
6. COMMIT + REFRESH.
   Response: созданный объект правила.
   Errors: 409 (дубликат rule_name); 422 (min/max нарушены или негативные значения); 404 (отсутствующий FK); системные.
   Data: `pricing_rules`, `suppliers`, `brands`, `categories`.

### PUT /api/pricingrules/admin/{rule_id}

Что: обновление параметров правила.
Как: загрузка, проверка связей и границ, изменение полей.
Почему: корректировка условий маржи и наценки.
Детали:
Path: `rule_id`. Тело: PricingRuleUpdate (все поля опциональны). Шаги: (1) SELECT правило; (2) при смене `rule_name` — проверка уникальности; (3) сбор новых значений min_cost/max_cost для проверки min ≤ max; (4) при изменении FK — проверка их существования; (5) обновление полей; (6) COMMIT+REFRESH. Ответ: обновлённое правило. Ошибки: 404 (не найдено), 409 (имя занято), 422 (min/max нарушены).
Структурировано:
Request: PUT `/api/pricingrules/admin/{rule_id}`.
Path: `rule_id` (int >0).
Body (PricingRuleUpdate): любые из перечисленных в create.
Steps:

1. SELECT правило.
2. Если None → 404.
3. Если меняется `rule_name` → проверка уникальности.
4. Вычисление потенциальных min/max → проверка.
5. Проверка существования новых FK.
6. Присвоение новых значений.
7. COMMIT + REFRESH.
   Response: обновлённый объект.
   Errors: 404 (нет правила); 409 (конфликт имени); 422 (min/max); системные.
   Data: `pricing_rules`, `suppliers`, `brands`, `categories`.

### DELETE /api/pricingrules/admin/{rule_id}

Что: удаление правила.
Как: удаление по ID при наличии.
Почему: прекращение использования устаревшей логики.
Детали:
Path: `rule_id`. Шаги: SELECT → если отсутствует 404 → DELETE → COMMIT. Ответ: 204 без тела. Ошибки: 404.
Структурировано:
Request: DELETE `/api/pricingrules/admin/{rule_id}`.
Path: `rule_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.DELETE; 4.COMMIT.
Response: 204 No Content.
Errors: 404 (не найдено); 422 (тип ID); системные.
Data: `pricing_rules`.

### POST /api/pricingrules/admin/bulk-create

Что: массовое создание правил.
Как: последовательная валидация каждого входного элемента.
Почему: ускоренное внедрение набора ценовых стратегий.
Детали:
Тело: массив PricingRuleCreate. Для каждого: проверки уникальности имени, min/max отношения, существования FK. Валидные добавляются в сессию, ошибки протоколируются в список. После цикла единый COMMIT. Ответ: `{total, created, failed, errors[]}`. Ошибки: индивидуальные — не прерывают общее выполнение.
Структурировано:
Request: POST `/api/pricingrules/admin/bulk-create`.
Body: `[ PricingRuleCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого элемента: валидация; проверка rule_name; min/max; FK.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[ {id,rule_name} ] }`.
   Errors: Ошибки элементов внутри `errors`; 422 (не массив). 409 не применяется глобально.
   Data: `pricing_rules`.

### POST /api/pricingrules/admin/bulk-delete?rule_ids=...

Что: массовое удаление набора правил.
Как: итерация и удаление найденных.
Почему: пакетная очистка.
Детали:
Query: `rule_ids` (список int). Шаги: парсинг списка → для каждого SELECT → при наличии DELETE → счётчики. Один COMMIT. Ответ: `{total, deleted, failed}`. Ошибки: отсутствующие ID в failed.
Структурировано:
Request: POST `/api/pricingrules/admin/bulk-delete`.
Query: `rule_ids` (CSV список int required).
Steps:

1. Парсинг CSV.
2. Для каждого id SELECT.
3. Если найдено → DELETE иначе failed++.
4. Один COMMIT.
   Response: `{ total:int, deleted:int, failed:int, errors?:[str] }`.
   Errors: 422 (формат списка); отсутствующие ID в failed.
   Data: `pricing_rules`.

### GET /api/pricingrules/admin/statistics

Что: сводная статистика (активность, уникальные измерения, диапазоны).
Как: агрегаты COUNT, AVG, MIN, MAX по соответствующим полям.
Почему: обзор структуры и плотности правил.
Детали:
Метрики: общее число правил, число активных/неактивных, MIN/MAX/AVG `margin_percent`, MIN/MAX/AVG `markup_fixed`, уникальные бренды/категории/поставщики/регионы (COUNT DISTINCT), распределение по `priority` (может быть массив пар `{priority, count}`). Ответ: объект статистики. Ошибки: при отсутствии правил значения нули или null.
Структурировано:
Request: GET `/api/pricingrules/admin/statistics`.
Steps:

1. COUNT всех правил.
2. COUNT активных WHERE is_active=true.
3. COUNT неактивных.
4. MIN/MAX/AVG margin_percent.
5. MIN/MAX/AVG markup_fixed.
6. COUNT DISTINCT supplier_id / brand_id / category_id / region.
7. GROUP BY priority → массив `{priority,count}`.
   Response: `{ total:int, active:int, inactive:int, margin:{min:decimal?, max:decimal?, avg:decimal?}, markup:{min:decimal?, max:decimal?, avg:decimal?}, distinct:{suppliers:int, brands:int, categories:int, regions:int}, priority_distribution:[{priority:int,count:int}] }`.
   Errors: Пустая таблица → значения 0 или null; системные.
   Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-active/{is_active}

Что: фильтрация по признаку активности.
Как: выборка `is_active`.
Почему: разделение применимых и выключенных правил.
Детали:
Path: `is_active` (bool). WHERE is_active = :flag. Ответ: массив правил. Ошибки: пустой массив при отсутствии.
Структурировано:
Request: GET `/api/pricingrules/admin/by-active/{is_active}`.
Path: `is_active` (bool true/false или 0/1).
Steps: SELECT WHERE is_active=:flag.
Response: `[ { id, rule_name, is_active } ]`.
Errors: 422 (некорректное значение); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-supplier/{supplier_id}

Что: правила по поставщику.
Как: фильтр по `supplier_id`.
Почему: анализ индивидуальной ценовой политики.
Детали:
Path: `supplier_id`. WHERE supplier_id = :id. Ответ: массив. Ошибки: пустой массив (поставщик может существовать без правил).
Структурировано:
Request: GET `/api/pricingrules/admin/by-supplier/{supplier_id}`.
Path: `supplier_id` (int >0).
Steps: SELECT WHERE supplier_id=:id.
Response: `[ { id, rule_name, supplier_id, priority } ]`.
Errors: 422 (тип ID); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-brand/{brand_id}

Что: правила по бренду.
Как: фильтр по `brand_id`.
Почему: настройка маржи под бренд.
Детали:
Path: `brand_id`. WHERE brand_id = :id. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/by-brand/{brand_id}`.
Path: `brand_id` (int >0).
Steps: SELECT WHERE brand_id=:id.
Response: `[ { id, rule_name, brand_id, priority } ]`.
Errors: 422 (тип ID); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-category/{category_id}

Что: правила по категории.
Как: фильтр `category_id`.
Почему: управление маржой на уровне категории.
Детали:
Path: `category_id`. WHERE category_id = :id. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/by-category/{category_id}`.
Path: `category_id` (int >0).
Steps: SELECT WHERE category_id=:id.
Response: `[ { id, rule_name, category_id, priority } ]`.
Errors: 422 (тип ID); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-region/{region}

Что: правила по региону склада.
Как: фильтр ILIKE по строковому региону.
Почему: адаптация цены к логистическому региону.
Детали:
Path: `region` (строка). WHERE region ILIKE `%region%`. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/by-region/{region}`.
Path: `region` (str 1..50).
Steps: SELECT WHERE region ILIKE '%region%'.
Response: `[ { id, rule_name, region, priority } ]`.
Errors: 422 (пустая строка); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/by-priority/{priority}

Что: правила конкретного приоритета.
Как: фильтр `priority`.
Почему: анализ группы одного уровня.
Детали:
Path: `priority` (int ≥0). WHERE priority = :p. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/by-priority/{priority}`.
Path: `priority` (int ≥0).
Steps: SELECT WHERE priority=:p.
Response: `[ { id, rule_name, priority } ]`.
Errors: 422 (негативное значение); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/search?name=...

Что: поиск правил по имени.
Как: `rule_name ILIKE %name%`.
Почему: быстрый доступ к нужному правилу.
Детали:
Query: `name` (строка). WHERE rule_name ILIKE `%name%`. Ответ: массив. Ошибки: пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/search`.
Query: `name` (str 1..120 required).
Steps: SELECT WHERE rule_name ILIKE '%name%'.
Response: `[ { id, rule_name, priority } ]`.
Errors: 422 (пустая строка); пустой массив.
Data: `pricing_rules`.

### GET /api/pricingrules/admin/price-range-analysis

Что: частота встречаемости диапазонов цен.
Как: сбор всех записей и группировка по строковому ключу диапазона.
Почему: обзор покрытых интервалов стоимости.
Детали:
Формирование ключа: если заданы `min_cost` и `max_cost` → `"min-max"`; если только `min_cost` → `"min+"`; если только `max_cost` → `"0-max"`; если оба null → `"ANY"`. Группировка COUNT по ключу. Ответ: массив `{range_key, count}` отсортированный по min_cost либо по count. Ошибки: при отсутствии правил возвращается пустой массив.
Структурировано:
Request: GET `/api/pricingrules/admin/price-range-analysis`.
Steps:

1. SELECT всех правил (min_cost,max_cost).
2. Построение ключа диапазона для каждой строки.
3. Группировка по ключу с COUNT.
4. (Опционально) сортировка по диапазону или count.
   Response: `[ { range_key:str, count:int } ]`.
   Errors: Пустая таблица → [].
   Data: `pricing_rules`.
