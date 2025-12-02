# PARTS ROUTER — Функциональное описание эндпоинтов

## 1. Админские эндпоинты (`/api/parts/admin`)

### GET /api/parts/admin

Что: листинг частей с фильтрами.
Как: базовый запрос `Part` + опциональные фильтры по `category_id` и `supplier_id` через подзапрос `SupplierPrice`.
Почему: администрирование ассортимента с учётом поставщиков и категорий.
Детали:
Query параметры: `skip` (int ≥0), `limit` (int 1..1000), `category_id` (int >0, опционально), `supplier_id` (int >0, опционально). Логика: формируется базовый SELECT из таблицы частей; если задан `category_id` добавляется фильтр равенства; если указан `supplier_id`, добавляется EXISTS/IN к `SupplierPrice` связывающий `parts.id = supplier_price.part_id AND supplier_price.supplier_id = :supplier_id`. Сортировка отсутствует (натуральный порядок). Ответ: массив объектов части без расширенных расчётов. Ошибки: 0 результатов → пустой массив; некорректные типы параметров приводят к 422.
Структурировано:
Request: GET `/api/parts/admin`.
Query: `skip` (int ≥0, default 0); `limit` (int 1..1000, default 50); `category_id` (int >0 optional); `supplier_id` (int >0 optional).
Path: отсутствует.
Body: отсутствует.
Steps:

1. Парсинг и валидация параметров.
2. Базовый SELECT из `parts`.
3. Применение фильтра по `category_id` если задан.
4. Применение EXISTS для `supplier_id`.
5. OFFSET/LIMIT.
   Response: `[ { id:int, part_number:str, normalized_part_number:str, brand_id:int, category_id:int, ... } ]`.
   Errors: 422 (невалидные числа); результат пуст → массив [] без ошибки.
   Data: таблицы `parts`, `supplier_price` (EXISTS).

### POST /api/parts/admin

Что: создание части.
Как: проверки существования связанных FK; проверка уникальной пары (brand, normalized_part_number); вставка.
Почему: добавление нового артикула в каталог.
Детали:
Тело: JSON (схема PartCreate) содержит обязательные поля: `part_number`, `normalized_part_number`, `brand_id`, `category_id`, дополнительные атрибуты описания и классификации. Шаги: (1) Проверка, что brand и category существуют; (2) Запрос на существование части с тем же `brand_id` и `normalized_part_number`; (3) При нахождении конфликта возвращается HTTP 409 с сообщением о дубликате; (4) INSERT + COMMIT; (5) REFRESH объекта для получения ID. Ответ: созданная часть. Ошибки: 409 при нарушении уникальности, 404 если FK не найдены.
Структурировано:
Request: POST `/api/parts/admin`.
Body Schema (PartCreate):
`part_number` (str 1..120) — обязательное.
`normalized_part_number` (str 1..120) — обязательное.
`brand_id` (int >0) — обязательное.
`category_id` (int >0) — обязательное.
Доп. поля: `description` (str?), `attributes` (obj/json?), `status` (str?) если присутствуют.
Steps:

1. Валидация тела схемой.
2. SELECT brand по `brand_id`; SELECT category по `category_id`.
3. SELECT часть WHERE brand_id=:brand_id AND normalized_part_number=:normalized_part_number.
4. При наличии → 409.
5. INSERT новой строки.
6. COMMIT + REFRESH.
   Response: `{ id:int, part_number:str, normalized_part_number:str, brand_id:int, category_id:int, ... }`.
   Errors: 404 (brand или category отсутствуют); 409 (дубликат пары); 422 (валидация тела).
   Data: `brands`, `categories`, `parts`.

### GET /api/parts/admin/{part_id}

Что: детальный админский вид части с минимальной ценой закупки.
Как: загрузка части; вычисление лучшей себестоимости через обход связанных `SupplierPrice` и курсов FX.
Почему: предоставление базовой экономической информации для управления.
Детали:
Path: `part_id` (int >0). Шаги: (1) SELECT часть; (2) запрос всех связанных предложений (цены поставщика) с активными курсами валют; (3) нормализация цены: при отличии валют используется FX множитель; (4) выбор минимальной нормализованной себестоимости; (5) вычисление доп. полей (например, best_cost). Ответ: объект части + поле минимальной себестоимости (если реализовано). Ошибки: 404 если часть отсутствует.
Структурировано:
Request: GET `/api/parts/admin/{part_id}`.
Path: `part_id` (int >0).
Steps:

1. SELECT часть по ID.
2. Если не найдена → 404.
3. SELECT все supplier_price WHERE part_id=:part_id.
4. JOIN/получение соответствующих FX курсов при необходимости конверсии.
5. Нормализация: `normalized_cost = base_price * fx_rate?`.
6. Выбор минимального `normalized_cost`.
7. Формирование объекта с `best_cost`.
   Response: `{ id, part_number, ..., best_cost:float? }`.
   Errors: 404 (часть отсутствует); 422 (некорректный ID тип).
   Data: `parts`, `supplier_price`, `fx_rates`.

### PUT /api/parts/admin/{part_id}

Что: обновление атрибутов части.
Как: проверка FK и конфликта уникальности сочетания brand + normalized_part_number; применение изменений.
Почему: актуализация данных товара.
Детали:
Тело: PartUpdate (все поля опциональны). Шаги: (1) SELECT часть; (2) при изменении brand/category — проверка их существования; (3) при изменении `normalized_part_number` или `brand_id` — проверка отсутствия другой части с той же парой; (4) обновление атрибутов через итерацию по входным данным; (5) COMMIT + REFRESH. Ответ: обновлённая часть. Ошибки: 404 (не найдена), 409 (конфликт уникальности).
Структурировано:
Request: PUT `/api/parts/admin/{part_id}`.
Path: `part_id` (int >0).
Body (PartUpdate): опциональные поля `part_number`, `normalized_part_number`, `brand_id`, `category_id`, и др.
Steps:

1. SELECT часть.
2. При отсутствии → 404.
3. Если изменяется `brand_id` или `category_id` → проверка FK.
4. Если изменяется `normalized_part_number` или `brand_id` → проверка уникальности пары.
5. Присвоение новых значений.
6. COMMIT + REFRESH.
   Response: обновлённая строка части.
   Errors: 404 (нет части), 409 (дубликат пары), 422 (валидация данных).
   Data: `parts`, `brands`, `categories`.

### DELETE /api/parts/admin/{part_id}

Что: удаление части.
Как: прямое удаление по ID.
Почему: вывод товара из каталога.
Детали:
Path: `part_id`. Шаги: SELECT → при отсутствии 404 → DELETE → COMMIT. Ответ: статус 204 (без тела). Ошибки: 404.
Структурировано:
Request: DELETE `/api/parts/admin/{part_id}`.
Path: `part_id` (int >0).
Steps: 1.SELECT; 2.Если None→404; 3.DELETE; 4.COMMIT.
Response: 204 No Content.
Errors: 404 (часть не найдена); 422 (тип ID некорректен).
Data: `parts`.

### POST /api/parts/admin/bulk-create

Что: массовое добавление частей.
Как: последовательная проверка FK и уникальности; пакетная вставка.
Почему: быстрое наполнение каталога.
Детали:
Тело: массив объектов PartCreate. Итерация: для каждой записи проверка существования brand/category + уникальности пары brand+normalized_part_number. Успешные объекты добавляются в сессию; после цикла один COMMIT; сбор статистики: `total`, `created`, `failed`, `errors[]`. Ответ: JSON статистика + массив созданных (или без детальных данных, зависит от реализации). Ошибки: логические собираются в массив, глобальных HTTP 409 нет — пакет обрабатывается индивидуально.
Структурировано:
Request: POST `/api/parts/admin/bulk-create`.
Body: `[ PartCreate, ... ]`.
Steps:

1. Инициализация счетчиков.
2. Для каждого элемента: валидация; проверка FK; проверка уникальности пары.
3. Добавление валидных в сессию.
4. Один COMMIT.
5. Формирование статистики.
   Response: `{ total:int, created:int, failed:int, errors:[str], items?:[ {id,...} ] }`.
   Errors: ошибки каждого элемента внутри `errors`; 422 если тело не массив.
   Data: `parts`, `brands`, `categories`.

## 2. Публичные эндпоинты (`/api/parts`)

### GET /api/parts/search

Что: поиск частей с расчётом цены и статуса.
Как: фильтрация по текстовым полям, бренду, категории; выбор лучшего предложения (минимальная стоимость + предпочтение региона) и применение правила ценообразования.
Почему: предоставление клиенту итоговой цены, наличия и ориентировочного срока.
Детали:
Query: `q` (строка поиска по part_number / нормализованному), `brand_id`, `category_id`, постраничные `skip`, `limit`. Шаги: (1) Формирование базового набора частей через LIKE/ILIKE фильтры; (2) Применение фильтров по brand/category; (3) Для каждой части получение всех предложений (SupplierPrice) с их валютами; (4) Конвертация base_price в единую валюту (если требуется); (5) Выбор лучшего предложения: минимальная нормализованная цена (при равенстве — предпочтение локального склада/регионального признака если реализовано); (6) Поиск применимого правила ценообразования по приоритету/условиям (бренд, категория, регион, поставщик); (7) Расчёт итоговой цены: base_cost \* коэффициент правила или наценка; (8) Формирование статуса наличия из `available_qty` и/или `stock_status`; (9) Определение lead_time_days и его диапазона если в предложении есть min/max. Ответ: массив объектов `{part_id, part_number, brand_id, category_id, best_offer: {supplier_id, warehouse_id, base_cost, final_price, currency, lead_time_days, available_qty}}`. Ошибки: пустой результат → пустой массив; 422 при некорректных типах параметров.
Структурировано:
Request: GET `/api/parts/search`.
Query: `q` (str 1..120 optional); `brand_id` (int >0 optional); `category_id` (int >0 optional); `skip` (int ≥0 default 0); `limit` (int 1..200 default 50).
Steps:

1. Базовый SELECT частей.
2. Применение LIKE/ILIKE для `q` по полям `part_number`, `normalized_part_number`.
3. Фильтры brand/category.
4. Для каждой части выбор всех поставщицких цен.
5. Нормализация цен по FX (если валюта отличается от базовой).
6. Выбор минимальной нормализованной стоимости; правило равенства → предпочтение условия (регион/склад) если реализовано.
7. Поиск подходящего pricing_rule по приоритету и условиям.
8. Расчёт `final_price`.
9. Формирование availability и lead_time.
10. Добавление в результат.
    Response: `[ { part_id:int, part_number:str, brand_id:int, category_id:int, best_offer:{ supplier_id:int, warehouse_id:int?, base_cost:float, final_price:float, currency:str, lead_time_days:int?, available_qty:int? } } ]`.
    Errors: 422 (параметры вне диапазона); пустой результат → [].
    Data: `parts`, `supplier_price`, `fx_rates`, `pricing_rules`.

### GET /api/parts/{part_id}

Что: деталь части с применённым предложением и диапазоном доставки.
Как: загрузка части, выбор лучшего предложения, расчёт продажной цены и диапазона дней.
Почему: формирование карточки товара для интерфейса покупателя.
Детали:
Path: `part_id`. Шаги: (1) SELECT часть; (2) сбор связанных предложений; (3) нормализация цен по валютным курсам; (4) выбор лучшего предложения; (5) применение правила ценообразования; (6) вычисление `delivery_days_min` / `delivery_days_max` (например на основе lead time и фиксированного транспортного интервала если реализовано); (7) формирование итогового JSON. Ответ: `{id, part_number, brand_id, category_id, pricing: {base_cost, final_price, currency}, availability: {available_qty, stock_status}, delivery_range: {min, max}}`. Ошибки: 404 при отсутствии части.
Структурировано:
Request: GET `/api/parts/{part_id}`.
Path: `part_id` (int >0).
Steps:

1. SELECT часть.
2. Если None → 404.
3. SELECT все цены поставщиков.
4. Нормализация цен.
5. Выбор минимальной.
6. Поиск pricing_rule.
7. Расчёт финальной цены.
8. Определение диапазона доставки (min/max) из lead time и доп. интервала.
   Response: `{ id:int, part_number:str, brand_id:int, category_id:int, pricing:{ base_cost:float, final_price:float, currency:str }, availability:{ available_qty:int?, stock_status:str? }, delivery_range:{ min:int?, max:int? } }`.
   Errors: 404 (часть не найдена); 422 (тип ID); системные.
   Data: `parts`, `supplier_price`, `fx_rates`, `pricing_rules`.
