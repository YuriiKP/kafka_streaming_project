import json 
import time

import pendulum 
import uuid
from confluent_kafka import Producer
from faker import Faker



def generate_list_of_dict() -> dict[str, str]:
    fake = Faker(locate='ru_Ru')

    return {
        "uuid": str(uuid.uuid4()),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "timestamp": pendulum.now("UTC").to_iso8601_string(),
    }

conf = {"bootstrap.servers": "localhost:19092"}

producer = Producer(conf)


sleep_time = 1

while True: 
    start = time.perf_counter()

    data = generate_list_of_dict()

    str_data = json.dumps(data)
    print(str_data)

    producer.produce(topic='my_topic')
    producer.flush()

    elspsed = time.perf_counter() - start
    time.sleep(1)