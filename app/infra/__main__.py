"""A minimal AWS Python Pulumi program for deploying the task application with Redis"""

import pulumi
import pulumi_aws as aws
from user_data import get_frontend_user_data, get_backend_user_data, get_db_user_data, get_redis_user_data

# Configuration
config = pulumi.Config()
db_user = config.get('database:user') or 'myuser'
db_password = config.get_secret('database:password') or 'mypassword'
db_name = config.get('database:name') or 'mydb'
region = config.get('aws:region')

# Create a VPC
vpc = aws.ec2.Vpc("minimal-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "minimal-vpc"}
)

# Create one public and one private subnet
public_subnet = aws.ec2.Subnet("public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    tags={"Name": "public-subnet"}
)

private_subnet = aws.ec2.Subnet("private-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="ap-southeast-1a",
    tags={"Name": "private-subnet"}
)

# Create a second private subnet for Redis (needed for subnet group)
private_subnet_2 = aws.ec2.Subnet("private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="ap-southeast-1b",  # Different AZ for better isolation
    tags={"Name": "private-subnet-2"}
)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("igw",
    vpc_id=vpc.id,
    tags={"Name": "minimal-igw"}
)

# Create a route table for the public subnet
public_rt = aws.ec2.RouteTable("public-rt",
    vpc_id=vpc.id,
    tags={"Name": "public-rt"}
)

# Create a route to the Internet Gateway
public_route = aws.ec2.Route("public-route",
    route_table_id=public_rt.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id
)

# Associate the public route table with the public subnet
public_rt_assoc = aws.ec2.RouteTableAssociation("public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id
)

# Create a NAT Gateway for the private subnet
eip = aws.ec2.Eip("nat-eip",
    # vpc=True,  # This is deprecated
    domain="vpc",  # This is the recommended replacement
    tags={"Name": "nat-eip"}
)

nat_gateway = aws.ec2.NatGateway("nat-gateway",
    allocation_id=eip.id,
    subnet_id=public_subnet.id,
    tags={"Name": "nat-gateway"}
)

# Create a route table for the private subnets
private_rt = aws.ec2.RouteTable("private-rt",
    vpc_id=vpc.id,
    tags={"Name": "private-rt"}
)

# Create a route to the NAT Gateway
private_route = aws.ec2.Route("private-route",
    route_table_id=private_rt.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id
)

# Associate the private route table with the private subnets
private_rt_assoc = aws.ec2.RouteTableAssociation("private-rt-assoc",
    subnet_id=private_subnet.id,
    route_table_id=private_rt.id
)

private_rt_assoc_2 = aws.ec2.RouteTableAssociation("private-rt-assoc-2",
    subnet_id=private_subnet_2.id,
    route_table_id=private_rt.id
)

# Create security groups
alb_sg = aws.ec2.SecurityGroup("alb-sg",
    vpc_id=vpc.id,
    description="Security group for ALB",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow HTTP"
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic"
        }
    ],
    tags={"Name": "alb-sg"}
)

app_sg = aws.ec2.SecurityGroup("app-sg",
    vpc_id=vpc.id,
    description="Security group for application instances",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "security_groups": [alb_sg.id],
            "description": "Allow HTTP from ALB"
        },
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "security_groups": [alb_sg.id],
            "description": "Allow API traffic from ALB"
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],  # Restrict this in production
            "description": "Allow SSH"
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic"
        }
    ],
    tags={"Name": "app-sg"}
)

db_sg = aws.ec2.SecurityGroup("db-sg",
    vpc_id=vpc.id,
    description="Security group for database",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "security_groups": [app_sg.id],
            "description": "Allow PostgreSQL from app"
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],  # Restrict this in production
            "description": "Allow SSH"
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic"
        }
    ],
    tags={"Name": "db-sg"}
)

# Create Redis security group
redis_sg = aws.ec2.SecurityGroup("redis-sg",
    vpc_id=vpc.id,
    description="Security group for Redis",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 6379,
            "to_port": 6379,
            "security_groups": [app_sg.id],
            "description": "Allow Redis traffic from app"
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],  # Restrict this in production
            "description": "Allow SSH"
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic"
        }
    ],
    tags={"Name": "redis-sg"}
)



# Create EC2 instance for PostgreSQL database instead of RDS
db_instance = aws.ec2.Instance("db-instance",
    ami='ami-01938df366ac2d954',
    instance_type="t3.micro",
    subnet_id=private_subnet.id,
    vpc_security_group_ids=[db_sg.id],
    user_data=get_db_user_data(db_user, db_password, db_name),
    tags={"Name": "postgres-db-instance"}
)

# Create EC2 instance for Redis instead of ElastiCache
redis_instance = aws.ec2.Instance("redis-instance",
    ami='ami-01938df366ac2d954',
    instance_type="t3.micro",
    subnet_id=private_subnet.id,
    vpc_security_group_ids=[redis_sg.id],
    user_data=get_redis_user_data(),
    tags={"Name": "redis-instance"}
)

# Create target groups for the ALB
frontend_tg = aws.lb.TargetGroup("frontend-tg",
    port=80,
    protocol="HTTP",
    vpc_id=vpc.id,
    health_check={
        "enabled": True,
        "path": "/",
        "port": "traffic-port",
        "protocol": "HTTP",
        "healthy_threshold": 2,
        "unhealthy_threshold": 2,
        "timeout": 5,
        "interval": 30,
        "matcher": "200-399"
    },
    tags={"Name": "frontend-tg"}
)

backend_tg = aws.lb.TargetGroup("backend-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc.id,
    health_check={
        "enabled": True,
        "path": "/health",
        "port": "traffic-port",
        "protocol": "HTTP",
        "healthy_threshold": 2,
        "unhealthy_threshold": 2,
        "timeout": 5,
        "interval": 30,
        "matcher": "200-399"
    },
    tags={"Name": "backend-tg"}
)

# Create an ALB
alb = aws.lb.LoadBalancer("app-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[public_subnet.id, private_subnet_2.id],  # Need 2 subnets for ALB
    enable_deletion_protection=False,
    tags={"Name": "app-alb"}
)

# Create ALB listeners
http_listener = aws.lb.Listener("http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[{
        "type": "forward",
        "target_group_arn": frontend_tg.arn
    }]
)

# Add a rule to route API traffic to the backend target group
api_listener_rule = aws.lb.ListenerRule("api-listener-rule",
    listener_arn=http_listener.arn,
    priority=100,
    actions=[{
        "type": "forward",
        "target_group_arn": backend_tg.arn
    }],
    conditions=[{
        "path_pattern": {
            "values": ["/tasks/*", "/health"]
        }
    }]
)

# Create EC2 instances
# ami = aws.ec2.get_ami(
#     most_recent=True,
#     owners=["amazon"],
#     filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
# )

# Frontend instance
frontend_instance = aws.ec2.Instance("frontend-instance",
    ami='ami-01938df366ac2d954',
    instance_type="t3.micro",
    subnet_id=private_subnet.id,
    vpc_security_group_ids=[app_sg.id],
    user_data=get_frontend_user_data(
        f"http://{alb.dns_name}/tasks"
    ),
    tags={"Name": "frontend-instance"}
)

# Backend instance
backend_instance = aws.ec2.Instance("backend-instance",
    ami='ami-01938df366ac2d954',
    instance_type="t3.micro",
    subnet_id=private_subnet.id,
    vpc_security_group_ids=[app_sg.id],
    user_data=get_backend_user_data(
        db_host=db_instance.private_ip,
        db_user=db_user,
        db_password=db_password,
        db_name=db_name,
        redis_host=redis_instance.private_ip
    ),
    tags={"Name": "backend-instance"}
)

# Register instances with target groups
frontend_attachment = aws.lb.TargetGroupAttachment("frontend-attachment",
    target_group_arn=frontend_tg.arn,
    target_id=frontend_instance.id,
    port=80
)

backend_attachment = aws.lb.TargetGroupAttachment("backend-attachment",
    target_group_arn=backend_tg.arn,
    target_id=backend_instance.id,
    port=8000
)

# Export outputs
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("db_endpoint", db_instance.private_ip)
pulumi.export("redis_endpoint", redis_instance.private_ip)
pulumi.export("frontend_instance_id", frontend_instance.id)
pulumi.export("backend_instance_id", backend_instance.id)
