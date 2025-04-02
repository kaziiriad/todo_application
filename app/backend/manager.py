from typing import Dict, Any, List, Optional, Union
from redis import Redis
from redis.sentinel import Sentinel
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages Redis connections using Sentinel for high availability.
    Provides methods for basic Redis operations and specialized session/room management.
    """
    
    def __init__(
        self, 
        sentinel_hosts: Optional[List[str]] = None, 
        sentinel_port: int = 26379, 
        service_name: str = 'mymaster',
        password: Optional[str] = None,
        socket_timeout: float = 0.5,
        socket_connect_timeout: float = 1.0,
        retry_on_timeout: bool = True,
        *args, 
        **kwargs
    ):
        """
        Initialize Redis manager with Sentinel connection.
        
        Args:
            sentinel_hosts: List of Sentinel host addresses
            sentinel_port: Sentinel port number
            service_name: Redis service name in Sentinel
            password: Redis password for authentication
            socket_timeout: Socket timeout for Redis operations
            socket_connect_timeout: Socket connection timeout
            retry_on_timeout: Whether to retry on timeout
            *args, **kwargs: Additional arguments passed to Sentinel
        """
        if sentinel_hosts is None:
            sentinel_hosts = ['localhost']
        
        logger.info(f"Initializing Redis Sentinel connection to {sentinel_hosts}")
            
        sentinel = Sentinel(
            [(host, sentinel_port) for host in sentinel_hosts], 
            socket_timeout=socket_connect_timeout,
            password=password,
            decode_responses=True, 
            retry_on_timeout=retry_on_timeout,
            **kwargs
        )
        
        self.master = sentinel.master_for(
            service_name, 
            socket_timeout=socket_timeout,
            retry_on_timeout=retry_on_timeout
        )
        
        self.slave = sentinel.slave_for(
            service_name, 
            socket_timeout=socket_timeout,
            retry_on_timeout=retry_on_timeout
        )
        
        # Test connection
        try:
            self.ping()
            logger.info("Successfully connected to Redis via Sentinel")
        except Exception as e:
            logger.error(f"Failed to connect to Redis via Sentinel: {e}")
            raise
        
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis with optional expiration.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            expire: Optional expiration time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            self.master.set(key, json.dumps(value), ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
            
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis by key.
        Tries slave first, falls back to master if needed.
        
        Args:
            key: Redis key
            
        Returns:
            The deserialized value or None if not found/error
        """
        try:
            value = self.slave.get(key)  # Read from slave for better read distribution
            return json.loads(value.decode('utf-8')) if value else None # type: ignore
        except Exception as e:
            logger.warning(f"Slave read failed for key {key}, falling back to master: {e}")
            # Fallback to master if slave read fails
            try:
                value = self.master.get(key)
                return json.loads(value.decode('utf-8')) if value else None # type: ignore
            except Exception as e:
                logger.error(f"Redis GET error for key {key}: {e}")
                return None
                
    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.master.delete(key)  # Delete should be performed on master
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def store_socket_session(self, sid: str, user_data: dict, expire: int = 3600) -> bool:
        """
        Store Socket.IO session data.
        
        Args:
            sid: Socket ID
            user_data: User session data
            expire: Session expiration time in seconds
            
        Returns:
            bool: Success status
        """
        key = f"socket:session:{sid}"
        user_data['last_seen'] = datetime.now().isoformat()
        return self.set(key, user_data, expire)
    
    def get_socket_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Get Socket.IO session data.
        
        Args:
            sid: Socket ID
            
        Returns:
            dict: Session data or None if not found
        """
        key = f"socket:session:{sid}"
        return self.get(key)
    
    def remove_socket_session(self, sid: str) -> bool:
        """
        Remove Socket.IO session data.
        
        Args:
            sid: Socket ID
            
        Returns:
            bool: Success status
        """
        key = f"socket:session:{sid}"
        return self.delete(key)
    
    def add_user_to_room(self, room_id: str, user_data: dict, expire: int = 3600) -> bool:
        """
        Add user to room in Redis.
        
        Args:
            room_id: Room identifier
            user_data: User data to store
            expire: Room data expiration time in seconds
            
        Returns:
            bool: Success status
        """
        key = f"room:members:{room_id}"
        room_data = self.get(key) or {}
        room_data[user_data['sid']] = user_data
        return self.set(key, room_data, expire)
    
    def remove_user_from_room(self, room_id: str, sid: str) -> bool:
        """
        Remove user from room in Redis.
        
        Args:
            room_id: Room identifier
            sid: Socket ID of user to remove
            
        Returns:
            bool: Success status
        """
        key = f"room:members:{room_id}"
        room_data = self.get(key) or {}
        if sid in room_data:
            del room_data[sid]
            return self.set(key, room_data)
        return False
    
    def get_room_members(self, room_id: str) -> Dict[str, Any]:
        """
        Get all members in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            dict: Room members data indexed by socket ID
        """
        key = f"room:members:{room_id}"
        return self.get(key) or {}
    
    def ping(self) -> bool:
        """
        Check if Redis server is responding.
        
        Returns:
            bool: True if Redis server is responding, False otherwise
            
        Raises:
            Exception: If Redis ping fails
        """
        try:
            return bool(self.slave.ping())
        except Exception as e:
            logger.warning(f"Slave ping failed, trying master: {e}")
            try:
                return bool(self.master.ping())
            except Exception as e:
                logger.error(f"Redis ping failed: {e}")
                raise Exception(f"Redis ping failed: {str(e)}")

