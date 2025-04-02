import base64


def get_backend_user_data(
    db_host,
    db_user,
    db_password,
    db_name,
    redis_sentinel_hosts,
    redis_sentinel_port,
    redis_password,
    redis_service_name,
    docker_username="kaziiriad",
    version="dev_deploy",
):
    redis_sentinel_hosts_str = ",".join(redis_sentinel_hosts)
    
    script = f"""#!/bin/bash
    # Update package lists
    sudo apt-get update
    
    # Install Docker and other tools
    sudo apt-get install -y docker.io docker-compose netcat
    
    # Set environment variables
    echo "export DB_NAME={db_name}" | sudo tee -a /etc/environment
    echo "export DB_USER={db_user}" | sudo tee -a /etc/environment
    echo "export DB_PASSWORD={db_password}" | sudo tee -a /etc/environment
    echo "export DB_HOST={db_host}" | sudo tee -a /etc/environment
    echo "export REDIS_SENTINEL_HOSTS={redis_sentinel_hosts_str}" | sudo tee -a /etc/environment
    echo "export REDIS_SENTINEL_PORT={redis_sentinel_port}" | sudo tee -a /etc/environment
    echo "export REDIS_SERVICE_NAME={redis_service_name}" | sudo tee -a /etc/environment
    echo "export REDIS_PASSWORD={redis_password or ''}" | sudo tee -a /etc/environment
    echo "export CORS_ALLOW_ORIGINS=*" | sudo tee -a /etc/environment
    
    # Load environment variables
    source /etc/environment
    
    # Start Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Create docker-compose directory
    mkdir -p /home/ubuntu/docker-compose
    
    # Create docker-compose.yml file for backend
    cat > /home/ubuntu/docker-compose/docker-compose.yml << EOL
version: '3'
services:
  backend:
    image: {docker_username}/todo-backend:{version}
    ports:
      - "8000:8000"
    environment:
      - DB_NAME={db_name}
      - DB_USER={db_user}
      - DB_PASSWORD={db_password}
      - DB_HOST={db_host}
      - REDIS_SENTINEL_HOSTS={redis_sentinel_hosts_str}
      - REDIS_SENTINEL_PORT={redis_sentinel_port}
      - REDIS_SERVICE_NAME={redis_service_name}
      - REDIS_PASSWORD={redis_password or ''}
      - CORS_ALLOW_ORIGINS=*
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << EOL
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
REDIS_SENTINEL_HOSTS={redis_sentinel_hosts_str}
REDIS_SENTINEL_PORT={redis_sentinel_port}
REDIS_SERVICE_NAME={redis_service_name}
REDIS_PASSWORD={redis_password or ''}
CORS_ALLOW_ORIGINS=*
EOL
    
    # Pull the latest backend image
    sudo docker pull {docker_username}/todo-backend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    sudo docker-compose up -d
    
    # Add a timestamp to force update
    echo "Last updated: $(date)" > /home/ubuntu/last_update.txt
    
    # Print environment for debugging
    echo "Environment variables:"
    env | grep -E 'DB_|REDIS_|CORS_'
    
    # Print docker-compose config for debugging
    echo "Docker Compose configuration:"
    cat /home/ubuntu/docker-compose/docker-compose.yml
    cat /home/ubuntu/docker-compose/.env
    
    # Check if the container is running
    sudo docker ps
    
    # Check container logs
    sleep 5
    sudo docker logs $(sudo docker ps -q --filter "name=docker-compose_backend")
    """
    return base64.b64encode(script.encode()).decode()


def get_frontend_user_data(
    backend_url, docker_username="kaziiriad", version="dev_deploy"
):
    # Ensure backend_url starts with http://
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = f"http://{backend_url}"
    
    script = f"""#!/bin/bash
    # Update package lists
    sudo apt-get update
    
    # Install Docker
    sudo apt-get install -y docker.io docker-compose curl
    
    # Set environment variables
    echo "export BACKEND_URL={backend_url}" | sudo tee -a /etc/environment
    echo "export VITE_API_URL={backend_url}" | sudo tee -a /etc/environment
    
    # Load environment variables
    source /etc/environment
    
    # Start Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Create docker-compose directory
    mkdir -p /home/ubuntu/docker-compose
    
    # Create docker-compose.yml file for frontend
    cat > /home/ubuntu/docker-compose/docker-compose.yml << EOL
version: '3'
services:
  frontend:
    image: {docker_username}/todo-frontend:{version}
    network_mode: "host"
    environment:
      - BACKEND_URL={backend_url}
      - VITE_API_URL={backend_url}
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << EOL
BACKEND_URL={backend_url}
VITE_API_URL={backend_url}
EOL
    
    # Pull the latest frontend image
    sudo docker pull {docker_username}/todo-frontend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    sudo docker-compose up -d
    
    # Test backend connectivity
    echo "Testing backend connectivity to {backend_url}..."
    curl -v {backend_url} || echo "Backend connection failed, but continuing..."
    
    # Add a timestamp to force update
    echo "Last updated: $(date)" > /home/ubuntu/last_update.txt
    """
    return base64.b64encode(script.encode()).decode()

def get_db_user_data(db_user, db_password, db_name, backend_subnet_cidr):
    script = f"""#!/bin/bash
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
    
    # Configure PostgreSQL for remote connections
    echo "Configuring PostgreSQL for remote connections..."
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$PG_CONF_PATH"
    
    # Create a backup of the original pg_hba.conf
    sudo cp "$PG_HBA_PATH" "$PG_HBA_PATH.bak"
    
    # Create a new pg_hba.conf file
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
# Allow connections from the backend subnet
host    all             all             {backend_subnet_cidr}   md5
EOL
    
    # Restart PostgreSQL to apply changes
    echo "Restarting PostgreSQL to apply changes..."
    sudo systemctl restart postgresql
    
    # Wait for PostgreSQL to restart
    echo "Waiting for PostgreSQL to restart..."
    sleep 5
    
    # Create database and user
    echo "Creating database and user..."
    sudo -u postgres psql -c "CREATE USER {db_user} WITH PASSWORD '{db_password}';"
    sudo -u postgres psql -c "CREATE DATABASE {db_name};"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"
    
    # Verify PostgreSQL is running and accessible
    echo "Verifying PostgreSQL setup..."
    sudo -u postgres psql -c "\\l"
    
    # Test remote connectivity
    echo "Testing configuration..."
    sudo grep "listen_addresses" "$PG_CONF_PATH"
    sudo cat "$PG_HBA_PATH"
    
    # Check if PostgreSQL is listening on all interfaces
    sudo netstat -tulpn | grep postgres
    
    echo "PostgreSQL setup complete!"
    """
    return base64.b64encode(script.encode()).decode()

def get_redis_user_data():
    script = """#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server
    
    # Configure Redis for remote connections
    sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
    
    # Disable protected mode for remote connections
    sudo sed -i 's/protected-mode yes/protected-mode no/g' /etc/redis/redis.conf
    
    # Start Redis service
    sudo systemctl restart redis-server
    sudo systemctl enable redis-server
    """
    return base64.b64encode(script.encode()).decode()
