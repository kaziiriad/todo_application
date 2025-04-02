import base64

def get_redis_master_user_data(redis_password):
    """
    User data script for Redis master instance
    """
    script = """#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server
    
    # Configure Redis for master role
    sudo tee /etc/redis/redis.conf > /dev/null << EOF
    bind 0.0.0.0
    protected-mode no
    port 6379
    daemonize yes
    supervised systemd
    pidfile /var/run/redis/redis-server.pid
    loglevel notice
    logfile /var/log/redis/redis-server.log
    databases 16
    always-show-logo yes
    save 900 1
    save 300 10
    save 60 10000
    stop-writes-on-bgsave-error yes
    rdbcompression yes
    rdbchecksum yes
    dbfilename dump.rdb
    dir /var/lib/redis
    replica-serve-stale-data yes
    replica-read-only yes
    repl-diskless-sync no
    repl-diskless-sync-delay 5
    repl-disable-tcp-nodelay no
    replica-priority 100
    requirepass {redis_password}
    maxmemory 256mb
    maxmemory-policy allkeys-lru
    appendonly yes
    appendfilename "appendonly.aof"
    appendfsync everysec
    EOF
    
    # Start Redis service
    sudo systemctl restart redis-server
    sudo systemctl enable redis-server
    """
    return base64.b64encode(script.encode()).decode()

def get_redis_replica_user_data(master_ip, redis_password):
    """
    User data script for Redis replica instances
    
    Args:
        master_ip: IP address of the Redis master
    """
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server
    
    # Configure Redis for replica role
    sudo tee /etc/redis/redis.conf > /dev/null << EOF
    bind 0.0.0.0
    protected-mode no
    port 6379
    daemonize yes
    supervised systemd
    pidfile /var/run/redis/redis-server.pid
    loglevel notice
    logfile /var/log/redis/redis-server.log
    databases 16
    always-show-logo yes
    save 900 1
    save 300 10
    save 60 10000
    stop-writes-on-bgsave-error yes
    rdbcompression yes
    rdbchecksum yes
    dbfilename dump.rdb
    dir /var/lib/redis
    replicaof {master_ip} 6379
    masterauth {redis_password}
    replica-serve-stale-data yes
    replica-read-only yes
    repl-diskless-sync no
    repl-diskless-sync-delay 5
    repl-disable-tcp-nodelay no
    replica-priority 100
    requirepass {redis_password}
    maxmemory 256mb
    maxmemory-policy allkeys-lru
    appendonly yes
    appendfilename "appendonly.aof"
    appendfsync everysec
    EOF
    
    # Start Redis service
    sudo systemctl restart redis-server
    sudo systemctl enable redis-server
    """
    return base64.b64encode(script.encode()).decode()

def get_redis_sentinel_user_data(master_ip, redis_password):
    """
    User data script for Redis Sentinel instances
    
    Args:
        master_ip: IP address of the Redis master
    """
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server
    
    # Configure Redis Sentinel
    sudo mkdir -p /etc/redis
    sudo tee /etc/redis/sentinel.conf > /dev/null << EOF
    port 26379
    daemonize yes
    pidfile /var/run/redis/redis-sentinel.pid
    logfile /var/log/redis/redis-sentinel.log
    dir /tmp
    
    sentinel monitor mymaster {master_ip} 6379 2
    sentinel down-after-milliseconds mymaster 5000
    sentinel failover-timeout mymaster 60000
    sentinel parallel-syncs mymaster 1
    sentinel auth-pass mymaster {redis_password}
    EOF
    
    # Create systemd service for Sentinel
    sudo tee /etc/systemd/system/redis-sentinel.service > /dev/null << EOF
    [Unit]
    Description=Redis Sentinel
    After=network.target
    
    [Service]
    ExecStart=/usr/bin/redis-server /etc/redis/sentinel.conf --sentinel
    Restart=always
    
    [Install]
    WantedBy=multi-user.target
    EOF
    
    # Start Sentinel service
    sudo systemctl daemon-reload
    sudo systemctl start redis-sentinel
    sudo systemctl enable redis-sentinel
    """
    return base64.b64encode(script.encode()).decode()