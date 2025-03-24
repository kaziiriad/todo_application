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
    apt-get update
    
    # Install Docker and other tools
    apt-get install -y docker.io docker-compose netcat
    
    # Set environment variables
    echo "export DB_NAME={db_name}" >> /etc/environment
    echo "export DB_USER={db_user}" >> /etc/environment
    echo "export DB_PASSWORD={db_password}" >> /etc/environment
    echo "export DB_HOST={db_host}" >> /etc/environment
    echo "export REDIS_HOST={redis_host}" >> /etc/environment
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    # Create docker-compose directory
    mkdir -p /home/ubuntu/docker-compose
    
    # Create docker-compose.yml file for backend
    cat > /home/ubuntu/docker-compose/docker-compose.yml << 'EOL'
version: '3'
services:
  backend:
    image: {docker_username}/todo-backend:{version}
    ports:
      - "8000:8000"
    environment:
      - DB_NAME=${{DB_NAME}}
      - DB_USER=${{DB_USER}}
      - DB_PASSWORD=${{DB_PASSWORD}}
      - DB_HOST=${{DB_HOST}}
      - REDIS_HOST=${{REDIS_HOST}}
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << 'EOL'
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
REDIS_HOST={redis_host}
EOL
    
    # Pull the latest backend image
    docker pull {docker_username}/todo-backend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    docker-compose up -d
    """
    return base64.b64encode(script.encode()).decode()


def get_frontend_user_data(
    backend_url, docker_username="kaziiriad", version="dev_deploy"
):
    script = f"""#!/bin/bash
    # Update package lists
    apt-get update
    
    # Install Docker
    apt-get install -y docker.io docker-compose
    
    # Set environment variables
    echo "export BACKEND_URL={backend_url}" >> /etc/environment
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    # Create docker-compose directory
    mkdir -p /home/ubuntu/docker-compose
    
    # Create docker-compose.yml file for frontend
    cat > /home/ubuntu/docker-compose/docker-compose.yml << 'EOL'
version: '3'
services:
  frontend:
    image: {docker_username}/todo-frontend:{version}
    ports:
      - "80:80"
    environment:
      - BACKEND_URL=${{BACKEND_URL}}
    restart: always
EOL
    
    # Create .env file with environment variables
    cat > /home/ubuntu/docker-compose/.env << 'EOL'
BACKEND_URL={backend_url}
EOL
    
    # Pull the latest frontend image
    docker pull {docker_username}/todo-frontend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    docker-compose up -d
    """
    return base64.b64encode(script.encode()).decode()


def get_db_user_data(
    db_user, db_password, db_name, backend_subnet_cidr="10.0.2.0/24"
):
    script = f"""#!/bin/bash
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install PostgreSQL
    apt-get install -y postgresql postgresql-contrib
    
    # PostgreSQL is automatically initialized on Ubuntu
    
    # Configure PostgreSQL for remote connections
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf
    
    # Remove default remote connection settings if they exist
    sed -i '/^host.*all.*all.*0.0.0.0\\/0/d' /etc/postgresql/*/main/pg_hba.conf
    
    # Add connection rule for backend subnet only
    echo "host    all             all             {backend_subnet_cidr}               md5" >> /etc/postgresql/*/main/pg_hba.conf
    
    # Restart PostgreSQL to apply changes
    systemctl restart postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE USER {db_user} WITH PASSWORD '{db_password}';"
    sudo -u postgres psql -c "CREATE DATABASE {db_name};"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"
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
