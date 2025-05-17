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
        # Get configuration from environment variables with fallbacks
        if sentinel_hosts is None:
            # Use environment variable or default to redis-sentinel service name
            sentinel_host = os.environ.get('REDIS_HOST', 'redis-sentinel')
            sentinel_hosts = [sentinel_host]
        
        sentinel_port = int(os.environ.get('REDIS_PORT', sentinel_port))
        service_name = os.environ.get('REDIS_SENTINEL_MASTER', service_name)
        password = os.environ.get('REDIS_PASSWORD', password)
        
        logger.info(f"Initializing Redis Sentinel connection to {sentinel_hosts} for master {service_name}")
        
        # Add retry logic for initial connection
        max_retries = 5
        retry_delay = 3  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
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
                    password=password,
                    decode_responses=True,
                    retry_on_timeout=retry_on_timeout
                )
                
                self.slave = sentinel.slave_for(
                    service_name, 
                    socket_timeout=socket_timeout,
                    password=password,
                    decode_responses=True,
                    retry_on_timeout=retry_on_timeout
                )
                
                # Test connection
                self.ping()
                logger.info(f"Successfully connected to Redis via Sentinel on attempt {attempt}")
                break
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Redis connection attempt {attempt} failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis via Sentinel after {max_retries} attempts: {e}")
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
            # Convert value to JSON string
            json_value = json.dumps(value)
            self.master.set(key, json_value, ex=expire)
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
            # Try to get from slave first
            value = self.slave.get(key)
            
            # If value exists, parse JSON
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # If not valid JSON, return as is
                    return value
            return None
            
        except Exception as e:
            logger.warning(f"Slave read failed for key {key}, falling back to master: {e}")
            
            # Fallback to master if slave read fails
            try:
                value = self.master.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        # If not valid JSON, return as is
                        return value
                return None
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
    Manages database connections with master-replica setup via pgpool.
    Provides connection pooling and automatic failover.
    """
    
    def __init__(self):
        """
        Initialize database connection pools for master and replicas.
        Configuration is read from environment variables.
        """
        # Get database configuration from environment variables
        self.db_host = os.environ.get('DB_HOST', 'pgpool').strip()
        if not self.db_host:
            raise ValueError("DB_HOST environment variable is not set.")
        self.db_user = os.environ.get('DB_USER', 'myuser')
        self.db_password = os.environ.get('DB_PASSWORD', 'mypassword')
        self.db_name = os.environ.get('DB_NAME', 'mydb')
        self.db_port = int(os.environ.get('DB_PORT', '5432'))
        
        # Optional replica configuration
        self.replica_hosts = [host.strip() for host in os.environ.get('DB_REPLICA_HOSTS', '').split(',') if host.strip()]
        
        # Connection pool settings
        self.min_conn = int(os.environ.get('DB_MIN_CONNECTIONS', '1'))
        self.max_conn = int(os.environ.get('DB_MAX_CONNECTIONS', '10'))
        
        # Retry settings
        self.max_retries = int(os.environ.get('DB_CONNECT_RETRIES', '30'))
        self.retry_delay = int(os.environ.get('DB_CONNECT_RETRY_DELAY', '5'))
        
        # Initial startup delay to allow database services to initialize
        self._apply_startup_delay()
        
        # Initialize connection pools with retry logic
        self._initialize_connection_pools()
        
    def _apply_startup_delay(self):
        """
        Apply an initial delay to allow database services to fully initialize.
        This helps prevent connection issues during container orchestration startup.
        """
        startup_delay = int(os.environ.get('DB_STARTUP_DELAY', '10'))
        if startup_delay > 0:
            logger.info(f"Applying initial startup delay of {startup_delay} seconds to allow database services to initialize...")
            time.sleep(startup_delay)
    
    def _wait_for_service(self, host: str, port: int, timeout: int = 30) -> bool:
        """
        Wait for a TCP service to become available.
        
        Args:
            host: Service hostname
            port: Service port
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if service is available, False otherwise
        """
        logger.info(f"Waiting for service at {host}:{port} to become available (timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=2):
                    logger.info(f"Service at {host}:{port} is available")
                    return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                time.sleep(1)
        
        logger.warning(f"Service at {host}:{port} did not become available within {timeout} seconds")
        return False
        
    def _initialize_connection_pools(self):
        """
        Initialize connection pools with retry logic.
        Attempts to connect to the database with exponential backoff.
        """
        logger.info(f"Initializing database connection pools with {self.max_retries} retries")
        
        # First, wait for the pgpool service to be available at TCP level
        self._wait_for_service(self.db_host, self.db_port, timeout=60)
        
        # Initialize master pool with retries
        retry_count = 0
        last_error = None
        self.master_pool = None
        
        while retry_count < self.max_retries and self.master_pool is None:
            try:
                logger.info(f"Attempting to connect to database at {self.db_host} (attempt {retry_count + 1}/{self.max_retries})")
                
                # Try with different application_name values to help pgpool identify the connection
                try:
                    self.master_pool = self._create_connection_pool(
                        self.db_host, 
                        application_name="backend_master"
                    )
                except Exception as e:
                    logger.warning(f"Failed first connection attempt with application_name: {e}")
                    # Try without application_name as fallback
                    self.master_pool = self._create_connection_pool(self.db_host)
                
                # Test the connection with a simple query
                with self.master_pool.getconn() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    self.master_pool.putconn(conn)
                
                logger.info(f"Successfully connected to database at {self.db_host}")
                break
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count < self.max_retries:
                    # Use exponential backoff with a cap
                    delay = min(self.retry_delay * (2 ** (retry_count - 1)), 60)
                    logger.warning(f"Failed to connect to database: {e}. Retrying in {delay} seconds... (attempt {retry_count}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to connect to database after {self.max_retries} attempts: {e}")
        
        if self.master_pool is None:
            raise Exception(f"Failed to connect to database after {self.max_retries} attempts: {last_error}")
        
        # For pgpool setup, we don't need separate replica pools as pgpool handles that
        self.replica_pools = {}
        
        logger.info(f"Database manager initialized with connection to pgpool at {self.db_host}")
    
    def _create_connection_pool(self, host: str, **extra_params) -> ThreadedConnectionPool:
        """
        Create a connection pool for a specific database host.
        
        Args:
            host: Database host address
            **extra_params: Additional connection parameters
            
        Returns:
            ThreadedConnectionPool: Connection pool for the specified host
        """
        try:
            # Connection parameters optimized for pgpool
            conn_params = {
                "minconn": self.min_conn,
                "maxconn": self.max_conn,
                "host": host,
                "port": self.db_port,
                "user": self.db_user,
                "password": self.db_password,
                "database": self.db_name,
                "cursor_factory": RealDictCursor,
                "connect_timeout": 10,  # 10 seconds timeout for connection attempts
                "options": "-c statement_timeout=30000",  # 30 second statement timeout
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
            
            # Add any extra parameters
            conn_params.update(extra_params)
            
            # Create the connection pool
            pool = ThreadedConnectionPool(**conn_params)
            logger.info(f"Created connection pool for {host}")
            return pool
        except Exception as e:
            logger.error(f"Failed to create connection pool for {host}: {e}")
            raise
    
    @contextmanager
    def get_connection(self, read_only: bool = False) -> Iterator[Tuple[Any, bool]]:
        """
        Get a database connection from the pool.
        With pgpool, all connections go through the same pool, but we can set
        session variables to indicate read-only intent.
        
        Args:
            read_only: Whether the connection will be used for read-only operations
            
        Yields:
            Tuple[connection, is_master]: Database connection and whether it's from the master
        """
        conn = None
        is_master = True
        
        try:
            # Get connection from the pool
            conn = self.master_pool.getconn()
            
            # For read-only operations, set the session to use replicas via pgpool
            if read_only:
                with conn.cursor() as cursor:
                    # This tells pgpool to use a replica if available
                    cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
                    # Additional pgpool-specific setting if needed
                    # cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;")
                is_master = False
            
            yield (conn, is_master)
            
        except Exception as e:
            logger.error(f"Error while using database connection: {e}")
            raise
            
        finally:
            if conn is not None:
                try:
                    # Reset any session variables before returning to pool
                    if read_only:
                        with conn.cursor() as cursor:
                            cursor.execute("RESET SESSION CHARACTERISTICS;")
                    self.master_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
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
                    # For read-only connections, we don't commit changes
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
        Check the health of database connections.
        
        Returns:
            Dictionary with host as key and health status as value
        """
        health = {self.db_host: False}
        
        # Check connection through pgpool
        try:
            with self.get_connection(read_only=False) as (conn, _):
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    health[self.db_host] = True
                    
                    # Try to get pgpool status if possible
                    try:
                        cursor.execute("SHOW pool_nodes")
                        nodes = cursor.fetchall()
                        for node in nodes:
                            logger.info(f"PgPool node status: {node}")
                    except Exception as e:
                        logger.warning(f"Could not query pgpool status: {e}")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            
        return health

# Singleton instance
db_manager = DatabaseManager()
