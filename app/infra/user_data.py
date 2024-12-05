import base64

def get_backend_user_data(db_host, db_user, db_password, db_name):
    script = f"""#!/bin/bash
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose nc

    # Start Docker
    systemctl start docker
    systemctl enable docker

    # Create app directory
    mkdir -p /app

    # Wait for database to be available
    until nc -z {db_host} 5432; do
        echo "Waiting for database..."
        sleep 5
    done

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
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
          interval: 30s
          timeout: 10s
          retries: 3
          start_period: 40s
        restart: always
    EOL

    # Start container
    cd /app
    docker-compose up -d
    """
    return base64.b64encode(script.encode()).decode()

def get_frontend_user_data(nginx_alb_dns):
    script = f"""#!/bin/bash
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose

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
          - BACKEND_URL=http://{nginx_alb_dns}:80  # Point to Nginx ALB
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
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose

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

def get_nginx_alb_user_data(region):
    nginx_conf = """
user www-data;
worker_processes auto;
events {
    worker_connections 1024;
}
http {
    upstream frontend_servers {
        least_conn;
    }
    upstream backend_servers {
        least_conn;
    }
    server {
        listen 80;
        location / {
            proxy_pass http://frontend_servers;
            proxy_set_header Host $host;
        }
        location /tasks {
            proxy_pass http://backend_servers;
            proxy_set_header Host $host;
        }
    }
}
"""

    update_script = """#!/bin/bash
frontend_instances=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name frontend-asg --query 'AutoScalingGroups[0].Instances[*].InstanceId' --output text)
backend_instances=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name backend-asg --query 'AutoScalingGroups[0].Instances[*].InstanceId' --output text)

# Generate upstream configs
echo "upstream frontend_servers {" > /etc/nginx/conf.d/upstreams.conf
for id in $frontend_instances; do
    ip=$(aws ec2 describe-instances --instance-ids $id --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
    echo "    server $ip:80;" >> /etc/nginx/conf.d/upstreams.conf
done
echo "}" >> /etc/nginx/conf.d/upstreams.conf

echo "upstream backend_servers {" >> /etc/nginx/conf.d/upstreams.conf
for id in $backend_instances; do
    ip=$(aws ec2 describe-instances --instance-ids $id --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
    echo "    server $ip:8000;" >> /etc/nginx/conf.d/upstreams.conf
done
echo "}" >> /etc/nginx/conf.d/upstreams.conf

nginx -s reload
"""

    return base64.b64encode(f"""#!/bin/bash
sudo apt-get update
sudo apt-get install -y nginx 
                            
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install       
                            

cat > /etc/nginx/nginx.conf << 'EOL'
{nginx_conf}
EOL

cat > /usr/local/bin/update-nginx-conf.sh << 'EOL'
{update_script}
EOL

chmod +x /usr/local/bin/update-nginx-conf.sh
echo "* * * * * /usr/local/bin/update-nginx-conf.sh" | crontab -
/usr/local/bin/update-nginx-conf.sh
""".encode()).decode()