import base64

def get_backend_user_data(db_host, db_user, db_password, db_name, redis_host):
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
    """
    return base64.b64encode(script.encode()).decode()

def get_frontend_user_data(backend_url):
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
    """
    return base64.b64encode(script.encode()).decode()


def get_db_user_data(db_user, db_password, db_name):
    script = f"""#!/bin/bash
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install PostgreSQL
    apt-get install -y postgresql postgresql-contrib
    
    # PostgreSQL is automatically initialized on Ubuntu
    
    # Configure PostgreSQL for remote connections
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf
    echo "host    all             all             0.0.0.0/0               md5" >> /etc/postgresql/*/main/pg_hba.conf
    
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

