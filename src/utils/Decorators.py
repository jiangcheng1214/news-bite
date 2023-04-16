# utils/Decorators.py
import json
from functools import wraps
from utils.RabbitMQProducer import RabbitMQProducer

def rabbitmq_decorator(queue_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            processed_data = json.dumps(result)
            rabbitmq_producer = RabbitMQProducer()
            rabbitmq_producer.publish(queue_name, processed_data)
            return result
        return wrapper
    return decorator