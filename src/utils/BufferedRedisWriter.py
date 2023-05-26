import json
import os
import time
import redis
from utils.Decorators import rabbitmq_decorator
from utils.RedisClient import RedisClient
from utils.Utilities import get_today_date, get_current_hour

class BufferedRedisWriter:
    def __init__(self, master_key, sub_key_prefix, filename_date=0, filename_hour=0, flush_interval=1.0):
        self.master_key = master_key
        self.sub_key_prefix = sub_key_prefix
        self.filename_date = filename_date
        self.filename_hour = filename_hour
        self.flush_interval = flush_interval
        self.last_flush_time = time.monotonic()
        self.redis = RedisClient().connect()

    @rabbitmq_decorator('twitter_raw_data')
    def append(self, data):
        date_dir_name = get_today_date() if self.filename_date == 0 else self.filename_date
        current_file_index = get_current_hour() if self.filename_hour == 0 else self.filename_hour
        sub_key = f":{date_dir_name}:{self.sub_key_prefix}:{current_file_index}"
        key = self.master_key + sub_key
        self.redis.rpush(key, data)

        data = json.loads(data)
        return [ data['tweet_type'], data ]


