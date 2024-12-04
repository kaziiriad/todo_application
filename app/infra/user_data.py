import base64

def get_frontend_user_data(alb_dns):
    script = f"""#!/bin/bash
# Install Docker
apt-get update
apt-get install -y docker.io docker-compose

# Start Docker
systemctl start docker
systemctl enable docker

# Create app directory
mkdir -p /app

# Create docker-compose.yml
cat > /app/docker-compose.yml << 'EOL'
version: '3'
services:
  frontend:
    image: kaziiriad/todo-frontend:deploy
    ports:
      - "80:80"
    environment:
      - BACKEND_URL=http://{alb_dns}
    restart: always
EOL

# Start container
cd /app
docker-compose up -d
"""
    return base64.b64encode(script.encode()).decode()

def get_backend_user_data(db_host, db_user, db_password, db_name):
    script = f"""#!/bin/bash
# Install Docker
apt-get update
apt-get install -y docker.io docker-compose

# Start Docker
systemctl start docker
systemctl enable docker

# Create app directory
mkdir -p /app

# Create docker-compose.yml
cat > /app/docker-compose.yml << 'EOL'
version: '3'
services:
  backend:
    image: kaziiriad/todo-backend:deploy
    ports:
      - "8000:8000"
    environment:
      - DB_HOST={db_host}
      - DB_USER={db_user}
      - DB_PASSWORD={db_password}
      - DB_NAME={db_name}
    restart: always
EOL

# Start container
cd /app
docker-compose up -d
"""
    return base64.b64encode(script.encode()).decode()

def get_database_user_data(db_user, db_password, db_name):
    script = f"""#!/bin/bash
    # Install Docker
    apt-get update
    apt-get install -y docker.io docker-compose

    # Start Docker
    systemctl start docker
    systemctl enable docker

    # Create app directory
    mkdir -p /app

    # Create docker-compose.yml
    cat > /app/docker-compose.yml << 'EOL'
    version: '3'
    services:
      database:
        image: postgres
        ports:
          - "5432:5432"
        environment:
          - MYSQL_ROOT_PASSWORD={db_password}
          - MYSQL_DATABASE={db_name}
          - MYSQL_USER={db_user}
          - MYSQL_PASSWORD={db_password}
        restart: always
    EOL

    # Start container
    cd /app
    docker-compose up -d
    """
    return base64.b64encode(script.encode()).decode()