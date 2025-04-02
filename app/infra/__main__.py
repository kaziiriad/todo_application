"""A minimal AWS Python Pulumi program for deploying the task application with Redis and Auto Scaling"""

import pulumi
import pulumi_aws as aws
from user_data import get_frontend_user_data, get_backend_user_data, get_db_user_data, get_redis_user_data
from db_scaling_user_data import db_master_user_data, db_replica_user_data
import time
import json
from redis_sentinel_config import get_redis_sentinel_user_data, get_redis_master_user_data, get_redis_replica_user_data
# Configuration
config = pulumi.Config()
db_user = config.get('database:user') or 'myuser'
db_password = config.get_secret('database:password') or 'mypassword'
db_name = config.get('database:name') or 'mydb'
redis_password = config.get_secret('redis:password') or 'myredispassword'
replication_password = config.get_secret('redis:replication_password') or 'myreplicationpassword'
region = config.get('aws:region') or 'ap-southeast-1'
docker_username = config.get('docker:username') or 'kaziiriad'  # Your DockerHub username
docker_image_version = config.get('docker:version') or 'dev_deploy'  # Your image version/tag
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
# alb_sg = aws.ec2.SecurityGroup("alb-sg",
#     vpc_id=vpc.id,
#     opts=base_opts,
#     description="Security group for public ALB",
#     ingress=[
#         {
#             "protocol": "tcp",
#             "from_port": 80,
#             "to_port": 80,
#             "cidr_blocks": ["0.0.0.0/0"],
#             "description": "Allow HTTP"
#         }
#     ],
#     egress=[
#         {
#             "protocol": "-1",
#             "from_port": 0,
#             "to_port": 0,
#             "cidr_blocks": ["0.0.0.0/0"],
#             "description": "Allow all outbound traffic"
#         }
#     ],
#     tags={"Name": "alb-sg"}
# )

# Create a security group for internal API communication
# internal_api_sg = aws.ec2.SecurityGroup("internal-api-sg",
#     vpc_id=vpc.id,
#     opts=base_opts,
#     description="Security group for internal API ALB",
#     ingress=[
#         {
#             "protocol": "tcp",
#             "from_port": 8000,
#             "to_port": 8000,
#             "cidr_blocks": ["10.0.0.0/16"],
#             "description": "Allow API traffic from within VPC"
#         }
#     ],
#     egress=[
#         {
#             "protocol": "-1",
#             "from_port": 0,
#             "to_port": 0,
#             "cidr_blocks": ["0.0.0.0/0"],
#             "description": "Allow all outbound traffic"
#         }
#     ],
#     tags={"Name": "internal-api-sg"}
# )

# Create a security group for the bastion host
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
        # {
        #     "protocol": "tcp",
        #     "from_port": 5432,
        #     "to_port": 5432,
        #     "cidr_blocks": ["10.0.0.0/16"],  # Allow from entire VPC
        #     "description": "Allow PostgreSQL from VPC"
        # },
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
            "description": "Allow Redis traffic from app"
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
db_master_instance = aws.ec2.Instance("db-instance",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]  # Force replacement when these change
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=private_subnet_1.id,  # Use private subnet
    vpc_security_group_ids=[db_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(db_user, db_password, db_name, replication_password).apply(
        lambda args: db_master_user_data(
            db_user=args[0],
            db_password=args[1],
            db_name=args[2],
            replication_password=args[3],
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
    user_data=pulumi.Output.all(db_master_instance.private_ip, replication_password).apply(
        lambda args: db_replica_user_data(
            master_ip=args[0],
            replication_password=args[1],
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
    user_data=pulumi.Output.all(redis_password).apply(
        lambda args: get_redis_master_user_data(
            redis_password=args[0]
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
    user_data=pulumi.Output.all(redis_master.private_ip, redis_password).apply(
        lambda args: get_redis_replica_user_data(
            master_ip=args[0],
            redis_password=args[1]
        )
    ),
    tags={"Name": "redis-instance", "UpdatedAt": str(time.time())},
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
    user_data=pulumi.Output.all(redis_master.private_ip, redis_password).apply(
        lambda args: get_redis_sentinel_user_data(
            master_ip=args[0],
            redis_password=args[1]
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
    subnet_id=private_subnets[i],  # Use private subnet # type: ignore
    vpc_security_group_ids=[app_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(db_master_instance.private_ip, [rs.private_ip for rs in redis_sentinels], redis_password).apply(
        lambda args: get_backend_user_data(
            db_host=args[0],
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            redis_sentinel_hosts=args[1],
            redis_sentinel_port=26379,
            redis_password=args[2],
            redis_service_name="mymaster",
            docker_username=docker_username,
            version=docker_image_version,
        )    
    ),
    tags={"Name": "backend-instance", "UpdatedAt": str(time.time())},
) for i in range(len(private_subnets))]

frontend_instance = [aws.ec2.Instance(
    f"frontend-instance-{i+1}",
    ami=ubuntu_ami.id,
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
        replace_on_changes=["user_data"]
    ),
    instance_type="t2.micro",  # Free tier eligible
    subnet_id=public_subnets[i],  # Use public subnet # type: ignore
    vpc_security_group_ids=[app_sg.id],
    key_name=KEY_PAIR,  # Change this to your key pair
    user_data=pulumi.Output.all(backend_instances[i].private_dns).apply(
        lambda args: get_frontend_user_data(
            backend_url=f"http://{args[0]}:8000",
            docker_username=docker_username,
            version=docker_image_version,
        )       
    ),
    tags={"Name": "frontend-instance", "UpdatedAt": str(time.time())},
) for i in range(len(public_subnets))]

# # Create public ALB for frontend traffic
# alb = aws.lb.LoadBalancer("app-alb",
#     internal=False,
#     load_balancer_type="application",
#     security_groups=[alb_sg.id],
#     subnets=[public_subnet_1.id, public_subnet_b.id, public_subnet_c.id],  # Use all public subnets
#     enable_deletion_protection=False,
#     opts=base_opts,
#     tags={"Name": "app-alb"}
# )

# # Create internal ALB for backend API traffic
# backend_alb = aws.lb.LoadBalancer("backend-api-alb",
#     internal=True,  # This makes it an internal ALB
#     load_balancer_type="application",
#     security_groups=[internal_api_sg.id],
#     subnets=[private_subnet_1.id, private_subnet_2.id, private_subnet_3.id],  # Use all private subnets
#     enable_deletion_protection=False,
#     opts=base_opts,
#     tags={"Name": "backend-api-alb"}
# )

# # Create target groups for the ALBs
# frontend_tg = aws.lb.TargetGroup("frontend-tg",
#     port=80,
#     protocol="HTTP",
#     vpc_id=vpc.id,
#     target_type="instance",
#     health_check={
#         "enabled": True,
#         "path": "/",
#         "port": "traffic-port",
#         "protocol": "HTTP",
#         "healthy_threshold": 2,
#         "unhealthy_threshold": 2,
#         "timeout": 5,
#         "interval": 30,
#         "matcher": "200-399"
#     },
#     opts=base_opts,
#     tags={"Name": "frontend-tg"}
# )

# backend_tg = aws.lb.TargetGroup("backend-tg",
#     port=8000,
#     protocol="HTTP",
#     vpc_id=vpc.id,
#     target_type="instance",
#     health_check={
#         "enabled": True,
#         "path": "/health",
#         "port": "traffic-port",
#         "protocol": "HTTP",
#         "healthy_threshold": 2,
#         "unhealthy_threshold": 2,
#         "timeout": 5,
#         "interval": 30,
#         "matcher": "200-399"
#     },
#     opts=base_opts,
#     tags={"Name": "backend-tg"}
# )

# Create ALB listeners
# http_listener = aws.lb.Listener("http-listener",
#     load_balancer_arn=alb.arn,
#     port=80,
#     default_actions=[{
#         "type": "forward",
#         "target_group_arn": frontend_tg.arn
#     }],
#     opts=base_opts
# )

# # Create a listener for the internal ALB
# backend_listener = aws.lb.Listener("backend-api-listener",
#     load_balancer_arn=backend_alb.arn,
#     port=8000,
#     protocol="HTTP",
#     default_actions=[{
#         "type": "forward",
#         "target_group_arn": backend_tg.arn
#     }],
#     opts=base_opts
# )

# Create launch template for frontend instances


# # Create IAM role for EC2 instances to publish CloudWatch metrics
# instance_role = aws.iam.Role("instance-role",
#     assume_role_policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Action": "sts:AssumeRole",
#             "Effect": "Allow",
#             "Principal": {
#                 "Service": "ec2.amazonaws.com"
#             }
#         }]
#     }),
#     opts=base_opts
# )

# # Create IAM policy for CloudWatch metrics
# cloudwatch_policy = aws.iam.Policy("cloudwatch-policy",
#     policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Effect": "Allow",
#                 "Action": [
#                     "cloudwatch:PutMetricData",
#                     "cloudwatch:GetMetricStatistics",
#                     "cloudwatch:ListMetrics"
#                 ],
#                 "Resource": "*"
#             },
#             {
#                 "Effect": "Allow",
#                 "Action": [
#                     "ec2:DescribeTags"
#                 ],
#                 "Resource": "*"
#             }
#         ]
#     }),
#     opts=base_opts
# )

# # Attach the policy to the role
# role_policy_attachment = aws.iam.RolePolicyAttachment("cloudwatch-policy-attachment",
#     role=instance_role.name,
#     policy_arn=cloudwatch_policy.arn,
#     opts=base_opts
# )

# # Create an instance profile for the role
# instance_profile = aws.iam.InstanceProfile("instance-profile",
#     role=instance_role.name,
#     opts=base_opts
# )
# frontend_launch_template = aws.ec2.LaunchTemplate("frontend-launch-template",
#     name_prefix="frontend-",
#     image_id=ubuntu_ami.id,
#     instance_type="t2.micro",
#     key_name=KEY_PAIR,
#     vpc_security_group_ids=[app_sg.id],
#     iam_instance_profile={
#         "name": instance_profile.name
#     },
#     user_data=pulumi.Output.all(backend_alb.dns_name).apply(
#         lambda args: get_frontend_user_data(
#             backend_url=f"http://{args[0]}:8000",
#             docker_username=docker_username,
#             version=docker_image_version
#         )
#     ),
#     block_device_mappings=[{
#         "deviceName": "/dev/sda1",
#         "ebs": {
#             "volumeSize": 8,
#             "volumeType": "gp2",
#             "deleteOnTermination": True
#         }
#     }],
#     tag_specifications=[{
#         "resourceType": "instance",
#         "tags": {
#             "Name": "frontend-instance",
#             "UpdatedAt": str(time.time())
#         }
#     }],
#     opts=pulumi.ResourceOptions(
#         provider=aws_provider,
#         depends_on=[backend_alb, instance_profile]
#     )
# )

# # Create launch template for backend instances
# backend_launch_template = aws.ec2.LaunchTemplate("backend-launch-template",
#     name_prefix="backend-",
#     image_id=ubuntu_ami.id,
#     instance_type="t2.micro",
#     key_name=KEY_PAIR,
#     vpc_security_group_ids=[app_sg.id],
#     iam_instance_profile={
#         "name": instance_profile.name
#     },
#     user_data=pulumi.Output.all(db_instance.private_ip, redis_instance.private_ip).apply(
#         lambda args: get_backend_user_data(
#             db_host=args[0],
#             db_user=db_user,
#             db_password=db_password,
#             db_name=db_name,
#             redis_host=args[1],
#             docker_username=docker_username,
#             version=docker_image_version
#         )
#     ),
#     block_device_mappings=[{
#         "deviceName": "/dev/sda1",
#         "ebs": {
#             "volumeSize": 8,
#             "volumeType": "gp2",
#             "deleteOnTermination": True
#         }
#     }],
#     tag_specifications=[{
#         "resourceType": "instance",
#         "tags": {
#             "Name": "backend-instance",
#             "UpdatedAt": str(time.time())
#         }
#     }],
#     opts=pulumi.ResourceOptions(
#         provider=aws_provider,
#         depends_on=[db_instance, redis_instance, instance_profile]
#     )
# )
# Create a service-linked role for Auto Scaling if it doesn't exist
# autoscaling_service_role = aws.iam.ServiceLinkedRole("autoscaling-service-role",
#     aws_service_name="autoscaling.amazonaws.com",
#     description="Service linked role for Auto Scaling",
#     opts=pulumi.ResourceOptions(provider=aws_provider, ignore_changes=["aws_service_name"])
# )

# # Create auto scaling group for frontend instances
# frontend_asg = aws.autoscaling.Group("frontend-asg",
#     launch_template={
#         "id": frontend_launch_template.id,
#         "version": "$Latest"
#     },
#     min_size=2,
#     max_size=5,
#     desired_capacity=2,
#     vpc_zone_identifiers=[private_subnet_1.id, private_subnet_2.id, private_subnet_3.id],
#     target_group_arns=[frontend_tg.arn],
#     health_check_type="ELB",
#     health_check_grace_period=300,
#     tags=[
#         {
#             "key": "Name",
#             "value": "frontend-asg-instance",
#             "propagateAtLaunch": True
#         }
#     ],
#     opts=pulumi.ResourceOptions(
#         provider=aws_provider,
#         depends_on=[frontend_launch_template, frontend_tg]
#     )
# )

# # Create auto scaling group for backend instances
# backend_asg = aws.autoscaling.Group("backend-asg",
#     launch_template={
#         "id": backend_launch_template.id,
#         "version": "$Latest"
#     },
#     min_size=2,
#     max_size=5,
#     desired_capacity=2,
#     vpc_zone_identifiers=[private_subnet_1.id, private_subnet_2.id, private_subnet_3.id],
#     target_group_arns=[backend_tg.arn],
#     health_check_type="ELB",
#     health_check_grace_period=300,
#     tags=[
#         {
#             "key": "Name",
#             "value": "backend-asg-instance",
#             "propagateAtLaunch": True
#         }
#     ],
#     opts=pulumi.ResourceOptions(
#         provider=aws_provider,
#         depends_on=[backend_launch_template, backend_tg]
#     )
# )

# # Create scaling policies for frontend ASG
# frontend_scale_up_policy = aws.autoscaling.Policy("frontend-scale-up-policy",
#     scaling_adjustment=1,
#     adjustment_type="ChangeInCapacity",
#     cooldown=300,
#     autoscaling_group_name=frontend_asg.name,
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# frontend_scale_down_policy = aws.autoscaling.Policy("frontend-scale-down-policy",
#     scaling_adjustment=-1,
#     adjustment_type="ChangeInCapacity",
#     cooldown=300,
#     autoscaling_group_name=frontend_asg.name,
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# # Create scaling policies for backend ASG
# backend_scale_up_policy = aws.autoscaling.Policy("backend-scale-up-policy",
#     scaling_adjustment=1,
#     adjustment_type="ChangeInCapacity",
#     cooldown=300,
#     autoscaling_group_name=backend_asg.name,
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# backend_scale_down_policy = aws.autoscaling.Policy("backend-scale-down-policy",
#     scaling_adjustment=-1,
#     adjustment_type="ChangeInCapacity",
#     cooldown=300,
#     autoscaling_group_name=backend_asg.name,
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# Create CloudWatch alarms for frontend scaling
# frontend_high_cpu_alarm = aws.cloudwatch.MetricAlarm("frontend-high-cpu-alarm",
#     comparison_operator="GreaterThanThreshold",
#     evaluation_periods=2,
#     metric_name="CPUUtilization",
#     namespace="AWS/EC2",
#     period=300,
#     statistic="Average",
#     threshold=70.0,
#     alarm_description="Scale up when CPU exceeds 70%",
#     alarm_actions=[frontend_scale_up_policy.arn],
#     dimensions={
#         "AutoScalingGroupName": frontend_asg.name
#     },
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# frontend_low_cpu_alarm = aws.cloudwatch.MetricAlarm("frontend-low-cpu-alarm",
#     comparison_operator="LessThanThreshold",
#     evaluation_periods=2,
#     metric_name="CPUUtilization",
#     namespace="AWS/EC2",
#     period=300,
#     statistic="Average",
#     threshold=30.0,
#     alarm_description="Scale down when CPU is below 30%",
#     alarm_actions=[frontend_scale_down_policy.arn],
#     dimensions={
#         "AutoScalingGroupName": frontend_asg.name
#     },
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# # Create CloudWatch alarms for backend scaling
# backend_high_cpu_alarm = aws.cloudwatch.MetricAlarm("backend-high-cpu-alarm",
#     comparison_operator="GreaterThanThreshold",
#     evaluation_periods=2,
#     metric_name="CPUUtilization",
#     namespace="AWS/EC2",
#     period=300,
#     statistic="Average",
#     threshold=70.0,
#     alarm_description="Scale up when CPU exceeds 70%",
#     alarm_actions=[backend_scale_up_policy.arn],
#     dimensions={
#         "AutoScalingGroupName": backend_asg.name
#     },
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

# backend_low_cpu_alarm = aws.cloudwatch.MetricAlarm("backend-low-cpu-alarm",
#     comparison_operator="LessThanThreshold",
#     evaluation_periods=2,
#     metric_name="CPUUtilization",
#     namespace="AWS/EC2",
#     period=300,
#     statistic="Average",
#     threshold=30.0,
#     alarm_description="Scale down when CPU is below 30%",
#     alarm_actions=[backend_scale_down_policy.arn],
#     dimensions={
#         "AutoScalingGroupName": backend_asg.name
#     },
#     opts=pulumi.ResourceOptions(provider=aws_provider)
# )

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
    pulumi.export(f"frontend_instance_{i+1}_ip", frontend_instance[i].public_ip)
    pulumi.export(f"frontend_instance_{i+1}_public_dns", frontend_instance[i].public_dns)
pulumi.export("vpc_id", vpc.id)

