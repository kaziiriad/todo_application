"""A minimal AWS Python Pulumi program for deploying the task application with Redis"""

import pulumi
import pulumi_aws as aws
from user_data import get_frontend_user_data, get_backend_user_data, get_db_user_data, get_redis_user_data

# Configuration
config = pulumi.Config()
db_user = config.get('database:user') or 'myuser'
db_password = config.get_secret('database:password')
db_name = config.get('database:name') or 'mydb'
region = config.get('aws:region') or 'ap-southeast-1'
docker_username = config.get('docker:username') or 'kaziiriad'  # Your DockerHub username
docker_image_version = config.get('docker:version') or 'dev_deploy'  # Your image version/tag

aws_provider = aws.Provider("aws-provider", region=region)

# Create a VPC
base_opts = pulumi.ResourceOptions(provider=aws_provider)

# Then for each resource, either use this directly:
vpc = aws.ec2.Vpc("minimal-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    opts=base_opts,
    tags={"Name": "minimal-vpc"}
)


# Create one public and one private subnet
public_subnet = aws.ec2.Subnet("public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    opts=base_opts,
    tags={"Name": "public-subnet"}
)

private_subnet = aws.ec2.Subnet("private-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="ap-southeast-1a",
    opts=base_opts,
    tags={"Name": "private-subnet"}
)

# Create a second private subnet for ALB (needed for ALB)
private_subnet_2 = aws.ec2.Subnet("private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="ap-southeast-1b",  # Different AZ for better isolation
    opts=base_opts,
    tags={"Name": "private-subnet-2"}
)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("igw",
    vpc_id=vpc.id,
    opts=base_opts,
    tags={"Name": "minimal-igw"}
)

# Create a route table for the public subnet
public_rt = aws.ec2.RouteTable("public-rt",
    vpc_id=vpc.id,
    opts=base_opts,
    tags={"Name": "public-rt"}
)

# Create a route to the Internet Gateway
public_route = aws.ec2.Route("public-route",
    route_table_id=public_rt.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,
    opts=base_opts
)

# Associate the public route table with the public subnet
public_rt_assoc = aws.ec2.RouteTableAssociation("public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id,
    opts=base_opts
)

# Create a route table for the private subnets
private_rt = aws.ec2.RouteTable("private-rt",
    vpc_id=vpc.id,
    opts=base_opts,
    tags={"Name": "private-rt"}
)

# Associate the private route table with the private subnets
private_rt_assoc = aws.ec2.RouteTableAssociation("private-rt-assoc",
    subnet_id=private_subnet.id,
    route_table_id=private_rt.id,
    opts=base_opts
)

private_rt_assoc_2 = aws.ec2.RouteTableAssociation("private-rt-assoc-2",
    subnet_id=private_subnet_2.id,
    route_table_id=private_rt.id,
    opts=base_opts
)

# Create security groups
app_sg = aws.ec2.SecurityGroup("app-sg",
    vpc_id=vpc.id,
    opts=base_opts,
    description="Security group for application instances",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow HTTP"
        },
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow API traffic"
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
    opts=base_opts,
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
    opts=base_opts,
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

# Get the latest Ubuntu 20.04 LTS AMI (free tier eligible)
ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,

    owners=["099720109477"],  # Canonical's owner ID
    filters=[
        {"name": "name", "values": ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]},
        {"name": "virtualization-type", "values": ["hvm"]}
    ]
)

# Create EC2 instance for PostgreSQL database
db_instance = aws.ec2.Instance("db-instance",
    ami=ubuntu_ami.id,
    opts=base_opts,
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnet.id,  # Use public subnet for direct access
    vpc_security_group_ids=[db_sg.id],
    user_data=get_db_user_data(db_user, db_password, db_name, private_subnet.cidr_block), # type: ignore
    tags={"Name": "postgres-db-instance"},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
)

# Create EC2 instance for Redis
redis_instance = aws.ec2.Instance("redis-instance",
    ami=ubuntu_ami.id,
    opts=base_opts,
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnet.id,  # Use public subnet for direct access
    vpc_security_group_ids=[redis_sg.id],
    user_data=get_redis_user_data(),
    tags={"Name": "redis-instance"},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
)

# Frontend instance with DockerHub image
# Backend instance with DockerHub image
backend_instance = aws.ec2.Instance("backend-instance",
    ami=ubuntu_ami.id,
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnet.id,  # Use public subnet for direct access
    vpc_security_group_ids=[app_sg.id],
    user_data=pulumi.Output.all(db_instance.public_ip, redis_instance.public_ip).apply(
        lambda args: get_backend_user_data(
            db_host=args[0],
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            redis_host=args[1],
            docker_username=docker_username,
            version=docker_image_version
        )
    ),
    tags={"Name": "backend-instance"},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    },
    opts=pulumi.ResourceOptions(
        depends_on=[db_instance, redis_instance]
    )
)

frontend_instance = aws.ec2.Instance("frontend-instance",
    ami=ubuntu_ami.id,
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnet.id,  # Use public subnet for direct access
    vpc_security_group_ids=[app_sg.id],
    user_data=pulumi.Output.all(backend_instance.public_ip).apply(
        lambda args: get_frontend_user_data(
            backend_url=f"http://{args[0]}:8000/tasks",
            docker_username=docker_username,
            version=docker_image_version
        )
    ),
    tags={"Name": "frontend-instance"},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    },
    opts=pulumi.ResourceOptions(
        depends_on=[backend_instance]
    )
)


# Export outputs
pulumi.export("frontend_url", pulumi.Output.concat("http://", frontend_instance.public_ip))
pulumi.export("backend_url", pulumi.Output.concat("http://", backend_instance.public_ip, ":8000"))
pulumi.export("db_endpoint", db_instance.public_ip)
pulumi.export("redis_endpoint", redis_instance.public_ip)
pulumi.export("frontend_instance_id", frontend_instance.id)
pulumi.export("backend_instance_id", backend_instance.id)
pulumi.export("db_instance_id", db_instance.id)
pulumi.export("redis_instance_id", redis_instance.id)