def db_master_user_data(
    db_name: str,
    db_user: str,
    db_password: str,
    replication_password: str,
) -> str:
    return f"""#!/bin/bash
       # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install PostgreSQL
    sudo apt-get install -y postgresql postgresql-contrib
    
    # Wait for PostgreSQL to initialize
    echo "Waiting for PostgreSQL to initialize..."
    sleep 10
    
    # Make sure PostgreSQL is running
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Wait for PostgreSQL to start
    echo "Waiting for PostgreSQL to start..."
    sleep 5
    
    # Find the actual PostgreSQL configuration files
    echo "Finding PostgreSQL configuration files..."
    PG_VERSION=$(sudo -u postgres psql -c "SHOW server_version;" | head -3 | tail -1 | cut -d. -f1)
    echo "PostgreSQL version: $PG_VERSION"

        # Find the configuration directory
    PG_CONF_PATH=$(sudo find /etc/postgresql -name "postgresql.conf" | head -1)
    PG_HBA_PATH=$(sudo find /etc/postgresql -name "pg_hba.conf" | head -1)
    
    if [ -z "$PG_CONF_PATH" ] || [ -z "$PG_HBA_PATH" ]; then
        echo "ERROR: Could not find PostgreSQL configuration files!"
        echo "Searching for any postgresql.conf files:"
        sudo find / -name postgresql.conf 2>/dev/null
        echo "Searching for any pg_hba.conf files:"
        sudo find / -name pg_hba.conf 2>/dev/null
        exit 1
    fi
    
    echo "Found postgresql.conf at: $PG_CONF_PATH"
    echo "Found pg_hba.conf at: $PG_HBA_PATH"
    

    # Configure PostgreSQL for remote connections and replication
    echo "Configuring PostgreSQL for remote connections and replication..."
    
    # Create a backup of the original postgresql.conf
    sudo cp "$PG_CONF_PATH" "$PG_CONF_PATH.bak"
    
    # Update the postgresql.conf file with replication settings
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$PG_CONF_PATH"
    
    # Add replication settings to the end of postgresql.conf
    sudo tee -a "$PG_CONF_PATH" > /dev/null << EOL
    
# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
EOL
    
    # Update pg_hba.conf to allow replication connections
    sudo tee "$PG_HBA_PATH" > /dev/null << EOL
# PostgreSQL Client Authentication Configuration File
# ===================================================
#
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# Allow connections from anywhere
host    all             all             0.0.0.0/0               md5
# Allow replication connections
host    replication     all             0.0.0.0/0               md5
EOL
    
    # Restart PostgreSQL to apply changes
    echo "Restarting PostgreSQL to apply changes..."
    sudo systemctl restart postgresql
    
    # Wait for PostgreSQL to restart
    echo "Waiting for PostgreSQL to restart..."
    sleep 5
    
    # Create database and user
    echo "Creating database and user..."
    sudo -u postgres psql -c "CREATE USER {db_user} WITH PASSWORD '{db_password}' SUPERUSER;"
    sudo -u postgres psql -c "CREATE DATABASE {db_name};"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"
    
    # Create replication user
    sudo -u postgres psql -c "CREATE USER replicator WITH LOGIN REPLICATION PASSWORD {replication_password};"
    # -- Verify the user was created
    sudo -u postgres psql -c "\'du replicator"
    # -- Verify the user has replication privileges
    sudo systemctl restart postgresql
    sudo systemctl status postgresql


    # Verify PostgreSQL is running and accessible
    echo "Verifying PostgreSQL setup..."
    sudo -u postgres psql -c "\\l"
    
    # Test configuration
    echo "Testing configuration..."
    sudo grep "listen_addresses" "$PG_CONF_PATH"
    sudo grep "wal_level" "$PG_CONF_PATH"
    sudo grep "max_wal_senders" "$PG_CONF_PATH"
    sudo cat "$PG_HBA_PATH"
    
    # Check if PostgreSQL is listening on all interfaces
    sudo netstat -tulpn | grep postgres
    
    echo "PostgreSQL master setup complete!"
    """

def db_replica_user_data(
    master_ip: str,
    replication_password: str,
) -> str:
    return f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install PostgreSQL
    sudo apt-get install -y postgresql postgresql-contrib
    
    # Wait for PostgreSQL to initialize
    echo "Waiting for PostgreSQL to initialize..."
    sleep 10
    
    # Stop PostgreSQL service to configure replica
    sudo systemctl stop postgresql
    
    # Find the actual PostgreSQL configuration files and data directory
    echo "Finding PostgreSQL configuration files..."
    PG_VERSION=$(ls /etc/postgresql/)
    echo "PostgreSQL version: $PG_VERSION"
    
    PG_CONF_PATH="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
    PG_HBA_PATH="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    PG_DATA_DIR="/var/lib/postgresql/$PG_VERSION/main"
    
    if [ ! -f "$PG_CONF_PATH" ] || [ ! -f "$PG_HBA_PATH" ] || [ ! -d "$PG_DATA_DIR" ]; then
        echo "ERROR: Could not find PostgreSQL configuration files or data directory!"
        echo "Searching for any postgresql.conf files:"
        sudo find / -name postgresql.conf 2>/dev/null
        echo "Searching for any pg_hba.conf files:"
        sudo find / -name pg_hba.conf 2>/dev/null
        echo "Searching for PostgreSQL data directories:"
        sudo find /var/lib/postgresql -type d -name "main" 2>/dev/null
        exit 1
    fi
    
    echo "Found postgresql.conf at: $PG_CONF_PATH"
    echo "Found pg_hba.conf at: $PG_HBA_PATH"
    echo "Found data directory at: $PG_DATA_DIR"
    
    # Backup the original data directory
    sudo -u postgres mkdir -p /var/lib/postgresql/backup
    sudo -u postgres cp -R $PG_DATA_DIR/* /var/lib/postgresql/backup/
    
    # Clear the data directory for replica setup
    sudo -u postgres rm -rf $PG_DATA_DIR/*
    
    # Create a backup of the original configuration files
    sudo cp "$PG_CONF_PATH" "$PG_CONF_PATH.bak"
    sudo cp "$PG_HBA_PATH" "$PG_HBA_PATH.bak"
    
    # Configure pg_hba.conf for replication
    sudo tee "$PG_HBA_PATH" > /dev/null << EOL
# PostgreSQL Client Authentication Configuration File
# ===================================================
#
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# Allow connections from the master server
host    all             all             {master_ip}/32          md5
# Allow replication connections
host    replication     replicator      {master_ip}/32          md5
EOL
    
    # Configure postgresql.conf for replica
    sudo tee "$PG_CONF_PATH" > /dev/null << EOL
# PostgreSQL configuration file
listen_addresses = '*'
port = 5432
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'

# Replication settings
hot_standby = on
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby_feedback = on
EOL
    
    # Create recovery.conf (or standby.signal for PostgreSQL 12+)
    PG_MAJOR_VERSION=$(echo $PG_VERSION | cut -d. -f1)
    
    if [ "$PG_MAJOR_VERSION" -ge "12" ]; then
        # PostgreSQL 12 and later use standby.signal and postgresql.auto.conf
        sudo -u postgres touch "$PG_DATA_DIR/standby.signal"
        
        sudo -u postgres tee "$PG_DATA_DIR/postgresql.auto.conf" > /dev/null << EOL
# PostgreSQL standby configuration
primary_conninfo = 'host={master_ip} port=5432 user=replicator password={replication_password} application_name=replica1'
restore_command = 'cp /var/lib/postgresql/$PG_VERSION/archive/%f %p'
EOL
    else
        # PostgreSQL 11 and earlier use recovery.conf
        sudo -u postgres tee "$PG_DATA_DIR/recovery.conf" > /dev/null << EOL
# PostgreSQL recovery configuration
standby_mode = 'on'
primary_conninfo = 'host={master_ip} port=5432 user=replicator password={replication_password} application_name=replica1'
restore_command = 'cp /var/lib/postgresql/$PG_VERSION/archive/%f %p'
trigger_file = '/tmp/postgresql.trigger'
EOL
    fi
    
    # Create archive directory
    sudo -u postgres mkdir -p /var/lib/postgresql/$PG_VERSION/archive
    sudo chmod 700 /var/lib/postgresql/$PG_VERSION/archive
    
    # Perform initial base backup from master
    echo "Performing initial base backup from master..."
    sudo -u postgres PGPASSWORD=f{replication_password} pg_basebackup -h {master_ip} -p 5432 -U replicator -D $PG_DATA_DIR -Fp -Xs -P -R
    
    # Set proper permissions on data directory
    sudo chown -R postgres:postgres $PG_DATA_DIR
    sudo chmod 700 $PG_DATA_DIR
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Wait for PostgreSQL to start
    echo "Waiting for PostgreSQL to start..."
    sleep 10
    
    # Check replication status
    echo "Checking replication status..."
    sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
    
    # Verify PostgreSQL is running and accessible
    echo "Verifying PostgreSQL setup..."
    sudo -u postgres psql -c "SELECT current_timestamp;"
    
    # Check if PostgreSQL is listening on all interfaces
    sudo netstat -tulpn | grep postgres
    
    echo "PostgreSQL replica setup complete!"
    """

