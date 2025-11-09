import json
import uuid
import os
from datetime import UTC, datetime

from dotenv import load_dotenv
import pandas as pd
from confluent_kafka import Consumer, TopicPartition
import pendulum


load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
KAFKA_TOPIC = "music_events"
KAFKA_GROUP = "ParquetConsumerGroup"
BATCH_SIZE = 100

BUCKET_NAME = "prod-python"

STORAGE_OPTIONS = {
    "key": ACCESS_KEY,
    "secret": SECRET_KEY,
    "client_kwargs": {"endpoint_url": "http://localhost:9000"},
}


def save_batch_to_s3(batch: list): 
    '''
    Метод сохраняет сообщения батч данных из кафки в хранилище s3 
    '''

    df = pd.json_normalize(batch)
    date = pendulum.now('UTC').format('YYYY-MM-DD')
    file_uuid = uuid.uuid4()
    path = f's3://{BUCKET_NAME}/{date}/{file_uuid}.parquet'

    df.to_parquet(
        path=path,
        index=False,
        storage_options=STORAGE_OPTIONS
    )
    print(f'Батч сохранен: {path}')



def consume_message(
    topic: str | None = None, 
    offset: int | None = None,
    batch_size: int = 100
    
    ) -> None:
    '''
    Метод читает сообщения из кафки и сохраняет в s3
    '''

    conf = {
        "bootstrap.servers": "localhost:19092",
        "group.id": "mygroup",
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)

    if offset:
        partitions = consumer.list_topics(topic).topics[topic].partitions # Получаем все партиции топика 
        for partition in partitions:
            consumer.assign([TopicPartition(topic, partition, offset)])
    else:
        consumer.subscribe([topic])

    batch = []   
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                print(f'Ошбика в кафке: {message.error()}')
                continue
            
            try: 
                event = json.loads(message.value().decode('utf-8'))
                batch.append(event)
            except Exception as e:
                print(f"Ошибка в сообщении: {e}")
                continue

            if len(batch) >= batch_size:
                save_batch_to_s3(batch)
                batch = []
            
    except KeyboardInterrupt: 
        pass
    
    finally:
        if batch:
            save_batch_to_s3(batch)
        consumer.close()


if __name__ == "__main__":
    consume_message(topic=KAFKA_TOPIC, batch_size=BATCH_SIZE)
