from redis import Redis
import json
from datetime import datetime
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
            return json.loads(value.decode('utf-8')) if value else None # type: ignore
        except Exception as e:
            return None
    
    def delete(self, key):
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            return False
    
    def store_socket_session(self, sid: str, user_data: dict, expire: int = 3600):
        """Store Socket.IO session data"""
        key = f"socket:session:{sid}"
        user_data['last_seen'] = datetime.now().isoformat()
        return self.set(key, user_data, expire)
    
    def get_socket_session(self, sid: str):
        """Get Socket.IO session data"""
        key = f"socket:session:{sid}"
        return self.get(key)
    
    def remove_socket_session(self, sid: str):
        """Remove Socket.IO session data"""
        key = f"socket:session:{sid}"
        return self.delete(key)
    
    def add_user_to_room(self, room_id: str, user_data: dict, expire: int = 3600):
        """Add user to room in Redis"""
        key = f"room:members:{room_id}"
        room_data = self.get(key) or {}
        room_data[user_data['sid']] = user_data
        return self.set(key, room_data, expire)
    
    def remove_user_from_room(self, room_id: str, sid: str):
        """Remove user from room in Redis"""
        key = f"room:members:{room_id}"
        room_data = self.get(key) or {}
        if sid in room_data:
            del room_data[sid]
            return self.set(key, room_data)
        return False
    
    def get_room_members(self, room_id: str):
        """Get all members in a room"""
        key = f"room:members:{room_id}"
        return self.get(key) or {}
    
    def ping(self):
        """
        Check if Redis server is responding.
        
        Returns:
            bool: True if Redis server is responding, False otherwise
        """
        try:
            return self.redis_client.ping()
        except Exception as e:
            raise Exception(f"Redis ping failed: {str(e)}")

