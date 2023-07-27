import os
from dotenv import load_dotenv
import redis
import threading

class RedisClient:
    _instance_lock = threading.Lock()
    _connection = None
    _params_set = False

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(RedisClient, "_instance"):
            with RedisClient._instance_lock:
                if not hasattr(RedisClient, "_instance"):
                    RedisClient._instance = super().__new__(cls)
        return RedisClient._instance

    @staticmethod
    def shared():
        if not RedisClient._params_set:
            load_dotenv()  # 加载 .env 文件中的环境变量
            RedisClient.host = os.getenv("REDIS_HOST", 'localhost')
            RedisClient.port = int(os.getenv("REDIS_PORT", 6379))
            RedisClient.db = int(os.getenv("REDIS_DB", 0))
            RedisClient.password = os.getenv("REDIS_PASS", None)
            RedisClient._params_set = True
        if not RedisClient._connection:
            RedisClient._connection = redis.Redis(
                host=RedisClient.host, port=RedisClient.port, db=RedisClient.db, password=RedisClient.password)
        return RedisClient()._connection
