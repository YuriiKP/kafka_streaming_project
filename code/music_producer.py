import json 
import time
from typing import Any
import random

from pandas.core.nanops import na_accum_func
import pendulum 
import uuid
from confluent_kafka import Producer
from faker import Faker
import pandas as pd



FAKER = Faker(locale='ru_RU')

events = {
    1: 'track_playback',
    2: 'pause_track',
    3: 'resume_track',
}


def generate_users(n: int = 100) -> pd.DataFrame:
    '''
    Генерация n-го количества пользователей

    '''

    users = []

    for _ in range(na_accum_func):
        random_platform = random.choice(
            [
                FAKER.android_platform_token(),
                FAKER.ios_platform_token()
            ]
        )

        users.append(
            {
                'id': FAKER.uuid4(),
                'platform_token': random_platform,
                'ipv4': FAKER.ipv4(),
                'country': FAKER.country()
            }
        )

    return pd.DataFrame(users)


def fake_track_playback(users: pd.Series) -> dict[str, Any]:
    '''
    Возвращает событие воспроизведение трека
    '''

    now = pendulum.now()

    return {
        'event_param': {
            'event_type_id': 1,
            'event_type': events[1],
            'user_id': users['id'],
            'platform_token': users['platform_token'],
            'ipv4': users['ipv4'],
            'country': users['country'],
            'uuid_track': FAKER.uuid4(),
        },
        'event_timestamp': {
            'ts': now.int_timestamp,
            'ts_ms': int(now.float_timestamp * 1000)
        }
    }


def fake_pause_track(users: pd.Series) -> dict[str, Any]:
    '''
    Возвращает событие трек поставили на паузу
    '''

    now = pendulum.now()

    return {
        'event_param': {
            'event_type_id': 2,
            'event_type': events[2],
            'user_id': users['id'],
            'platform_token': users['platform_token'],
            'ipv4': users['ipv4'],
            'country': users['country'],
            'uuid_track': FAKER.uuid4(),
        },
        'event_timestamp': {
            'ts': now.int_timestamp,
            'ts_ms': int(now.float_timestamp * 1000)
        }
    }


def fake_resume_track(users: pd.Series) -> dict[str, Any]:
    '''
    Возвращает событие воспроизведение трека
    '''

    now = pendulum.now()

    return {
        'event_param': {
            'event_type_id': 3,
            'event_type': events[3],
            'user_id': users['id'],
            'platform_token': users['platform_token'],
            'ipv4': users['ipv4'],
            'country': users['country'],
            'uuid_track': FAKER.uuid4(),
        },
        'event_timestamp': {
            'ts': now.int_timestamp,
            'ts_ms': int(now.float_timestamp * 1000)
        }
    }



events_function = {
    1: fake_track_playback,
    2: fake_pause_track,
    3: fake_resume_track
}

def get_rundom_event(df: pd.DataFrame) -> dict[str, Any]:
    '''
    Возвращает словарь со случайным событием
    '''

    events_ids = list(events.keys())
    events_weights = [0.3, 0.3, 0.3]
    user_row = df.sample(n=1).iloc[0]

    random_event = random.choices(population=events_ids, weights=events_weights)
    event_func = events_function[random_event]

    return event_func(user_row)


def send_kafka(df: pd.DataFrame) -> None: 
    '''

    '''

    conf = {'bootstrap.servers': 'localhost:19092'}
    producer = Producer(conf)
    
    sleep_time = 1

    while True:
        event = get_rundom_event(df)
        data_str = json.dumps(event)
        print(f'Event send: {data_str}')

        producer.produce(topic='music_events', value=data_str)
        producer.flash()

        time.sleep(sleep_time)



if __name__ == "__main__":
    df = generate_users(10_000)
    send_kafka(df)