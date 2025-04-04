"""A minimal AWS Python Pulumi program for deploying the task application with Redis and Auto Scaling"""

import pulumi
import pulumi_aws as aws
from new_user_data import db_instance_user_data, redis_master_instance_user_data, redis_replica_instance_user_data, redis_sentinel_instance_user_data, backend_instance_user_data, frontend_instance_user_data
from ssh_config_generator import setup_ssh_config

import time
import json

# Configuration
config = pulumi.Config()
docker_username = config.get("docker_username") or 'kaziiriad'
version = config.get("version") or 'dev_deploy'
db_user = config.get("db_user") or 'myuser'
db_password = config.get("db_password") or 'mypassword'
db_name = config.get("db_name") or 'mydb'
replication_password = config.get("replication_password") or 'mydbreplication'
redis_password = config.get("redis_password") or 'myredispassword'
redis_service_name = config.get("redis_service_name") or "mymaster"
region = config.get('aws:region') or 'ap-southeast-1'
KEY_PAIR = 'MyKeyPair' 
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

# Create subnets across multiple AZs
public_subnet_1 = aws.ec2.Subnet("public-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    opts=base_opts,
    tags={"Name": "public-subnet-a"}
)

public_subnet_2 = aws.ec2.Subnet("public-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="ap-southeast-1b",
    map_public_ip_on_launch=True,
    opts=base_opts,
    tags={"Name": "public-subnet-b"}
)

public_subnet_3 = aws.ec2.Subnet("public-subnet-c",
    vpc_id=vpc.id,
    cidr_block="10.0.5.0/24",
    availability_zone="ap-southeast-1c",
    map_public_ip_on_launch=True,
    opts=base_opts,
    tags={"Name": "public-subnet-c"}
)

private_subnet_1 = aws.ec2.Subnet("private-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="ap-southeast-1a",
    opts=base_opts,
    tags={"Name": "private-subnet-a"}
)

private_subnet_2 = aws.ec2.Subnet("private-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="ap-southeast-1b",
    opts=base_opts,
    tags={"Name": "private-subnet-b"}
)

private_subnet_3 = aws.ec2.Subnet("private-subnet-c",
    vpc_id=vpc.id,
    cidr_block="10.0.6.0/24",
    availability_zone="ap-southeast-1c",
    opts=base_opts,
    tags={"Name": "private-subnet-c"}
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

# Associate the public route table with the public subnets
public_rt_assoc_a = aws.ec2.RouteTableAssociation("public-rt-assoc-a",
    subnet_id=public_subnet_1.id,
    route_table_id=public_rt.id,
    opts=base_opts
)

public_rt_assoc_b = aws.ec2.RouteTableAssociation("public-rt-assoc-b",
    subnet_id=public_subnet_2.id,
    route_table_id=public_rt.id,
    opts=base_opts
)

public_rt_assoc_c = aws.ec2.RouteTableAssociation("public-rt-assoc-c",
    subnet_id=public_subnet_3.id,
    route_table_id=public_rt.id,
    opts=base_opts
)

# Create an Elastic IP for the NAT Gateway
nat_eip = aws.ec2.Eip("nat-eip",
    domain="vpc",
    opts=base_opts,
    tags={"Name": "nat-eip"}
)

# Create a NAT Gateway
nat_gateway = aws.ec2.NatGateway("nat-gateway",
    allocation_id=nat_eip.id,
    subnet_id=public_subnet_1.id,
    opts=base_opts,
    tags={"Name": "nat-gateway"}
)

# Create a route table for the private subnets
private_rt = aws.ec2.RouteTable("private-rt",
    vpc_id=vpc.id,
    opts=base_opts,
    tags={"Name": "private-rt"}
)

# Create a route to the NAT Gateway
private_route = aws.ec2.Route("private-route",
    route_table_id=private_rt.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id,
    opts=base_opts
)


# Associate the private route table with the private subnets
private_rt_assoc_a = aws.ec2.RouteTableAssociation("private-rt-assoc-a",
    subnet_id=private_subnet_1.id,
    route_table_id=private_rt.id,
    opts=base_opts
)

private_rt_assoc_b = aws.ec2.RouteTableAssociation("private-rt-assoc-b",
    subnet_id=private_subnet_2.id,
    route_table_id=private_rt.id,
    opts=base_opts
)

private_rt_assoc_c = aws.ec2.RouteTableAssociation("private-rt-assoc-c",
    subnet_id=private_subnet_3.id,
    route_table_id=private_rt.id,
    opts=base_opts
)

# Create security groups
bastion_sg = aws.ec2.SecurityGroup("bastion-sg",
    vpc_id=vpc.id,
    opts=base_opts,
    description="Security group for bastion host",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],  # Restrict this to your IP in production
            "description": "Allow SSH from anywhere"
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
    tags={"Name": "bastion-sg"}
)

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
            "description": "Allow HTTP from outside of the vpc"
        },
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "cidr_blocks": ["10.0.0.0/16"],  
            "description": "Allow API traffic from internal vpc"
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "security_groups": [bastion_sg.id],  # Allow SSH only from bastion
            "description": "Allow SSH from bastion host"
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
            "security_groups": [bastion_sg.id],  # Allow SSH only from bastion
            "description": "Allow SSH from bastion host"
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
            "from_port": 26379,
            "to_port": 26379,
            "security_groups": [app_sg.id],
            "description": "Allow Redis Sentinel traffic from app"
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "security_groups": [bastion_sg.id],  # Allow SSH only from bastion
            "description": "Allow SSH from bastion host"
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

# Get the latest Ubuntu 22.04 LTS AMI (free tier eligible)
ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical's owner ID
    filters=[
        {"name": "name", "values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]},
        {"name": "virtualization-type", "values": ["hvm"]},
        {"name": "state", "values": ["available"]},
        {"name": "root-device-type", "values": ["ebs"]}
    ]
)
public_subnets = [
    public_subnet_1,
    public_subnet_2,
    public_subnet_3
]
private_subnets = [
    private_subnet_1,
    private_subnet_2,
    private_subnet_3
]

# Create a bastion host in the public subnet
bastion_host = aws.ec2.Instance("bastion-host",
    ami=ubuntu_ami.id,
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnet_1.id,  # Place in public subnet
    vpc_security_group_ids=[bastion_sg.id],
    key_name=KEY_PAIR,
    associate_public_ip_address=True,  # Ensure it gets a public IP
    user_data="""#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install useful tools
apt-get install -y tmux htop vim

# Create SSH key directory
mkdir -p /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh
chown ubuntu:ubuntu /home/ubuntu/.ssh

# Copy the key from the instance to allow SSH to other instances
cp /home/ubuntu/.ssh/authorized_keys /home/ubuntu/.ssh/id_rsa
chmod 600 /home/ubuntu/.ssh/id_rsa
chown ubuntu:ubuntu /home/ubuntu/.ssh/id_rsa

# Generate a public key from the private key
ssh-keygen -y -f /home/ubuntu/.ssh/id_rsa > /home/ubuntu/.ssh/id_rsa.pub
chmod 644 /home/ubuntu/.ssh/id_rsa.pub
chown ubuntu:ubuntu /home/ubuntu/.ssh/id_rsa.pub

echo "Bastion host setup complete!"
""",
    tags={"Name": "bastion-host"},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    },
    opts=base_opts
)

# Create EC2 instance for PostgreSQL database
db_master_instance = aws.ec2.Instance("db-master-instance",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]  # Force replacement when these change
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnet_1.id,  # Use private subnet
    vpc_security_group_ids=[db_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(db_user, db_password, db_name, vpc.cidr_block, replication_password).apply(
        lambda args: db_instance_user_data(
            db_user=args[0],
            db_password=args[1],
            db_name=args[2],
            backend_subnet_cidr=args[3],
            replication_password=args[4]
        )
    ),
    tags={"Name": "postgres-db-instance", "UpdatedAt": str(time.time())},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
)

db_replica_instances = [aws.ec2.Instance(f"db-replica-instance-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[i+1].id,  # Use private subnet
    vpc_security_group_ids=[db_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(db_user, db_password, db_name, vpc.cidr_block, replication_password).apply(
        lambda args: db_instance_user_data(
            db_user=args[0],
            db_password=args[1],
            db_name=args[2],
            backend_subnet_cidr=args[3],
            replication_password=args[4]
        )
    ),
    tags={"Name": "postgres-db-replica-instance", "UpdatedAt": str(time.time())},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
) for i in range(2)]

redis_master = aws.ec2.Instance("redis-master",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[0].id,  # Use private subnet
    vpc_security_group_ids=[redis_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(redis_password, vpc.cidr_block).apply(
        lambda args: redis_master_instance_user_data(
            redis_password=args[0],
            backend_subnet_cidr=args[1]
        )
    ),
    tags={"Name": "redis-master-instance", "UpdatedAt": str(time.time())},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
)
# Create EC2 instance for Redis
redis_replicas = [aws.ec2.Instance(f"redis-replica-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[i+1].id,  # Use private subnet
    vpc_security_group_ids=[redis_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(redis_master.private_ip, redis_password, vpc.cidr_block).apply(
        lambda args: redis_replica_instance_user_data(
            master_ip=args[0],
            redis_password=args[1],
            backend_subnet_cidr=args[2]
        )
    ),
    tags={"Name": "redis-replica-instance", "UpdatedAt": str(time.time())},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
) for i in range(2)]
 

redis_sentinels = [aws.ec2.Instance(f"redis-sentinel-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[i].id,  # Use private subnet
    vpc_security_group_ids=[redis_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(redis_master.private_ip, redis_password, vpc.cidr_block).apply(
        lambda args: redis_sentinel_instance_user_data(
            master_ip=args[0],
            redis_password=args[1],
            backend_subnet_cidr=args[2]
        )
    ),
    tags={"Name": "redis-sentinel-instance", "UpdatedAt": str(time.time())},
    root_block_device={
        "volume_size": 8,  # Minimum size, free tier eligible
        "volume_type": "gp2",
        "delete_on_termination": True
    }
) for i in range(3)]


backend_instances = [aws.ec2.Instance(
    f"backend-instance-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[i].id,  # Use private subnet # type: ignore
    vpc_security_group_ids=[app_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(docker_username, version, db_master_instance.private_ip, redis_master.private_ip, [rr.private_ip for rr in redis_replicas], [rs.private_ip for rs in redis_sentinels]).apply(
        lambda args: backend_instance_user_data(
            docker_username=args[0],
            version=args[1],
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            db_host=args[2],
            redis_master_host_str=args[3],
            redis_replica_hosts_str=args[4],
            redis_sentinel_hosts_str=args[5],
            redis_sentinel_port=26379,
            redis_service_name=redis_service_name,
            redis_password=redis_password
        )
    ),
    tags={"Name": "backend-instance", "UpdatedAt": str(time.time())},
) for i in range(len(private_subnets))]

# Create frontend instances in public subnets with public IPs
frontend_instances = [aws.ec2.Instance(
    f"frontend-instance-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnets[i].id,  # Use public subnet for frontend
    vpc_security_group_ids=[app_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    associate_public_ip_address=True,  # Ensure it gets a public IP
    user_data=pulumi.Output.all(docker_username, version, backend_instances[i].private_ip).apply(
        lambda args: frontend_instance_user_data(
            docker_username=args[0],
            version=args[1],
            backend_url=args[2]
        )
    ),
    tags={"Name": "frontend-instance", "UpdatedAt": str(time.time())},
) for i in range(len(public_subnets))]

# Export outputs
pulumi.export("bastion_host_ip", bastion_host.public_ip)
pulumi.export("redis_master_ip", redis_master.private_ip)
pulumi.export("db_master_instance_ip", db_master_instance.private_ip)
for i in range(2):
    pulumi.export(f"redis_replica_{i+1}_ip", redis_replicas[i].private_ip)
    pulumi.export(f"db_replica_{i+1}_ip", db_replica_instances[i].private_ip)
for i in range(3):
    pulumi.export(f"redis_sentinel_{i+1}_ip", redis_sentinels[i].private_ip)
    pulumi.export(f"backend_instance_{i+1}_ip", backend_instances[i].private_ip)
    pulumi.export(f"frontend_instance_{i+1}_ip", frontend_instances[i].private_ip)
    pulumi.export(f"frontend_instance_{i+1}_public_dns", frontend_instances[i].public_dns)
pulumi.export("vpc_id", vpc.id)

# Generate SSH config file
setup_ssh_config(
    bastion_host=bastion_host,
    db_master=db_master_instance,
    db_replicas=db_replica_instances,
    redis_master=redis_master,
    redis_replicas=redis_replicas,
    redis_sentinels=redis_sentinels,
    backend_instances=backend_instances,
    frontend_instances=frontend_instances
)