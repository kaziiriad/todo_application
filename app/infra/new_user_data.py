import base64

def db_instance_user_data(
   db_user, db_password, db_name, backend_subnet_cidr, replication_password
):
    """
    User data script for minimal instance
    """
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    # sudo apt-get upgrade -y
    
    # Install necessary packages
    sudo apt-get install -y postgresql postgresql-contrib
    
    # Wait for PostgreSQL to initialize
    echo "DB_USER={db_user}" >> /etc/environment
    echo "DB_PASSWORD={db_password}" >> /etc/environment
    echo "DB_NAME={db_name}" >> /etc/environment
    echo "BACKEND_SUBNET_CIDR={backend_subnet_cidr}" >> /etc/environment
    echo "REPLICATION_PASSWORD={replication_password}" >> /etc/environment
    # Load environment variables
    source /etc/environment
    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    """
    
    return base64.b64encode(script.encode()).decode()

def redis_master_instance_user_data(
    redis_password, backend_subnet_cidr
):
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server

    echo "REDIS_PASSWORD={redis_password}" >> /etc/environment
    echo "BACKEND_SUBNET_CIDR={backend_subnet_cidr}" >> /etc/environment
    # Load environment variables
    source /etc/environment
    
    """

    return base64.b64encode(script.encode()).decode()

def redis_replica_instance_user_data(
    master_ip, redis_password, backend_subnet_cidr
):
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server

    echo "MASTER_IP={master_ip}" >> /etc/environment
    echo "REDIS_PASSWORD={redis_password}" >> /etc/environment
    echo "BACKEND_SUBNET_CIDR={backend_subnet_cidr}" >> /etc/environment
    # Load environment variables
    source /etc/environment
    
    """
    return base64.b64encode(script.encode()).decode()

def redis_sentinel_instance_user_data(
    master_ip, redis_password, backend_subnet_cidr
):
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Redis
    sudo apt-get install -y redis-server

    echo "MASTER_IP={master_ip}" >> /etc/environment
    echo "REDIS_PASSWORD={redis_password}" >> /etc/environment
    echo "BACKEND_SUBNET_CIDR={backend_subnet_cidr}" >> /etc/environment
    # Load environment variables
    source /etc/environment
    
    """
    return base64.b64encode(script.encode()).decode()

def backend_instance_user_data(
    docker_username, version, db_user,
    db_password, db_name, db_host, redis_master_host_str, redis_replica_hosts_str, redis_sentinel_hosts_str,
    redis_sentinel_port, redis_service_name, redis_password
):
    """
    User data script for backend instances
    """
    redis_sentinel_hosts_str = ",".join(redis_sentinel_hosts_str)
    redis_replica_hosts_str = ",".join(redis_replica_hosts_str)
    redis_master_host_str = ",".join(redis_master_host_str)
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Docker
    sudo apt-get install -y docker.io docker-compose curl

    echo "DOCKER_USERNAME={docker_username}" >> /etc/environment
    echo "VERSION={version}" >> /etc/environment
    echo "DB_USER={db_user}" >> /etc/environment
    echo "DB_PASSWORD={db_password}" >> /etc/environment
    echo "DB_NAME={db_name}" >> /etc/environment
    echo "DB_HOST={db_host}" >> /etc/environment
    echo "REDIS_MASTER_HOST={redis_master_host_str}" >> /etc/environment
    echo "REDIS_REPLICA_HOSTS={redis_replica_hosts_str}" >> /etc/environment
    echo "REDIS_SENTINEL_HOSTS={redis_sentinel_hosts_str}" >> /etc/environment
    echo "REDIS_SENTINEL_PORT={redis_sentinel_port}" >> /etc/environment
    echo "REDIS_SERVICE_NAME={redis_service_name}" >> /etc/environment
    echo "REDIS_PASSWORD={redis_password or ''}" >> /etc/environment
    echo "CORS_ALLOW_ORIGINS=*" >> /etc/environment
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
    network_mode: "host"
    environment:
      - DB_USER={db_user}
      - DB_PASSWORD={db_password}
      - DB_NAME={db_name}
      - DB_HOST={db_host}
      - REDIS_MASTER_HOST={redis_master_host_str}
      - REDIS_REPLICA_HOSTS={redis_replica_hosts_str}
      - REDIS_SENTINEL_HOSTS={redis_sentinel_hosts_str}
      - REDIS_SENTINEL_PORT={redis_sentinel_port}
      - REDIS_SERVICE_NAME={redis_service_name}
      - REDIS_PASSWORD={redis_password or ''}
      - CORS_ALLOW_ORIGINS=*
    restart: always

EOL
    # Pull the latest backend image
    sudo docker pull {docker_username}/todo-backend:{version}
    
    # Run the container
    cd /home/ubuntu/docker-compose
    sudo docker-compose up -d
    
    # Test backend connectivity
    curl -v localhost:8000/health || echo "Backend connection failed, but continuing..."
    
    # Add a timestamp to force update
    echo "Last updated: $(date)" > /home/ubuntu/last_update.txt
    """
    return base64.b64encode(script.encode()).decode()


def frontend_instance_user_data(
    backend_url, docker_username, version
):
    """
    User data script for frontend instances
    """
    script = f"""#!/bin/bash
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Docker
    sudo apt-get install -y docker.io docker-compose curl

    echo "BACKEND_URL={backend_url}" >> /etc/environment
    echo "DOCKER_USERNAME={docker_username}" >> /etc/environment
    echo "VERSION={version}" >> /etc/environment
    # Load environment variables
    source /etc/environment
    
    # Start Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Create docker-compose directory
    mkdir -p /home/ubuntu/docker-compose

    # Create nginx configuration
    cat > /home/ubuntu/docker-compose/nginx.conf << EOL
    
    # Create docker-compose.yml file for frontend
    cat > /home/ubuntu/docker-compose/docker-compose.yml << EOL
version: '3'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    restart: always
  frontend:
    image: {docker_username}/todo-frontend:{version}
    network_mode: "host"
    environment:
      - VITE_API_URL={backend_url}
      - BACKEND_URL={backend_url}
    restart: always
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

