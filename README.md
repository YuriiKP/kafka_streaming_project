# Kafka Streaming Project

Проект для потоковой обработки данных с использованием Apache Kafka и хранения в S3-совместимом хранилище (MinIO) и ClickHouse. Система генерирует музыкальные события, сохраняет их в Kafka, а затем переносит данные в S3 в формате Parquet для дальнейшего анализа.

## 📋 Описание

Проект представляет собой pipeline для обработки событий музыкального стримингового сервиса:
- **Producer** генерирует события о воспроизведении треков (playback, pause, resume)
- **Consumer** читает события из Kafka и сохраняет их батчами в S3 в формате Parquet
- **Analytics** использует DuckDB для чтения и анализа данных из S3

## 🏗️ Архитектура

```
Music Producer → Kafka → Kafka Consumer → S3 (MinIO)|(ClickHouse) → DuckDB Analytics
```

### Компоненты:

1. **Kafka Producer** (`music_producer.py`) - генерирует и отправляет музыкальные события в Kafka
2. **Kafka Consumer** (`kafka_to_s3.py`) - читает события из Kafka и сохраняет в S3 батчами
3. **S3 Reader** (`read_from_s3.py`) - анализирует данные из S3 с помощью DuckDB
4. **Примеры** (`easy_producer.py`, `easy_consumer.py`) - простые примеры работы с Kafka

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Python 3.8+
- `.env` файл с учетными данными для MinIO

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd Kafka
```

2. Установите зависимости:
```bash
pip install -r reqirements.txt
```

3. Создайте `.env` файл в корне проекта:
```env
ACCESS_KEY=minioadmin
SECRET_KEY=minioadmin
```

4. Запустите инфраструктуру с помощью Docker Compose:
```bash
docker-compose up -d
```

Это запустит:
- **Kafka** на портах `9092` и `19092`
- **Zookeeper** на порту `2181`
- **Kafka UI** на порту `8080` (веб-интерфейс для управления Kafka)
- **MinIO** на портах `9000` (API)
- **ClickHouse** на порту `8123`

5. Откройте MinIO: http://localhost:9000
   - Логин: `minioadmin`
   - Пароль: `minioadmin`
   - Создайте bucket с именем `prod-python`

6. Откройте Kafka UI: http://localhost:8080

## 📖 Использование Kafka + s3 (MinIO)

### 1. Генерация музыкальных событий

Запустите продюсер для генерации событий:

```bash
python code/music_producer.py
```

Продюсер будет отправлять события каждую секунду в топик `music_events`. 
Генерируется три простых типа событий:
- `track_playback` - воспроизведение трека
- `pause_track` - пауза трека
- `resume_track` - возобновление воспроизведения

### 2. Сохранение событий в S3

Запустите консьюмер для чтения событий из Kafka и сохранения в S3:

```bash
python code/kafka_to_s3.py
```

Консьюмер:
- Читает события из топика `music_events`
- Группирует события в батчи (по умолчанию 100 событий)
- Сохраняет батчи в S3 в формате Parquet
- Путь сохранения: `s3://prod-python/YYYY-MM-DD/UUID.parquet`

### 3. Чтение данных из S3

Запустите скрипт для чтения сохраненных данных:

```bash
python code/read_from_s3.py
```

Скрипт выполняет:
- Подсчет общего количества записей
- Получение схемы данных
- Выборку первых 10 записей
- Фильтрацию по типу события (например, только `event_type_id = 1`)


### Примеры работы

#### Простой producer/consumer

Для тестирования базовой функциональности Kafka:

```bash
# В одном терминале
python code/easy_producer.py

# В другом терминале
python code/easy_consumer.py
```

## 📖 Использование Kafka + ClickHouse

### 1 Подключаемся к ClickHouse
Хост: localhost:8123
Пользователь: click
Пароль: click

### 2 Создаем в ClickHouse необходимые таблицы

Таблицы и материализованное передставление для взаимодействия с простым producer через ClickHouse.

```bash
create table easy_consumer (
    uuid String,
    first_name String,
    last_name String,
    middle_name String,
    timestamp String
) engine Kafka settings
 	kafka_broker_list = 'kafka',
    kafka_topic_list = 'my_topic',
    kafka_group_name = 'foo',
    kafka_format = 'JSON';


create table easy_consumer_phys (
    uuid String,
    first_name String,
    last_name String,
    middle_name String,
    timestamp String
) engine = MergeTree()
order by (uuid);


create materialized view easy_consumer_mat_view to easy_consumer_phys
	as select * from easy_consumer;
```

Таблицы и материализованное передставление для взаимодействия с музыкальными событиями

```bash
create table music_counsumer (
    event_param String,
    event_timestamp String
) engine = Kafka settings
    kafka_broker_list = 'kafka',
    kafka_topic_list = 'music_events',
    kafka_group_name = 'foo',
    kafka_format = 'JSON';


create table music_consumer_phys (
    event_param String,
    event_timestamp String,
    uuid UUID DEFAULT generateUUIDv4()
) engine = MergeTree()
order by (uuid);


create materialized view music_consumer_mat_view to music_consumer_phys
	  as select * from music_counsumer;
```

### 3 Читаем с данными в ClickHouse

Читаем данные из топика my_topic

```bash
-- 10 первых строк 
select * from easy_consumer_mat_view limit 10;

-- Схема таблицы 
describe table easy_consumer_mat_view;

-- 10 самых часто встречающихся имен
select first_name, 
	   count(uuid) cnt 
from easy_consumer_mat_view 
group by first_name 
order by cnt desc 
limit 10;
```

Читаем данные из топика music_events

```bash
-- Все события воспроизведения трека
select * 
from music_consumer_mat_view
where JSONExtractInt(event_param, 'event_type_id') = 1


-- Количество событий по типам
select 
    JSONExtractInt(event_param, 'event_type_id') event_type_id,
    JSONExtractString(event_param, 'event_type') event_type,
    count(*) as cnt
from music_consumer_mat_view
group by event_type_id, event_type
order by cnt desc;

```re


## 📊 Мониторинг

- **Kafka UI**: http://localhost:8080
- **MinIO UI**: http://localhost:9000


## 📁 Структура проекта

```
Kafka/
├── code/
│   ├── easy_producer.py      # Простой пример producer
│   ├── easy_consumer.py      # Простой пример consumer
│   ├── music_producer.py     # Producer музыкальных событий
│   ├── kafka_to_s3.py        # Consumer для сохранения в S3
│   └── read_from_s3.py       # Анализ данных из S3
├── data/                     # Данные MinIO (монтируется как volume)
├── docker-compose.yaml       # Конфигурация Docker инфраструктуры
├── reqirements.txt           # Зависимости Python
├── .env                      # Переменные окружения (создать вручную)
└── README.md                 # Документация
```

## 🔍 Формат данных

### Событие в Kafka

```json
{
  "event_param": {
    "event_type_id": 1,
    "event_type": "track_playback",
    "user_id": "uuid",
    "platform_token": "platform_token",
    "ipv4": "ip_address",
    "country": "country_name",
    "uuid_track": "track_uuid"
  },
  "event_timestamp": {
    "ts": 1234567890,
    "ts_ms": 1234567890123
  }
}
```

### Структура в Parquet

После нормализации с помощью `pandas.json_normalize()` данные сохраняются в формате Parquet со следующей структурой:
- `event_param.event_type_id`
- `event_param.event_type`
- `event_param.user_id`
- `event_param.platform_token`
- `event_param.ipv4`
- `event_param.country`
- `event_param.uuid_track`
- `event_timestamp.ts`
- `event_timestamp.ts_ms`

## 🛠️ Технологии

- **Apache Kafka** - потоковая платформа для обработки событий
- **MinIO** - S3-совместимое объектное хранилище
- **ClickHouse** - колоночная СУБД
- **DuckDB** - аналитическая СУБД для обработки данных
- **Pandas** - библиотека для обработки данных
- **Confluent Kafka** - Python клиент для Kafka
- **Pendulum** - библиотека для работы с датами и временем
- **Faker** - генерация тестовых данных

