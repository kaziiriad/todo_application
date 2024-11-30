"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws 

config = pulumi.Config()


from ec2 import EC2Instance
from security_groups import SecurityGroup
from vpc import VPC

KEY_PAIR_NAME = 'MyNewKeyPair'

USER_DATA = """
#!/bin/bash
# Install Docker
sudo apt-get update -y
sudo apt-get install -y docker.io
sudo usermod -aG docker $(whoami)

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl start docker
systemctl enable docker

# Create app directory
mkdir -p /home/ubuntu/app

"""

# lb_docker_compose = """
# version: '3'
# services:
#   nginx:
#     image: nginx:alpine
#     ports:
#       - "80:80"
#       - "443:443"
#     volumes:
#       - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
#     restart: always
# """


# create a VPC
vpc_module = VPC('my-vpc', cider_block='10.0.0.0/16')

# create subnets
public_subnets = vpc_module.create_subnet( # public subnets
    cidr_block='10.0.1.0/24',
    availability_zone='ap-southeast-1a',
    name='public-subnet-1'
)

private_subnets = vpc_module.create_subnet( # private subnets
    cidr_block='10.0.2.0/24',
    availability_zone='ap-southeast-1b',
    name='private-subnet-1'
)

# create route tables
public_route_table = vpc_module.create_route_table( # public route table
    name='public-route-table'

)
private_route_table = vpc_module.create_route_table( # private route table
    name='private-route-table'
)

# create gateways
internet_gateway = vpc_module.create_internet_gateway( # internet gateway
    name='my-internet-gateway'
)

nat_gateway = vpc_module.create_nat_gateway( # nat gateway
    name="my-nat-gateway",
    subnet_id=public_subnets.id
)

# create route table associations
vpc_module.create_route_table_association( # associate public route table with public subnets
    route_table_id=public_route_table.id,
    subnet_id=public_subnets.id
)

vpc_module.create_route_table_association( # associate private route table with private subnets
    route_table_id=private_route_table.id,
    subnet_id=private_subnets.id
)

# create routes
vpc_module.create_route( # route to internet gateway
    route_table_id=public_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    gateway_id=internet_gateway.id
)

vpc_module.create_route( # route to nat gateway
    route_table_id=private_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    nat_gateway_id=nat_gateway.id
)

# create security groups
backend_security_group = SecurityGroup('backend-security-group', vpc_id=vpc_module.vpc.id)
frontend_security_group = SecurityGroup('frontend-security-group', vpc_id=vpc_module.vpc.id)
lb_security_group = SecurityGroup('lb-security-group', vpc_id=vpc_module.vpc.id)
db_security_group = SecurityGroup('db-security-group', vpc_id=vpc_module.vpc.id)

lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=80,
    to_port=80,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow HTTP traffic'
)
lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=443,
    to_port=443,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow HTTPS traffic'

)
lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow SSH traffic'
)

lb_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"]
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=80,
    to_port=80,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=443,
    to_port=443,
    description='Allow HTTPS traffic',
    source_security_group_id=lb_security_group.id
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow SSH traffic',
)

frontend_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

backend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=8000,
    to_port=8000,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

backend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

backend_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

backend_security_group.create_egress_rule(
    protocol='tcp',
    from_port=5432,
    to_port=5432,
    description='Allow PostgreSQL traffic',
    source_security_group_id=db_security_group.id
)

db_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=5432,
    to_port=5432,
    description='Allow PostgreSQL traffic',
    source_security_group_id=backend_security_group.id
)

db_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)


# create instances
instance_module = EC2Instance()


# create load balancer
lb_instance = instance_module.create(
    name="nginx_load_balancer",
    number=1,
    security_groups=[lb_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=public_subnets.id,
    user_data=USER_DATA,
    associate_public_ip_address=True
    
)


# create frontend instances
frontend_instances = instance_module.create(
    name="frontend_instance",
    number=2,
    security_groups=[frontend_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=public_subnets.id,
    user_data=USER_DATA
)

backend_instances = instance_module.create(
    name='backend_instance',
    number=2,
    security_groups=[backend_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=private_subnets.id,
    user_data=USER_DATA
)

database_instance = instance_module.create(
    name='database_instance',
    number=1,
    security_groups=[db_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=private_subnets.id,
    user_data=USER_DATA
)

pulumi.export("vpc_id", vpc_module.vpc.id)
pulumi.export("load_balancer_ip", lb_instance.public_ip)
pulumi.export("frontend_instance_ips", [instance.private_ip for instance in frontend_instances])
pulumi.export("backend_instance_ips", [instance.private_ip for instance in backend_instances])
pulumi.export("database_instance_ip", database_instance.private_ip)