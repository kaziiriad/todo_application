from redis import Redis
import json
# Define the Redis configuration

# Connect to the Redis server
class RedisManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = Redis(host=host, port=port, db=db)

    def set(self, key, value, expire=None):
        try:
            self.redis_client.set(key, json.dumps(value), ex=expire)
            return True
        except Exception as e:
            return False
    
    def get(self, key):
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            return None
    
    def delete(self, key):
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            return False
    