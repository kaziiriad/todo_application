from typing import Dict, Any, List, Optional, Union
from redis import Redis
from redis.sentinel import Sentinel
import json
from datetime import datetime
import logging
import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Iterator
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


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

class DatabaseManager:
    """
    Manages database connections with master-replica setup.
    Provides connection pooling and automatic failover.
    """
    
    def __init__(self):
        """
        Initialize database connection pools for master and replicas.
        Configuration is read from environment variables.
        """
        # Get database configuration from environment variables
        self.db_host = os.environ.get('DB_HOST', '').strip()
        if not self.db_host:
            raise ValueError("DB_HOST environment variable is not set.")
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_name = os.environ.get('DB_NAME')
        
        # Optional replica configuration
        self.replica_hosts = [host.strip() for host in os.environ.get('DB_REPLICA_HOSTS', '').split(',') if host.strip()]
        
        # Connection pool settings
        self.min_conn = int(os.environ.get('DB_MIN_CONNECTIONS', '1'))
        self.max_conn = int(os.environ.get('DB_MAX_CONNECTIONS', '10'))
        
        # Initialize connection pools
        if not self.db_host:
            raise ValueError("DB_HOST environment variable is not set.")
        self.master_pool = self._create_connection_pool(self.db_host)
        
        # Create replica pools if replica hosts are provided
        self.replica_pools = {}
        for host in self.replica_hosts:
            if host and host.strip():
                self.replica_pools[host] = self._create_connection_pool(host.strip())
        
        logger.info(f"Database manager initialized with master: {self.db_host} and replicas: {self.replica_hosts}")
    
    def _create_connection_pool(self, host: str) -> ThreadedConnectionPool:
        """
        Create a connection pool for a specific database host.
        
        Args:
            host: Database host address
            
        Returns:
            ThreadedConnectionPool: Connection pool for the specified host
        """
        try:
            pool = ThreadedConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                host=host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Created connection pool for {host}")
            return pool
        except Exception as e:
            logger.error(f"Failed to create connection pool for {host}: {e}")
            raise
    
    @contextmanager
    def get_connection(self, read_only: bool = False) -> Iterator[Tuple[Any, bool]]:
        """
        Get a database connection from the appropriate pool.
        For read-only operations, tries to get a connection from a replica pool first.
        Falls back to master if no replicas are available or if they fail.
        
        Args:
            read_only: Whether the connection will be used for read-only operations
            
        Yields:
            Tuple[connection, is_master]: Database connection and whether it's from the master
        """
        conn = None
        is_master = True
        
        try:
            # For read-only operations, try to get a connection from a replica pool first
            if read_only and self.replica_pools:
                for host, pool in self.replica_pools.items():
                    try:
                        conn = pool.getconn()
                        is_master = False
                        break
                    except Exception as e:
                        logger.warning(f"Failed to get connection from replica {host}: {e}")
            
            # If no replica connection was obtained or if write access is needed, use master
            if conn is None:
                conn = self.master_pool.getconn()
                is_master = True
            
            yield (conn, is_master)
            
        except Exception as e:
            logger.error(f"Error while using database connection: {e}")
            raise
            
        finally:
            if conn is not None:
                if is_master:
                    self.master_pool.putconn(conn)
                else:
                    for pool in self.replica_pools.values():
                        try:
                            pool.putconn(conn)
                            break
                        except Exception:
                            # This connection doesn't belong to this pool, try the next one
                            pass
    
    @contextmanager
    def get_cursor(self, read_only: bool = False):
        """
        Get a database cursor from the appropriate connection.
        
        Args:
            read_only: Whether the cursor will be used for read-only operations
            
        Yields:
            Tuple[cursor, is_master]: Database cursor and whether it's from the master
        """
        with self.get_connection(read_only) as (conn, is_master):
            cursor = conn.cursor()
            try:
                yield cursor, is_master
                if not is_master:
                    # For replica connections, we don't commit changes
                    pass
                else:
                    # For master connections, commit the transaction
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error, transaction rolled back: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, read_only: bool = False) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            read_only: Whether this is a read-only query
            
        Returns:
            List of dictionaries representing the query results
        """
        with self.get_cursor(read_only) as (cursor, _):
            cursor.execute(query, params or {})
            if cursor.description:  # If the query returns rows
                return cursor.fetchall()
            return []
    
    def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute a write operation (INSERT, UPDATE, DELETE) and return the number of affected rows.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_cursor(read_only=False) as (cursor, _):
            cursor.execute(query, params or {})
            return cursor.rowcount
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check the health of all database connections.
        
        Returns:
            Dictionary with host as key and health status as value
        """
        health = {self.db_host: False}
        
        # Check master
        try:
            with self.get_connection(read_only=False) as (conn, _):
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    health[self.db_host] = True
        except Exception as e:
            logger.error(f"Master database health check failed: {e}")
        
        # Check replicas
        for host in self.replica_hosts:
            health[host] = False
            if host in self.replica_pools:
                try:
                    pool = self.replica_pools[host]
                    conn = pool.getconn()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT 1")
                            health[host] = True
                    finally:
                        pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Replica {host} health check failed: {e}")
            
        return {key: value for key, value in health.items() if key is not None}
        

# Singleton instance
db_manager = DatabaseManager()