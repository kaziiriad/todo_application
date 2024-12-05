"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws 

from user_data import get_frontend_user_data, get_backend_user_data, get_database_user_data, get_nginx_alb_user_data
from asg import create_asg
import json

config = pulumi.Config()
db_user = config.get('database:user') or 'myuser'
db_password = config.get_secret('database:password')
db_name = config.get('database:name') or 'mydb'
region = config.get('aws:region')

from ec2 import EC2Instance
from security_groups import SecurityGroup
from vpc import VPC

KEY_PAIR_NAME = 'MyNewKeyPair3'

# Add at the beginning of __main__.py
# Create IAM role for Nginx ALB

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
public_subnets_1 = vpc_module.create_subnet( # public subnets
    cidr_block='10.0.1.0/24',
    availability_zone='ap-southeast-1a',
    name='public-subnet-1',
    map_public_ip_on_launch=True
)

public_subnets_2 = vpc_module.create_subnet( # public subnets
    cidr_block='10.0.3.0/24',
    availability_zone='ap-southeast-1b',
    name='public-subnet-2',
    map_public_ip_on_launch=True
)

private_subnets_1 = vpc_module.create_subnet( # private subnets
    cidr_block='10.0.2.0/24',
    availability_zone='ap-southeast-1a',
    name='private-subnet-1'
)

private_subnets_2 = vpc_module.create_subnet( # private subnets
    cidr_block='10.0.4.0/24',
    availability_zone='ap-southeast-1b',
    name='private-subnet-2'
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


nat_gateway_1 = vpc_module.create_nat_gateway( # nat gateway
    name="my-nat-gateway-1",
    subnet_id=public_subnets_1.id
)
# nat_gateway_2 = vpc_module.create_nat_gateway( # nat gateway
#     name="my-nat-gateway-2",
#     subnet_id=public_subnets_2.id
# )

# create route table associations
vpc_module.create_route_table_association( # associate public route table with public subnets
    name="public-1",
    route_table_id=public_route_table.id,
    subnet_id=public_subnets_1.id
)

vpc_module.create_route_table_association( # associate public route table with public subnets
    name="public-2",
    route_table_id=public_route_table.id,
    subnet_id=public_subnets_2.id
)

vpc_module.create_route_table_association( # associate private route table with private subnets
    name="private-1",    
    route_table_id=private_route_table.id,
    subnet_id=private_subnets_1.id
)

vpc_module.create_route_table_association( # associate private route table with private subnets
    name="private-2",
    route_table_id=private_route_table.id,
    subnet_id=private_subnets_2.id
)

# create routes
igw_route = vpc_module.create_route( # route to internet gateway
    name="my-internet-gateway",
    route_table_id=public_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    gateway_id=internet_gateway.id
)

nat_gw_route_1 = vpc_module.create_route( # route to nat gateway
    name="my-nat-gateway-1",
    route_table_id=private_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    nat_gateway_id=nat_gateway_1.id
)


# create security groups
app_security_group = SecurityGroup('app-security-group', vpc_id=vpc_module.vpc.id)
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
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

app_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=80,
    to_port=80,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

app_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=443,
    to_port=443,
    description='Allow HTTPS traffic',
    source_security_group_id=lb_security_group.id
)

app_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow SSH traffic',
)

app_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=8000,
    to_port=8000,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

app_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

app_security_group.create_egress_rule(
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
    source_security_group_id=app_security_group.id
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


# create frontend instances

database_instance = instance_module.create(
    name='database_instance',
    number=1,
    security_groups=[db_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=private_subnets_1.id,
    user_data=get_database_user_data(
        db_user,
        db_password,
        db_name
    )
)

nginx_alb = instance_module.create(
    name='nginx-alb',
    number=1,
    security_groups=[lb_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=public_subnets_1.id,
    user_data=get_nginx_alb_user_data(
        region    
    ),
    associate_public_ip_address=True
)



frontend_lt = aws.ec2.LaunchTemplate("frontend-lt",
    name_prefix="frontend-",
    image_id="ami-047126e50991d067b",
    instance_type="t2.micro",
    vpc_security_group_ids=[app_security_group.id],
    user_data=get_frontend_user_data(
        nginx_alb_dns=nginx_alb.private_ip,  # Use Nginx ALB DNS
    ),
    key_name=KEY_PAIR_NAME
)

backend_lt = aws.ec2.LaunchTemplate("backend-lt",
    name_prefix="backend-",
    image_id="ami-047126e50991d067b",  # Use your AMI ID
    instance_type="t2.micro",
    vpc_security_group_ids=[app_security_group.id],
    user_data=get_backend_user_data(
        database_instance.private_ip,
        db_user,
        db_password,
        db_name
    ),
    key_name=KEY_PAIR_NAME
)


frontend_asg = create_asg(
    name="frontend",
    launch_template_id=frontend_lt.id,
    vpc_zone_identifiers=[public_subnets_1.id, public_subnets_2.id],
    health_check_type="EC2",  # Changed from ELB to EC2
    health_check_grace_period=300,
    target_group_arns=None,  # If you're not using ALB target groups
    min_size=1,  # At least 1 instances for high availability
    max_size=3,  # Allow scaling up to 3 instances
    desired_capacity=2,

)

backend_asg = create_asg(
    name="backend",
    launch_template_id=backend_lt.id,
    vpc_zone_identifiers=[private_subnets_1.id, private_subnets_2.id],
    health_check_type="EC2",  # Changed from ELB to EC2
    health_check_grace_period=300,
    target_group_arns=None,
    min_size=1,  # At least 1 instances for high availability
    max_size=3,  # Allow scaling up to 3 instances
    desired_capacity=2,
)

pulumi.export("nginx_alb_1_public_ip", nginx_alb.public_ip)
pulumi.export("database_private_ip", database_instance.private_ip)
pulumi.export("frontend_asg_name", frontend_asg["asg"].name)
pulumi.export("backend_asg_name", backend_asg["asg"].name)

