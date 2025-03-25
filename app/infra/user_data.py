import base64


def get_backend_user_data(
    db_host,
    db_user,
    db_password,
    db_name,
    redis_host,
    docker_username="kaziiriad",
    version="dev_deploy",
):
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
    echo "export REDIS_HOST={redis_host}" | sudo tee -a /etc/environment
    
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
      - REDIS_HOST={redis_host}
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << EOL
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
REDIS_HOST={redis_host}
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
    env | grep -E 'DB_|REDIS_'
    
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
    script = f"""#!/bin/bash
    # Update package lists
    sudo apt-get update
    
    # Install Docker
    sudo apt-get install -y docker.io docker-compose
    
    # Set environment variables
    echo "export BACKEND_URL={backend_url}" | sudo tee -a /etc/environment
    
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
    ports:
      - "80:80"
    environment:
      - BACKEND_URL={backend_url}
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << EOL
BACKEND_URL={backend_url}
EOL
    
    # Pull the latest frontend image
    sudo docker pull {docker_username}/todo-frontend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    sudo docker-compose up -d
    
    # Add a timestamp to force update
    echo "Last updated: $(date)" > /home/ubuntu/last_update.txt
    """
    return base64.b64encode(script.encode()).decode()


def get_db_user_data(db_user, db_password, db_name, backend_subnet_cidr="10.0.2.0/24"):
    # Ensure backend_subnet_cidr is a string
    
    
    script = f"""#!/bin/bash
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install PostgreSQL
    apt-get install -y postgresql postgresql-contrib
    
    # Wait for PostgreSQL to initialize
    echo "Waiting for PostgreSQL to initialize..."
    sleep 10
    
    # Make sure PostgreSQL is running
    systemctl start postgresql
    systemctl enable postgresql
    
    # Wait for PostgreSQL to start
    echo "Waiting for PostgreSQL to start..."
    sleep 5
    
    # Detect PostgreSQL version and set the config path
    PG_VERSION=$(psql --version | awk '{{print $3}}' | cut -d. -f1)
    PG_CONF_DIR=$(find /etc/postgresql -name "postgresql.conf" | head -n 1 | xargs dirname)
    
    if [ -z "$PG_CONF_DIR" ]; then
        echo "Could not find PostgreSQL config directory, using default pattern"
        PG_CONF_DIR="/etc/postgresql/$PG_VERSION/main"
    fi
    
    echo "Using PostgreSQL config directory: $PG_CONF_DIR"
    
    # Configure PostgreSQL for remote connections - safer approach
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$PG_CONF_DIR/postgresql.conf"
    
    # Create a new pg_hba.conf file instead of modifying the existing one
    sudo tee "$PG_CONF_DIR/pg_hba.conf" > /dev/null << EOL
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
host    all             all             {backend_subnet_cidr}  md5
# Allow all connections (for testing - remove in production)
host    all             all             0.0.0.0/0               md5
EOL
    
    # Restart PostgreSQL to apply changes
    systemctl restart postgresql
    
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
    
    echo "PostgreSQL setup complete!"
    """
    return base64.b64encode(script.encode()).decode()

def get_redis_user_data():
    script = """#!/bin/bash
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install Redis
    apt-get install -y redis-server
    
    # Configure Redis for remote connections
    sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
    
    # Disable protected mode for remote connections
    sed -i 's/protected-mode yes/protected-mode no/g' /etc/redis/redis.conf
    
    # Start Redis service
    systemctl restart redis-server
    systemctl enable redis-server
    """
    return base64.b64encode(script.encode()).decode()
