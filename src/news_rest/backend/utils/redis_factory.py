import json

from django.conf import settings
from django_redis import get_redis_connection

class RedisFactory:
    def __init__(self, connection_name=settings.REDIS_CACHE_ALIAS):
        self.conn = get_redis_connection(connection_name)

        # Check if REDIS_CACHE_PASSWORD is defined in settings
        redis_cache_password = getattr(settings, 'REDIS_CACHE_PASSWORD', None)
        if redis_cache_password:
            # Set the client name and authenticate with the password
            self.conn.client_setname('django_cache')
            self.conn.auth(redis_cache_password)
        
    def set_key_value(self, key, value, expiration=None):
        """
        Set key-value in Redis cache
        :param key: Redis key
        :param value: Redis value
        :param expiration: Expiration time in seconds (optional)
        :return: True if successful, False otherwise
        """
        try:
            if expiration is not None:
                self.conn.set(key, self.serialize(value), ex=expiration)
            else:
                self.conn.set(key, self.serialize(value))
            return True
        except:
            return False
        
    def get_key_value(self, key):
        """
        Get value for a key in Redis cache
        :param key: Redis key
        :return: Redis value if exists, otherwise None
        """
        try:
            value = self.conn.get(key)
            if value is not None:
                return self.deserialize(value)
            else:
                return None
        except:
            return None
    
    def hset(self, key, field, value):
        """
        Set a field value in Redis hash
        :param key: Redis hash key
        :param field: Redis hash field
        :param value: Redis hash value
        :return: True if successful, False otherwise
        """
        try:
            self.conn.hset(key, field, self.serialize(value))
            return True
        except:
            return False
        
    def hmset(self, key, mapping):
        """
        Set multiple field values in Redis hash
        :param key: Redis hash key
        :param mapping: Redis hash mapping (dictionary)
        :return: True if successful, False otherwise
        """
        try:
            new_mapping = {k: self.serialize(v) for k, v in mapping.items()}
            self.conn.hmset(key, new_mapping)
            return True
        except:
            return False
    
    def hget(self, key, field):
        """
        Get value for a field in Redis hash
        :param key: Redis hash key
        :param field: Redis hash field
        :return: Redis hash value if exists, otherwise None
        """
        try:
            value = self.conn.hget(key, field)
            if value is not None:
                return self.deserialize(value)
            else:
                return None
        except:
            return None
    
    def hmget(self, key, fields):
        """
        Get values for multiple fields in Redis hash
        :param key: Redis hash key
        :param fields: List of Redis hash fields
        :return: Dictionary containing the hash values
        """
        try:
            values = self.conn.hmget(key, fields)
            return {fields[i]: self.deserialize(values[i]) if values[i] is not None else None for i in range(len(fields))}
        except:
            return {}
        
    def lpush(self, key, value):
        """
        Push an element to the left end of a Redis list
        :param key: Redis list key
        :param value: Value to push
        :return: True if successful, False otherwise
        """
        try:
            self.conn.lpush(key, self.serialize(value))
            return True
        except:
            return False

    
    def serialize(self, value):
        """
        Serialize a value using JSON
        :param value: Value to serialize
        :return: Serialized string
        """
        if isinstance(value, (int, float, str, list, dict)): #int, float, str, 
            return json.dumps(value)
        else:
            return str(value)
    
    def deserialize(self, value):
        """
        Deserialize a value using JSON
        :param value: Serialized string
        :return: Deserialized value
        """

        return json.loads
    
